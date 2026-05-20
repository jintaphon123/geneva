from __future__ import annotations

from dataclasses import asdict, dataclass


DEFAULT_MODE_ID = "medium"


@dataclass(frozen=True)
class ModeProfile:
    id: str
    label: str
    description: str
    provider_name: str
    primary_model: str
    fallback_model: str
    context_budget_tokens: int
    tool_autonomy: str
    research_depth: str
    cost_tier: str
    latency_tier: str
    background_policy: str
    is_default: bool = False

    def to_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["provider"] = self.provider_name
        payload["model"] = self.primary_model
        payload["default"] = self.is_default
        return payload


_MODE_PROFILES: dict[str, ModeProfile] = {
    "low": ModeProfile(
        id="low",
        label="Low",
        description="Fast, light reasoning",
        provider_name="openrouter",
        primary_model="openrouter/free",
        fallback_model="deepseek/deepseek-v4-flash",
        context_budget_tokens=24_000,
        tool_autonomy="minimal",
        research_depth="light",
        cost_tier="low",
        latency_tier="fast",
        background_policy="off",
    ),
    "medium": ModeProfile(
        id="medium",
        label="Medium",
        description="Balanced default",
        provider_name="openrouter",
        primary_model="deepseek/deepseek-v4-flash",
        fallback_model="openrouter/free",
        context_budget_tokens=64_000,
        tool_autonomy="guided",
        research_depth="standard",
        cost_tier="balanced",
        latency_tier="balanced",
        background_policy="manual",
        is_default=True,
    ),
    "high": ModeProfile(
        id="high",
        label="High",
        description="More careful work",
        provider_name="openrouter",
        primary_model="deepseek/deepseek-v4-flash",
        fallback_model="openrouter/free",
        context_budget_tokens=96_000,
        tool_autonomy="expanded",
        research_depth="deep",
        cost_tier="high",
        latency_tier="slower",
        background_policy="ask_first",
    ),
    "extra_high": ModeProfile(
        id="extra_high",
        label="Extra High",
        description="Deepest pass",
        provider_name="openrouter",
        primary_model="deepseek/deepseek-v4-flash",
        fallback_model="openrouter/free",
        context_budget_tokens=128_000,
        tool_autonomy="max_visible_control",
        research_depth="exhaustive",
        cost_tier="highest",
        latency_tier="slowest",
        background_policy="ask_first",
    ),
}


def normalize_mode_id(mode_id: str | None) -> str:
    normalized = str(mode_id or "").strip().lower().replace(" ", "_").replace("-", "_")
    return normalized if normalized in _MODE_PROFILES else DEFAULT_MODE_ID


def get_mode_profile(mode_id: str | None) -> ModeProfile:
    return _MODE_PROFILES[normalize_mode_id(mode_id)]


def available_mode_profiles() -> list[ModeProfile]:
    return list(_MODE_PROFILES.values())


def mode_profile_payloads() -> list[dict[str, object]]:
    return [profile.to_payload() for profile in available_mode_profiles()]
