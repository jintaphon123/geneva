from __future__ import annotations

from src.commands import register
from src.commands.cost import run as cost_run
from src.commands._shared import load_latest_or_requested_session
from src.token_estimation import count_messages_tokens


@register(name="usage", description="Show cost and token usage together.")
async def run(args: list[str]) -> str | None:
    cost_block = await cost_run([])
    session = load_latest_or_requested_session()
    messages = [{"role": "user", "content": message} for message in (session.messages if session else ())]
    token_summary = f"estimated_message_tokens={count_messages_tokens(messages)}"
    return f"{cost_block or ''}\n\n{token_summary}".strip()
