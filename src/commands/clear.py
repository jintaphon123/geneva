from __future__ import annotations

from src.bootstrap import state
from src.commands import register


@register(name="clear", description="Clear the terminal and optionally reset the buffer.")
async def run(args: list[str]) -> str | None:
    if "--reset" in args and hasattr(state, "current_conversation"):
        try:
            state.current_conversation.clear()
        except Exception:
            pass
    return "\033[H\033[J"
