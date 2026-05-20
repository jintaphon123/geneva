"""R10.4 — B.L.A.S.T. Auto-writer: generate and maintain project docs.

B.L.A.S.T. = Background · Log · Activity · Status · Task-plan
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


_TEMPLATES: dict[str, str] = {
    "CLAUDE.md": (
        "# {name}\n\n"
        "> Created: {date}\n\n"
        "## Goal\n{goal}\n\n"
        "## Context\n(Add project context here — key decisions, constraints, links)\n\n"
        "## Team\n(Add team members / stakeholders)\n"
    ),
    "task-plan.md": (
        "# {name} — Task Plan\n\n"
        "> Created: {date}\n\n"
        "## Tasks\n"
        "- [ ] Define project scope\n"
        "- [ ] Set up initial structure\n"
        "- [ ] Build first prototype\n\n"
        "## Completed\n"
        "(Completed tasks move here)\n"
    ),
    "findings.md": (
        "# {name} — Research Findings\n\n"
        "> Created: {date}\n\n"
        "## Findings\n"
        "(Research findings and insights will appear here automatically)\n"
    ),
    "progress.md": (
        "# {name} — Progress Log\n\n"
        "> Created: {date}\n\n"
        "## Progress\n"
        "(Turn-by-turn progress updates appear here automatically)\n"
    ),
    "decisions.md": (
        "# {name} — Decision Log\n\n"
        "> Created: {date}\n\n"
        "## Decisions\n"
        "(Detected decisions are appended here automatically)\n"
    ),
}


def _blast_folder(project_id: str, folder_path: Path | str | None = None) -> Path:
    if folder_path is not None:
        return Path(folder_path)
    from src.memdir.brain_engine import _resolve_db_path

    return _resolve_db_path().parent / "projects" / project_id


def create_blast_docs(
    project_id: str,
    project_name: str,
    goal: str = "",
    folder_path: Path | str | None = None,
) -> dict[str, Path]:
    """Create B.L.A.S.T. docs in folder_path (default: ~/.geneva/projects/{id}/).

    Skips files that already exist. Returns {filename: Path} mapping.
    """
    folder = _blast_folder(project_id, folder_path)
    folder.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    result: dict[str, Path] = {}
    for filename, template in _TEMPLATES.items():
        content = template.format(name=project_name, goal=goal or "(not specified)", date=date)
        p = folder / filename
        if not p.exists():
            p.write_text(content, encoding="utf-8")
        result[filename] = p
    return result


def append_to_blast(
    project_id: str,
    filename: str,
    content: str,
    folder_path: Path | str | None = None,
) -> bool:
    """Append a line to a specific B.L.A.S.T. file. Returns True if file existed."""
    p = _blast_folder(project_id, folder_path) / filename
    if not p.exists():
        return False
    with p.open("a", encoding="utf-8") as f:
        f.write(f"\n{content}\n")
    return True


def get_blast_paths(
    project_id: str,
    folder_path: Path | str | None = None,
) -> dict[str, Path]:
    """Return path dict for all B.L.A.S.T. files (whether they exist or not)."""
    folder = _blast_folder(project_id, folder_path)
    return {filename: folder / filename for filename in _TEMPLATES}
