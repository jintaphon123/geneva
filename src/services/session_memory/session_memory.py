from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ...memdir.brain_engine import Memory, search
from ...memdir.memory_scan import MemoryHeader
from ...memdir.paths import get_auto_mem_path
from .prompts import build_session_memory_cache_prompt
from .session_memory_utils import dedup_memories

_session_memory_cache: dict = {}
_last_refreshed: datetime | None = None
REFRESH_INTERVAL_TURNS = 5


async def load_session_memory(
    memory_dir: Path | None = None,
    force_refresh: bool = False,
) -> str:
    global _last_refreshed
    target_memory_dir = (memory_dir or get_auto_mem_path(Path.cwd())).expanduser()

    turns = int(_session_memory_cache.get("turns", 0))
    if not force_refresh and _session_memory_cache and turns < REFRESH_INTERVAL_TURNS:
        _session_memory_cache["turns"] = turns + 1
        return str(_session_memory_cache.get("prompt", ""))

    memories = dedup_memories(search("", include_archived=False))
    prompt = build_session_memory_cache_prompt(memories)
    _session_memory_cache.clear()
    _session_memory_cache.update(
        {
            "prompt": prompt,
            "memories": memories,
            "turns": 1,
            "memory_dir": str(target_memory_dir),
        }
    )
    _last_refreshed = datetime.now(timezone.utc)
    return prompt


def build_session_memory_context(headers: list[MemoryHeader], content_map: dict) -> str:
    memories: list[Memory] = []
    for header in headers:
        content = str(content_map.get(header.path, content_map.get(str(header.path), ""))).strip()
        if not content:
            continue
        memories.append(
            Memory(
                id=str(header.path),
                path=str(header.path),
                name=header.name,
                type=header.type,
                status="active",
                content=content,
                confidence=0.7,
                importance=0.5,
                source_type="file_import",
                created_at="",
                updated_at=None,
                retention_days=365,
                expires_at=None,
                superseded_by=None,
            )
        )
    return build_session_memory_cache_prompt(memories)


def get_current_session_memory() -> dict:
    return dict(_session_memory_cache)
