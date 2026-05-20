from __future__ import annotations

import datetime as dt
import enum
import hashlib
import json
import os
import sqlite3
from dataclasses import replace
from difflib import SequenceMatcher
from pathlib import Path
from typing import Callable, cast

from ..token_estimation import count_tokens, rough_token_count
from .memdir import ENTRYPOINT_NAME, load_memory_prompt
from .memory_conflicts import MemoryConflict, find_memory_conflict
from .memory_markdown import (
    description_for_memory as _description_for_memory,
    memory_file_path as _markdown_memory_file_path,
    memory_root as _markdown_memory_root,
    read_markdown_memory as _read_markdown_memory,
    remove_entrypoint as _markdown_remove_entrypoint,
    upsert_entrypoint as _markdown_upsert_entrypoint,
    write_memory_markdown as _write_memory_markdown,
)
from .memory_models import Memory, MemoryOperation, MemoryResult, MemoryStatus, RebuildResult, SourceType
from .memory_policy import MemoryWritePolicy, build_write_policy, memory_rank_score
from .memory_schema import initialize_memory_schema
from .memory_types import MemoryType
from .memory_utils import (
    _INACTIVE_MEMORY_STATUSES,
    coerce_float as _coerce_float,
    coerce_int as _coerce_int,
    content_hash as _content_hash,
    ensure_parent as _ensure_parent,
    fts_query_from_text as _fts_query_from_text,
    iso_now as _iso_now,
    like_pattern as _like_pattern,
    normalize_text as _normalize_text,
    parse_control_directive as _parse_control_directive,
    safe_name_from_content as _safe_name_from_content,
    scope_value as _scope_value,
    search_terms as _search_terms,
    status_value as _status_value,
    utcnow as _utcnow,
)
from .paths import get_auto_mem_path


DB_PATH = Path.home() / ".geneva" / "brain.db"
EVENTS_DIR = Path.home() / ".geneva" / "memory" / "events"
DB_PATH_ENV = "GENEVA_BRAIN_DB_PATH"
EVENTS_DIR_ENV = "GENEVA_MEMORY_EVENTS_DIR"


def _compute_trust_score(memory: "Memory") -> float:
    """Compute a trust score [0.0, 1.0] from existing memory fields."""
    import datetime as _dt

    source_weights = {
        "user_direct": 1.0,
        "assistant_inferred": 0.7,
        "tool_output": 0.5,
        "file_import": 0.6,
        "system_consolidation": 0.4,
    }
    source_w = source_weights.get(memory.source_type or "", 0.5)
    recency_score = 1.0
    try:
        created = _dt.datetime.fromisoformat((memory.created_at or "").replace("Z", "+00:00"))
        if created.tzinfo is None:
            created = created.replace(tzinfo=_dt.timezone.utc)
        age_days = max(0, (_dt.datetime.now(_dt.timezone.utc) - created).days)
        recency_score = max(0.0, 1.0 - age_days / 90.0)
    except Exception:
        pass
    evidence_bonus = 0.1 if memory.evidence_quote else 0.0
    base = (memory.confidence or 0.5) * 0.5 + source_w * 0.3 + recency_score * 0.2
    return min(1.0, base + evidence_bonus)


def _can_auto_supersede_conflict(
    *,
    conflict: MemoryConflict,
    existing: Memory,
    policy: MemoryWritePolicy,
    source_type: str,
    sensitivity: str,
    evidence_quote: str | None,
) -> bool:
    if conflict.suggested_action != "supersede":
        return False
    if source_type != "user_direct":
        return False
    if sensitivity == "restricted" or existing.sensitivity == "restricted":
        return False
    if not evidence_quote:
        return False
    if policy.confidence < 0.85:
        return False
    return policy.memory_kind in {"identity", "preference", "project", "decision", "feedback"}


def expire_stale_memories() -> int:
    """Archive memories whose validity_window_days has elapsed. Returns count expired."""
    import datetime as _dt

    init_db()
    now = _dt.datetime.now(_dt.timezone.utc)
    expired_count = 0
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, created_at, validity_window_days FROM memories "
            "WHERE status = 'active' AND validity_window_days IS NOT NULL"
        ).fetchall()
        for row in rows:
            try:
                created = _dt.datetime.fromisoformat(str(row["created_at"]).replace("Z", "+00:00"))
                if created.tzinfo is None:
                    created = created.replace(tzinfo=_dt.timezone.utc)
                age_days = (now - created).days
                if age_days >= int(row["validity_window_days"]):
                    _apply_memory_status(conn, str(row["id"]), "expired", now.strftime("%Y-%m-%dT%H:%M:%SZ"))
                    expired_count += 1
            except Exception:
                continue
    return expired_count


def _resolve_db_path(db_path: Path | None = None) -> Path:
    if db_path is not None:
        return db_path
    override = os.environ.get(DB_PATH_ENV)
    return Path(override).expanduser() if override else DB_PATH


def _resolve_events_dir(events_dir: Path | None = None) -> Path:
    if events_dir is not None:
        return events_dir
    override = os.environ.get(EVENTS_DIR_ENV)
    return Path(override).expanduser() if override else EVENTS_DIR


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    resolved = _resolve_db_path(db_path)
    _ensure_parent(resolved)
    conn = sqlite3.connect(resolved)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _memory_from_row(row: sqlite3.Row) -> Memory:
    keys = set(row.keys())
    sensitivity = row["sensitivity"] if "sensitivity" in keys else "private"
    if sensitivity not in {"public", "private", "restricted"}:
        sensitivity = "private"
    validity_window_days = row["validity_window_days"] if "validity_window_days" in keys else None
    try:
        validity_window_days = int(validity_window_days) if validity_window_days is not None else None
    except (TypeError, ValueError):
        validity_window_days = None
    return Memory(
        id=row["id"],
        path=row["path"],
        name=row["name"],
        type=row["type"],
        status=row["status"],
        content=row["content"],
        confidence=row["confidence"],
        importance=row["importance"],
        memory_kind=row["memory_kind"] if "memory_kind" in keys else row["type"],
        source_type=row["source_type"],
        source_session_id=row["source_session_id"] if "source_session_id" in keys else None,
        captured_at=row["captured_at"] if "captured_at" in keys else None,
        last_validated_at=row["last_validated_at"] if "last_validated_at" in keys else None,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        retention_days=row["retention_days"],
        expires_at=row["expires_at"],
        superseded_by=row["superseded_by"],
        scope=row["scope"],
        fts_score=float(row["fts_score"]) if "fts_score" in row.keys() else 0.0,
        evidence_quote=row["evidence_quote"] if "evidence_quote" in keys else None,
        sensitivity=sensitivity,
        validity_window_days=validity_window_days,
    )


