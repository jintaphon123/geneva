from __future__ import annotations

import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from src.memdir.brain_engine import init_db, set_memory_status
from src.memdir.memory_utils import iso_now

WRITE_TYPES = {"auto_saved", "draft", "explicit", "imported"}
EVENT_STATUSES = {"saved", "draft", "undone", "dismissed", "edited"}
SENSITIVITY_LEVELS = {"public", "private", "restricted"}


def _db_path() -> Path:
    override = os.environ.get("GENEVA_BRAIN_DB_PATH")
    return Path(override).expanduser() if override else Path.home() / ".geneva" / "brain.db"


def _conn() -> sqlite3.Connection:
    init_db(_db_path())
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _memory_row(memory_id: str) -> sqlite3.Row | None:
    with _conn() as conn:
        return conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()


def _truncate(text: object, max_chars: int = 320) -> str:
    value = str(text or "").strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip() + "…"


def _default_status(
    *,
    write_type: str,
    confidence: float | None,
    sensitivity: str,
    explicit_status: str | None,
) -> str:
    if explicit_status in EVENT_STATUSES:
        return explicit_status
    if write_type == "draft" or sensitivity == "restricted":
        return "draft"
    if confidence is not None and confidence < 0.7:
        return "draft"
    return "saved"


def record_memory_write_event(
    *,
    memory_id: str,
    session_id: str | None = None,
    turn_id: str | None = None,
    project_id: str | None = None,
    write_type: str = "auto_saved",
    confidence: float | None = None,
    sensitivity: str | None = None,
    user_visible_text: str | None = None,
    source_excerpt: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    memory = _memory_row(memory_id)
    if memory is None:
        raise ValueError(f"Memory not found: {memory_id}")

    normalized_write_type = write_type if write_type in WRITE_TYPES else "auto_saved"
    normalized_sensitivity = sensitivity if sensitivity in SENSITIVITY_LEVELS else str(memory["sensitivity"] or "private")
    if normalized_sensitivity not in SENSITIVITY_LEVELS:
        normalized_sensitivity = "private"
    event_confidence = confidence if confidence is not None else memory["confidence"]
    event_status = _default_status(
        write_type=normalized_write_type,
        confidence=event_confidence,
        sensitivity=normalized_sensitivity,
        explicit_status=status,
    )
    now = iso_now()
    event_id = f"mwe_{uuid.uuid4().hex[:12]}"
    visible = _truncate(user_visible_text or memory["content"])
    excerpt = _truncate(source_excerpt or memory["evidence_quote"] or memory["content"], 240)
    resolved_project_id = project_id if project_id is not None else memory["scope"]

    if event_status == "draft":
        set_memory_status(memory_id, "archived", reason="memory_write_review_draft")

    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO memory_write_events(
                id, memory_id, session_id, turn_id, project_id, write_type,
                confidence, sensitivity, user_visible_text, source_excerpt,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                memory_id,
                session_id,
                turn_id,
                resolved_project_id,
                normalized_write_type,
                event_confidence,
                normalized_sensitivity,
                visible,
                excerpt,
                event_status,
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM memory_write_events WHERE id = ?", (event_id,)).fetchone()
    return _row_to_dict(row)


def list_memory_write_events(
    *,
    session_id: str | None = None,
    memory_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    conditions: list[str] = []
    params: list[Any] = []
    if session_id:
        conditions.append("session_id = ?")
        params.append(session_id)
    if memory_id:
        conditions.append("memory_id = ?")
        params.append(memory_id)
    if status and status != "all":
        conditions.append("status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    bounded_limit = max(1, min(int(limit), 100))
    bounded_offset = max(0, int(offset))
    with _conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM memory_write_events {where}", params).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT * FROM memory_write_events
            {where}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            [*params, bounded_limit, bounded_offset],
        ).fetchall()
    return {
        "items": [_row_to_dict(row) for row in rows],
        "total": total,
        "has_more": bounded_offset + bounded_limit < total,
    }


def get_memory_write_event(event_id: str) -> dict[str, Any] | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM memory_write_events WHERE id = ?", (event_id,)).fetchone()
    return _row_to_dict(row) if row else None


def _set_event_status(event_id: str, status: str) -> dict[str, Any] | None:
    now = iso_now()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM memory_write_events WHERE id = ?", (event_id,)).fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE memory_write_events SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, event_id),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM memory_write_events WHERE id = ?", (event_id,)).fetchone()
    return _row_to_dict(updated)


def undo_memory_write_event(event_id: str) -> dict[str, Any] | None:
    event = get_memory_write_event(event_id)
    if event is None:
        return None
    set_memory_status(str(event["memory_id"]), "archived", reason="memory_write_undo")
    return _set_event_status(event_id, "undone")


def approve_memory_write_event(event_id: str) -> dict[str, Any] | None:
    event = get_memory_write_event(event_id)
    if event is None:
        return None
    set_memory_status(str(event["memory_id"]), "active", reason="memory_write_approve")
    return _set_event_status(event_id, "saved")


def record_memory_revision(
    *,
    memory_id: str,
    previous_content: str,
    new_content: str,
    edited_by: str = "user",
    reason: str | None = None,
) -> dict[str, Any]:
    if _memory_row(memory_id) is None:
        raise ValueError(f"Memory not found: {memory_id}")
    revision_id = f"mrev_{uuid.uuid4().hex[:12]}"
    now = iso_now()
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO memory_revisions(
                id, memory_id, previous_content, new_content, edited_by, reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                revision_id,
                memory_id,
                previous_content,
                new_content,
                edited_by,
                reason,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM memory_revisions WHERE id = ?", (revision_id,)).fetchone()
    return _row_to_dict(row)

