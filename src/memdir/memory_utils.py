from __future__ import annotations

import datetime as dt
import hashlib
import os
import re
import tempfile
from pathlib import Path
from typing import cast

from .memory_models import MemoryStatus

_NULL_LIKE = {"", "null", "none", "None"}
_VALID_MEMORY_STATUSES = {"active", "archived", "expired", "superseded", "deleted"}
_INACTIVE_MEMORY_STATUSES = {"archived", "expired", "superseded", "deleted"}


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso_now() -> str:
    return utcnow().isoformat()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def atomic_write_text(path: Path, content: str) -> None:
    ensure_parent(path)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        temp_path = None
        try:
            dir_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except OSError:
                pass


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def search_terms(text: str) -> list[str]:
    terms = [term.strip() for term in re.findall(r"[\w\u0E00-\u0E7F./-]+", text, flags=re.UNICODE)]
    return [term for term in terms if term]


def fts_query_from_text(text: str) -> str:
    terms = search_terms(text)
    return " OR ".join(f'"{term.replace(chr(34), chr(34) + chr(34))}"' for term in terms[:8])


def like_pattern(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def scope_value(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return None if text in _NULL_LIKE else text


def status_value(value: object, default: MemoryStatus = "active") -> MemoryStatus:
    text = str(value if value is not None else default).strip().lower()
    if text in _VALID_MEMORY_STATUSES:
        return cast(MemoryStatus, text)
    return default


def coerce_float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def coerce_int(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_name_from_content(content: str, memory_type: str) -> tuple[str, str]:
    lines = [line.strip("-* ").strip() for line in content.splitlines() if line.strip()]
    first = lines[0] if lines else memory_type.title()
    name = re.sub(r"\s+", " ", first)
    name = name[:80] if len(name) > 80 else name
    description = re.sub(r"\s+", " ", content.strip())
    description = description[:140]
    return name or memory_type.title(), description


def parse_control_directive(content: str, directive: str) -> str | None:
    pattern = rf"^\s*{directive}\s*:\s*([A-Za-z0-9_-]+)\s*$"
    for line in content.splitlines()[:5]:
        match = re.match(pattern, line, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None
