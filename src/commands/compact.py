from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from src.agent.conversation import Conversation
from src.commands import register
from src.commands._shared import current_session_id, latest_session_id, load_latest_or_requested_session
from src.compact_service.service import compact_conversation
from src.session_store import DEFAULT_SESSION_DIR
from src.token_estimation import count_messages_tokens


@register(name="compact", description="Compact the current or most recent session.")
async def run(args: list[str]) -> str | None:
    session_id = args[0] if args else current_session_id() or latest_session_id()
    stored = load_latest_or_requested_session(session_id)
    if stored is None:
        return "No session available to compact."

    conversation = Conversation()
    for message in stored.messages:
        conversation.add_user_message(message)

    before = count_messages_tokens(conversation.get_messages())
    result = await compact_conversation(
        conversation=conversation,
        provider=object(),  # fallback summary path
        model="compact-fallback",
        session_id=stored.session_id,
    )
    after = count_messages_tokens(conversation.get_messages())

    path = DEFAULT_SESSION_DIR / f"{stored.session_id}.json"
    payload = {
        "session_id": stored.session_id,
        "messages": tuple(
            block["content"] if isinstance(block, dict) and isinstance(block.get("content"), str) else str(block.get("content"))
            for block in conversation.get_messages()
        ),
        "input_tokens": stored.input_tokens,
        "output_tokens": stored.output_tokens,
    }
    path.write_text(json.dumps(payload, indent=2))
    return f"Compacted: {before} → {after} tokens saved ({max(before - after, 0)})"
