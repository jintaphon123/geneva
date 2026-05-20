from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .team_mem_secret_guard import check_team_mem_secrets
from .types import TeamMemoryContent
from .watcher import watch_team_memory


def init_team_memory_sync(
    team_mem_dir: Path | None = None,
    on_secret_found: Callable | None = None,
) -> None:
    root = (team_mem_dir or (Path.cwd() / ".geneva" / "team-memory")).expanduser()
    if not root.exists():
        return

    def handle_change(path: Path) -> None:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return
        payload = TeamMemoryContent(
            name=path.stem,
            description=f"Team memory file {path.name}",
            type="reference",
            content=content,
        )
        findings = check_team_mem_secrets(payload)
        if findings and on_secret_found is not None:
            on_secret_found(path, findings)
        elif findings:
            print(f"[team-memory-sync] secret-like values detected in {path}")

    watch_team_memory(root, handle_change)


__all__ = [
    "TeamMemoryContent",
    "check_team_mem_secrets",
    "init_team_memory_sync",
    "watch_team_memory",
]
