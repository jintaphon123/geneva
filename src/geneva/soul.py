from __future__ import annotations

import re
from pathlib import Path

from src.memdir.paths import get_data_dir


class SoulLoader:
    SOUL_FILENAME = "soul.md"

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else get_data_dir()

    @property
    def soul_path(self) -> Path:
        return self.data_dir / self.SOUL_FILENAME

    def candidate_paths(self) -> list[Path]:
        return [
            self.data_dir / self.SOUL_FILENAME,
            self.data_dir / "context" / self.SOUL_FILENAME,
            self.data_dir / "memory" / self.SOUL_FILENAME,
        ]

    def resolved_soul_path(self) -> Path | None:
        for path in self.candidate_paths():
            if path.exists() and path.is_file():
                return path
        return None

    def exists(self) -> bool:
        return self.resolved_soul_path() is not None

    def load_raw(self) -> str | None:
        """Return raw soul.md content, or None if not found / unreadable."""
        path = self.resolved_soul_path()
        if path is None:
            return None
        try:
            return path.read_text(encoding="utf-8").strip()
        except OSError:
            return None

    def get_schema_version(self) -> int:
        """Parse the YAML frontmatter `version:` field. Returns 0 if not found."""
        raw = self.load_raw()
        if not raw:
            return 0
        match = re.search(r"^version:\s*(\d+)", raw, re.MULTILINE)
        return int(match.group(1)) if match else 0

    def get_injected_block(self) -> str:
        """
        Return the formatted block to inject as the first context section.
        Returns empty string if soul.md is not found (graceful skip).
        """
        raw = self.load_raw()
        if not raw:
            return ""
        body = re.sub(r"^---\n.*?\n---\n?", "", raw, flags=re.DOTALL).strip()
        if not body:
            body = raw
        return f"## Soul — Identity Contract\n{body}"
