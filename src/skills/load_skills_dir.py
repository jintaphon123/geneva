from __future__ import annotations

from pathlib import Path

from ._prompt_skill_utils import build_prompt_skill_from_file
from .model import PromptSkill


def load_skills_dir(skills_dir: Path) -> list[PromptSkill]:
    root = skills_dir.expanduser().resolve()
    if not root.exists():
        return []

    skills: list[PromptSkill] = []
    for skill_file in sorted(root.rglob("SKILL.md")):
        skills.append(build_prompt_skill_from_file(skill_file, loaded_from="skills"))
    return skills