def _memory_root(cwd: Path | None = None) -> Path:
    return _markdown_memory_root(cwd, get_auto_mem_path)


def _memory_file_path(memory_type: str, memory_id: str, name: str, cwd: Path | None = None) -> Path:
    return _markdown_memory_file_path(memory_type, memory_id, name, cwd, get_auto_mem_path)


def _upsert_entrypoint(memory: Memory, description: str, cwd: Path | None = None) -> None:
    _markdown_upsert_entrypoint(memory, description, cwd, get_auto_mem_path)


def _remove_entrypoint(path: str, cwd: Path | None = None) -> None:
    _markdown_remove_entrypoint(path, cwd, get_auto_mem_path)


def _next_memory_id(conn: sqlite3.Connection) -> str:
    import uuid as _uuid

    today = _utcnow().strftime("%Y%m%d")
    return f"mem_{today}_{_uuid.uuid4().hex[:8]}"


def init_db(db_path: Path | None = None) -> None:
    with _connect(db_path) as conn:
        initialize_memory_schema(conn, _iso_now())
        conn.commit()


def write_event(memory_id: str, event_type: str, payload: dict, db_path: Path | None = None) -> None:
    init_db(db_path)
    created_at = _iso_now()
    event_id = hashlib.sha256(f"{memory_id}:{event_type}:{created_at}".encode("utf-8")).hexdigest()[:16]
    events_dir = _resolve_events_dir()
    events_dir.mkdir(parents=True, exist_ok=True)
    event_file = events_dir / f"{_utcnow().date().isoformat()}.events.jsonl"
    record = {
        "id": event_id,
        "memory_id": memory_id,
        "event_type": event_type,
        "payload": payload,
        "created_at": created_at,
    }
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO memory_events(id, memory_id, event_type, payload, created_at) VALUES (?, ?, ?, ?, ?)",
            (event_id, memory_id, event_type, json.dumps(payload, ensure_ascii=True), created_at),
        )
        conn.commit()
    with event_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def _queue_memory_conflict(
    conn: sqlite3.Connection,
    *,
    existing: Memory,
    proposed_content: str,
    proposed_hash: str,
    policy: MemoryWritePolicy,
    source_type: str,
    conflict_type: str,
    reason: str,
    similarity: float,
    token_overlap: float,
) -> str:
    now = _iso_now()
    conflict_id = hashlib.sha256(
        f"{existing.id}:{proposed_hash}".encode("utf-8")
    ).hexdigest()[:16]
    conn.execute(
        """
        INSERT INTO memory_conflicts(
            id, existing_memory_id, proposed_content, proposed_content_hash,
            proposed_type, proposed_scope, proposed_memory_kind, proposed_source_type,
            proposed_source_session_id, proposed_confidence, proposed_importance,
            proposed_retention_days, proposed_expires_at, conflict_type, reason,
            similarity, token_overlap, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            proposed_content = excluded.proposed_content,
            reason = excluded.reason,
            similarity = excluded.similarity,
            token_overlap = excluded.token_overlap,
            updated_at = excluded.updated_at
        """,
        (
            conflict_id,
            existing.id,
            proposed_content,
            proposed_hash,
            policy.type,
            existing.scope,
            policy.memory_kind,
            source_type,
            policy.source_session_id,
            policy.confidence,
            policy.importance,
            policy.retention_days,
            policy.expires_at,
            conflict_type,
            reason,
            similarity,
            token_overlap,
            now,
            now,
        ),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO memory_edges(id, source_id, target_id, relation, confidence, created_at)
        VALUES (?, ?, ?, 'conflicts_with', ?, ?)
        """,
        (
            hashlib.sha256(f"{conflict_id}:{existing.id}".encode("utf-8")).hexdigest()[:16],
            existing.id,
            conflict_id,
            max(0.5, min(1.0, similarity)),
            now,
        ),
    )
    return conflict_id


def _apply_memory_status(
    conn: sqlite3.Connection,
    memory_id: str,
    status: MemoryStatus,
    updated_at: str,
    superseded_by: str | None = None,
) -> Memory | None:
    row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    if row is None:
        return None
    memory = _memory_from_row(row)
    updated = replace(
        memory,
        status=status,
        updated_at=updated_at,
        superseded_by=superseded_by if superseded_by is not None else memory.superseded_by,
    )
    _write_memory_markdown(updated)
    if status == "active":
        _upsert_entrypoint(updated, _description_for_memory(updated))
    else:
        _remove_entrypoint(updated.path)
    conn.execute(
        """
        UPDATE memories
        SET status = ?, updated_at = ?, indexed_at = ?, last_seen = ?, superseded_by = ?
        WHERE id = ?
        """,
        (status, updated_at, updated_at, updated_at, updated.superseded_by, memory_id),
    )
    return updated


def _rank_memories(memories: list[Memory]) -> list[Memory]:
    now = _utcnow()
    ranked: list[tuple[float, Memory]] = []
    for memory in memories:
        ts = memory.updated_at or memory.created_at
        try:
            when = dt.datetime.fromisoformat(ts)
            age_days = max(0.0, (now - when).total_seconds() / 86_400.0)
        except Exception:
            age_days = 365.0
        recency = max(0.0, 1.0 - min(age_days, 365.0) / 365.0)
        score = memory_rank_score(
            fts_score=memory.fts_score,
            recency=recency,
            confidence=memory.confidence,
            importance=memory.importance,
            memory_kind=memory.memory_kind,
        )
        ranked.append((score, memory))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in ranked]


def _fallback_like_rows(
    conn: sqlite3.Connection,
    query: str,
    sql_filters: str,
    params: list[object],
    limit: int = 10,
) -> list[sqlite3.Row]:
    terms = _search_terms(query) or [query.strip()]
    terms = [term for term in terms if term][:6]
    if not terms:
        return []
    like_parts = []
    like_params: list[object] = []
    for term in terms:
        like_parts.append("(m.name LIKE ? ESCAPE '\\' OR m.content LIKE ? ESCAPE '\\')")
        pattern = _like_pattern(term)
        like_params.extend([pattern, pattern])
    sql = f"""
        SELECT m.*, 0.2 AS fts_score
        FROM memories AS m
        WHERE {sql_filters} AND ({" OR ".join(like_parts)})
        ORDER BY COALESCE(m.updated_at, m.created_at) DESC
        LIMIT ?
    """
    return conn.execute(sql, [*params, *like_params, limit]).fetchall()


def _semantic_fallback_rows(
    conn: sqlite3.Connection,
    query: str,
    sql_filters: str,
    params: list[object],
    limit: int = 10,
) -> list[sqlite3.Row]:
    lowered = query.lower().strip()
    identity_signals = (
        "ชื่ออะไร",
        "ฉันชื่อ",
        "ผมชื่อ",
        "ชื่อของฉัน",
        "ชื่อของผม",
        "my name",
        "who am i",
        "what is my name",
    )
    work_signals = (
        "ทำงานที่ไหน",
        "ฉันทำงาน",
        "ผมทำงาน",
        "เรียนที่ไหน",
        "what do i do",
        "where do i work",
    )
    if any(signal in lowered for signal in identity_signals):
        sql = f"""
            SELECT m.*, 0.35 AS fts_score
            FROM memories AS m
            WHERE {sql_filters}
              AND m.type = 'user'
              AND m.memory_kind = 'identity'
            ORDER BY m.importance DESC, COALESCE(m.updated_at, m.created_at) DESC
            LIMIT ?
        """
        return conn.execute(sql, [*params, limit]).fetchall()
    if any(signal in lowered for signal in work_signals):
        sql = f"""
            SELECT m.*, 0.3 AS fts_score
            FROM memories AS m
            WHERE {sql_filters}
              AND m.type = 'user'
              AND m.memory_kind IN ('identity', 'preference')
            ORDER BY m.importance DESC, COALESCE(m.updated_at, m.created_at) DESC
            LIMIT ?
        """
        return conn.execute(sql, [*params, limit]).fetchall()
    return []


def search(
    query: str,
    type: str | None = None,
    scope: str | None = None,
    min_confidence: float = 0.5,
    include_archived: bool = False,
) -> list[Memory]:
    init_db()
    filters = ["m.confidence >= ?"]
    params: list[object] = [min_confidence]
    if include_archived:
        filters.append("m.status IN ('active', 'archived', 'expired', 'superseded')")
    else:
        filters.append("m.status = 'active'")
    if type:
        filters.append("m.type = ?")
        params.append(type)
    if scope is not None:
        filters.append("m.scope IS ?")
        params.append(scope)
    sql_filters = " AND ".join(filters)
    rows: list[sqlite3.Row]
    with _connect() as conn:
        if query.strip():
            rows = []
            match_query = _fts_query_from_text(query)
            if match_query:
                sql = f"""
                    SELECT m.*, (1.0 / (1.0 + abs(bm25(memory_fts)))) AS fts_score
                    FROM memory_fts
                    JOIN memories AS m ON m.rowid = memory_fts.rowid
                    WHERE memory_fts MATCH ? AND {sql_filters}
                    ORDER BY bm25(memory_fts)
                    LIMIT 10
                """
                try:
                    rows = conn.execute(sql, [match_query, *params]).fetchall()
                except sqlite3.OperationalError:
                    rows = []
            if not rows:
                rows = _fallback_like_rows(conn, query, sql_filters, params)
            if not rows:
                rows = _semantic_fallback_rows(conn, query, sql_filters, params)
        else:
            sql = f"""
                SELECT m.*, 0.0 AS fts_score
                FROM memories AS m
                WHERE {sql_filters}
                ORDER BY COALESCE(m.updated_at, m.created_at) DESC
                LIMIT 10
            """
            rows = conn.execute(sql, params).fetchall()
        memories = [_memory_from_row(row) for row in rows]
        seen = {memory.id for memory in memories}
        if seen:
            placeholders = ",".join("?" for _ in seen)
            edge_rows = conn.execute(
                f"""
                SELECT DISTINCT m.*, 0.15 AS fts_score
                FROM memory_edges e
                JOIN memories m
                  ON (m.id = e.target_id AND e.source_id IN ({placeholders}))
                  OR (m.id = e.source_id AND e.target_id IN ({placeholders}))
                WHERE m.status = 'active'
                """,
                [*seen, *seen],
            ).fetchall()
            for row in edge_rows:
                memory = _memory_from_row(row)
                if memory.id not in seen:
                    memories.append(memory)
                    seen.add(memory.id)
    results = _rank_memories(memories)

    import datetime as _dt
    import os as _os

    ghost_mode = _os.environ.get("GENEVA_GHOST") == "1"
    now = _dt.datetime.now(_dt.timezone.utc)
    filtered: list[Memory] = []
    for mem in results:
        # R2.3 stale expiry filter
        if mem.validity_window_days is not None:
            try:
                created = _dt.datetime.fromisoformat((mem.created_at or "").replace("Z", "+00:00"))
                if created.tzinfo is None:
                    created = created.replace(tzinfo=_dt.timezone.utc)
                if (now - created).days >= mem.validity_window_days:
                    continue
            except Exception:
                pass
        # R2.5 sensitivity enforcement
        if ghost_mode and mem.sensitivity == "restricted":
            continue
        # R2.4 trust score
        mem.trust_score = _compute_trust_score(mem)
        filtered.append(mem)
    results = sorted(filtered, key=lambda m: (m.trust_score or 0.0), reverse=True)
    return results


async def remember(
    content: str,
    type: str,
    source_type: str = "assistant_inferred",
    scope: str | None = None,
    memory_kind: str | None = None,
    confidence: float | None = None,
    importance: float | None = None,
    retention_days: int | None = None,
    expires_at: str | None = None,
    source_session_id: str | None = None,
    captured_at: str | None = None,
    last_validated_at: str | None = None,
    evidence_quote: str | None = None,
    sensitivity: str | None = None,
    validity_window_days: int | None = None,
    agent_caller: Callable | None = None,
) -> MemoryResult:
    del agent_caller
    init_db()
    normalized = _normalize_text(content)
    if not normalized:
        return MemoryResult(operation="noop", memory_id=None, success=True, message="Empty memory content")
    policy = build_write_policy(
        content=normalized,
        memory_type=type,
        source_type=source_type,
        scope=scope,
        memory_kind=memory_kind,
        confidence=confidence,
        importance=importance,
        retention_days=retention_days,
        expires_at=expires_at,
        source_session_id=source_session_id,
        captured_at=captured_at,
        last_validated_at=last_validated_at,
    )
    type = policy.type
    requested_sensitivity = sensitivity if sensitivity in {"public", "private", "restricted"} else None
    memory_sensitivity = requested_sensitivity or "private"
    memory_evidence_quote = evidence_quote.strip() if isinstance(evidence_quote, str) and evidence_quote.strip() else None
    try:
        memory_validity_window_days = int(validity_window_days) if validity_window_days is not None else None
    except (TypeError, ValueError):
        memory_validity_window_days = None

    supersede_target = _parse_control_directive(content, "supersedes")
    archive_target = _parse_control_directive(content, "archive")
    with _connect() as conn:
        existing_rows = conn.execute(
            """
            SELECT * FROM memories
            WHERE status = 'active' AND type = ? AND scope IS ?
            ORDER BY COALESCE(updated_at, created_at) DESC
            """,
            (type, scope),
        ).fetchall()
        existing = [_memory_from_row(row) for row in existing_rows]
        new_hash = _content_hash(normalized)
        for memory in existing:
            if _content_hash(_normalize_text(memory.content)) == new_hash:
                conn.execute(
                    "UPDATE memories SET last_seen = ?, last_validated_at = ? WHERE id = ?",
                    (_iso_now(), policy.last_validated_at, memory.id),
                )
                conn.commit()
                write_event(memory.id, "noop", {"reason": "content_hash_match"})
                return MemoryResult(operation="noop", memory_id=memory.id, success=True, message="Memory already stored")

        if archive_target:
            if _apply_memory_status(conn, archive_target, "archived", _iso_now()) is not None:
                conn.commit()
                write_event(archive_target, "archive", {"reason": "explicit_archive"})
                return MemoryResult(operation="archive", memory_id=archive_target, success=True, message="Archived memory")

        if supersede_target:
            target_row = conn.execute("SELECT * FROM memories WHERE id = ?", (supersede_target,)).fetchone()
            if target_row is not None:
                target = _memory_from_row(target_row)
                memory_id = _next_memory_id(conn)
                name, description = _safe_name_from_content(normalized, type)
                path = _memory_file_path(type, memory_id, name)
                created_at = _iso_now()
                memory = Memory(
                    id=memory_id,
                    path=str(path),
                    name=name,
                    type=type,
                    status="active",
                    content=normalized,
                    confidence=policy.confidence,
                    importance=policy.importance,
                    memory_kind=policy.memory_kind,
                    source_type=source_type,
                    source_session_id=policy.source_session_id,
                    captured_at=policy.captured_at,
                    last_validated_at=policy.last_validated_at,
                    created_at=created_at,
                    updated_at=None,
                    retention_days=policy.retention_days,
                    expires_at=policy.expires_at,
                    superseded_by=None,
                    scope=scope,
                    evidence_quote=memory_evidence_quote,
                    sensitivity=memory_sensitivity,
                    validity_window_days=memory_validity_window_days,
                )
                _write_memory_markdown(memory, description)
                _upsert_entrypoint(memory, description)
                conn.execute(
                    """
                    INSERT INTO memories(
                        id, path, name, type, status, scope, content, content_hash,
                        confidence, importance, memory_kind, source_type, source_ref,
                        source_session_id, captured_at, last_validated_at, created_at,
                        updated_at, indexed_at, last_seen, retention_days, expires_at, superseded_by,
                        evidence_quote, sensitivity, validity_window_days
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        memory.id,
                        memory.path,
                        memory.name,
                        memory.type,
                        memory.status,
                        memory.scope,
                        memory.content,
                        new_hash,
                        memory.confidence,
                        memory.importance,
                        memory.memory_kind,
                        memory.source_type,
                        None,
                        memory.source_session_id,
                        memory.captured_at,
                        memory.last_validated_at,
                        memory.created_at,
                        None,
                        created_at,
                        created_at,
                        memory.retention_days,
                        memory.expires_at,
                        None,
                        memory.evidence_quote,
                        memory.sensitivity,
                        memory.validity_window_days,
                    ),
                )
                _apply_memory_status(conn, target.id, "superseded", created_at, superseded_by=memory_id)
                conn.commit()
                write_event(memory_id, "supersede", {"supersedes": target.id})
                return MemoryResult(operation="supersede", memory_id=memory_id, success=True, message="Superseded prior memory")

        best_match: Memory | None = None
        best_ratio = 0.0
        if type != MemoryType.episodic.value:
            for memory in existing:
                ratio = SequenceMatcher(None, normalized.lower(), _normalize_text(memory.content).lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = memory

        conflict = find_memory_conflict(
            normalized,
            existing,
            memory_kind=policy.memory_kind,
            memory_type=type,
            new_confidence=policy.confidence,
        )
        if conflict is not None:
            existing_memory = next(memory for memory in existing if memory.id == conflict.existing_id)
            if _can_auto_supersede_conflict(
                conflict=conflict,
                existing=existing_memory,
                policy=policy,
                source_type=source_type,
                sensitivity=memory_sensitivity,
                evidence_quote=memory_evidence_quote,
            ):
                memory_id = _next_memory_id(conn)
                name, description = _safe_name_from_content(normalized, type)
                path = _memory_file_path(type, memory_id, name)
                created_at = _iso_now()
                memory = Memory(
                    id=memory_id,
                    path=str(path),
                    name=name,
                    type=type,
                    status="active",
                    content=normalized,
                    confidence=policy.confidence,
                    importance=policy.importance,
                    memory_kind=policy.memory_kind,
                    source_type=source_type,
                    source_session_id=policy.source_session_id,
                    captured_at=policy.captured_at,
                    last_validated_at=policy.last_validated_at,
                    created_at=created_at,
                    updated_at=None,
                    retention_days=policy.retention_days,
                    expires_at=policy.expires_at,
                    superseded_by=None,
                    scope=scope,
                    evidence_quote=memory_evidence_quote,
                    sensitivity=memory_sensitivity,
                    validity_window_days=memory_validity_window_days,
                )
                _write_memory_markdown(memory, description)
                _upsert_entrypoint(memory, description)
                conn.execute(
                    """
                    INSERT INTO memories(
                        id, path, name, type, status, scope, content, content_hash,
                        confidence, importance, memory_kind, source_type, source_ref,
                        source_session_id, captured_at, last_validated_at, created_at,
                        updated_at, indexed_at, last_seen, retention_days, expires_at, superseded_by,
                        evidence_quote, sensitivity, validity_window_days
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        memory.id,
                        memory.path,
                        memory.name,
                        memory.type,
                        memory.status,
                        memory.scope,
                        memory.content,
                        new_hash,
                        memory.confidence,
                        memory.importance,
                        memory.memory_kind,
                        memory.source_type,
                        None,
                        memory.source_session_id,
                        memory.captured_at,
                        memory.last_validated_at,
                        memory.created_at,
                        None,
                        created_at,
                        created_at,
                        memory.retention_days,
                        memory.expires_at,
                        None,
                        memory.evidence_quote,
                        memory.sensitivity,
                        memory.validity_window_days,
                    ),
                )
                _apply_memory_status(conn, existing_memory.id, "superseded", created_at, superseded_by=memory_id)
                conn.commit()
                write_event(memory_id, "supersede", {"supersedes": existing_memory.id, "reason": conflict.reason})
                return MemoryResult(
                    operation="supersede",
                    memory_id=memory_id,
                    success=True,
                    message="Superseded lower-confidence conflicting memory",
                )
            conflict_id = _queue_memory_conflict(
                conn,
                existing=existing_memory,
                proposed_content=normalized,
                proposed_hash=new_hash,
                policy=policy,
                source_type=source_type,
                conflict_type=conflict.conflict_type,
                reason=conflict.reason,
                similarity=conflict.similarity,
                token_overlap=conflict.token_overlap,
            )
            conn.commit()
            write_event(
                existing_memory.id,
                "conflict_detected",
                {
                    "conflict_id": conflict_id,
                    "conflict_type": conflict.conflict_type,
                    "reason": conflict.reason,
                    "similarity": conflict.similarity,
                    "token_overlap": conflict.token_overlap,
                    "suggested_action": conflict.suggested_action,
                },
            )
            return MemoryResult(
                operation="conflict",
                memory_id=existing_memory.id,
                success=True,
                message="Queued memory conflict for review",
                conflict_id=conflict_id,
            )

        name, description = _safe_name_from_content(normalized, type)
        now = _iso_now()
        if best_match is not None and best_ratio >= 0.82:
            updated = Memory(
                id=best_match.id,
                path=best_match.path,
                name=name,
                type=type,
                status="active",
                content=normalized,
                confidence=max(best_match.confidence, policy.confidence, 0.8),
                importance=max(best_match.importance, policy.importance),
                memory_kind=policy.memory_kind,
                source_type=source_type,
                source_session_id=policy.source_session_id or best_match.source_session_id,
                captured_at=policy.captured_at or best_match.captured_at,
                last_validated_at=policy.last_validated_at,
                created_at=best_match.created_at,
                updated_at=now,
                retention_days=max(best_match.retention_days, policy.retention_days),
                expires_at=policy.expires_at or best_match.expires_at,
                superseded_by=None,
                scope=scope,
                evidence_quote=memory_evidence_quote or best_match.evidence_quote,
                sensitivity=requested_sensitivity or best_match.sensitivity,
                validity_window_days=(
                    memory_validity_window_days
                    if memory_validity_window_days is not None
                    else best_match.validity_window_days
                ),
            )
            _write_memory_markdown(updated, description)
            _upsert_entrypoint(updated, description)
            conn.execute(
                """
                UPDATE memories
                SET name = ?, content = ?, content_hash = ?, source_type = ?, updated_at = ?,
                    indexed_at = ?, last_seen = ?, confidence = ?, importance = ?, memory_kind = ?,
                    source_session_id = ?, captured_at = ?, last_validated_at = ?,
                    retention_days = ?, expires_at = ?, scope = ?, path = ?,
                    evidence_quote = ?, sensitivity = ?, validity_window_days = ?
                WHERE id = ?
                """,
                (
                    updated.name,
                    updated.content,
                    new_hash,
                    updated.source_type,
                    now,
                    now,
                    now,
                    updated.confidence,
                    updated.importance,
                    updated.memory_kind,
                    updated.source_session_id,
                    updated.captured_at,
                    updated.last_validated_at,
                    updated.retention_days,
                    updated.expires_at,
                    updated.scope,
                    updated.path,
                    updated.evidence_quote,
                    updated.sensitivity,
                    updated.validity_window_days,
                    updated.id,
                ),
            )
            conn.commit()
            write_event(updated.id, "update", {"reason": "high_similarity", "similarity": round(best_ratio, 4)})
            return MemoryResult(operation="update", memory_id=updated.id, success=True, message="Updated similar memory")

        memory_id = _next_memory_id(conn)
        path = _memory_file_path(type, memory_id, name)
        memory = Memory(
            id=memory_id,
            path=str(path),
            name=name,
            type=type,
            status="active",
            content=normalized,
            confidence=policy.confidence,
            importance=policy.importance,
            memory_kind=policy.memory_kind,
            source_type=source_type,
            source_session_id=policy.source_session_id,
            captured_at=policy.captured_at,
            last_validated_at=policy.last_validated_at,
            created_at=now,
            updated_at=None,
            retention_days=policy.retention_days,
            expires_at=policy.expires_at,
            superseded_by=None,
            scope=scope,
            evidence_quote=memory_evidence_quote,
            sensitivity=memory_sensitivity,
            validity_window_days=memory_validity_window_days,
        )
        _write_memory_markdown(memory, description)
        _upsert_entrypoint(memory, description)
        conn.execute(
            """
            INSERT INTO memories(
                id, path, name, type, status, scope, content, content_hash,
                confidence, importance, memory_kind, source_type, source_ref,
                source_session_id, captured_at, last_validated_at, created_at,
                updated_at, indexed_at, last_seen, retention_days, expires_at, superseded_by,
                evidence_quote, sensitivity, validity_window_days
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory.id,
                memory.path,
                memory.name,
                memory.type,
                memory.status,
                memory.scope,
                memory.content,
                new_hash,
                memory.confidence,
                memory.importance,
                memory.memory_kind,
                memory.source_type,
                None,
                memory.source_session_id,
                memory.captured_at,
                memory.last_validated_at,
                memory.created_at,
                None,
                now,
                now,
                memory.retention_days,
                memory.expires_at,
                None,
                memory.evidence_quote,
                memory.sensitivity,
                memory.validity_window_days,
            ),
        )
        conn.commit()
        write_event(memory.id, "add", {"scope": scope, "type": type})
        return MemoryResult(operation="add", memory_id=memory.id, success=True, message="Stored new memory")


def update_memory(
    memory_id: str,
    content: str,
    source_type: str = "user_direct",
) -> MemoryResult:
    init_db()
    normalized = _normalize_text(content)
    if not normalized:
        return MemoryResult(operation="noop", memory_id=memory_id, success=False, message="Empty memory content")

    now = _iso_now()
    content_hash = _content_hash(normalized)
    with _connect() as conn:
        row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        if row is None:
            return MemoryResult(operation="noop", memory_id=memory_id, success=False, message="Memory not found")

        current = _memory_from_row(row)
        policy = build_write_policy(
            content=normalized,
            memory_type=current.type,
            source_type=source_type,
            scope=current.scope,
            memory_kind=current.memory_kind,
            confidence=current.confidence,
            importance=current.importance,
            retention_days=current.retention_days,
            expires_at=current.expires_at,
            source_session_id=current.source_session_id,
            captured_at=current.captured_at,
        )
        name, description = _safe_name_from_content(normalized, current.type)
        updated = replace(
            current,
            name=name,
            content=normalized,
            source_type=source_type,
            last_validated_at=policy.last_validated_at,
            updated_at=now,
        )
        _write_memory_markdown(updated, description)
        _upsert_entrypoint(updated, description)
        conn.execute(
            """
            UPDATE memories
            SET name = ?, content = ?, content_hash = ?, source_type = ?,
                updated_at = ?, indexed_at = ?, last_seen = ?, last_validated_at = ?
            WHERE id = ?
            """,
            (
                updated.name,
                updated.content,
                content_hash,
                updated.source_type,
                now,
                now,
                now,
                updated.last_validated_at,
                updated.id,
            ),
        )
        conn.commit()
    write_event(memory_id, "update", {"reason": "explicit_update"})
    return MemoryResult(operation="update", memory_id=memory_id, success=True, message="Updated memory")


def list_memory_conflicts(
    status: str = "open",
    limit: int = 50,
    offset: int = 0,
) -> dict[str, object]:
    init_db()
    conditions: list[str] = []
    params: list[object] = []
    if status and status != "all":
        conditions.append("c.status = ?")
        params.append(status)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    safe_limit = max(1, min(int(limit), 100))
    safe_offset = max(0, int(offset))
    with _connect() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM memory_conflicts c {where}",
            params,
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT c.*, m.name AS existing_name, m.content AS existing_content,
                   m.type AS existing_type, m.memory_kind AS existing_memory_kind,
                   m.scope AS existing_scope
            FROM memory_conflicts c
            LEFT JOIN memories m ON m.id = c.existing_memory_id
            {where}
            ORDER BY COALESCE(c.updated_at, c.created_at) DESC
            LIMIT ? OFFSET ?
            """,
            [*params, safe_limit, safe_offset],
        ).fetchall()
    return {
        "items": [_conflict_row_to_dict(row) for row in rows],
        "total": total,
        "has_more": safe_offset + safe_limit < total,
    }


def get_memory_conflict(conflict_id: str) -> dict[str, object] | None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT c.*, m.name AS existing_name, m.content AS existing_content,
                   m.type AS existing_type, m.memory_kind AS existing_memory_kind,
                   m.scope AS existing_scope
            FROM memory_conflicts c
            LEFT JOIN memories m ON m.id = c.existing_memory_id
            WHERE c.id = ?
            """,
            (conflict_id,),
        ).fetchone()
    return _conflict_row_to_dict(row) if row else None


