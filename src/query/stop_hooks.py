from __future__ import annotations

import logging
from collections import deque
from typing import Callable

from src.bootstrap.state import per_model_tokens

from .config import QueryConfig

logger = logging.getLogger(__name__)

StopHook = Callable[[], bool]

_stop_hooks: list[StopHook] = []
_signal_history: deque[str] = deque(maxlen=64)


def register_stop_hook(hook: StopHook) -> None:
    _stop_hooks.append(hook)


def check_stop_hooks() -> bool:
    for hook in list(_stop_hooks):
        try:
            if hook():
                return True
        except Exception:
            logger.exception("Stop hook failed")
    return False


def record_stop_signal(signal: str) -> None:
    _signal_history.append(signal)


def loop_detector_hook(max_consecutive_identical: int = 3) -> StopHook:
    threshold = max(2, max_consecutive_identical)

    def _hook() -> bool:
        if len(_signal_history) < threshold:
            return False
        tail = list(_signal_history)[-threshold:]
        return len(set(tail)) == 1

    return _hook


def budget_exceeded_hook(config: QueryConfig) -> StopHook:
    def _hook() -> bool:
        used_tokens = sum(
            usage.input + usage.output + usage.cache_read + usage.cache_write
            for usage in per_model_tokens.values()
        )
        return used_tokens >= config.max_tokens

    return _hook
