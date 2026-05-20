"""Initial heuristic model capability registry.

Scores are not ground truth and need calibration after smoke eval:
tests/smoke/model_compensation/
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal


ModelTier = Literal["strong", "medium", "weak"]


@dataclass(frozen=True)
class ModelCapability:
    tool_use_reliability: float
    json_reliability: float
    context_window: int
    supports_vision: bool
    cost_tier: Literal["cheap", "medium", "expensive"]
    reasoning_strength: Literal["low", "medium", "high"]


MODEL_CAPABILITIES: dict[str, ModelCapability] = {
    "claude-opus-4-6": ModelCapability(0.99, 0.98, 200_000, True, "expensive", "high"),
    "claude-opus-4-7": ModelCapability(0.99, 0.98, 200_000, True, "expensive", "high"),
    "claude-sonnet-4-6": ModelCapability(0.98, 0.97, 200_000, True, "medium", "high"),
    "claude-sonnet-4-5": ModelCapability(0.97, 0.96, 200_000, True, "medium", "high"),
    "claude-haiku-4-5": ModelCapability(0.85, 0.80, 200_000, True, "cheap", "medium"),
    "claude-haiku-4-5-20251001": ModelCapability(0.85, 0.80, 200_000, True, "cheap", "medium"),
    "gpt-5.4": ModelCapability(0.97, 0.96, 128_000, True, "expensive", "high"),
    "gpt-4o": ModelCapability(0.96, 0.95, 128_000, True, "medium", "high"),
    "gpt-4o-mini": ModelCapability(0.88, 0.88, 128_000, True, "cheap", "medium"),
    "gpt-5.2": ModelCapability(0.90, 0.89, 128_000, True, "cheap", "medium"),
    "gpt-5.3-codex": ModelCapability(0.92, 0.91, 128_000, False, "medium", "high"),
    "deepseek/deepseek-v4-flash": ModelCapability(0.82, 0.78, 64_000, False, "cheap", "medium"),
    "zai/glm-5": ModelCapability(0.75, 0.72, 32_000, False, "cheap", "low"),
    "minimax-m2.7": ModelCapability(0.78, 0.74, 32_000, False, "cheap", "low"),
}

# Env-var override pattern from claude_code_clone utils/model/modelSupportOverrides.ts.
_TIER_OVERRIDE_ENV = "GENEVA_MODEL_TIER_OVERRIDE"

# Mutable success counters (in-memory, reset on restart).
_success_counters: dict[str, dict[str, int]] = {}
# Keys: model_name -> {"calls": int, "successes": int}


def get_capability(model: str) -> ModelCapability | None:
    """Return ModelCapability for a model string, or None if unknown.

    Tries exact match first, then normalized match by stripping date suffix and
    provider prefix.
    """
    if model in MODEL_CAPABILITIES:
        return MODEL_CAPABILITIES[model]
    normalized = model.lower().split("/")[-1]
    for key in sorted(MODEL_CAPABILITIES, key=len, reverse=True):
        key_normalized = key.lower().split("/")[-1]
        if normalized.startswith(key_normalized) or key_normalized.startswith(normalized):
            return MODEL_CAPABILITIES[key]
    return None


def classify_model_tier(model: str) -> ModelTier:
    """Classify model into strong / medium / weak tier.

    Tier determines whether Geneva applies weak-model compensation (medium/weak)
    or uses the fast path with minimal scaffolding (strong).

    Priority: GENEVA_MODEL_TIER_OVERRIDE env > capability registry > "weak" fallback.
    """
    override = os.environ.get(_TIER_OVERRIDE_ENV, "").strip().lower()
    if override in ("strong", "medium", "weak"):
        return override  # type: ignore[return-value]

    cap = get_capability(model)
    if cap is None:
        return "weak"
    if cap.reasoning_strength == "high":
        return "strong"
    if cap.reasoning_strength == "medium":
        return "medium"
    return "weak"


def record_outcome(model: str, success: bool) -> None:
    """Record a model call outcome for success rate tracking (R5.3)."""
    if model not in _success_counters:
        _success_counters[model] = {"calls": 0, "successes": 0}
    _success_counters[model]["calls"] += 1
    if success:
        _success_counters[model]["successes"] += 1


def get_success_rate(model: str) -> float | None:
    """Return observed success rate for a model, or None if <10 calls."""
    counters = _success_counters.get(model)
    if counters is None or counters["calls"] < 10:
        return None
    return counters["successes"] / counters["calls"]
