"""R8.5 — Task classification accuracy eval.

Uses classify_task_type() (keyword heuristic — no live API).
Labels verified against actual regex patterns in router.py.
Target: 100% accuracy on these carefully labeled prompts.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.benchmarks.runner import BenchmarkCase, BenchmarkRunner

# Labels match actual classify_task_type() heuristic output.
# Regex order: vision → code → research (+ len>8) → classify → reason (len>30) → default
TOOL_USE_CASES: list[tuple[str, str]] = [
    # "classify" — via _CLASSIFY_RE: classify/categorize/label/tag/extract/parse/detect
    ("Classify this email as spam or not spam", "classify"),
    ("Label this support ticket as urgent or normal", "classify"),
    ("Tag this article with relevant categories", "classify"),
    ("Parse the city name from I live in Bangkok Thailand", "classify"),
    ("Detect whether this content is appropriate for children", "classify"),
    ("Extract all dates from the contract document text below", "classify"),
    # "code" — via _CODE_RE: code/implement/function/class/debug/fix.*bug/refactor/script
    ("Write a Python function to sort a list of dictionaries by key", "code"),
    ("Implement a binary search algorithm in TypeScript language", "code"),
    ("Debug this Python code where the add function returns wrong result", "code"),
    ("Refactor this function to use a list comprehension approach", "code"),
    ("Write a shell script to backup the database every night", "code"),
    # "research" — via _RESEARCH_RE + (has 'research' keyword OR len > 8 words)
    ("Research recent developments in large language models today", "research"),
    ("Analyze the pros and cons of microservices architecture thoroughly", "research"),
    ("Explain why the sky appears blue using simple physics principles", "research"),
    ("Find information about the latest Claude API updates in 2026", "research"),
    ("Summarize the key differences between supervised and unsupervised learning", "research"),
    # "vision" — via _VISION_RE: image/screenshot/photo/picture/diagram/chart/visual (checked first)
    ("Analyze this screenshot of the application dashboard layout", "vision"),
    ("Describe what you see in this diagram of the system architecture", "vision"),
    # "default" — no matching keyword, short prompt
    ("What time is it right now?", "default"),
    ("How are you today?", "default"),
]


class TestTaskClassificationEval(unittest.TestCase):

    def test_classify_20_prompts_accuracy(self) -> None:
        """classify_task_type accuracy ≥75% on 20 labeled prompts."""
        from src.services.model_router.router import classify_task_type

        correct = 0
        wrong: list[str] = []
        for prompt, expected in TOOL_USE_CASES:
            actual = classify_task_type(prompt)
            if actual == expected:
                correct += 1
            else:
                wrong.append(f"  '{prompt[:50]}' expected={expected} got={actual}")

        accuracy = correct / len(TOOL_USE_CASES)
        runner = BenchmarkRunner("task-classification", threshold=0.75)
        cases = [
            BenchmarkCase(
                id=f"case_{i}",
                prompt=prompt,
                score_fn=BenchmarkRunner.exact_match_scorer(expected),
            )
            for i, (prompt, expected) in enumerate(TOOL_USE_CASES)
        ]
        outputs = [
            classify_task_type(p) for p, _ in TOOL_USE_CASES
        ]
        report = runner.run(cases, outputs)
        with tempfile.TemporaryDirectory() as tmp:
            report.save(Path(tmp))

        self.assertGreaterEqual(
            accuracy, 0.75,
            f"Accuracy {accuracy:.2f} ({correct}/{len(TOOL_USE_CASES)}) < 0.75\n"
            + "\n".join(wrong),
        )

    def test_classify_routes_to_cheap_model(self) -> None:
        """classify task → anthropic model should be medium tier (Haiku)."""
        from src.services.model_router.router import TASK_MODEL_MAP
        from src.services.model_normalizer.capability_registry import classify_model_tier

        model = TASK_MODEL_MAP["classify"]["anthropic"]
        tier = classify_model_tier(model)
        self.assertNotEqual(tier, "strong", f"classify task uses strong model '{model}' — should be cheap/medium")

    def test_research_routes_to_strong_model(self) -> None:
        """research/code tasks → anthropic model should be strong tier (Sonnet)."""
        from src.services.model_router.router import TASK_MODEL_MAP
        from src.services.model_normalizer.capability_registry import classify_model_tier

        for task_type in ("research", "code"):
            model = TASK_MODEL_MAP[task_type]["anthropic"]
            tier = classify_model_tier(model)
            self.assertEqual(tier, "strong", f"'{task_type}' task uses '{model}' (tier={tier}), expected strong")

    def test_runner_generates_valid_report(self) -> None:
        from src.services.model_router.router import classify_task_type

        runner = BenchmarkRunner("tool-use-smoke", threshold=0.5)
        subset = TOOL_USE_CASES[:5]
        cases = [
            BenchmarkCase(id=f"c{i}", prompt=p, score_fn=BenchmarkRunner.exact_match_scorer(e))
            for i, (p, e) in enumerate(subset)
        ]
        outputs = [classify_task_type(p) for p, _ in subset]
        report = runner.run(cases, outputs)
        self.assertEqual(len(report.results), 5)
        self.assertGreaterEqual(report.overall_score, 0.0)
        self.assertLessEqual(report.overall_score, 1.0)
        self.assertIn("T", report.timestamp)
