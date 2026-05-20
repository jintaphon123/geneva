from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from src.context_system.context_analyzer import get_context_window_for_model
from src.token_estimation import count_messages_tokens, count_tokens

if TYPE_CHECKING:
    from src.compact_service.service import CompactResult


@dataclass
class AutoCompact:
    threshold: float = 0.7
    cooldown_seconds: float = 60.0
    last_compact_timestamp: float = field(default=0.0)

    async def maybe_compact(
        self,
        *,
        conversation: Any,
        provider: Any,
        model: str,
        system_prompt: str = "",
        session_id: str | None = None,
    ) -> "CompactResult | None":
        from src.compact_service.service import compact_conversation

        used = count_messages_tokens(conversation.get_messages()) + count_tokens(system_prompt)
        max_tokens = get_context_window_for_model(model)
        if max_tokens <= 0 or used / max_tokens < self.threshold:
            return None
        now = time.time()
        if now - self.last_compact_timestamp < self.cooldown_seconds:
            return None
        self.last_compact_timestamp = now
        return await compact_conversation(
            conversation=conversation,
            provider=provider,
            model=model,
            trigger="auto",
            fresh_tail_messages=6,
            session_id=session_id,
        )
