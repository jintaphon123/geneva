"""R8.1 — Benchmark runner framework for Geneva capability evals."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


@dataclass
class BenchmarkCase:
    id: str
    prompt: str
    score_fn: Callable[[str], float]
    tags: list[str] = field(default_factory=list)
    weight: float = 1.0


@dataclass
class BenchmarkResult:
    case_id: str
    score: float
    passed: bool
    details: str = ""
    latency_ms: float = 0.0


@dataclass
class BenchmarkReport:
    suite_name: str
    timestamp: str
    results: list[BenchmarkResult]
    overall_score: float
    pass_rate: float

    def save(self, report_dir: Path | None = None) -> Path:
        if report_dir is None:
            report_dir = Path(__file__).parent / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        safe_ts = self.timestamp.replace(":", "-").replace(".", "-").replace("+", "p")
        fname = f"{self.suite_name}-{safe_ts}.json"
        path = report_dir / fname
        path.write_text(
            json.dumps({
                "suite_name": self.suite_name,
                "timestamp": self.timestamp,
                "overall_score": self.overall_score,
                "pass_rate": self.pass_rate,
                "results": [
                    {
                        "case_id": r.case_id,
                        "score": r.score,
                        "passed": r.passed,
                        "details": r.details,
                        "latency_ms": r.latency_ms,
                    }
                    for r in self.results
                ],
            }, indent=2),
            encoding="utf-8",
        )
        return path

    def check_regression(self, baseline_path: Path, max_drop: float = 0.05) -> bool:
        """True if overall_score >= baseline - max_drop. True if no baseline."""
        if not baseline_path.exists():
            return True
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        return self.overall_score >= (baseline.get("overall_score", 0.0) - max_drop)


class BenchmarkRunner:
    def __init__(self, suite_name: str, threshold: float = 0.7):
        self.suite_name = suite_name
        self.threshold = threshold

    def run(self, cases: list[BenchmarkCase], actual_outputs: list[str]) -> BenchmarkReport:
        assert len(cases) == len(actual_outputs)
        results = []
        total_weight = sum(c.weight for c in cases)
        weighted_sum = 0.0
        for case, output in zip(cases, actual_outputs):
            t0 = time.monotonic()
            try:
                score = float(case.score_fn(output))
                score = max(0.0, min(1.0, score))
            except Exception:
                score = 0.0
            lat = (time.monotonic() - t0) * 1000
            passed = score >= self.threshold
            results.append(BenchmarkResult(
                case_id=case.id,
                score=score,
                passed=passed,
                details=f"len={len(output)}",
                latency_ms=lat,
            ))
            weighted_sum += score * case.weight
        overall = weighted_sum / total_weight if total_weight > 0 else 0.0
        pass_rate = sum(1 for r in results if r.passed) / len(results) if results else 0.0
        return BenchmarkReport(
            suite_name=self.suite_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            results=results,
            overall_score=overall,
            pass_rate=pass_rate,
        )

    @staticmethod
    def keyword_scorer(keywords: list[str]) -> Callable[[str], float]:
        def score(response: str) -> float:
            if not keywords:
                return 1.0
            lower = response.lower()
            return sum(1 for kw in keywords if kw.lower() in lower) / len(keywords)
        return score

    @staticmethod
    def exact_match_scorer(expected: str) -> Callable[[str], float]:
        def score(response: str) -> float:
            return 1.0 if expected.lower() in response.lower() else 0.0
        return score

    @staticmethod
    def regex_scorer(pattern: str) -> Callable[[str], float]:
        import re
        compiled = re.compile(pattern, re.IGNORECASE | re.DOTALL)
        def score(response: str) -> float:
            return 1.0 if compiled.search(response) else 0.0
        return score
