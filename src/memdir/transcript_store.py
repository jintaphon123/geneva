from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from .brain_engine import _connect


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def write_turn(
    session_id: str,
    turn_index: int,
    role: str,
    content: str,
    *,
    project_id: Optional[str] = None,
    ghost_mode: bool = False,
    model: Optional[str] = None,
    cost: Optional[float] = None,
    trace_id: Optional[str] = None,
) -> None:
    """Write a single conversation turn to session_transcripts. No-op if ghost_mode=True."""
    if ghost_mode:
        return
    if not content or not content.strip():
        return
    row_id = str(uuid.uuid4())
    created = _now()
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO session_transcripts
                    (id, session_id, project_id, ghost_mode, turn_index, role, content, model, cost, trace_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (row_id, session_id, project_id, 0, turn_index, role, content, model, cost, trace_id, created),
            )
    except Exception:
        pass


def search_transcripts(query: str, *, limit: int = 20) -> list[dict]:
    """Full-text search across all session transcripts using FTS5. Returns list of dicts."""
    if not query or not query.strip():
        return []
    try:
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT st.session_id, st.role, st.content, st.created_at
                FROM transcript_fts fts
                JOIN session_transcripts st ON st.rowid = fts.rowid
                WHERE transcript_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
        return [dict(row) for row in rows]
    except Exception:
        return []


def get_session_transcript(session_id: str) -> list[dict]:
    """Return all turns for a session ordered by turn_index."""
    try:
        with _connect() as conn:
            rows = conn.execute(
                """
                SELECT role, content, turn_index, model, created_at
                FROM session_transcripts
                WHERE session_id = ? AND ghost_mode = 0
                ORDER BY turn_index ASC
                """,
                (session_id,),
            ).fetchall()
        return [dict(row) for row in rows]
    except Exception:
        return []
