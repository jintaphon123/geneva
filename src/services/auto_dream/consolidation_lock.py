from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

LOCK_FILENAME = ".consolidate-lock"
LAST_CONSOLIDATED_FILENAME = ".last-consolidated.json"
LOCK_STALE_MINUTES = 60


def _lock_path(memory_dir: Path) -> Path:
    return memory_dir / LOCK_FILENAME


def _last_consolidated_path(memory_dir: Path) -> Path:
    return memory_dir / LAST_CONSOLIDATED_FILENAME


def try_acquire_consolidation_lock(memory_dir: Path) -> bool:
    memory_dir.mkdir(parents=True, exist_ok=True)
    lock_path = _lock_path(memory_dir)
    if lock_path.exists():
        mtime = datetime.fromtimestamp(lock_path.stat().st_mtime, tz=timezone.utc)
        if datetime.now(timezone.utc) - mtime <= timedelta(minutes=LOCK_STALE_MINUTES):
            return False
        lock_path.unlink(missing_ok=True)

    payload = {
        "pid": os.getpid(),
        "acquired_at": datetime.now(timezone.utc).isoformat(),
    }
    lock_path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
    return True


def read_last_consolidated_at(memory_dir: Path) -> datetime | None:
    last_path = _last_consolidated_path(memory_dir)
    if last_path.exists():
        try:
            raw = json.loads(last_path.read_text(encoding="utf-8"))
            consolidated_at = raw.get("consolidated_at")
            if isinstance(consolidated_at, str):
                return datetime.fromisoformat(consolidated_at)
        except Exception:
            pass

    lock_path = _lock_path(memory_dir)
    if not lock_path.exists():
        return None
    try:
        raw = json.loads(lock_path.read_text(encoding="utf-8"))
        acquired_at = raw.get("acquired_at")
        if isinstance(acquired_at, str):
            return datetime.fromisoformat(acquired_at)
    except Exception:
        pass
    return datetime.fromtimestamp(lock_path.stat().st_mtime, tz=timezone.utc)


def mark_consolidated(memory_dir: Path, consolidated_at: datetime | None = None) -> None:
    memory_dir.mkdir(parents=True, exist_ok=True)
    when = consolidated_at or datetime.now(timezone.utc)
    payload = {"consolidated_at": when.isoformat()}
    _last_consolidated_path(memory_dir).write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")


def list_sessions_touched_since(session_dir: Path, since: datetime) -> list[Path]:
    if not session_dir.exists():
        return []
    touched: list[Path] = []
    for path in sorted(session_dir.glob("*.json")):
        try:
            modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        if modified_at > since:
            touched.append(path)
    return touched


def release_consolidation_lock(memory_dir: Path) -> None:
    _lock_path(memory_dir).unlink(missing_ok=True)
