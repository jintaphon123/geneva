"""R9 - Artifact Store: persist blobs from Research / Documents / Computer Use / Trace."""
from __future__ import annotations

import hashlib
import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from src.memdir.brain_engine import _resolve_db_path, init_db

ArtifactType = Literal["screenshot", "citation_map", "document_preview", "research_trace", "research_report", "tool_output"]

# Retention TTL in days. None = permanent (delete only on explicit request).
TTL_DAYS: dict[str, int | None] = {
    "screenshot": 7,
    "citation_map": None,
    "document_preview": None,
    "research_trace": 30,
    "research_report": None,
    "tool_output": 7,
}

# Blobs larger than this go to disk; smaller ones are stored inline.
_LARGE_BYTES = 10_240  # 10 KB

_REDACT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"['\"]?(api[_\-]?key|password|passwd|secret|token|auth[_\-]?token)['\"]?\s*[=:]\s*['\"]?[^'\"\s,}]+['\"]?",
        re.IGNORECASE,
    ),
    re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9]{32,}\b"),
]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _artifact_dir() -> Path:
    d = _resolve_db_path().parent / "artifacts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _connect() -> sqlite3.Connection:
    p = _resolve_db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _redact_data(data: str) -> str:
    """Strip known-sensitive patterns from a string."""
    for pat in _REDACT_PATTERNS:
        data = pat.sub("[REDACTED]", data)
    return data


def _expires_at(artifact_type: str) -> str | None:
    ttl = TTL_DAYS.get(artifact_type)
    if ttl is None:
        return None
    return (datetime.now(timezone.utc) + timedelta(days=ttl)).isoformat()


def save_artifact(
    artifact_type: str,
    data: str,
    session_id: str | None = None,
    *,
    redact: bool = False,
) -> str | None:
    """Persist an artifact blob.

    Returns artifact_id on success, None when GENEVA_GHOST=1.
    """
    if os.environ.get("GENEVA_GHOST") == "1":
        return None

    init_db()

    payload = _redact_data(data) if redact else data

    artifact_id = hashlib.sha256(
        f"{artifact_type}:{session_id}:{payload[:256]}:{_iso_now()}".encode()
    ).hexdigest()[:24]

    size = len(payload.encode("utf-8", errors="replace"))
    content: str | None = None
    content_path: str | None = None

    if size > _LARGE_BYTES:
        ext = "json" if artifact_type in ("citation_map", "research_trace", "research_report") else "bin"
        p = _artifact_dir() / f"{artifact_id}.{ext}"
        p.write_text(payload, encoding="utf-8")
        content_path = str(p)
    else:
        content = payload

    with _connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO artifacts(
                artifact_id, type, session_id, created_at, expires_at,
                size_bytes, redacted, content_path, content
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_id,
                artifact_type,
                session_id,
                _iso_now(),
                _expires_at(artifact_type),
                size,
                int(redact),
                content_path,
                content,
            ),
        )
        conn.commit()

    return artifact_id


def get_artifact(artifact_id: str) -> dict | None:
    """Return artifact dict including content, or None if not found."""
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,)
        ).fetchone()
    if row is None:
        return None
    result = dict(row)
    if result.get("content_path"):
        p = Path(result["content_path"])
        result["content"] = p.read_text(encoding="utf-8") if p.exists() else None
    return result


def list_artifacts(
    session_id: str | None = None,
    artifact_type: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """List artifacts (no content blob). Filter by session_id and/or type."""
    init_db()
    filters = ["1=1"]
    params: list[object] = []
    if session_id:
        filters.append("session_id = ?")
        params.append(session_id)
    if artifact_type:
        filters.append("type = ?")
        params.append(artifact_type)
    params.append(limit)
    sql = (
        f"SELECT artifact_id, type, session_id, created_at, expires_at, size_bytes, redacted "
        f"FROM artifacts WHERE {' AND '.join(filters)} "
        f"ORDER BY created_at DESC LIMIT ?"
    )
    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def delete_artifact(artifact_id: str) -> bool:
    """Delete artifact by id. Returns True if it existed."""
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT content_path FROM artifacts WHERE artifact_id = ?", (artifact_id,)
        ).fetchone()
        if row is None:
            return False
        if row["content_path"]:
            p = Path(row["content_path"])
            if p.exists():
                p.unlink(missing_ok=True)
        conn.execute("DELETE FROM artifacts WHERE artifact_id = ?", (artifact_id,))
        conn.commit()
    return True


def expire_artifacts() -> int:
    """Hard-delete artifacts whose expires_at < now. Returns count removed."""
    init_db()
    now = _iso_now()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT artifact_id, content_path FROM artifacts "
            "WHERE expires_at IS NOT NULL AND expires_at < ?",
            (now,),
        ).fetchall()
        for row in rows:
            if row["content_path"]:
                Path(row["content_path"]).unlink(missing_ok=True)
        ids = [r["artifact_id"] for r in rows]
        if ids:
            placeholders = ",".join("?" * len(ids))
            conn.execute(
                f"DELETE FROM artifacts WHERE artifact_id IN ({placeholders})", ids
            )
            conn.commit()
    return len(ids)
