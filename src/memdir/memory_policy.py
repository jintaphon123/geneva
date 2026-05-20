from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from typing import Literal

from .memory_types import MemoryType

MemoryKind = Literal[
    "identity",
    "preference",
    "project",
    "decision",
    "reflection",
    "reference",
    "episode",
    "skill",
    "feedback",
]


@dataclass(frozen=True)
class MemoryWritePolicy:
    type: str
    memory_kind: MemoryKind
    confidence: float
    importance: float
    retention_days: int
    expires_at: str | None
    source_session_id: str | None
    captured_at: str | None
    last_validated_at: str


_VALID_TYPES = {item.value for item in MemoryType}
_VALID_KINDS = {
    "identity",
    "preference",
    "project",
    "decision",
    "reflection",
    "reference",
    "episode",
    "skill",
    "feedback",
}
_KIND_TO_STORAGE_TYPE = {
    "identity": MemoryType.user.value,
    "preference": MemoryType.user.value,
    "feedback": MemoryType.feedback.value,
    "project": MemoryType.project.value,
    "decision": MemoryType.project.value,
    "reflection": MemoryType.project.value,
    "reference": MemoryType.reference.value,
    "skill": MemoryType.reference.value,
    "episode": MemoryType.episodic.value,
}
_IMPORTANCE_BY_KIND = {
    "identity": 0.90,
    "preference": 0.86,
    "decision": 0.88,
    "project": 0.78,
    "reflection": 0.68,
    "skill": 0.74,
    "feedback": 0.82,
    "reference": 0.56,
    "episode": 0.34,
}
_RETENTION_BY_KIND = {
    "identity": 3650,
    "preference": 3650,
    "decision": 2555,
    "project": 1825,
    "feedback": 1825,
    "skill": 1825,
    "reflection": 1095,
    "reference": 1095,
    "episode": 365,
}
_KIND_PRIORITY = {
    "identity": 0.18,
    "preference": 0.16,
    "decision": 0.16,
    "project": 0.12,
    "feedback": 0.11,
    "skill": 0.08,
    "reflection": 0.06,
    "reference": 0.02,
    "episode": -0.08,
}


def build_write_policy(
    *,
    content: str,
    memory_type: str,
    source_type: str,
    scope: str | None,
    memory_kind: str | None = None,
    confidence: float | None = None,
    importance: float | None = None,
    retention_days: int | None = None,
    expires_at: str | None = None,
    source_session_id: str | None = None,
    captured_at: str | None = None,
    last_validated_at: str | None = None,
) -> MemoryWritePolicy:
    kind = normalize_memory_kind(memory_kind) or infer_memory_kind(content, memory_type, scope)
    storage_type = storage_type_for(memory_type, kind)
    now = _iso_now()
    return MemoryWritePolicy(
        type=storage_type,
        memory_kind=kind,
        confidence=_clamp(confidence if confidence is not None else default_confidence(source_type, kind)),
        importance=_clamp(importance if importance is not None else _IMPORTANCE_BY_KIND[kind]),
        retention_days=retention_days or _RETENTION_BY_KIND[kind],
        expires_at=_clean_text(expires_at),
        source_session_id=_clean_text(source_session_id) or extract_source_session_id(content),
        captured_at=_clean_text(captured_at) or extract_captured_at(content) or now,
        last_validated_at=_clean_text(last_validated_at) or now,
    )


def normalize_memory_kind(value: str | None) -> MemoryKind | None:
    if value is None:
        return None
    normalized = value.strip().lower().replace("-", "_")
    aliases = {
        "episode": "episode",
        "episodic": "episode",
        "user": "identity",
        "personal": "identity",
        "procedural": "skill",
        "semantic": "reference",
        "next_action": "project",
    }
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in _VALID_KINDS else None  # type: ignore[return-value]


def infer_memory_kind(content: str, memory_type: str, scope: str | None = None) -> MemoryKind:
    normalized_type = normalize_storage_type(memory_type)
    text = content.lower()
    if normalized_type == MemoryType.episodic.value:
        return "episode"
    if normalized_type == MemoryType.feedback.value:
        return "feedback"
    if normalized_type == MemoryType.reference.value:
        if any(term in text for term in ("skill", "workflow", "procedure", "ขั้นตอน", "วิธีทำ")):
            return "skill"
        return "reference"
    if normalized_type == MemoryType.project.value or scope:
        if re.search(r"\b(decision|decided|verdict)\b", text) or "ตัดสิน" in text:
            return "decision"
        if any(term in text for term in ("reflection", "lesson", "learned", "สรุปบทเรียน")):
            return "reflection"
        return "project"
    if any(term in text for term in ("prefer", "preference", "อยากให้", "ต้องการให้", "ไม่อยากให้")):
        return "preference"
    return "identity"


def normalize_storage_type(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    aliases = {
        "identity": MemoryType.user.value,
        "preference": MemoryType.user.value,
        "decision": MemoryType.project.value,
        "reflection": MemoryType.project.value,
        "episode": MemoryType.episodic.value,
        "skill": MemoryType.reference.value,
    }
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in _VALID_TYPES else MemoryType.reference.value


def storage_type_for(memory_type: str, kind: MemoryKind) -> str:
    requested = normalize_storage_type(memory_type)
    if memory_type and requested in _VALID_TYPES:
        if requested == MemoryType.episodic.value:
            return requested
        if requested == MemoryType.user.value and kind in {"identity", "preference"}:
            return requested
        if requested == MemoryType.project.value and kind in {"project", "decision", "reflection"}:
            return requested
        if requested == MemoryType.feedback.value and kind == "feedback":
            return requested
        if requested == MemoryType.reference.value and kind in {"reference", "skill"}:
            return requested
    return _KIND_TO_STORAGE_TYPE[kind]


def default_confidence(source_type: str, kind: MemoryKind) -> float:
    if source_type == "user_direct":
        return 0.96
    if source_type == "file_import":
        return 0.88
    if source_type == "tool_output":
        return 0.82
    if kind == "episode":
        return 0.92
    return 0.78


def memory_rank_score(
    *,
    fts_score: float,
    recency: float,
    confidence: float,
    importance: float,
    memory_kind: str | None,
) -> float:
    kind = normalize_memory_kind(memory_kind) or "reference"
    return (
        0.34 * max(0.0, fts_score)
        + 0.18 * max(0.0, recency)
        + 0.23 * _clamp(confidence)
        + 0.25 * _clamp(importance)
        + _KIND_PRIORITY[kind]
    )


def extract_source_session_id(content: str) -> str | None:
    match = re.search(
        r"(?:^|\s)Session:\s*(.+?)(?=\s+Captured at:|\s+User:|\s+Assistant:|$)",
        content,
        flags=re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def extract_captured_at(content: str) -> str | None:
    match = re.search(
        r"(?:^|\s)Captured at:\s*(.+?)(?=\s+User:|\s+Assistant:|$)",
        content,
        flags=re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def _iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 1.0))
