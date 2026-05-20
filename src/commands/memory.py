from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from src.commands import register

try:
    from src.memdir.brain_engine import rebuild_index, refresh_context, remember, search

    HAS_BRAIN_ENGINE = True
except ImportError:
    HAS_BRAIN_ENGINE = False

try:
    from src.memdir.memory_scan import scan_memory_files
    from src.memdir.paths import get_auto_mem_path

    HAS_MEMDIR = True
except ImportError:
    HAS_MEMDIR = False


def _scan_items() -> list[Any]:
    if HAS_MEMDIR:
        try:
            items = scan_memory_files(get_auto_mem_path(Path.cwd()))
            return list(items) if items else []
        except Exception:
            return []
    return []


def _format_item(item: Any) -> str:
    if isinstance(item, dict):
        path = item.get("path") or item.get("file") or "unknown"
        status = item.get("status", "unknown")
        confidence = item.get("confidence", "")
        return f"{path} | {status} | {confidence}"
    return str(item)


@register(name="memory", description="Inspect and manage memory data.")
async def run(args: list[str]) -> str | None:
    if not HAS_BRAIN_ENGINE and not HAS_MEMDIR:
        return "Memory layer not available"
    subcommand = args[0] if args else "status"
    tail = args[1:]

    if subcommand == "list":
        items = _scan_items()
        if not items:
            return "No memory files found."
        return "\n".join(_format_item(item) for item in items)

    if subcommand == "add":
        if not tail:
            return "Usage: /memory add <text>"
        if not HAS_BRAIN_ENGINE:
            return "Memory layer not available"
        result = await remember(content=" ".join(tail), type="reference", source_type="user_direct")
        if isinstance(result, dict):
            op = result.get("operation", "ADD")
        else:
            op = getattr(result, "operation", "ADD")
        return str(op)

    if subcommand == "search":
        if not tail:
            return "Usage: /memory search <query>"
        query = " ".join(tail)
        if HAS_BRAIN_ENGINE:
            results = search(query, min_confidence=0.5)
            if not results:
                return "No memory matches."
            return "\n".join(str(item) for item in results)
        fallback = [item for item in _scan_items() if query.lower() in str(item).lower()]
        return "\n".join(_format_item(item) for item in fallback) if fallback else "No memory matches."

    if subcommand == "rebuild":
        if not HAS_BRAIN_ENGINE:
            return "Memory layer not available"
        result = rebuild_index()
        if isinstance(result, dict):
            return (
                f"files_scanned={result.get('files_scanned', 0)} "
                f"files_updated={result.get('files_updated', 0)} "
                f"errors={result.get('errors', 0)}"
            )
        return str(result)

    if subcommand == "status":
        items = _scan_items()
        counts = Counter()
        for item in items:
            if isinstance(item, dict):
                counts[str(item.get("status", "unknown"))] += 1
        lines = [
            f"brain_engine={'available' if HAS_BRAIN_ENGINE else 'missing'}",
            f"memdir={'available' if HAS_MEMDIR else 'missing'}",
            f"memory_files={len(items)}",
        ]
        if counts:
            lines.extend(f"{status}={count}" for status, count in sorted(counts.items()))
        return "\n".join(lines)

    return "Usage: /memory list|add|search|rebuild|status"
