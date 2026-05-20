from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from src.context_system.context_analyzer import get_context_window_for_model
from src.token_estimation import count_messages_tokens, count_tokens

ContextPressure = Literal["low", "medium", "high", "critical"]


@dataclass(frozen=True)
class ContextBudget:
    model: str
    context_window: int
    used_tokens: int
    reserved_output_tokens: int
    available_input_tokens: int
    remaining_input_tokens: int
    pressure: ContextPressure
    percent_used: float
    memory_budget_tokens: int
    should_microcompact: bool
    should_compact: bool
    hard_overflow: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def estimate_context_budget(
    *,
    messages: list[dict[str, Any]],
    model: str,
    system_prompt: str = "",
    projected_extra_prompt: str = "",
    reserved_output_tokens: int = 4096,
    auto_compact_threshold: float = 0.75,
    critical_threshold: float = 0.9,
) -> ContextBudget:
    context_window = get_context_window_for_model(model)
    reserved = min(max(1024, reserved_output_tokens), max(1024, context_window // 4))
    available_input = max(1, context_window - reserved)
    used = (
        count_messages_tokens(messages)
        + count_tokens(system_prompt)
        + count_tokens(projected_extra_prompt)
    )
    remaining = max(0, available_input - used)
    percent = used / available_input if available_input > 0 else 1.0

    if percent >= critical_threshold:
        pressure: ContextPressure = "critical"
    elif percent >= auto_compact_threshold:
        pressure = "high"
    elif percent >= 0.55:
        pressure = "medium"
    else:
        pressure = "low"

    memory_budget = _memory_budget_for_pressure(
        remaining_input_tokens=remaining,
        context_window=context_window,
        pressure=pressure,
    )
    return ContextBudget(
        model=model,
        context_window=context_window,
        used_tokens=used,
        reserved_output_tokens=reserved,
        available_input_tokens=available_input,
        remaining_input_tokens=remaining,
        pressure=pressure,
        percent_used=round(percent * 100, 1),
        memory_budget_tokens=memory_budget,
        should_microcompact=pressure in {"medium", "high", "critical"},
        should_compact=pressure in {"high", "critical"},
        hard_overflow=used >= available_input,
    )


def trim_to_token_budget(text: str, max_tokens: int) -> str:
    if max_tokens <= 0 or not text:
        return ""
    if count_tokens(text) <= max_tokens:
        return text.strip()

    # Tokenizers differ by provider. Char trimming is deliberately conservative
    # and then tightened until the estimator says it fits.
    candidate = text[: max(0, max_tokens * 4)].rstrip()
    while candidate and count_tokens(candidate) > max_tokens:
        candidate = candidate[: max(0, int(len(candidate) * 0.85))].rstrip()
    if not candidate:
        return ""
    return candidate + "\n[context trimmed to fit budget]"


def _memory_budget_for_pressure(
    *,
    remaining_input_tokens: int,
    context_window: int,
    pressure: ContextPressure,
) -> int:
    if remaining_input_tokens <= 0:
        return 0
    if pressure == "critical":
        target = min(900, remaining_input_tokens // 3)
    elif pressure == "high":
        target = min(1_600, remaining_input_tokens // 3)
    elif pressure == "medium":
        target = min(3_000, remaining_input_tokens // 2)
    else:
        target = min(6_000, max(1_200, context_window // 40), remaining_input_tokens)
    return max(0, min(target, remaining_input_tokens))
