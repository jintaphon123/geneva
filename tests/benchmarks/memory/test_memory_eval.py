"""R8.4 — Memory retention and conflict detection eval.

No live API. Uses temp brain.db set by conftest (GENEVA_BRAIN_DB_PATH).
"""
from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from tests.benchmarks.runner import BenchmarkCase, BenchmarkRunner


FACTS: list[str] = [
    "Bond is a 3rd-year Mechanical Engineering student at Kasetsart University.",
    "Geneva is a model-agnostic personal AI cognitive runtime.",
    "The brain.db is stored at the dot-geneva directory in the user home folder.",
    "Bond's location is Muang Thong Thani Pak Kret Nonthaburi Thailand.",
    "Bond's personal north star is deep structural AI mastery.",
    "The Geneva backend runs on Python at port 8765.",
    "The Geneva frontend is built with React and TypeScript.",
    "Bond is the sole architect and builder of the Second Brain project.",
    "The Second Brain project aims to be an AI-to-AI collaboration protocol.",
    "Bond's rental business is called Impact Arena Condo.",
    "TW EV is Bond's electric bicycle import project currently paused.",
    "Geneva uses FTS5 SQLite full-text search for memory retrieval.",
    "The GENEVA_GHOST env var disables trace writes for privacy.",
    "The GENEVA_DEBUG env var logs context assembly order to stderr.",
    "Claude Sonnet 4.6 is classified as a strong tier model in Geneva.",
    "Haiku 4.5 is classified as a medium tier model in Geneva.",
    "The TASK_MODEL_MAP routes classify and extract tasks to cheap models.",
    "Memory trust score is computed from confidence source weight and recency.",
    "Geneva Phase R8 adds an eval and benchmark harness capability.",
    "Bond's email address is jintaphonteosuwan at gmail dot com.",
]


def _query(fact: str) -> str:
    words = [w.strip(".,'\"") for w in fact.split() if len(w.strip(".,'\"")) > 4]
    return " ".join(words[-4:])


class TestMemoryRetentionEval(unittest.TestCase):
    """Write 20 facts → search → verify retention ≥95%."""

    def _write_facts(self) -> None:
        from src.memdir.brain_engine import init_db, remember
        init_db()
        for fact in FACTS:
            asyncio.run(remember(
                content=fact,
                type="user",
                source_type="user_direct",
                confidence=0.9,
            ))

    def test_retention_20_facts(self) -> None:
        from src.memdir.brain_engine import search as mem_search
        self._write_facts()
        runner = BenchmarkRunner("memory-retention", threshold=0.5)
        cases: list[BenchmarkCase] = []
        outputs: list[str] = []
        for i, fact in enumerate(FACTS):
            q = _query(fact)
            results = mem_search(q)
            combined = " ".join(m.content for m in results)
            key_words = [w for w in fact.split() if len(w) > 4][:3]
            cases.append(BenchmarkCase(
                id=f"fact_{i}",
                prompt=q,
                score_fn=BenchmarkRunner.keyword_scorer(key_words),
            ))
            outputs.append(combined)
        report = runner.run(cases, outputs)
        with tempfile.TemporaryDirectory() as tmp:
            report.save(Path(tmp))
        self.assertGreaterEqual(
            report.overall_score, 0.95,
            f"Retention {report.overall_score:.2f} < 0.95 (pass_rate={report.pass_rate:.2f})",
        )

    def test_conflict_detection_trust_score(self) -> None:
        from src.memdir.brain_engine import init_db, remember, search as mem_search, _compute_trust_score
        init_db()
        asyncio.run(remember(
            content="Bond is a 2nd-year student at Kasetsart University.",
            type="user",
            source_type="user_direct",
            confidence=0.6,
        ))
        asyncio.run(remember(
            content="Bond is a 3rd-year student at Kasetsart University.",
            type="user",
            source_type="user_direct",
            confidence=0.95,
        ))
        results = mem_search("Bond year student Kasetsart")
        self.assertGreater(len(results), 0, "No results for conflict query")
        if len(results) >= 2:
            trust_scores = [(_compute_trust_score(m), m) for m in results[:2]]
            trust_scores.sort(key=lambda x: x[0], reverse=True)
            top_content = trust_scores[0][1].content
            self.assertIn(
                "3rd", top_content,
                f"Expected 3rd-year as top trust result, got: {top_content}",
            )


