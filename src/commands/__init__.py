from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Awaitable, Callable

from src.models import PortingBacklog, PortingModule
from src.utils.asyncio_tools import run_awaitable_sync

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "reference_data" / "commands_snapshot.json"


@dataclass(frozen=True)
class CommandExecution:
    name: str
    source_hint: str
    prompt: str
    handled: bool
    message: str


@dataclass(frozen=True)
class CommandMeta:
    name: str
    description: str
    aliases: list[str]
    run: Callable[[list[str]], Awaitable[str | None]]


COMMANDS: dict[str, CommandMeta] = {}


def register(name: str, description: str, aliases: list[str] | None = None):
    def decorator(func: Callable[[list[str]], Awaitable[str | None]]):
        meta = CommandMeta(
            name=name,
            description=description,
            aliases=list(aliases or []),
            run=func,
        )
        COMMANDS[name.lower()] = meta
        for alias in meta.aliases:
            COMMANDS[alias.lower()] = meta
        return func

    return decorator


def lookup(name: str) -> CommandMeta | None:
    if not name:
        return None
    return COMMANDS.get(name.lower())


@lru_cache(maxsize=1)
def load_command_snapshot() -> tuple[PortingModule, ...]:
    raw_entries = json.loads(SNAPSHOT_PATH.read_text())
    return tuple(
        PortingModule(
            name=entry["name"],
            responsibility=entry["responsibility"],
            source_hint=entry["source_hint"],
            status="mirrored",
        )
        for entry in raw_entries
    )


PORTED_COMMANDS = load_command_snapshot()


@lru_cache(maxsize=1)
def built_in_command_names() -> frozenset[str]:
    return frozenset(module.name for module in PORTED_COMMANDS)


def build_command_backlog() -> PortingBacklog:
    return PortingBacklog(title="Command surface", modules=list(PORTED_COMMANDS))


def command_names() -> list[str]:
    return [module.name for module in PORTED_COMMANDS]


def get_command(name: str) -> PortingModule | None:
    needle = name.lower()
    for module in PORTED_COMMANDS:
        if module.name.lower() == needle:
            return module
    return None


def get_commands(
    cwd: str | None = None,
    include_plugin_commands: bool = True,
    include_skill_commands: bool = True,
) -> tuple[PortingModule, ...]:
    del cwd
    commands = list(PORTED_COMMANDS)
    if not include_plugin_commands:
        commands = [module for module in commands if "plugin" not in module.source_hint.lower()]
    if not include_skill_commands:
        commands = [module for module in commands if "skills" not in module.source_hint.lower()]
    return tuple(commands)


def find_commands(query: str, limit: int = 20) -> list[PortingModule]:
    needle = query.lower()
    matches = [
        module
        for module in PORTED_COMMANDS
        if needle in module.name.lower() or needle in module.source_hint.lower()
    ]
    return matches[:limit]


def execute_command(name: str, prompt: str = "") -> CommandExecution:
    command = lookup(name)
    if command is not None:
        parts = prompt.split() if prompt else []
        message = run_awaitable_sync(command.run(parts))
        return CommandExecution(
            name=command.name,
            source_hint="src.commands",
            prompt=prompt,
            handled=True,
            message=message or "",
        )

    module = get_command(name)
    if module is None:
        return CommandExecution(
            name=name,
            source_hint="",
            prompt=prompt,
            handled=False,
            message=f"Unknown mirrored command: {name}",
        )
    action = f"Mirrored command '{module.name}' from {module.source_hint} would handle prompt {prompt!r}."
    return CommandExecution(
        name=module.name,
        source_hint=module.source_hint,
        prompt=prompt,
        handled=True,
        message=action,
    )


def render_command_index(limit: int = 20, query: str | None = None) -> str:
    modules = find_commands(query, limit) if query else list(PORTED_COMMANDS[:limit])
    lines = [f"Command entries: {len(PORTED_COMMANDS)}", ""]
    if query:
        lines.append(f"Filtered by: {query}")
        lines.append("")
    lines.extend(f"- {module.name} — {module.source_hint}" for module in modules)
    return "\n".join(lines)


from . import clear as _clear  # noqa: E402,F401
from . import compact as _compact  # noqa: E402,F401
from . import config as _config  # noqa: E402,F401
from . import context as _context  # noqa: E402,F401
from . import cost as _cost  # noqa: E402,F401
from . import doctor as _doctor  # noqa: E402,F401
from . import env as _env  # noqa: E402,F401
from . import files as _files  # noqa: E402,F401
from . import help as _help  # noqa: E402,F401
from . import hooks as _hooks  # noqa: E402,F401
from . import mcp as _mcp  # noqa: E402,F401
from . import memory as _memory  # noqa: E402,F401
from . import model as _model  # noqa: E402,F401
from . import output_style as _output_style  # noqa: E402,F401
from . import permissions as _permissions  # noqa: E402,F401
from . import resume as _resume  # noqa: E402,F401
from . import status as _status  # noqa: E402,F401
from . import tasks as _tasks  # noqa: E402,F401
from . import usage as _usage  # noqa: E402,F401

__all__ = [
    "COMMANDS",
    "CommandExecution",
    "CommandMeta",
    "PORTED_COMMANDS",
    "build_command_backlog",
    "built_in_command_names",
    "command_names",
    "execute_command",
    "find_commands",
    "get_command",
    "get_commands",
    "lookup",
    "register",
    "render_command_index",
]
