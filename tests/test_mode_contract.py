from __future__ import annotations

from types import SimpleNamespace

from src.geneva.web_api import JsonApiResult, chat_request_from_payload, dispatch_api_request


def test_mode_profiles_are_user_facing_and_default_medium() -> None:
    from src.services.model_router.modes import DEFAULT_MODE_ID, mode_profile_payloads

    payloads = mode_profile_payloads()
    ids = [item["id"] for item in payloads]

    assert ids == ["low", "medium", "high", "extra_high"]
    assert DEFAULT_MODE_ID == "medium"
    assert [item["label"] for item in payloads] == ["Low", "Medium", "High", "Extra High"]
    assert [item["id"] for item in payloads if item["default"]] == ["medium"]
    for item in payloads:
        assert item["description"]
        assert item["context_budget_tokens"] > 0
        assert item["cost_tier"] in {"low", "balanced", "high", "highest"}
        assert item["latency_tier"] in {"fast", "balanced", "slower", "slowest"}


def test_route_mode_applies_selected_profile(monkeypatch) -> None:
    monkeypatch.delenv("GENEVA_PROVIDER", raising=False)
    monkeypatch.delenv("GENEVA_MODEL", raising=False)
    monkeypatch.delenv("GENEVA_COST_BUDGET", raising=False)

    from src.services.model_router.router import route_mode

    low = route_mode("low", "quick summary")
    high = route_mode("high", "carefully reason through the architecture")

    assert low.mode_id == "low"
    assert low.mode_label == "Low"
    assert low.cost_tier == "low"
    assert high.mode_id == "high"
    assert high.mode_label == "High"
    assert high.context_budget_tokens > low.context_budget_tokens
    assert high.tool_autonomy != low.tool_autonomy
    assert high.reason.startswith("mode:")


def test_api_exposes_user_facing_modes() -> None:
    result = dispatch_api_request(object(), "GET", "/api/modes")  # type: ignore[arg-type]

    assert isinstance(result, JsonApiResult)
    assert result.payload["default_mode_id"] == "medium"  # type: ignore[index]
    modes = result.payload["modes"]  # type: ignore[index]
    assert [item["label"] for item in modes] == ["Low", "Medium", "High", "Extra High"]
    assert all("provider" in item and "model" in item for item in modes)


def test_chat_payload_accepts_mode_id() -> None:
    request, error = chat_request_from_payload({"message": "hi", "mode_id": "high"})

    assert error is None
    assert request is not None
    assert request.mode_id == "high"


def test_session_manager_reconfigures_existing_session_for_mode(monkeypatch) -> None:
    from src.geneva import web_runtime
    from src.geneva.web_runtime import SessionManager

    class _FakeSession:
        def __init__(
            self,
            provider_name: str | None = None,
            model: str | None = None,
            session_id: str | None = None,
            mode_id: str | None = None,
        ) -> None:
            self.session_id = session_id or "session_1"
            self.provider_name = provider_name or "openrouter"
            self.provider = SimpleNamespace(model=model or "deepseek/deepseek-v4-flash")
            self.mode_id = mode_id or "medium"
            self.configured_modes: list[str | None] = []

        def configure_mode(
            self,
            mode_id: str | None,
            *,
            provider_name: str | None = None,
            model: str | None = None,
            user_input: str = "",
        ) -> None:
            del user_input
            self.configured_modes.append(mode_id)
            self.mode_id = mode_id or self.mode_id
            if provider_name:
                self.provider_name = provider_name
            if model:
                self.provider.model = model

    monkeypatch.setattr(SessionManager, "_start_auto_dream_scheduler", lambda self: None)
    monkeypatch.setattr(web_runtime, "GenevaSession", _FakeSession)

    manager = SessionManager()
    first = manager.get(session_id="session_1", mode_id="medium")
    second = manager.get(session_id="session_1", mode_id="low")

    assert second is first
    assert first.configured_modes == ["low"]
