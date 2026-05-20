from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .argument_substitution import parse_argument_names
from .frontmatter import parse_frontmatter
from .model import PromptSkill


def _as_str_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    text = str(value).strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    parts = [part.strip() for part in text.split(",")]
    return [part for part in parts if part]


def build_prompt_skill(
    markdown: str,
    *,
    skill_name: str,
    loaded_from: str,
    skill_root: Path | None,
    description: str | None = None,
) -> PromptSkill:
    parsed = parse_frontmatter(markdown)
    fm = parsed.frontmatter
    body = parsed.body
    resolved_name = str(fm.get("name") or skill_name)
    resolved_description = description or str(fm.get("description") or _first_body_line(body) or f"Skill: {resolved_name}")
    user_invocable = bool(fm.get("user-invocable", True))
    disable_model_invocation = bool(fm.get("disable-model-invocation", False))
    when_to_use = str(fm.get("when_to_use")) if fm.get("when_to_use") is not None else None
    version = str(fm.get("version")) if fm.get("version") is not None else None
    model = str(fm.get("model")) if fm.get("model") is not None else None
    context = "fork" if str(fm.get("context", "")).lower() == "fork" else "inline"
    agent = str(fm.get("agent")) if fm.get("agent") is not None else None
    effort = str(fm.get("effort")) if fm.get("effort") is not None else None
    paths = _as_str_list(fm.get("paths")) or None
    return PromptSkill(
        name=resolved_name,
        description=resolved_description,
        loaded_from=loaded_from,
        user_invocable=user_invocable,
        disable_model_invocation=disable_model_invocation,
        content_length=len(body),
        is_hidden=not user_invocable,
        skill_root=str(skill_root) if skill_root is not None else None,
        when_to_use=when_to_use,
        version=version,
        model=model,
        allowed_tools=_as_str_list(fm.get("allowed-tools")),
        arg_names=parse_argument_names(fm.get("arguments")),
        context=context,
        agent=agent,
        effort=effort,
        paths=paths,
        markdown_content=body,
    )


def build_prompt_skill_from_file(skill_file: Path, *, loaded_from: str) -> PromptSkill:
    return build_prompt_skill(
        skill_file.read_text(encoding="utf-8"),
        skill_name=skill_file.parent.name,
        loaded_from=loaded_from,
        skill_root=skill_file.parent,
    )


def _first_body_line(body: str) -> str | None:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None
