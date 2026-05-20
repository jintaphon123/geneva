from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

WORKSPACE_DEFAULT = Path.home() / "Documents" / "Geneva"
GENEVA_DIR = Path.home() / ".geneva"


@dataclass
class ImportResult:
    skills_imported: int = 0
    context_imported: int = 0
    brain_md_created: bool = False
    errors: list[str] = field(default_factory=list)


class GenevaImporter:
    def __init__(self, workspace_path: Path | None = None) -> None:
        self.source = workspace_path or WORKSPACE_DEFAULT
        self.dest = GENEVA_DIR
        self.dest.mkdir(parents=True, exist_ok=True)

    def import_all(self) -> ImportResult:
        result = ImportResult()
        result.brain_md_created = self._import_brain_md(result)
        result.skills_imported = self._import_skills(result)
        result.context_imported = self._import_context(result)
        return result

    def _import_brain_md(self, result: ImportResult) -> bool:
        """Read CLAUDE.md, strip Claude-specific lines, write as BRAIN.md."""
        src = self.source / "CLAUDE.md"
        dest = self.dest / "BRAIN.md"
        if not src.exists():
            return False
        try:
            content = src.read_text(encoding="utf-8")
            lines = content.splitlines()
            filtered: list[str] = []
            for line in lines:
                if any(
                    phrase in line
                    for phrase in [
                        "Claude Code",
                        "Anthropic's official CLI",
                        "claude code",
                        "anthropic.com",
                    ]
                ):
                    if "Claude Code" in line and "official" in line:
                        filtered.append("# Geneva - AI Assistant")
                    continue
                filtered.append(line)
            dest.write_text("\n".join(filtered), encoding="utf-8")
            return True
        except Exception as exc:
            logger.warning("brain_md import failed: %s", exc)
            result.errors.append(f"BRAIN.md import failed: {exc}")
            return False

    def _import_skills(self, result: ImportResult) -> int:
        """Copy all skill folders from .claude/skills/ to ~/.geneva/skills/."""
        src_skills = self.source / ".claude" / "skills"
        dest_skills = self.dest / "skills"
        dest_skills.mkdir(parents=True, exist_ok=True)
        if not src_skills.exists():
            return 0
        count = 0
        for skill_dir in src_skills.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            dest_dir = dest_skills / skill_dir.name
            try:
                if dest_dir.exists():
                    shutil.rmtree(dest_dir)
                shutil.copytree(skill_dir, dest_dir)
                count += 1
            except Exception as exc:
                logger.warning("Failed to copy skill %s: %s", skill_dir.name, exc)
                result.errors.append(f"Failed to copy skill {skill_dir.name}: {exc}")
        return count

    def _import_context(self, result: ImportResult) -> int:
        """Copy context/*.md and rules/*.md to ~/.geneva/."""
        count = 0
        for src_subdir, dest_subdir in [
            (self.source / "context", self.dest / "context"),
            (self.source / ".claude" / "rules", self.dest / "rules"),
        ]:
            if not src_subdir.exists():
                continue
            dest_subdir.mkdir(parents=True, exist_ok=True)
            for md_file in src_subdir.glob("*.md"):
                try:
                    shutil.copy2(md_file, dest_subdir / md_file.name)
                    count += 1
                except Exception as exc:
                    logger.warning("Failed to copy %s: %s", md_file, exc)
                    result.errors.append(f"Failed to copy {md_file}: {exc}")
        return count
