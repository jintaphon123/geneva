from __future__ import annotations

from ...memdir.brain_engine import Memory


def dedup_memories(memories: list[Memory]) -> list[Memory]:
    seen: set[str] = set()
    deduped: list[Memory] = []
    for memory in memories:
        if memory.id in seen:
            continue
        seen.add(memory.id)
        deduped.append(memory)
    return deduped


def truncate_to_budget(text: str, max_tokens: int = 3000) -> str:
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip()
