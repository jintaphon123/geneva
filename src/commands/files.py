from __future__ import annotations

from src.commands import register
from src.commands._shared import git_modified_files


@register(name="files", description="List files modified in the current session.")
async def run(args: list[str]) -> str | None:
    del args
    files = git_modified_files()
    return "\n".join(files) if files else "No modified files found."
