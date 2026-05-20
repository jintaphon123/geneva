from __future__ import annotations

import os
import re
from pathlib import Path


def _slugify_cwd(cwd: Path) -> str:
    expanded = cwd.expanduser().resolve()
    normalized = expanded.as_posix()
    normalized = re.sub(r"[^A-Za-z0-9._/-]+", "-", normalized)
    normalized = normalized.replace("/", "-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized or "memory"


def get_data_dir() -> Path:
    override = os.environ.get("GENEVA_DATA_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".geneva"


def get_auto_mem_path(cwd: Path) -> Path:
    override = os.environ.get("GENEVA_AUTO_MEM_PATH")
    if override:
        return Path(override).expanduser()
    return get_data_dir() / "memory"


def get_legacy_mem_path(cwd: Path) -> Path:
    slug = _slugify_cwd(cwd)
    return Path.home() / ".claude" / "projects" / slug / "memory"


def is_auto_memory_enabled() -> bool:
    return os.environ.get("GENEVA_AUTO_MEMORY", "0") == "1"
