from __future__ import annotations

from src.commands import register
from src.commands._shared import load_latest_or_requested_session, save_session_to_state


@register(name="resume", description="Resume a saved session.")
async def run(args: list[str]) -> str | None:
    stored = load_latest_or_requested_session(args[0] if args else None)
    if stored is None:
        return "No saved session found."
    save_session_to_state(stored)
    return f"Resumed session {stored.session_id} ({len(stored.messages)} turns)"
