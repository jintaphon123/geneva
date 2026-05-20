from __future__ import annotations

from .commands import built_in_command_names, get_commands
from .setup import run_setup
from .tools import get_tools


def build_system_init_message(trusted: bool = True) -> str:
    setup = run_setup(trusted=trusted)
    commands = get_commands()
    tools = get_tools()

    cognition_block = ""
    try:
        from src.geneva.cognition import build_cognition_block
        cognition_block = build_cognition_block("unknown").strip()
    except Exception:
        pass

    system_lines = [
        '# System Init',
        '',
        f'Trusted: {setup.trusted}',
        f'Built-in command names: {len(built_in_command_names())}',
        f'Loaded command entries: {len(commands)}',
        f'Loaded tool entries: {len(tools)}',
        '',
        'Startup steps:',
        *(f'- {step}' for step in setup.setup.startup_steps()),
    ]

    if cognition_block:
        return cognition_block + "\n\n" + '\n'.join(system_lines)
    return '\n'.join(system_lines)
