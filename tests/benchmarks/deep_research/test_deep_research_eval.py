"""R8.2 — Deep Research eval (requires live API + web access).

Skip by default. Set GENEVA_RUN_BENCHMARKS=1 to run.
Acceptance: citation coverage ≥80%, conflict detection ≥70% on 10 prompts.
"""
from __future__ import annotations

import os
import unittest

import pytest

BENCHMARK_ENABLED = os.environ.get("GENEVA_RUN_BENCHMARKS") == "1"
skip_live = pytest.mark.skipif(
    not BENCHMARK_ENABLED,
    reason="Set GENEVA_RUN_BENCHMARKS=1 to run live benchmark tests",
)

RESEARCH_PROMPTS = [
    "What are the key architectural differences between GPT-4 and Claude?",
    "What is the current state of open-source LLMs in 2026?",
    "Explain the retrieval-augmented generation technique and its limitations.",
    "What are the main security risks in multi-agent AI systems?",
    "How does chain-of-thought prompting improve reasoning in LLMs?",
    "What is the significance of the transformer attention mechanism?",
    "Compare the capabilities of Claude Sonnet vs GPT-4o for code generation.",
    "What are the best practices for prompt injection prevention?",
    "Describe the current landscape of AI agent frameworks in 2026.",
    "What are the trade-offs between fine-tuning and RAG for knowledge injection?",
]


@skip_live
class TestDeepResearchEval(unittest.TestCase):
    """R8.2: citation coverage ≥80%, conflict detection ≥70%.
    Implement after E2+ (Deep Research Pro). Requires GENEVA_RUN_BENCHMARKS=1.
    """

    def test_citation_coverage_geq_80(self) -> None:
        self.skipTest("Implement after E2+ Deep Research Pro")

    def test_conflict_detection_geq_70(self) -> None:
        self.skipTest("Implement after E2+ Deep Research Pro")

    def test_accuracy_on_factual_prompts(self) -> None:
        self.skipTest("LLM judge eval — implement after BenchmarkRunner has judge support")
