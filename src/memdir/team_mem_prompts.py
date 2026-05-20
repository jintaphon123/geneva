from __future__ import annotations

from pathlib import Path


def build_team_memory_prompt(team_mem_dir: Path) -> str:
    if not team_mem_dir.exists():
        return ""

    sections: list[str] = ["### TEAM MEMORY"]
    for path in sorted(team_mem_dir.rglob("*.md")):
        try:
            content = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if not content:
            continue
        sections.append(f"#### Source: {path.relative_to(team_mem_dir)}")
        sections.append(content)
    sections.append("### END TEAM MEMORY")
    return "\n".join(sections)
