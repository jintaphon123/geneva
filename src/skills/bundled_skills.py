from __future__ import annotations

from pathlib import Path

from ._prompt_skill_utils import build_prompt_skill_from_file
from .model import PromptSkill

BUNDLED_SKILLS_DIR = Path(__file__).parent / "bundled"


def load_bundled_skills() -> list[PromptSkill]:
    skills: list[PromptSkill] = []
    if not BUNDLED_SKILLS_DIR.exists():
        return skills
    for skill_dir in sorted(BUNDLED_SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if skill_file.exists():
            skills.append(build_prompt_skill_from_file(skill_file, loaded_from="bundled"))
    return skills
