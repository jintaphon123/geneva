from __future__ import annotations

from ...memdir.brain_engine import Memory
from .session_memory_utils import truncate_to_budget


def build_session_memory_cache_prompt(memories: list[Memory], max_tokens: int = 3000) -> str:
    ordered = sorted(
        memories,
        key=lambda memory: (
            memory.confidence,
            memory.updated_at or memory.created_at,
        ),
        reverse=True,
    )
    lines = ["## Memory"]
    for memory in ordered:
        lines.append(f"- [{memory.type}] {memory.name}: {memory.content}")
    return truncate_to_budget("\n".join(lines), max_tokens=max_tokens)
