"""Model router — task-aware provider and model selection."""
from __future__ import annotations

from src.services.model_router.health import (
    ProviderHealth,
    get_all_health,
    get_health,
    record_provider_outcome,
    should_switch_provider,
)
from src.services.model_router.router import (
    RouteDecision,
    TaskType,
    classify_model_tier,
    classify_task_type,
    record_token_usage,
    route,
    route_fallback,
    route_mode,
)
from src.services.model_router.modes import (
    DEFAULT_MODE_ID,
    ModeProfile,
    available_mode_profiles,
    get_mode_profile,
    mode_profile_payloads,
    normalize_mode_id,
)

__all__ = [
    "ProviderHealth",
    "RouteDecision",
    "TaskType",
    "DEFAULT_MODE_ID",
    "ModeProfile",
    "available_mode_profiles",
    "classify_model_tier",
    "classify_task_type",
    "get_mode_profile",
    "get_all_health",
    "get_health",
    "mode_profile_payloads",
    "normalize_mode_id",
    "record_provider_outcome",
    "record_token_usage",
    "route",
    "route_fallback",
    "route_mode",
    "should_switch_provider",
]
