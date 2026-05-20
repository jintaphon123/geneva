"""Model calibration suite — R6.1.

These tests are marked @pytest.mark.calibration and are SKIPPED in normal CI.
Run with: python -m pytest tests/calibration/ -m calibration --run-calibration

They validate real model behavior against known prompts per tier.
"""
from __future__ import annotations

import os
import unittest

import pytest


# Guard: skip unless explicitly opted in
CALIBRATION_ENABLED = os.environ.get("GENEVA_RUN_CALIBRATION") == "1"
skip_if_no_calibration = pytest.mark.skipif(
    not CALIBRATION_ENABLED,
    reason="Set GENEVA_RUN_CALIBRATION=1 to run calibration tests",
)


# ── Tier classification tests (no API needed) ─────────────────────────────────

class TestModelTierClassification(unittest.TestCase):
    """Verify tier classification matches expected heuristics."""

    def test_sonnet_is_strong(self):
        from src.services.model_normalizer.capability_registry import classify_model_tier
        self.assertEqual(classify_model_tier("claude-sonnet-4-6"), "strong")

    def test_haiku_is_medium(self):
        from src.services.model_normalizer.capability_registry import classify_model_tier
        self.assertEqual(classify_model_tier("claude-haiku-4-5"), "medium")

    def test_gpt4o_mini_is_medium(self):
        from src.services.model_normalizer.capability_registry import classify_model_tier
        self.assertEqual(classify_model_tier("gpt-4o-mini"), "medium")

    def test_unknown_model_is_weak(self):
        from src.services.model_normalizer.capability_registry import classify_model_tier
        self.assertEqual(classify_model_tier("unknown-model-xyz"), "weak")

    def test_tier_override_env(self):
        from src.services.model_normalizer.capability_registry import classify_model_tier
        os.environ["GENEVA_MODEL_TIER_OVERRIDE"] = "weak"
        try:
            self.assertEqual(classify_model_tier("claude-sonnet-4-6"), "weak")
        finally:
            del os.environ["GENEVA_MODEL_TIER_OVERRIDE"]


# ── Compensation config tests (no API needed) ─────────────────────────────────

class TestCompensationConfig(unittest.TestCase):
    """Verify compensation configs have correct values per tier."""

    def test_strong_tier_no_compensation(self):
        from src.services.model_normalizer.compensation_mode import get_compensation_config
        cfg = get_compensation_config("strong")
        self.assertIsNone(cfg.max_turns_cap)
        self.assertFalse(cfg.add_tool_json_examples)
        self.assertFalse(cfg.restrict_destructive)

    def test_medium_tier_has_turns_cap(self):
        from src.services.model_normalizer.compensation_mode import get_compensation_config
        cfg = get_compensation_config("medium")
        self.assertIsNotNone(cfg.max_turns_cap)
        self.assertLessEqual(cfg.max_turns_cap, 10)
        self.assertTrue(cfg.add_tool_json_examples)

    def test_weak_tier_most_restrictive(self):
        from src.services.model_normalizer.compensation_mode import get_compensation_config
        cfg = get_compensation_config("weak")
        self.assertIsNotNone(cfg.max_turns_cap)
        self.assertTrue(cfg.restrict_destructive)
        self.assertTrue(cfg.add_tool_json_examples)

    def test_disable_env_returns_strong(self):
        """R6.4: GENEVA_DISABLE_MODEL_COMPENSATION=1 returns strong config for any tier."""
        from src.services.model_normalizer.compensation_mode import get_compensation_config
        os.environ["GENEVA_DISABLE_MODEL_COMPENSATION"] = "1"
        try:
            cfg_weak = get_compensation_config("weak")
            cfg_med  = get_compensation_config("medium")
            self.assertIsNone(cfg_weak.max_turns_cap)
            self.assertIsNone(cfg_med.max_turns_cap)
            self.assertFalse(cfg_weak.restrict_destructive)
        finally:
            del os.environ["GENEVA_DISABLE_MODEL_COMPENSATION"]

    def test_verify_cycles_by_tier(self):
        """R6.2: verify cycles — strong=0, medium=1, weak=2."""
        from src.services.model_normalizer.compensation_mode import get_compensation_config
        self.assertEqual(get_compensation_config("strong").max_verify_cycles, 0)
        self.assertEqual(get_compensation_config("medium").max_verify_cycles, 1)
        self.assertEqual(get_compensation_config("weak").max_verify_cycles, 2)


# ── Repair function tests (no API needed) ─────────────────────────────────────

class TestToolCallRepair(unittest.TestCase):
    """Verify repair_tool_call_json handles common malformed inputs."""

    def test_valid_json_passthrough(self):
        from src.services.model_normalizer.tool_call_repair import repair_tool_call_json
        result = repair_tool_call_json('{"key": "value"}')
        self.assertEqual(result, {"key": "value"})

    def test_markdown_fence_stripped(self):
        from src.services.model_normalizer.tool_call_repair import repair_tool_call_json
        result = repair_tool_call_json('```json\n{"key": "value"}\n```')
        self.assertEqual(result, {"key": "value"})

    def test_json_embedded_in_text(self):
        from src.services.model_normalizer.tool_call_repair import repair_tool_call_json
        result = repair_tool_call_json('Here is the result: {"key": "value"} done.')
        self.assertEqual(result, {"key": "value"})

    def test_invalid_returns_none(self):
        from src.services.model_normalizer.tool_call_repair import repair_tool_call_json
        self.assertIsNone(repair_tool_call_json("not json at all"))

    def test_none_input_returns_none(self):
        from src.services.model_normalizer.tool_call_repair import repair_tool_call_json
        self.assertIsNone(repair_tool_call_json(None))


# ── Live calibration prompts (require GENEVA_RUN_CALIBRATION=1) ───────────────

@skip_if_no_calibration
class TestLiveModelCalibration(unittest.TestCase):
    """Live API calibration — skipped unless GENEVA_RUN_CALIBRATION=1.

    Validates that each model tier meets minimum quality bars.
    """

    CLASSIFY_PROMPTS = [
        ("Classify this email as spam or not spam: 'Win $1000 now!'", "spam"),
        ("Extract the city from: 'I live in Bangkok, Thailand'", "Bangkok"),
        ("Tag this as positive or negative: 'I love this product!'", "positive"),
    ]

    REASON_PROMPTS = [
        "Explain in 3 sentences why the sky is blue.",
        "What are the trade-offs between SQL and NoSQL databases?",
    ]

    def _get_session(self):
        from src.geneva.session import GenevaSession
        return GenevaSession()

    def test_classify_prompts_get_response(self):
        """Each classify prompt returns a non-empty response."""
        session = self._get_session()
        for prompt, _ in self.CLASSIFY_PROMPTS:
            result = session.chat(prompt)
            self.assertTrue(len(result.text or "") > 0, f"Empty response for: {prompt}")

    def test_tool_json_repair_under_load(self):
        """Verify repair triggers when model returns malformed tool JSON."""
        from src.services.model_normalizer.tool_call_repair import repair_tool_call_json
        malformed_inputs = [
            '```json\n{"command": "ls -la"}\n```',
            'The args are: {"command": "echo hello"}',
            '{"command": "pwd"}',
        ]
        for raw in malformed_inputs:
            result = repair_tool_call_json(raw)
            self.assertIsNotNone(result, f"Repair failed for: {raw}")
            self.assertIsInstance(result, dict)
