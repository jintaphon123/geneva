from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

if False:  # pragma: no cover
    from src.hooks.post_sampling_hooks import PostSamplingHook


@dataclass
class TokenUsage:
    input: int = 0
    output: int = 0
    cache_read: int = 0
    cache_write: int = 0


_state_lock = threading.RLock()
_thread_local = threading.local()

session_id: str = str(uuid4())
total_cost_usd: float = 0.0
per_model_tokens: dict[str, TokenUsage] = {}
hook_registry: list["PostSamplingHook"] = []
api_duration: float = 0.0
tool_duration: float = 0.0
lines_added: int = 0
lines_removed: int = 0
plan_mode: bool = False
auto_mode: bool = False
coordinator_mode: bool = False
current_working_directory: Path = Path.cwd()


def _touch_thread_context() -> None:
    _thread_local.session_id = session_id
    _thread_local.cwd = current_working_directory


def feature_enabled(name: str, default: bool = False) -> bool:
    normalized = name.upper()
    if not normalized.startswith("GENEVA_FEATURE_"):
        normalized = f"GENEVA_FEATURE_{normalized}"
    value = os.getenv(normalized)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_session_id() -> str:
    with _state_lock:
        return session_id


def regenerate_session_id() -> str:
    global session_id
    with _state_lock:
        previous = session_id
        session_id = str(uuid4())
        _thread_local.previous_session_id = previous
        _touch_thread_context()
        return session_id


def add_to_total_cost_state(
    model: str,
    cost_usd: float,
    input_tokens: int,
    output_tokens: int,
    cache_read: int,
    cache_write: int,
) -> None:
    global total_cost_usd
    with _state_lock:
        usage = per_model_tokens.setdefault(model, TokenUsage())
        usage.input += max(0, input_tokens)
        usage.output += max(0, output_tokens)
        usage.cache_read += max(0, cache_read)
        usage.cache_write += max(0, cache_write)
        total_cost_usd += float(cost_usd)


def get_total_cost_usd() -> float:
    with _state_lock:
        return total_cost_usd


def reset_cost_state() -> None:
    global total_cost_usd
    with _state_lock:
        total_cost_usd = 0.0
        per_model_tokens.clear()


def register_hook_callbacks(hooks: list["PostSamplingHook"]) -> None:
    with _state_lock:
        hook_registry.extend(hooks)


def get_registered_hooks() -> list["PostSamplingHook"]:
    with _state_lock:
        return list(hook_registry)


def clear_registered_hooks() -> None:
    with _state_lock:
        hook_registry.clear()


def add_to_tool_duration(seconds: float) -> None:
    global tool_duration
    with _state_lock:
        tool_duration += max(0.0, float(seconds))


def add_to_total_lines_changed(added: int, removed: int) -> None:
    global lines_added, lines_removed
    with _state_lock:
        lines_added += max(0, added)
        lines_removed += max(0, removed)


def set_current_working_directory(path: str | Path) -> Path:
    global current_working_directory
    with _state_lock:
        current_working_directory = Path(path).expanduser().resolve()
        _touch_thread_context()
        return current_working_directory


def set_api_duration(seconds: float) -> float:
    global api_duration
    with _state_lock:
        api_duration = max(0.0, float(seconds))
        return api_duration


def increment_api_duration(seconds: float) -> float:
    global api_duration
    with _state_lock:
        api_duration += max(0.0, float(seconds))
        return api_duration


def telemetry_noop(*_: object, **__: object) -> None:
    return None


def init_datadog(*args: object, **kwargs: object) -> None:
    telemetry_noop(*args, **kwargs)


def init_otel(*args: object, **kwargs: object) -> None:
    telemetry_noop(*args, **kwargs)


def emit_telemetry_event(*args: object, **kwargs: object) -> None:
    telemetry_noop(*args, **kwargs)


def flush_telemetry(*args: object, **kwargs: object) -> None:
    telemetry_noop(*args, **kwargs)


_touch_thread_context()