class TestBenchmarkRunnerUnit(unittest.TestCase):
    """Unit tests for runner.py."""

    def test_keyword_scorer_full_match(self) -> None:
        scorer = BenchmarkRunner.keyword_scorer(["hello", "world"])
        self.assertEqual(scorer("Hello World!"), 1.0)

    def test_keyword_scorer_partial_match(self) -> None:
        scorer = BenchmarkRunner.keyword_scorer(["hello", "world"])
        self.assertEqual(scorer("hello only"), 0.5)

    def test_keyword_scorer_no_match(self) -> None:
        scorer = BenchmarkRunner.keyword_scorer(["hello", "world"])
        self.assertEqual(scorer("nothing here"), 0.0)

    def test_exact_match_scorer_hit(self) -> None:
        scorer = BenchmarkRunner.exact_match_scorer("geneva")
        self.assertEqual(scorer("Geneva is a runtime"), 1.0)

    def test_exact_match_scorer_miss(self) -> None:
        scorer = BenchmarkRunner.exact_match_scorer("geneva")
        self.assertEqual(scorer("nothing matches"), 0.0)

    def test_regex_scorer_hit(self) -> None:
        scorer = BenchmarkRunner.regex_scorer(r"\d{4}")
        self.assertEqual(scorer("Year 2026"), 1.0)

    def test_regex_scorer_miss(self) -> None:
        scorer = BenchmarkRunner.regex_scorer(r"\d{4}")
        self.assertEqual(scorer("no numbers"), 0.0)

    def test_runner_weighted_average(self) -> None:
        runner = BenchmarkRunner("test-suite", threshold=0.7)
        cases = [
            BenchmarkCase("c1", "p1", lambda r: 1.0, weight=2.0),
            BenchmarkCase("c2", "p2", lambda r: 0.0, weight=1.0),
        ]
        report = runner.run(cases, ["r1", "r2"])
        self.assertAlmostEqual(report.overall_score, 2 / 3, places=3)
        self.assertEqual(report.pass_rate, 0.5)

    def test_report_save_creates_json(self) -> None:
        runner = BenchmarkRunner("test-save")
        cases = [BenchmarkCase("c1", "p1", lambda r: 1.0)]
        report = runner.run(cases, ["response"])
        with tempfile.TemporaryDirectory() as tmp:
            path = report.save(Path(tmp))
            self.assertTrue(path.exists())
            data = json.loads(path.read_text())
            self.assertEqual(data["suite_name"], "test-save")
            self.assertAlmostEqual(data["overall_score"], 1.0)

    def test_regression_no_baseline_passes(self) -> None:
        runner = BenchmarkRunner("reg")
        report = runner.run([BenchmarkCase("c1", "p1", lambda r: 0.5)], ["r"])
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(report.check_regression(Path(tmp) / "none.json"))

    def test_regression_detects_large_drop(self) -> None:
        runner = BenchmarkRunner("drop")
        report = runner.run([BenchmarkCase("c1", "p1", lambda r: 0.5)], ["r"])
        with tempfile.TemporaryDirectory() as tmp:
            bl = Path(tmp) / "baseline.json"
            bl.write_text(json.dumps({"overall_score": 0.9}))
            self.assertFalse(report.check_regression(bl, max_drop=0.05))

    def test_regression_within_threshold_passes(self) -> None:
        runner = BenchmarkRunner("ok")
        report = runner.run([BenchmarkCase("c1", "p1", lambda r: 0.88)], ["r"])
        with tempfile.TemporaryDirectory() as tmp:
            bl = Path(tmp) / "baseline.json"
            bl.write_text(json.dumps({"overall_score": 0.90}))
            self.assertTrue(report.check_regression(bl, max_drop=0.05))