def resolve_memory_conflict(
    conflict_id: str,
    resolution: str,
    merged_content: str | None = None,
) -> MemoryResult:
    init_db()
    normalized_resolution = resolution.strip().lower()
    if normalized_resolution in {"dismiss", "keep", "keep_existing"}:
        return _mark_conflict_resolved(conflict_id, "keep_existing")
    if normalized_resolution not in {"replace", "merge"}:
        return MemoryResult(
            operation="noop",
            memory_id=None,
            success=False,
            message="Invalid conflict resolution",
            conflict_id=conflict_id,
        )

    conflict = get_memory_conflict(conflict_id)
    if conflict is None:
        return MemoryResult(
            operation="noop",
            memory_id=None,
            success=False,
            message="Memory conflict not found",
            conflict_id=conflict_id,
        )
    if conflict.get("status") != "open":
        return MemoryResult(
            operation="noop",
            memory_id=str(conflict.get("existing_memory_id") or ""),
            success=False,
            message="Memory conflict is already resolved",
            conflict_id=conflict_id,
        )

    existing_memory_id = str(conflict["existing_memory_id"])
    content = (merged_content or str(conflict.get("proposed_content") or "")).strip()
    if not content:
        return MemoryResult(
            operation="noop",
            memory_id=existing_memory_id,
            success=False,
            message="Merged memory content is required",
            conflict_id=conflict_id,
        )
    result = update_memory(existing_memory_id, content, source_type="user_direct")
    if not result.success:
        return MemoryResult(
            operation=result.operation,
            memory_id=result.memory_id,
            success=False,
            message=result.message,
            conflict_id=conflict_id,
        )
    _mark_conflict_resolved(conflict_id, normalized_resolution, resolved_memory_id=existing_memory_id)
    return MemoryResult(
        operation="update",
        memory_id=existing_memory_id,
        success=True,
        message="Resolved memory conflict",
        conflict_id=conflict_id,
    )


