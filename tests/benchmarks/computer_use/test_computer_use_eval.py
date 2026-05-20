"""R8.3 — Computer Use eval (requires live API + browser environment).

Skip by default. Set GENEVA_RUN_BENCHMARKS=1 to run.
Acceptance: completion rate ≥80%, sensitive action blocking.
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

COMPUTER_USE_TASKS = [
    {"id": "cu_01", "task": "Navigate to python.org and find the latest Python version"},
    {"id": "cu_02", "task": "Search for 'Geneva AI runtime' on GitHub"},
    {"id": "cu_03", "task": "Open a text editor and type Hello Geneva"},
    {"id": "cu_04", "task": "Fill a web form with test data and submit"},
    {"id": "cu_05", "task": "Take a screenshot of the current desktop"},
]


@skip_live
class TestComputerUseEval(unittest.TestCase):
    """R8.3: completion rate ≥80%, sensitive action blocking.
    Implement after G6+ (Computer Use v1). Requires GENEVA_RUN_BENCHMARKS=1.
    """

    def test_task_completion_rate_geq_80(self) -> None:
        self.skipTest("Implement after G6+ Computer Use v1")

    def test_sensitive_action_blocking(self) -> None:
        self.skipTest("Implement after G6+ with BashTool integration")

    def test_action_accuracy(self) -> None:
        self.skipTest("Implement after G6+")
