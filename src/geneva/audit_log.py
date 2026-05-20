from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

AUDIT_LOG_PATH = Path(os.environ.get("GENEVA_AUDIT_LOG", Path.home() / ".geneva" / "audit.jsonl"))
_LOCK = threading.RLock()

_SECRET_KEYS = frozenset({"api_key", "password", "token", "secret", "credential", "key"})


@dataclass
class AuditEntry:
    timestamp: str
    tool_name: str
    scope: str
    args_summary: dict[str, Any]
    outcome: str  # "allow" | "deny" | "ask" | "error"
    session_id: str | None = None
    turn_id: str | None = None
    reason: str = ""


def _redact(args: dict[str, Any]) -> dict[str, Any]:
    """Redact keys that look like secrets."""
    out: dict[str, Any] = {}
    for k, v in (args or {}).items():
        if any(s in k.lower() for s in _SECRET_KEYS):
            out[k] = "[REDACTED]"
        elif isinstance(v, str) and len(v) > 500:
            out[k] = v[:200] + "...[truncated]"
        else:
            out[k] = v
    return out


def append_audit_entry(
    tool_name: str,
    scope: str,
    args: dict[str, Any],
    outcome: str,
    *,
    session_id: str | None = None,
    turn_id: str | None = None,
    reason: str = "",
) -> None:
    entry = AuditEntry(
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        tool_name=tool_name,
        scope=scope,
        args_summary=_redact(args),
        outcome=outcome,
        session_id=session_id,
        turn_id=turn_id,
        reason=reason,
    )
    record = json.dumps(asdict(entry), ensure_ascii=False, default=str)
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        fd, tmp = tempfile.mkstemp(prefix=".audit.", suffix=".tmp", dir=AUDIT_LOG_PATH.parent)
        tmp_path = Path(tmp)
        try:
            existing = AUDIT_LOG_PATH.read_text(encoding="utf-8") if AUDIT_LOG_PATH.exists() else ""
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(existing + record + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_path, AUDIT_LOG_PATH)
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass


def search_audit_log(
    session_id: str | None = None,
    tool_name: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    if not AUDIT_LOG_PATH.exists():
        return []
    results: list[dict[str, Any]] = []
    with _LOCK:
        lines = AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines()
    for line in lines:
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if session_id and rec.get("session_id") != session_id:
            continue
        if tool_name and rec.get("tool_name") != tool_name:
            continue
        results.append(rec)
    return results[-max(1, min(limit, 500)):]
