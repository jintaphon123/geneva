from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Protocol


class MemoryLike(Protocol):
    id: str
    content: str
    type: str
    memory_kind: str
    confidence: float | None


@dataclass
class MemoryConflict:
    existing_id: str
    conflict_type: str
    reason: str
    similarity: float
    token_overlap: float
    suggested_action: str = "ask_user"  # "supersede" | "ask_user" | "keep_both"


ConflictCandidate = MemoryConflict


_NEGATION_TERMS = {
    "not",
    "no",
    "never",
    "dont",
    "don't",
    "doesnt",
    "doesn't",
    "cannot",
    "can't",
    "เลิก",
    "ไม่",
    "ห้าม",
}
_CORRECTION_TERMS = {
    "actually",
    "instead",
    "rather",
    "changed",
    "change",
    "correction",
    "correct",
    "update",
    "no longer",
    "not anymore",
    "แทน",
    "เปลี่ยน",
    "จริงๆ",
    "ไม่ใช่",
    "เอาเป็น",
}
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "but",
    "for",
    "he",
    "his",
    "is",
    "it",
    "of",
    "or",
    "she",
    "the",
    "they",
    "to",
    "user",
    "bond",
    "prefers",
    "preference",
    "wants",
    "want",
    "should",
    "must",
    "ต้องการ",
    "อยากให้",
    "ชอบ",
}
_CONFLICT_KINDS = {"identity", "preference", "project", "decision", "feedback", "skill"}


def find_memory_conflict(
    proposed_content: str,
    existing: list[MemoryLike],
    *,
    memory_kind: str,
    memory_type: str,
    new_confidence: float | None = None,
) -> ConflictCandidate | None:
    if memory_kind == "episode" or memory_type == "episodic":
        return None

    proposed = _normalize(proposed_content)
    proposed_tokens = _keywords(proposed)
    proposed_has_correction = _has_correction_cue(proposed)
    proposed_has_negation = _has_negation(proposed)
    best: MemoryConflict | None = None

    for memory in existing:
        existing_kind = str(memory.memory_kind or memory.type)
        if memory_kind in _CONFLICT_KINDS and existing_kind in _CONFLICT_KINDS:
            pass
        elif memory.type != memory_type:
            continue

        current = _normalize(memory.content)
        similarity = SequenceMatcher(None, proposed, current).ratio()
        token_overlap = _token_overlap(proposed_tokens, _keywords(current))
        current_has_negation = _has_negation(current)

        # Near-identical memories should flow through the existing high-similarity update path.
        if similarity >= 0.82 and not proposed_has_correction and proposed_has_negation == current_has_negation:
            continue

        same_subject = similarity >= 0.52 or token_overlap >= 0.46
        if not same_subject:
            continue

        conflict_type: str | None = None
        reason: str | None = None
        if proposed_has_negation != current_has_negation:
            conflict_type = "polarity_change"
            reason = "Proposed memory reverses or negates an existing active memory."
        elif proposed_has_correction:
            conflict_type = "correction"
            reason = "Proposed memory contains a correction cue and overlaps an existing active memory."
        elif memory_kind in {"preference", "decision", "feedback"} and similarity < 0.82:
            conflict_type = "durable_fact_overlap"
            reason = "Proposed durable memory overlaps an existing memory but is not similar enough to auto-merge."

        if conflict_type is None or reason is None:
            continue
        candidate = MemoryConflict(
            existing_id=memory.id,
            conflict_type=conflict_type,
            reason=reason,
            similarity=round(similarity, 4),
            token_overlap=round(token_overlap, 4),
        )
        existing_confidence = _confidence_value(getattr(memory, "confidence", None))
        proposed_confidence = _confidence_value(new_confidence)
        # R2 trust-score auto-resolution stub: high-confidence new memories can supersede.
        if proposed_confidence is not None and existing_confidence is not None:
            if proposed_confidence - existing_confidence >= 0.2:
                candidate.suggested_action = "supersede"
            elif existing_confidence - proposed_confidence >= 0.2:
                candidate.suggested_action = "keep_both"
        if best is None or (candidate.similarity, candidate.token_overlap) > (best.similarity, best.token_overlap):
            best = candidate

    return best


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _keywords(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+|[ก-๙]+", text.lower())
    return {word for word in words if len(word) > 1 and word not in _STOPWORDS}


def _token_overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / max(1, min(len(left), len(right)))


def _has_negation(text: str) -> bool:
    return any(term in text for term in _NEGATION_TERMS)


def _has_correction_cue(text: str) -> bool:
    return any(term in text for term in _CORRECTION_TERMS)


def _confidence_value(value: object) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
