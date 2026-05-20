from __future__ import annotations

import os
import re as _re
from dataclasses import dataclass
from typing import Literal

from src.services.model_router.modes import get_mode_profile

TaskType = Literal["classify", "extract", "reason", "research", "code", "vision", "default"]

_VISION_RE = _re.compile(r"\b(image|screenshot|photo|picture|diagram|chart|visual)\b", _re.IGNORECASE)
_CODE_RE = _re.compile(r"\b(code|implement|function|class|debug|fix.*bug|refactor|script)\b", _re.IGNORECASE)
_RESEARCH_RE = _re.compile(r"\b(research|find|search|what is|explain|analyze|compare|summarize)\b", _re.IGNORECASE)
_CLASSIFY_RE = _re.compile(r"\b(classify|categorize|label|tag|extract|parse|detect)\b", _re.IGNORECASE)


def classify_task_type(user_input: str) -> TaskType:
    """Classify user input into a task type for model selection."""
    if _VISION_RE.search(user_input):
        return "vision"
    if _CODE_RE.search(user_input):
        return "code"
    if _RESEARCH_RE.search(user_input) and (_re.search(r"\bresearch\b", user_input, _re.IGNORECASE) or len(user_input.split()) > 8):
        return "research"
    if _CLASSIFY_RE.search(user_input):
        return "classify"
    if len(user_input.split()) > 30:
        return "reason"
    return "default"


DEFAULT_PROVIDER = "openrouter"
DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-5.4",
    "glm": "zai/glm-5",
    "minimax": "MiniMax-M2.7",
    "openrouter": "deepseek/deepseek-v4-flash",
}

TASK_MODEL_MAP: dict[TaskType, dict[str, str]] = {
    "classify": {"anthropic": "claude-haiku-4-5", "openai": "gpt-4o-mini", "openrouter": "deepseek/deepseek-v4-flash"},
    "extract": {"anthropic": "claude-haiku-4-5", "openai": "gpt-4o-mini", "openrouter": "deepseek/deepseek-v4-flash"},
    "reason": {"anthropic": "claude-sonnet-4-6", "openai": "gpt-5.4", "openrouter": "deepseek/deepseek-v4-flash"},
    "research": {"anthropic": "claude-sonnet-4-6", "openai": "gpt-5.4", "openrouter": "deepseek/deepseek-v4-flash"},
    "code": {"anthropic": "claude-sonnet-4-6", "openai": "gpt-5.4", "openrouter": "deepseek/deepseek-v4-flash"},
    "vision": {"anthropic": "claude-sonnet-4-6", "openai": "gpt-5.4", "openrouter": "deepseek/deepseek-v4-flash"},
    "default": {"anthropic": "claude-sonnet-4-6", "openai": "gpt-5.4", "openrouter": "deepseek/deepseek-v4-flash"},
}

_session_token_counts: dict[str, int] = {}


@dataclass(frozen=True)
class RouteDecision:
    provider_name: str
    model: str
    reason: str
    mode_id: str | None = None
    mode_label: str | None = None
    fallback_model: str | None = None
    context_budget_tokens: int | None = None
    tool_autonomy: str | None = None
    research_depth: str | None = None
    cost_tier: str | None = None
    latency_tier: str | None = None
    background_policy: str | None = None


def route(user_input: str) -> RouteDecision:
    """R5.1: Task-aware model routing with cost budget awareness."""
    provider = os.environ.get("GENEVA_PROVIDER", DEFAULT_PROVIDER).lower().strip()
    if provider not in DEFAULT_MODELS:
        provider = DEFAULT_PROVIDER

    # Explicit model override takes priority.
    if os.environ.get("GENEVA_MODEL"):
        model = os.environ["GENEVA_MODEL"].strip()
        return RouteDecision(provider_name=provider, model=model, reason="env_override")

    # R5.2: Cost budget — downgrade to cheap model when budget >= 80%.
    budget_pct = _get_budget_pct()
    if budget_pct >= 0.80:
        cheap_models = {"anthropic": "claude-haiku-4-5", "openai": "gpt-4o-mini", "openrouter": "deepseek/deepseek-v4-flash"}
        model = cheap_models.get(provider, DEFAULT_MODELS[provider])
        return RouteDecision(provider_name=provider, model=model, reason=f"budget_downgrade_{budget_pct:.0%}")

    # R5.1: Task-based model selection.
    task_type = classify_task_type(user_input)
    task_models = TASK_MODEL_MAP.get(task_type, TASK_MODEL_MAP["default"])
    model = task_models.get(provider, DEFAULT_MODELS[provider])

    reason = f"task:{task_type}"
    if os.environ.get("GENEVA_PROVIDER"):
        reason = f"env_provider+task:{task_type}"
    return RouteDecision(provider_name=provider, model=model, reason=reason)


