from __future__ import annotations

from pathlib import Path


class PathTraversalError(Exception):
    pass


def get_team_mem_path(base: Path, filename: str) -> Path:
    if "\x00" in filename:
        raise PathTraversalError("Null byte in team memory filename")
    root = base.expanduser().resolve()
    candidate = (root / filename).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise PathTraversalError(f"Path escapes team memory root: {filename}") from exc
    return candidate
