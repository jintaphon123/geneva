from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..skills.frontmatter import parse_frontmatter
from .memory_age import memory_age_days


@dataclass
class MemoryHeader:
    path: Path
    name: str
    description: str
    type: str
    age_days: float


def scan_memory_files(memory_dir: Path) -> list[MemoryHeader]:
    if not memory_dir.exists():
        return []

    headers: list[MemoryHeader] = []
    for path in sorted(memory_dir.rglob("*.md")):
        if path.name == "MEMORY.md":
            continue
        try:
            parsed = parse_frontmatter(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        fm = parsed.frontmatter
        headers.append(
            MemoryHeader(
                path=path,
                name=str(fm.get("name") or path.stem),
                description=str(fm.get("description") or "").strip(),
                type=str(fm.get("type") or "reference"),
                age_days=memory_age_days(path),
            )
        )
    headers.sort(key=lambda item: (item.age_days, item.name.lower()))
    return headers


def format_memory_manifest(headers: list[MemoryHeader]) -> str:
    lines = ["| Name | Type | Age | Description |", "| --- | --- | --- | --- |"]
    for header in headers[:198]:
        age = f"{int(header.age_days)}d" if header.age_days != float("inf") else "?"
        description = header.description.replace("\n", " ").strip()
        rel = header.path.name
        lines.append(f"| {rel} | {header.type} | {age} | {description} |")
    return "\n".join(lines[:200])
