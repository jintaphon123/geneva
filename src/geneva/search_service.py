from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from src.memdir.brain_engine import _connect, init_db

SEARCH_TYPES = {"chat", "project", "memory", "source", "research_report"}


@dataclass
class SearchResult:
    id: str
    type: str
    title: str
    snippet: str
    matched_fields: list[str]
    score: float
    scope: str = "global"
    project_id: str | None = None
    session_id: str | None = None
    source_id: str | None = None
    artifact_id: str | None = None
    badges: list[str] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def full_brain_search(
    query: str,
    *,
    types: Iterable[str] | str | None = None,
    project_id: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Search Geneva's lean product-brain corpus and return grouped results."""
    clean_query = query.strip()
    safe_limit = _safe_limit(limit)
    selected_types = _normalize_types(types)
    if not clean_query:
        return _empty_payload(clean_query, safe_limit)

    _ensure_search_tables()
    results: list[SearchResult] = []
    with _connect() as conn:
        if "chat" in selected_types:
            results.extend(_search_chats(conn, clean_query, project_id, safe_limit))
        if "project" in selected_types:
            results.extend(_search_projects(conn, clean_query, project_id, safe_limit))
        if "memory" in selected_types:
            results.extend(_search_memories(conn, clean_query, project_id, safe_limit))
        if "source" in selected_types:
            results.extend(_search_sources(conn, clean_query, project_id, safe_limit))
        if "research_report" in selected_types:
            results.extend(_search_research_reports(conn, clean_query, project_id, safe_limit))

    ordered = sorted(
        results,
        key=lambda result: (result.score, result.created_at or ""),
        reverse=True,
    )[:safe_limit]
    return _payload(clean_query, ordered, safe_limit)


def search_suggestions(
    query: str,
    *,
    project_id: str | None = None,
    limit: int = 8,
) -> dict[str, Any]:
    payload = full_brain_search(query, project_id=project_id, limit=limit)
    suggestions = [
        {
            "id": result["id"],
            "type": result["type"],
            "title": result["title"],
            "snippet": result["snippet"],
            "project_id": result["project_id"],
            "session_id": result["session_id"],
            "source_id": result["source_id"],
            "artifact_id": result["artifact_id"],
            "badges": result["badges"],
            "actions": result["actions"][:1],
        }
        for result in payload["results"]
    ]
    return {
        "query": payload["query"],
        "suggestions": suggestions,
        "count": len(suggestions),
        "limit": payload["limit"],
    }


def _empty_payload(query: str, limit: int) -> dict[str, Any]:
    return {"query": query, "results": [], "groups": {}, "count": 0, "limit": limit}


def _payload(query: str, results: list[SearchResult], limit: int) -> dict[str, Any]:
    result_dicts = [result.to_dict() for result in results]
    groups: dict[str, dict[str, Any]] = {}
    for result in result_dicts:
        result_type = result["type"]
        group = groups.setdefault(
            result_type,
            {"type": result_type, "count": 0, "results": []},
        )
        group["count"] += 1
        group["results"].append(result)
    return {
        "query": query,
        "results": result_dicts,
        "groups": groups,
        "count": len(result_dicts),
        "limit": limit,
    }


def _ensure_search_tables() -> None:
    init_db()
    for factory in (_ensure_projects, _ensure_sources, _ensure_research_runs):
        try:
            factory()
        except Exception:
            continue


def _ensure_projects() -> None:
    from src.geneva.project_store import ProjectStore

    ProjectStore()


def _ensure_sources() -> None:
    from src.geneva.project_sources import ProjectSourceStore

    ProjectSourceStore()


def _ensure_research_runs() -> None:
    from src.geneva.research_runs import ResearchRunStore

    ResearchRunStore()


def _safe_limit(limit: int) -> int:
    try:
        value = int(limit)
    except (TypeError, ValueError):
        value = 20
    return max(1, min(value, 100))


def _normalize_types(types: Iterable[str] | str | None) -> set[str]:
    if types is None:
        return set(SEARCH_TYPES)
    if isinstance(types, str):
        raw = types.split(",")
    else:
        raw = list(types)
    selected = {str(item).strip().lower() for item in raw if str(item).strip()}
    valid = selected & SEARCH_TYPES
    return valid or set(SEARCH_TYPES)


def _like(query: str) -> str:
    escaped = (
        query.lower()
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    return f"%{escaped}%"


def _matches(query: str, *values: str | None) -> bool:
    needle = query.lower()
    return any(needle in str(value or "").lower() for value in values)


def _matched_fields(query: str, fields: dict[str, str | None]) -> list[str]:
    needle = query.lower()
    return [
        name
        for name, value in fields.items()
        if needle in str(value or "").lower()
    ]


def _score(query: str, fields: dict[str, str | None], *, base: float) -> float:
    needle = query.lower()
    score = base
    for name, value in fields.items():
        text = str(value or "").lower()
        if not text or needle not in text:
            continue
        if name in {"title", "name", "query"}:
            score += 20
        else:
            score += 10
        score += min(5.0, len(needle) / max(1, len(text)) * 50)
    return round(score, 4)


def _snippet(text: str | None, query: str, *, max_chars: int = 220) -> str:
    clean_text = " ".join(str(text or "").split())
    if not clean_text:
        return ""
    index = clean_text.lower().find(query.lower())
    if index < 0:
        return clean_text[:max_chars].rstrip()
    start = max(0, index - 70)
    end = min(len(clean_text), index + len(query) + 140)
    snippet = clean_text[start:end].strip()
    if start > 0:
        snippet = f"...{snippet}"
    if end < len(clean_text):
        snippet = f"{snippet}..."
    return snippet


def _scope(project_id: str | None) -> str:
    return f"project:{project_id}" if project_id else "global"


def _json_loads(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _read_snapshot(path: str | None) -> str:
    if not path:
        return ""
    try:
        snapshot_path = Path(path)
        if not snapshot_path.exists():
            return ""
        return snapshot_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _search_chats(
    conn: sqlite3.Connection,
    query: str,
    project_id: str | None,
    limit: int,
) -> list[SearchResult]:
    if not _table_exists(conn, "session_transcripts"):
        return []
    filters = ["ghost_mode=0", "LOWER(content) LIKE ? ESCAPE '\\'"]
    params: list[Any] = [_like(query)]
    if project_id:
        filters.append("project_id=?")
        params.append(project_id)
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT id, session_id, project_id, role, content, model, created_at
        FROM session_transcripts
        WHERE {' AND '.join(filters)}
        ORDER BY created_at DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    results: list[SearchResult] = []
    for row in rows:
        content = str(row["content"] or "")
        fields = {"content": content, "role": str(row["role"] or "")}
        results.append(
            SearchResult(
                id=str(row["id"]),
                type="chat",
                title=f"Chat {row['session_id']}",
                snippet=_snippet(content, query),
                matched_fields=_matched_fields(query, fields),
                score=_score(query, fields, base=45),
                scope=_scope(row["project_id"]),
                project_id=row["project_id"],
                session_id=str(row["session_id"]),
                badges=["chat", str(row["role"] or "turn")],
                actions=[
                    {
                        "id": "open_chat",
                        "label": "Open chat",
                        "session_id": str(row["session_id"]),
                    }
                ],
                created_at=str(row["created_at"] or ""),
                metadata={"role": row["role"], "model": row["model"]},
            )
        )
    return results


def _search_projects(
    conn: sqlite3.Connection,
    query: str,
    project_id: str | None,
    limit: int,
) -> list[SearchResult]:
    if not _table_exists(conn, "projects"):
        return []
    like = _like(query)
    filters = [
        "archived=0",
        "(LOWER(name) LIKE ? ESCAPE '\\' OR LOWER(description) LIKE ? ESCAPE '\\' OR LOWER(context_md) LIKE ? ESCAPE '\\')",
    ]
    params: list[Any] = [like, like, like]
    if project_id:
        filters.append("id=?")
        params.append(project_id)
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT id, name, description, context_md, color, pinned, created_at, updated_at
        FROM projects
        WHERE {' AND '.join(filters)}
        ORDER BY updated_at DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    results: list[SearchResult] = []
    for row in rows:
        description = str(row["description"] or row["context_md"] or "")
        fields = {
            "name": str(row["name"] or ""),
            "description": str(row["description"] or ""),
            "context_md": str(row["context_md"] or ""),
        }
        results.append(
            SearchResult(
                id=str(row["id"]),
                type="project",
                title=str(row["name"] or "Untitled project"),
                snippet=_snippet(description or row["name"], query),
                matched_fields=_matched_fields(query, fields),
                score=_score(query, fields, base=50),
                scope=_scope(str(row["id"])),
                project_id=str(row["id"]),
                badges=["project"],
                actions=[
                    {
                        "id": "open_project",
                        "label": "Open project",
                        "project_id": str(row["id"]),
                    }
                ],
                created_at=str(row["updated_at"] or row["created_at"] or ""),
                metadata={"color": row["color"], "pinned": bool(row["pinned"])},
            )
        )
    return results


def _search_memories(
    conn: sqlite3.Connection,
    query: str,
    project_id: str | None,
    limit: int,
) -> list[SearchResult]:
    if not _table_exists(conn, "memories"):
        return []
    like = _like(query)
    filters = [
        "status='active'",
        "(LOWER(name) LIKE ? ESCAPE '\\' OR LOWER(content) LIKE ? ESCAPE '\\')",
    ]
    params: list[Any] = [like, like]
    if project_id:
        filters.append("scope=?")
        params.append(project_id)
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT id, path, name, type, scope, content, confidence, importance,
               memory_kind, source_type, created_at, updated_at
        FROM memories
        WHERE {' AND '.join(filters)}
        ORDER BY importance DESC, updated_at DESC, created_at DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    results: list[SearchResult] = []
    for row in rows:
        fields = {"name": row["name"], "content": row["content"]}
        project_scope = row["scope"] if row["scope"] else None
        results.append(
            SearchResult(
                id=str(row["id"]),
                type="memory",
                title=str(row["name"] or "Memory"),
                snippet=_snippet(row["content"], query),
                matched_fields=_matched_fields(query, fields),
                score=_score(query, fields, base=55) + float(row["importance"] or 0),
                scope=_scope(project_scope),
                project_id=project_scope,
                badges=["memory", str(row["memory_kind"] or row["type"] or "reference")],
                actions=[
                    {
                        "id": "review_memory",
                        "label": "Review memory",
                        "memory_id": str(row["id"]),
                    },
                    {
                        "id": "attach_to_context",
                        "label": "Attach to context",
                        "memory_id": str(row["id"]),
                    },
                ],
                created_at=str(row["updated_at"] or row["created_at"] or ""),
                metadata={
                    "path": row["path"],
                    "memory_type": row["type"],
                    "source_type": row["source_type"],
                    "confidence": row["confidence"],
                    "importance": row["importance"],
                },
            )
        )
    return results


def _search_sources(
    conn: sqlite3.Connection,
    query: str,
    project_id: str | None,
    limit: int,
) -> list[SearchResult]:
    if not _table_exists(conn, "project_sources"):
        return []
    filters = ["parse_status='ready'"]
    params: list[Any] = []
    if project_id:
        filters.append("project_id=?")
        params.append(project_id)
    rows = conn.execute(
        f"""
        SELECT *
        FROM project_sources
        WHERE {' AND '.join(filters)}
        ORDER BY updated_at DESC, created_at DESC
        LIMIT ?
        """,
        (*params, max(limit * 3, limit)),
    ).fetchall()
    results: list[SearchResult] = []
    for row in rows:
        snapshot = _read_snapshot(row["snapshot_path"])
        fields = {
            "title": row["title"],
            "uri": row["uri"],
            "content": snapshot,
        }
        if not _matches(query, *fields.values()):
            continue
        matched = _matched_fields(query, fields)
        snippet_text = snapshot if "content" in matched else str(row["title"] or row["uri"] or "")
        results.append(
            SearchResult(
                id=str(row["id"]),
                type="source",
                title=str(row["title"] or row["uri"] or "Project source"),
                snippet=_snippet(snippet_text, query),
                matched_fields=matched,
                score=_score(query, fields, base=48),
                scope=_scope(str(row["project_id"])),
                project_id=str(row["project_id"]),
                source_id=str(row["id"]),
                badges=["source", str(row["source_type"] or "text"), str(row["include_policy"] or "include")],
                actions=[
                    {
                        "id": "open_source",
                        "label": "Open source",
                        "project_id": str(row["project_id"]),
                        "source_id": str(row["id"]),
                    },
                    {
                        "id": "attach_to_context",
                        "label": "Attach to context",
                        "source_id": str(row["id"]),
                    },
                ],
                created_at=str(row["updated_at"] or row["created_at"] or ""),
                metadata={
                    "source_type": row["source_type"],
                    "include_policy": row["include_policy"],
                    "parse_status": row["parse_status"],
                    "uri": row["uri"],
                    "token_estimate": row["token_estimate"],
                    "source_metadata": _json_loads(row["metadata"]),
                },
            )
        )
    return results[:limit]


def _search_research_reports(
    conn: sqlite3.Connection,
    query: str,
    project_id: str | None,
    limit: int,
) -> list[SearchResult]:
    if not _table_exists(conn, "research_runs"):
        return []
    like = _like(query)
    filters = [
        "status='completed'",
        "(LOWER(query) LIKE ? ESCAPE '\\' OR LOWER(final_text) LIKE ? ESCAPE '\\')",
    ]
    params: list[Any] = [like, like]
    if project_id:
        filters.append("project_id=?")
        params.append(project_id)
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT id, session_id, project_id, mode, query, artifact_id, final_text,
               metadata, created_at, updated_at, completed_at
        FROM research_runs
        WHERE {' AND '.join(filters)}
        ORDER BY completed_at DESC, updated_at DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    results: list[SearchResult] = []
    for row in rows:
        fields = {"query": row["query"], "final_text": row["final_text"]}
        snippet_text = row["final_text"] or row["query"]
        results.append(
            SearchResult(
                id=str(row["id"]),
                type="research_report",
                title=str(row["query"] or "Research report"),
                snippet=_snippet(snippet_text, query),
                matched_fields=_matched_fields(query, fields),
                score=_score(query, fields, base=52),
                scope=_scope(row["project_id"]),
                project_id=row["project_id"],
                session_id=row["session_id"],
                artifact_id=row["artifact_id"],
                badges=["research_report", str(row["mode"] or "deep")],
                actions=[
                    {
                        "id": "open_report",
                        "label": "Open report",
                        "run_id": str(row["id"]),
                        "artifact_id": row["artifact_id"],
                    },
                    {
                        "id": "open_chat",
                        "label": "Open originating chat",
                        "session_id": row["session_id"],
                    },
                ],
                created_at=str(row["completed_at"] or row["updated_at"] or row["created_at"] or ""),
                metadata={"mode": row["mode"], "run_metadata": _json_loads(row["metadata"])},
            )
        )
    return results
