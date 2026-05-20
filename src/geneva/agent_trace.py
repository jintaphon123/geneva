from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import threading
from pathlib import Path
from typing import Any


TRACE_DIR = Path(os.environ.get("GENEVA_AGENT_TRACE_DIR", Path.home() / ".geneva" / "agent-traces"))
_TRACE_LOCK = threading.RLock()


def safe_session_id(session_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", session_id or "default")


def trace_path(session_id: str) -> Path:
    root = Path(os.environ.get("GENEVA_AGENT_TRACE_DIR", TRACE_DIR))
    return root / f"{safe_session_id(session_id)}.jsonl"


def append_trace_record(record: dict[str, Any]) -> None:
    path = trace_path(str(record.get("session_id") or ""))
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(record, ensure_ascii=False, sort_keys=True, default=str)
    max_records = _max_trace_records()
    with _TRACE_LOCK:
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        lines = [line for line in existing.splitlines() if line.strip()]
        payload = "\n".join([*lines, rendered][-max_records:]) + "\n"
        _atomic_write_text(path, payload)


def list_trace_records(session_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
    path = trace_path(session_id)
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with _TRACE_LOCK:
        lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records[-max(1, min(int(limit), 100)) :]


def hash_content(text: str | None) -> str | None:
    """Return a short sha256 hex digest for privacy-safe content fingerprinting."""
    if not text:
        return None
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def get_turn_trace(session_id: str, turn_id: str) -> dict[str, Any] | None:
    """Look up a single turn trace record by turn_id within a session."""
    for record in list_trace_records(session_id, limit=500):
        if record.get("turn_id") == turn_id or record.get("trace_id") == turn_id:
            return record
    return None


def append_research_trace(
    session_id: str,
    sources: list[dict[str, Any]],
    *,
    query: str = "",
    mode: str = "deep",
) -> None:
    """Persist research citations into the agent trace for a session."""
    import time as _time
    import uuid as _uuid

    if not session_id:
        return
    record = {
        "type": "research_citations",
        "turn_id": _uuid.uuid4().hex,
        "session_id": session_id,
        "query": query[:500],
        "mode": mode,
        "created_at": _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()),
        "citations": [
            {
                "id": s.get("id", ""),
                "title": s.get("title", ""),
                "url": s.get("url", ""),
                "snippet": (s.get("snippet") or "")[:300],
                "fetched": bool(s.get("fetched", False)),
            }
            for s in (sources or [])
        ],
    }
    append_trace_record(record)


def _max_trace_records() -> int:
    try:
        value = int(os.environ.get("GENEVA_AGENT_TRACE_MAX_RECORDS", "500"))
    except ValueError:
        value = 500
    return max(50, min(value, 5_000))


def _atomic_write_text(path: Path, content: str) -> None:
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