def _mark_conflict_resolved(
    conflict_id: str,
    resolution: str,
    resolved_memory_id: str | None = None,
) -> MemoryResult:
    init_db()
    now = _iso_now()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM memory_conflicts WHERE id = ?", (conflict_id,)).fetchone()
        if row is None:
            return MemoryResult(
                operation="noop",
                memory_id=None,
                success=False,
                message="Memory conflict not found",
                conflict_id=conflict_id,
            )
        memory_id = resolved_memory_id or row["existing_memory_id"]
        conn.execute(
            """
            UPDATE memory_conflicts
            SET status = 'resolved', resolution = ?, resolved_memory_id = ?,
                resolved_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (resolution, memory_id, now, now, conflict_id),
        )
        conn.commit()
    write_event(
        str(memory_id),
        "conflict_resolved",
        {"conflict_id": conflict_id, "resolution": resolution},
    )
    return MemoryResult(
        operation="noop",
        memory_id=str(memory_id),
        success=True,
        message="Resolved memory conflict",
        conflict_id=conflict_id,
    )


def _conflict_row_to_dict(row: sqlite3.Row) -> dict[str, object]:
    return {key: row[key] for key in row.keys()}


def set_memory_status(
    memory_id: str,
    status: MemoryStatus,
    reason: str,
) -> MemoryResult:
    if status not in {"active", "archived", "expired", "superseded", "deleted"}:
        return MemoryResult(operation="noop", memory_id=memory_id, success=False, message="Invalid memory status")
    init_db()
    now = _iso_now()
    with _connect() as conn:
        updated = _apply_memory_status(conn, memory_id, status, now)
        if updated is None:
            return MemoryResult(operation="noop", memory_id=memory_id, success=False, message="Memory not found")
        conn.commit()

    event_type = {
        "archived": "archive",
        "deleted": "delete",
        "expired": "expire",
        "superseded": "supersede",
    }.get(status, "update")
    write_event(memory_id, event_type, {"reason": reason, "status": status})
    operation: MemoryOperation = "delete" if status == "deleted" else "archive" if status == "archived" else "update"
    return MemoryResult(operation=operation, memory_id=memory_id, success=True, message=f"Set status to {status}")


def refresh_context(
    session_query: str,
    max_tokens: int = 3000,
    scope: str | None = None,
    include_identity_files: bool = True,
) -> str:
    blocks: list[tuple[str, str]] = []

    if include_identity_files:
        try:
            from src.geneva.runtime_identity import load_runtime_identity_blocks

            for identity_block in load_runtime_identity_blocks():
                content = _memory_section_content(identity_block.label, identity_block.text)
                if content:
                    blocks.append((identity_block.label, content))
        except Exception:
            pass

    base_memory = load_memory_prompt()
    if base_memory:
        blocks.append(("Core Memory", base_memory))

    root = _memory_root()
    _workspace_dir_env = os.environ.get("GENEVA_WORKSPACE_DIR", "")
    _workspace_root = Path(_workspace_dir_env).expanduser() if _workspace_dir_env else Path.home() / "Documents" / "Geneva"

    # Relevant memories — inject before DNA files so scoped results aren't cut by token budget
    _query = session_query.strip()
    if _query:
        _scoped = search(_query, scope=scope) if scope is not None else []
        _global = search(_query, scope=None)
        _results = _dedupe_memories([*_scoped, *_global])
        if _results:
            _durable = [m for m in _results if m.type != MemoryType.episodic.value]
            _episodes = [m for m in _results if m.type == MemoryType.episodic.value]
            if _durable:
                blocks.append(("Relevant Memories", "\n".join(_render_memory_hit(m) for m in _durable[:8])))
            if _episodes:
                blocks.append(("Relevant Closed Chats", "\n".join(_render_memory_hit(m) for m in _episodes[:3])))

    # decisions/log.md — last 50 non-empty lines only
    _log_candidates = [
        root / "decisions" / "log.md",
        root / "decisions_log.md",
        _workspace_root / "decisions" / "log.md",
    ]
    for _log_path in _log_candidates:
        if _log_path.exists():
            try:
                _log_lines = [l for l in _log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
                _log_tail = "\n".join(_log_lines[-50:]).strip()
            except OSError:
                break
            if _log_tail:
                blocks.append(("decisions/log.md (recent)", _log_tail))
            break

    try:
        from ..services.session_memory.session_memory import get_current_session_memory

        cache = get_current_session_memory()
        prompt_text = cache.get("prompt", "")
        if prompt_text:
            blocks.append(("Recent Session Memory", prompt_text))
    except Exception:
        pass

    lines = ["### MEMORY"]
    budget_used = rough_token_count(lines[0])
    for heading, content in blocks:
        section = f"## {heading}\n{content.strip()}"
        token_count = count_tokens(section)
        if budget_used + token_count > max_tokens:
            remaining_tokens = max(0, max_tokens - budget_used - count_tokens(f"## {heading}\n"))
            if remaining_tokens <= 0:
                continue
            max_chars = max(0, remaining_tokens * 4)
            section = f"## {heading}\n{content.strip()[:max_chars].rstrip()}"
            token_count = count_tokens(section)
        lines.append(section)
        budget_used += token_count
        if budget_used >= max_tokens:
            break
    lines.append("### END MEMORY")
    return "\n".join(lines)


def _memory_section_content(label: str, text: str) -> str:
    content = text.strip()
    heading = f"## {label}"
    if content.startswith(heading):
        return content[len(heading):].lstrip()
    return content


def _dedupe_memories(memories: list[Memory]) -> list[Memory]:
    seen: set[str] = set()
    result: list[Memory] = []
    for memory in memories:
        if memory.id in seen:
            continue
        result.append(memory)
        seen.add(memory.id)
    return result


def _render_memory_hit(memory: Memory) -> str:
    scope = f" scope={memory.scope}" if memory.scope else ""
    return f"- [{memory.memory_kind}/{memory.type}{scope}] {memory.name}: {memory.content}"


def rebuild_index(
    vault_path: Path | None = None,
    force: bool = False,
) -> RebuildResult:
    init_db()
    root = (vault_path or _memory_root()).expanduser()
    if not root.exists():
        return RebuildResult(files_scanned=0, files_updated=0, errors=[])

    files_scanned = 0
    files_updated = 0
    errors: list[str] = []
    now = _iso_now()
    with _connect() as conn:
        for path in sorted(root.rglob("*.md")):
            if path.name == ENTRYPOINT_NAME:
                continue
            files_scanned += 1
            try:
                frontmatter, body = _read_markdown_memory(path)
            except Exception as exc:
                errors.append(f"{path}: {exc}")
                continue
            memory_id = str(frontmatter.get("id") or path.stem)
            content = _normalize_text(body)
            content_hash = _content_hash(content)
            status = _status_value(frontmatter.get("status"))
            record_policy = build_write_policy(
                content=content,
                memory_type=str(frontmatter.get("type") or MemoryType.reference.value),
                source_type=str(frontmatter.get("source_type") or "file_import"),
                scope=_scope_value(frontmatter.get("scope")),
                memory_kind=_scope_value(frontmatter.get("memory_kind")),
                confidence=_coerce_float(frontmatter.get("confidence"), 0.9),
                importance=_coerce_float(frontmatter.get("importance"), 0.5),
                retention_days=_coerce_int(frontmatter.get("retention_days"), 365),
                expires_at=_scope_value(frontmatter.get("expires_at")),
                source_session_id=_scope_value(frontmatter.get("source_session_id")),
                captured_at=_scope_value(frontmatter.get("captured_at")),
                last_validated_at=_scope_value(frontmatter.get("last_validated_at")),
            )
            existing = conn.execute(
                "SELECT content_hash, status FROM memories WHERE id = ?",
                (memory_id,),
            ).fetchone()
            status_repair_needed = False
            if existing is not None:
                existing_status = _status_value(existing["status"])
                if existing_status in _INACTIVE_MEMORY_STATUSES and status == "active":
                    status = existing_status
                    status_repair_needed = True
            if (
                existing is not None
                and existing["content_hash"] == content_hash
                and existing["status"] == status
                and not force
                and not status_repair_needed
            ):
                if status != "active":
                    _remove_entrypoint(str(path))
                continue
            files_updated += 1
            record = {
                "id": memory_id,
                "path": str(path),
                "name": str(frontmatter.get("name") or path.stem),
                "type": record_policy.type,
                "status": status,
                "scope": _scope_value(frontmatter.get("scope")),
                "content": content,
                "content_hash": content_hash,
                "confidence": record_policy.confidence,
                "importance": record_policy.importance,
                "memory_kind": record_policy.memory_kind,
                "source_type": str(frontmatter.get("source_type") or "file_import"),
                "source_ref": None,
                "source_session_id": record_policy.source_session_id,
                "captured_at": record_policy.captured_at,
                "last_validated_at": record_policy.last_validated_at,
                "created_at": str(frontmatter.get("created_at") or now),
                "updated_at": _scope_value(frontmatter.get("updated_at")),
                "indexed_at": now,
                "last_seen": now,
                "retention_days": record_policy.retention_days,
                "expires_at": record_policy.expires_at,
                "superseded_by": _scope_value(frontmatter.get("superseded_by")),
            }
            conn.execute(
                """
                INSERT INTO memories(
                    id, path, name, type, status, scope, content, content_hash,
                    confidence, importance, memory_kind, source_type, source_ref,
                    source_session_id, captured_at, last_validated_at, created_at,
                    updated_at, indexed_at, last_seen, retention_days, expires_at, superseded_by
                ) VALUES (
                    :id, :path, :name, :type, :status, :scope, :content, :content_hash,
                    :confidence, :importance, :memory_kind, :source_type, :source_ref,
                    :source_session_id, :captured_at, :last_validated_at, :created_at,
                    :updated_at, :indexed_at, :last_seen, :retention_days, :expires_at, :superseded_by
                )
                ON CONFLICT(id) DO UPDATE SET
                    path = excluded.path,
                    name = excluded.name,
                    type = excluded.type,
                    status = excluded.status,
                    scope = excluded.scope,
                    content = excluded.content,
                    content_hash = excluded.content_hash,
                    confidence = excluded.confidence,
                    importance = excluded.importance,
                    memory_kind = excluded.memory_kind,
                    source_type = excluded.source_type,
                    source_session_id = excluded.source_session_id,
                    captured_at = excluded.captured_at,
                    last_validated_at = excluded.last_validated_at,
                    updated_at = excluded.updated_at,
                    indexed_at = excluded.indexed_at,
                    last_seen = excluded.last_seen,
                    retention_days = excluded.retention_days,
                    expires_at = excluded.expires_at,
                    superseded_by = excluded.superseded_by
                """,
                record,
            )
            if status_repair_needed:
                memory = Memory(
                    id=record["id"],
                    path=record["path"],
                    name=record["name"],
                    type=record["type"],
                    status=cast(MemoryStatus, record["status"]),
                    scope=record["scope"],
                    content=record["content"],
                    confidence=record["confidence"],
                    importance=record["importance"],
                    memory_kind=record["memory_kind"],
                    source_type=record["source_type"],
                    source_session_id=record["source_session_id"],
                    captured_at=record["captured_at"],
                    last_validated_at=record["last_validated_at"],
                    created_at=record["created_at"],
                    updated_at=record["updated_at"],
                    retention_days=record["retention_days"],
                    expires_at=record["expires_at"],
                    superseded_by=record["superseded_by"],
                )
                description = _scope_value(frontmatter.get("description"))
                _write_memory_markdown(memory, description)
            if status != "active":
                _remove_entrypoint(str(path))
        conn.commit()
    write_event("__rebuild__", "reindex", {"root": str(root), "force": force, "files_updated": files_updated})
    return RebuildResult(files_scanned=files_scanned, files_updated=files_updated, errors=errors)


def privacy_delete(
    memory_id: str,
    requester: str,
    reason: str,
) -> None:
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        if row is None:
            return
        memory = _memory_from_row(row)
        path = Path(memory.path)
        tombstone = replace(
            memory,
            status="deleted",
            content=f"[DELETED - privacy request {_utcnow().date().isoformat()}]",
            updated_at=_iso_now(),
        )
        _write_memory_markdown(tombstone, "Privacy deleted memory")
        conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
    _remove_entrypoint(str(path))
    write_event(memory_id, "privacy_delete", {"requester": requester, "reason": reason})