def route_mode(mode_id: str | None, user_input: str = "") -> RouteDecision:
    """Route using a user-facing effort mode.

    Explicit env model/provider overrides remain the advanced escape hatch.
    """
    profile = get_mode_profile(mode_id)
    provider = os.environ.get("GENEVA_PROVIDER", profile.provider_name).lower().strip()
    if provider not in DEFAULT_MODELS:
        provider = profile.provider_name

    if os.environ.get("GENEVA_MODEL"):
        model = os.environ["GENEVA_MODEL"].strip()
        reason = "mode:env_override"
    else:
        budget_pct = _get_budget_pct()
        if budget_pct >= 0.80:
            model = profile.fallback_model
            reason = f"mode:{profile.id}+budget_downgrade_{budget_pct:.0%}"
        else:
            task_type = classify_task_type(user_input)
            model = profile.primary_model
            reason = f"mode:{profile.id}+task:{task_type}"

    return RouteDecision(
        provider_name=provider,
        model=model,
        reason=reason,
        mode_id=profile.id,
        mode_label=profile.label,
        fallback_model=profile.fallback_model,
        context_budget_tokens=profile.context_budget_tokens,
        tool_autonomy=profile.tool_autonomy,
        research_depth=profile.research_depth,
        cost_tier=profile.cost_tier,
        latency_tier=profile.latency_tier,
        background_policy=profile.background_policy,
    )


def record_token_usage(session_id: str, tokens: int) -> None:
    """Record token usage for cost budget tracking."""
    _session_token_counts[session_id] = _session_token_counts.get(session_id, 0) + tokens


def _get_budget_pct() -> float:
    """Return fraction of GENEVA_COST_BUDGET used (0.0 if no budget set)."""
    budget_str = os.environ.get("GENEVA_COST_BUDGET", "")
    if not budget_str:
        return 0.0
    try:
        budget = int(budget_str)
        total_used = sum(_session_token_counts.values())
        return min(1.0, total_used / budget)
    except (ValueError, ZeroDivisionError):
        return 0.0


def _complexity_score(text: str) -> float:
    """Reserved for Phase 3 complexity-based routing. Stub for now."""
    del text
    return 0.5


FALLBACK_PROVIDER_ENV = "GENEVA_FALLBACK_PROVIDER"
FALLBACK_MODEL_ENV = "GENEVA_FALLBACK_MODEL"


def route_fallback() -> RouteDecision | None:
    """Return a fallback RouteDecision if GENEVA_FALLBACK_PROVIDER env is set, else None.

    Used when the primary provider fails with a retryable error (rate limit,
    network, timeout). Auth/quota failures do NOT trigger fallback.
    """
    provider = os.environ.get(FALLBACK_PROVIDER_ENV, "").lower().strip()
    if not provider or provider not in DEFAULT_MODELS:
        return None
    model = os.environ.get(FALLBACK_MODEL_ENV, DEFAULT_MODELS[provider]).strip()
    return RouteDecision(provider_name=provider, model=model, reason="fallback")


from ..model_normalizer.capability_registry import ModelTier
from ..model_normalizer.capability_registry import classify_model_tier as _classify_tier


def classify_model_tier(model: str) -> ModelTier:
    """Classify model into 'strong' / 'medium' / 'weak' tier.

    Wrapper around capability_registry.classify_model_tier for callers that
    already import from model_router.
    """
    return _classify_tier(model)
