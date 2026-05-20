from __future__ import annotations

import inspect
import logging
import os
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from src.bootstrap.state import (
    clear_registered_hooks,
    get_registered_hooks,
    register_hook_callbacks,
)

logger = logging.getLogger(__name__)


@dataclass
class REPLHookContext:
    messages: list[dict]
    system_prompt: str
    tool_use_context: dict
    user_context: dict


PostSamplingHook = Callable[[REPLHookContext], Awaitable[None]]

_MASK_PLACEHOLDER = "[Earlier tool observation masked for context efficiency.]"


def register_post_sampling_hook(hook: PostSamplingHook) -> None:
    register_hook_callbacks([hook])


async def observation_masking_hook(context: REPLHookContext) -> None:
    if os.getenv("GENEVA_DISABLE_OBSERVATION_MASKING", "").strip() == "1":
        return

    keep_last = max(2, int(os.getenv("GENEVA_OBSERVATION_MASK_KEEP_LAST", "8")))
    if len(context.messages) <= keep_last:
        return

    cutoff = len(context.messages) - keep_last
    for index, message in enumerate(context.messages):
        if index >= cutoff:
            break
        if not _is_observation_message(message):
            continue
        context.messages[index] = _mask_message(message)


def _is_observation_message(message: dict[str, Any]) -> bool:
    role = str(message.get("role", "")).lower()
    if role in {"tool", "tool_result", "observation"}:
        return True
    if "tool_name" in message or "tool_use_id" in message:
        return True
    content = message.get("content")
    if isinstance(content, list):
        return any(
            isinstance(block, dict)
            and str(block.get("type", "")).lower() in {"tool_result", "tool_use"}
            for block in content
        )
    return False


def _mask_message(message: dict[str, Any]) -> dict[str, Any]:
    masked = dict(message)
    content = message.get("content")
    if isinstance(content, list):
        masked["content"] = [{"type": "text", "text": _MASK_PLACEHOLDER}]
    else:
        masked["content"] = _MASK_PLACEHOLDER
    masked["_masked"] = True
    return masked


async def execute_post_sampling_hooks(context: REPLHookContext) -> None:
    hooks: list[PostSamplingHook] = [observation_masking_hook, *get_registered_hooks()]
    for hook in hooks:
        try:
            result = hook(context)
            if inspect.isawaitable(result):
                await result
        except Exception:
            logger.exception("Post-sampling hook failed")


def clear_post_sampling_hooks() -> None:
    clear_registered_hooks()
