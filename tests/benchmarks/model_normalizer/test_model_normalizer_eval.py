"""R8.6 — Model normalizer eval: repair success rate ≥90%, compensation correctness.

No live API calls. All tests use direct function calls or mocks.
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from tests.benchmarks.runner import BenchmarkCase, BenchmarkRunner

MALFORMED_JSONS: list[str] = [
    '```json\n{"command": "ls -la"}\n```',
    '```json\n{"path": "/tmp"}\n```',
    'The args are: {"command": "pwd"}',
    'Here is the tool call: {"key": "value", "nested": {"a": 1}}',
    '  {"command": "echo hello"}  ',
    '\n{"query": "search term"}\n',
    '{"model": "claude-sonnet-4-6", "temperature": 0.7}',
    'Result: {"action": "read", "file": "test.txt"} done.',
    '```\n{"url": "https://example.com"}\n```',
    '{"simple": true}',
]

INVALID_JSONS: list[str] = [
    "not json at all",
    "random text without braces",
    "",
]


class TestToolCallRepairEval(unittest.TestCase):
    """R8.6: repair_tool_call_json success rate benchmark."""

    def test_repair_success_rate_geq_90(self) -> None:
        """repair_tool_call_json should succeed on ≥90% of MALFORMED_JSONS."""
        from src.services.model_normalizer.tool_call_repair import repair_tool_call_json

        successes = [
            raw for raw in MALFORMED_JSONS
            if repair_tool_call_json(raw) is not None and isinstance(repair_tool_call_json(raw), dict)
        ]
        success_rate = len(successes) / len(MALFORMED_JSONS)

        runner = BenchmarkRunner("repair-success-rate", threshold=0.5)
        cases = []
        outputs = []
        for i, raw in enumerate(MALFORMED_JSONS):
            result = repair_tool_call_json(raw)
            is_ok = result is not None and isinstance(result, dict)
            fixed_score = 1.0 if is_ok else 0.0
            cases.append(BenchmarkCase(
                id=f"repair_{i}",
                prompt=raw[:40],
                score_fn=lambda r, s=fixed_score: s,
            ))
            outputs.append(str(result or ""))

        report = runner.run(cases, outputs)
        with tempfile.TemporaryDirectory() as tmp:
            report.save(Path(tmp))

        self.assertGreaterEqual(
            success_rate, 0.9,
            f"Repair rate {success_rate:.2f} ({len(successes)}/{len(MALFORMED_JSONS)}) < 0.90",
        )

    def test_invalid_json_returns_none(self) -> None:
        """Truly unparseable text returns None."""
        from src.services.model_normalizer.tool_call_repair import repair_tool_call_json

        for raw in INVALID_JSONS:
            result = repair_tool_call_json(raw)
            self.assertIsNone(result, f"Expected None for empty/plain text '{raw}', got {result}")

    def test_repair_benchmark_report_score(self) -> None:
        """BenchmarkReport for repair suite shows ≥90% score."""
        from src.services.model_normalizer.tool_call_repair import repair_tool_call_json

        runner = BenchmarkRunner("repair-report", threshold=0.5)
        cases = []
        outputs = []
        for i, raw in enumerate(MALFORMED_JSONS):
            result = repair_tool_call_json(raw)
            is_ok = result is not None and isinstance(result, dict)
            s = 1.0 if is_ok else 0.0
            cases.append(BenchmarkCase(
                id=f"r{i}",
                prompt=raw[:30],
                score_fn=lambda resp, score=s: score,
            ))
            outputs.append(str(result or ""))

        report = runner.run(cases, outputs)
        self.assertGreaterEqual(report.overall_score, 0.9)


class TestModelNormalizerCompensation(unittest.TestCase):
    """R8.6: Compensation mode triggers correctly per tier."""

    def test_haiku_gets_compensation(self) -> None:
        from src.services.model_normalizer.capability_registry import classify_model_tier
        from src.services.model_normalizer.compensation_mode import get_compensation_config

        tier = classify_model_tier("claude-haiku-4-5")
        cfg = get_compensation_config(tier)
        self.assertTrue(cfg.add_tool_json_examples, "Haiku should receive tool JSON examples")
        self.assertIsNotNone(cfg.max_turns_cap, "Haiku should have a turns cap")

    def test_gpt4o_mini_gets_compensation(self) -> None:
        from src.services.model_normalizer.capability_registry import classify_model_tier
        from src.services.model_normalizer.compensation_mode import get_compensation_config

        tier = classify_model_tier("gpt-4o-mini")
        cfg = get_compensation_config(tier)
        self.assertTrue(cfg.add_tool_json_examples)

    def test_sonnet_fast_path(self) -> None:
        from src.services.model_normalizer.capability_registry import classify_model_tier
        from src.services.model_normalizer.compensation_mode import get_compensation_config

        tier = classify_model_tier("claude-sonnet-4-6")
        cfg = get_compensation_config(tier)
        self.assertIsNone(cfg.max_turns_cap, "Sonnet should have no turns cap")
        self.assertFalse(cfg.add_tool_json_examples)

    def test_compensation_disabled_env(self) -> None:
        from src.services.model_normalizer.compensation_mode import get_compensation_config

        os.environ["GENEVA_DISABLE_MODEL_COMPENSATION"] = "1"
        try:
            cfg = get_compensation_config("weak")
            self.assertIsNone(cfg.max_turns_cap)
            self.assertFalse(cfg.add_tool_json_examples)
        finally:
            del os.environ["GENEVA_DISABLE_MODEL_COMPENSATION"]

    def test_all_tiers_have_verify_cycles_set(self) -> None:
        from src.services.model_normalizer.compensation_mode import get_compensation_config

        self.assertEqual(get_compensation_config("strong").max_verify_cycles, 0)
        self.assertEqual(get_compensation_config("medium").max_verify_cycles, 1)
        self.assertEqual(get_compensation_config("weak").max_verify_cycles, 2)
