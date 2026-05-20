from __future__ import annotations

from pathlib import Path

from .paths import get_auto_mem_path

ENTRYPOINT_NAME = "MEMORY.md"
MAX_ENTRYPOINT_LINES = 200
MAX_ENTRYPOINT_BYTES = 25_000


def truncate_entrypoint_content(content: str) -> str:
    encoded = content.encode("utf-8")
    if len(encoded) > MAX_ENTRYPOINT_BYTES:
        content = encoded[:MAX_ENTRYPOINT_BYTES].decode("utf-8", errors="ignore")
    lines = content.splitlines()
    if len(lines) > MAX_ENTRYPOINT_LINES:
        lines = lines[:MAX_ENTRYPOINT_LINES]
    return "\n".join(lines).strip()


def build_memory_lines(memory_path: Path) -> list[str]:
    if not memory_path.exists():
        return []
    try:
        content = memory_path.read_text(encoding="utf-8")
    except OSError:
        return []
    truncated = truncate_entrypoint_content(content)
    return truncated.splitlines()


def load_memory_prompt(cwd: Path | None = None) -> str:
    base = get_auto_mem_path(cwd or Path.cwd())
    entrypoint = base / ENTRYPOINT_NAME
    lines = build_memory_lines(entrypoint)
    if not lines:
        return ""
    body = "\n".join(lines)
    return f"### MEMORY\n{body}\n### END MEMORY"
