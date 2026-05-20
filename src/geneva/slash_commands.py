from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


CommandLevel = Literal["client", "server", "skill"]


@dataclass(frozen=True)
class SlashCommand:
    name: str
    level: CommandLevel
    description: str
    command: str
    params: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


AVAILABLE_COMMANDS: dict[str, SlashCommand] = {
    "help": SlashCommand(
        name="help",
        level="client",
        description="Show available commands.",
        command="/help",
        params=[],
    ),
    "clear": SlashCommand(
        name="clear",
        level="client",
        description="Clear the visible chat canvas.",
        command="/clear",
        params=[],
    ),
    "status": SlashCommand(
        name="status",
        level="server",
        description="Show session and runtime status.",
        command="/status",
        params=[],
    ),
    "cost": SlashCommand(
        name="cost",
        level="server",
        description="Show token and cost usage.",
        command="/cost",
        params=[],
    ),
    "memory": SlashCommand(
        name="memory",
        level="server",
        description="Inspect or search memory.",
        command="/memory",
        params=["subcommand", "query"],
    ),
    "context": SlashCommand(
        name="context",
        level="server",
        description="Show current token and context usage.",
        command="/context",
        params=[],
    ),
}

LEGACY_SKILL_COMMANDS: dict[str, SlashCommand] = {
    "consult": SlashCommand(
        name="consult",
        level="skill",
        description="Ask for a second-opinion style analysis.",
        command="/consult",
        params=["topic"],
    ),
    "engineer": SlashCommand(
        name="engineer",
        level="skill",
        description="Frame the request as an engineering task.",
        command="/engineer",
        params=["task"],
    ),
    "product-manager": SlashCommand(
        name="product-manager",
        level="skill",
        description="Frame the request as a product decision.",
        command="/product-manager",
        params=["question"],
    ),
    "gtm-advisor": SlashCommand(
        name="gtm-advisor",
        level="skill",
        description="Frame the request as GTM strategy work.",
        command="/gtm-advisor",
        params=["question"],
    ),
}


def get_all_commands() -> list[dict[str, object]]:
    from src.geneva.skill_engine import get_engine

    builtins = [command.to_dict() for command in AVAILABLE_COMMANDS.values()]
    skill_commands = [
        {
            "name": skill["name"],
            "level": "skill",
            "description": skill["description"],
            "command": skill["command"],
            "params": ["topic"],
        }
        for skill in get_engine().list_skills(active_only=True)
    ]
    seen: set[str] = set()
    merged: list[dict[str, object]] = []
    for command in [*builtins, *skill_commands]:
        name = str(command.get("name") or "")
        if name in seen:
            continue
        seen.add(name)
        merged.append(command)
    return merged


def list_slash_commands() -> list[dict[str, object]]:
    return get_all_commands()


def lookup_slash_command(name: str) -> SlashCommand | None:
    normalized = name.lower().strip().removeprefix("/")
    builtin = AVAILABLE_COMMANDS.get(normalized)
    if builtin is not None:
        return builtin

    from src.geneva.skill_engine import get_engine

    skill = get_engine().get(normalized)
    if skill is not None:
        return SlashCommand(
            name=skill.name,
            level="skill",
            description=skill.description,
            command=skill.command,
            params=["topic"],
        )
    return LEGACY_SKILL_COMMANDS.get(normalized)


def parse_slash_command(raw: str) -> tuple[SlashCommand | None, str]:
    text = raw.strip()
    if not text.startswith("/"):
        return None, ""
    command_text = text[1:].strip()
    if not command_text:
        return None, ""
    parts = command_text.split(maxsplit=1)
    command = lookup_slash_command(parts[0])
    args = parts[1] if len(parts) > 1 else ""
    return command, args
