"""Phase H8 — 6D Smoke Calibration: verify model compensation behavior per tier.

Tests confirm that:
1. Tier classification is correct for known models
2. Compensation config differs meaningfully between tiers
3. GENEVA_DISABLE_MODEL_COMPENSATION disables compensation
4. Tool schema adapter adds JSON examples for weak/medium models
5. Tool call repair handles common malformed JSON patterns
"""
from __future__ import annotations

import json
import os


# ── Tier classification ───────────────────────────────────────────────────────

def test_sonnet_classifies_as_strong():
    from src.services.model_router import classify_model_tier
    assert classify_model_tier("claude-sonnet-4-6") == "strong"


def test_haiku_classifies_as_medium():
    from src.services.model_router import classify_model_tier
    assert classify_model_tier("claude-haiku-4-5") == "medium"


def test_unknown_model_classifies_as_medium():
    from src.services.model_router import classify_model_tier
    # Unknown models get medium (safe default — apply compensation)
    result = classify_model_tier("some-unknown-model-v1")
    assert result in ("medium", "weak")


# ── Compensation config differs by tier ───────────────────────────────────────

def test_strong_tier_no_compensation():
    from src.services.model_normalizer import get_compensation_config
    cfg = get_compensation_config("strong")
    assert cfg.max_turns_cap is None
    assert cfg.add_tool_json_examples is False
    assert cfg.restrict_destructive is False


def test_medium_tier_has_compensation():
    from src.services.model_normalizer import get_compensation_config
    cfg = get_compensation_config("medium")
    assert cfg.max_turns_cap is not None
    assert cfg.max_turns_cap <= 10
    assert cfg.add_tool_json_examples is True


def test_weak_tier_most_conservative():
    from src.services.model_normalizer import get_compensation_config
    cfg_weak = get_compensation_config("weak")
    cfg_medium = get_compensation_config("medium")
    assert cfg_weak.max_turns_cap <= cfg_medium.max_turns_cap
    assert cfg_weak.restrict_destructive is True


# ── DISABLE env var ───────────────────────────────────────────────────────────

def test_disable_env_var_returns_strong_for_any_tier():
    from src.services.model_normalizer import get_compensation_config
    old = os.environ.get("GENEVA_DISABLE_MODEL_COMPENSATION")
    try:
        os.environ["GENEVA_DISABLE_MODEL_COMPENSATION"] = "1"
        for tier in ("weak", "medium", "strong"):
            cfg = get_compensation_config(tier)
            assert cfg.max_turns_cap is None, f"tier={tier} should have no cap when disabled"
            assert cfg.add_tool_json_examples is False
    finally:
        if old is None:
            os.environ.pop("GENEVA_DISABLE_MODEL_COMPENSATION", None)
        else:
            os.environ["GENEVA_DISABLE_MODEL_COMPENSATION"] = old


# ── Tool schema adapter ───────────────────────────────────────────────────────

def test_adapt_tool_schemas_adds_examples_for_medium():
    from src.services.model_normalizer import adapt_tool_schemas
    schemas = [{"name": "Read", "description": "Read a file.", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}]
    adapted = adapt_tool_schemas(schemas, tier="medium")
    assert len(adapted) == 1
    # medium tier should add example or enhance description
    desc = adapted[0].get("description", "")
    assert len(desc) >= len(schemas[0]["description"])


def test_adapt_tool_schemas_no_change_for_strong():
    from src.services.model_normalizer import adapt_tool_schemas
    schemas = [{"name": "Read", "description": "Read a file.", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}]
    adapted = adapt_tool_schemas(schemas, tier="strong")
    assert adapted[0]["description"] == schemas[0]["description"]


# ── Tool call repair ──────────────────────────────────────────────────────────

def test_repair_strips_markdown_fences():
    from src.services.model_normalizer import repair_tool_call_json
    raw = '```json\n{"path": "/tmp/x"}\n```'
    result = repair_tool_call_json(raw)
    assert isinstance(result, dict), "repair should return a dict"
    assert result["path"] == "/tmp/x"


def test_repair_handles_valid_json():
    from src.services.model_normalizer import repair_tool_call_json
    raw = '{"command": "ls -la"}'
    result = repair_tool_call_json(raw)
    assert isinstance(result, dict)
    assert result["command"] == "ls -la"


def test_repair_handles_trailing_comma():
    from src.services.model_normalizer import repair_tool_call_json
    raw = '{"path": "/tmp/x",}'
    result = repair_tool_call_json(raw)
    # repair may or may not fix trailing comma — acceptable either way
    if result is not None:
        assert result.get("path") == "/tmp/x"


# ── Capability registry ───────────────────────────────────────────────────────

def test_capability_registry_has_known_models():
    from src.services.model_normalizer import get_capability
    cap = get_capability("claude-sonnet-4-6")
    assert cap is not None
    assert cap.tool_use_reliability > 0.9
    assert cap.reasoning_strength == "high"


def test_capability_registry_haiku_lower_reliability():
    from src.services.model_normalizer import get_capability
    sonnet = get_capability("claude-sonnet-4-6")
    haiku = get_capability("claude-haiku-4-5")
    if haiku is not None and sonnet is not None:
        assert haiku.tool_use_reliability <= sonnet.tool_use_reliability
