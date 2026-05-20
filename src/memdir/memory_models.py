from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

MemoryStatus = Literal["active", "archived", "expired", "superseded", "deleted"]
MemoryOperation = Literal[
    "add",
    "update",
    "noop",
    "supersede",
    "archive",
    "expire",
    "delete",
    "privacy_delete",
    "reindex",
    "conflict",
]
SourceType = Literal["user_direct", "assistant_inferred", "tool_output", "file_import", "system_consolidation"]


@dataclass
class Memory:
    id: str
    path: str
    name: str
    type: str
    status: MemoryStatus
    content: str
    confidence: float
    importance: float
    source_type: str
    created_at: str
    updated_at: str | None
    retention_days: int
    expires_at: str | None
    superseded_by: str | None
    memory_kind: str = "reference"
    source_session_id: str | None = None
    captured_at: str | None = None
    last_validated_at: str | None = None
    scope: str | None = None
    fts_score: float = 0.0
    # Phase 3 evidence fields (schema v3)
    evidence_quote: str | None = None
    sensitivity: Literal["public", "private", "restricted"] = "private"
    validity_window_days: int | None = None
    trust_score: float | None = None


@dataclass
class MemoryResult:
    operation: MemoryOperation
    memory_id: str | None
    success: bool
    message: str = ""
    conflict_id: str | None = None


@dataclass
class RebuildResult:
    files_scanned: int
    files_updated: int
    errors: list[str] = field(default_factory=list)
