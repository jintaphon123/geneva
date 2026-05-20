"""
Skill Eval Runner (EP.1)
Runs a skill against test inputs and scores output quality.
Blocks skill activation if score < threshold.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class SkillEvalCase:
    id: str
    prompt: str
    score_fn: Callable[[str], float]
    expected_keywords: list[str] = field(default_factory=list)
    weight: float = 1.0


@dataclass
class SkillEvalResult:
    case_id: str
    score: float
    passed: bool
    output: str
    error: str | None = None


@dataclass
class SkillEvalReport:
    skill_name: str
    overall_score: float
    pass_rate: float
    results: list[SkillEvalResult]
    threshold: float

    @property
    def passed(self) -> bool:
        return self.overall_score >= self.threshold


class SkillEvalRunner:
    DEFAULT_THRESHOLD = 0.7

    def __init__(self, threshold: float = DEFAULT_THRESHOLD):
        self.threshold = threshold

    def run(
        self,
        skill_name: str,
        cases: list[SkillEvalCase],
        actual_outputs: list[str],
    ) -> SkillEvalReport:
        """
        Score each case against its actual_outputs[i].
        actual_outputs must have same length as cases.
        """
        if len(cases) != len(actual_outputs):
            raise ValueError(
                f"cases ({len(cases)}) and actual_outputs ({len(actual_outputs)}) must have the same length"
            )
        results = []
        total_weight = sum(c.weight for c in cases)
        weighted_score = 0.0

        for case, output in zip(cases, actual_outputs):
            try:
                score = case.score_fn(output)
            except Exception as exc:
                score = 0.0
                results.append(
                    SkillEvalResult(
                        case_id=case.id,
                        score=0.0,
                        passed=False,
                        output=output,
                        error=str(exc),
                    )
                )
                continue

            score = max(0.0, min(score, 1.0))
            passed = score >= self.threshold
            results.append(
                SkillEvalResult(
                    case_id=case.id,
                    score=score,
                    passed=passed,
                    output=output,
                )
            )
            weighted_score += score * case.weight

        overall = weighted_score / total_weight if total_weight > 0 else 0.0
        pass_rate = sum(1 for r in results if r.passed) / max(len(results), 1)

        return SkillEvalReport(
            skill_name=skill_name,
            overall_score=round(overall, 4),
            pass_rate=round(pass_rate, 4),
            results=results,
            threshold=self.threshold,
        )

    @staticmethod
    def keyword_scorer(keywords: list[str]) -> Callable[[str], float]:
        """Score = fraction of keywords present in output (case-insensitive)."""

        def _score(output: str) -> float:
            if not keywords:
                return 1.0
            output_lower = output.lower()
            hits = sum(1 for kw in keywords if kw.lower() in output_lower)
            return hits / len(keywords)

        return _score

    @staticmethod
    def min_length_scorer(min_chars: int) -> Callable[[str], float]:
        """Score = 1.0 if len(output) >= min_chars, else 0.0."""

        def _score(output: str) -> float:
            return 1.0 if len(output) >= min_chars else 0.0

        return _score

    @staticmethod
    def exact_match_scorer(expected: str) -> Callable[[str], float]:
        """Score = 1.0 if output contains expected string (case-insensitive)."""

        def _score(output: str) -> float:
            return 1.0 if expected.lower() in output.lower() else 0.0

        return _score
