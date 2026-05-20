from __future__ import annotations

import hashlib
import json
import os
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from src.token_estimation import count_messages_tokens, count_tokens

LedgerEvent = Literal["turn_context", "compact"]
LedgerAction = Literal["included", "trimmed", "compacted", "preserved", "omitted"]

CONTEXT_LEDGER_DIR = Path.home() / ".geneva" / "context-ledger"
_LEDGER_LOCK = threading.RLock()


@dataclass(frozen=True)
class ContextSourceBlock:
    source_type: str
    label: str
    text: str
    rendered_text: str | None = None
    action: LedgerAction = "included"
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContextLedgerEntry:
    source_type: str
    action: LedgerAction
    tokens_before: int
    tokens_after: int
    reason: str
    label: str = ""
    source_id: str | None = None
    message_count: int = 0
    chars: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["tokens_saved"] = max(0, self.tokens_before - self.tokens_after)
        return payload


@dataclass(frozen=True)
class ContextLedgerRecord:
    id: str
    session_id: str
    event: LedgerEvent
    created_at: str
    model: str
    trigger: str
    entries: list[ContextLedgerEntry]
    budget: dict[str, Any] = field(default_factory=dict)
    totals: dict[str, int | float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "event": self.event,
            "created_at": self.created_at,
            "model": self.model,
            "trigger": self.trigger,
            "budget": dict(self.budget),
            "entries": [entry.to_dict() for entry in self.entries],
            "totals": dict(self.totals),
            "metadata": dict(self.metadata),
        }


def new_context_ledger_id(prefix: str = "ctx") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def build_turn_context_ledger(
    *,
    session_id: str,
    model: str,
    budget: Any,
    user_input: str,
    messages: list[dict[str, Any]],
    source_blocks: list[ContextSourceBlock],
    final_context: str,
    memory_budget_tokens: int,
    trigger: str = "chat",
    record_id: str | None = None,
    turn_id: str | None = None,
    ghost_mode: bool = False,
    mode_id: str | None = None,
    mode_label: str | None = None,
    route_reason: str | None = None,
    cost_tier: str | None = None,
) -> ContextLedgerRecord:
    entries: list[ContextLedgerEntry] = []
    budget_payload = _budget_to_dict(budget)

    conversation_tokens = count_messages_tokens(messages)
    entries.append(
        ContextLedgerEntry(
            source_type="conversation_history",
            action="included",
            label="Existing conversation before this turn",
            tokens_before=conversation_tokens,
            tokens_after=conversation_tokens,
            reason="The current transcript remains available to the model.",
            message_count=len(messages),
        )
    )
    if user_input.strip():
        user_tokens = count_tokens(user_input)
        entries.append(
            ContextLedgerEntry(
                source_type="pending_user_input",
                action="included",
                label="Current user message",
                source_id=_digest(user_input),
                tokens_before=user_tokens,
                tokens_after=user_tokens,
                reason="The latest user instruction is always pinned into context.",
                chars=len(user_input),
            )
        )

    for block in source_blocks:
        rendered = block.rendered_text if block.rendered_text is not None else block.text
        before = count_tokens(block.text)
        after = count_tokens(rendered) if block.action != "omitted" else 0
        action = block.action
        if action == "included" and after < before:
            action = "trimmed"
        entries.append(
            ContextLedgerEntry(
                source_type=block.source_type,
                action=action,
                label=block.label,
                source_id=_digest(block.text),
                tokens_before=before,
                tokens_after=after,
                reason=block.reason or _default_reason(action),
                chars=len(block.text),
                metadata=_safe_metadata(block.metadata),
            )
        )

    final_tokens = count_tokens(final_context)
    entries.append(
        ContextLedgerEntry(
            source_type="assembled_extra_system_prompt",
            action="included" if final_tokens else "omitted",
            label="Final injected context block",
            source_id=_digest(final_context) if final_context else None,
            tokens_before=final_tokens,
            tokens_after=final_tokens,
            reason="This is the exact extra context handed to the agent loop.",
            chars=len(final_context),
            metadata={"memory_budget_tokens": memory_budget_tokens},
        )
    )
    return _record(
        record_id=record_id,
        session_id=session_id,
        event="turn_context",
        model=model,
        trigger=trigger,
        entries=entries,
        budget=budget_payload,
        metadata={
            "memory_budget_tokens": memory_budget_tokens,
            "turn_id": turn_id,
            "ghost_mode": ghost_mode,
            "mode_id": mode_id,
            "mode_label": mode_label,
            "route_reason": route_reason,
            "cost_tier": cost_tier,
        },
    )


def build_compact_context_ledger(
    *,
    session_id: str,
    model: str,
    trigger: str,
    pre_compact_tokens: int,
    post_compact_tokens: int,
    messages_summarized: int,
    fresh_tail_count: int,
    fresh_tail_tokens: int,
    summary_text: str,
    microcompact_tokens_saved: int,
    total_tokens_saved: int,
    summary_request_message_count: int,
    record_id: str | None = None,
) -> ContextLedgerRecord:
    summary_tokens = count_tokens(summary_text)
    entries = [
        ContextLedgerEntry(
            source_type="conversation_history",
            action="compacted",
            label="Older transcript replaced by compact summary",
            tokens_before=pre_compact_tokens,
            tokens_after=summary_tokens,
            reason="Older messages crossed the compact boundary and were summarized.",
            message_count=messages_summarized,
            metadata={"summary_request_message_count": summary_request_message_count},
        ),
        ContextLedgerEntry(
            source_type="conversation_tail",
            action="preserved",
            label="Fresh tail preserved verbatim",
            tokens_before=fresh_tail_tokens,
            tokens_after=fresh_tail_tokens,
            reason="Recent task state stays raw to avoid losing immediate intent.",
            message_count=fresh_tail_count,
        ),
        ContextLedgerEntry(
            source_type="tool_results",
            action="trimmed" if microcompact_tokens_saved else "included",
            label="Microcompact pre-processing",
            tokens_before=microcompact_tokens_saved,
            tokens_after=0,
            reason="Old compactable tool results were cleared before summary generation.",
            metadata={"microcompact_tokens_saved": microcompact_tokens_saved},
        ),
        ContextLedgerEntry(
            source_type="compact_summary",
            action="included",
            label="Generated compact summary",
            source_id=_digest(summary_text),
            tokens_before=summary_tokens,
            tokens_after=summary_tokens,
            reason="The summary becomes the durable handoff for compacted history.",
            chars=len(summary_text),
        ),
    ]
    return _record(
        record_id=record_id,
        session_id=session_id,
        event="compact",
        model=model,
        trigger=trigger,
        entries=entries,
        budget={
            "pre_compact_tokens": pre_compact_tokens,
            "post_compact_tokens": post_compact_tokens,
            "total_tokens_saved": total_tokens_saved,
        },
        metadata={
            "messages_summarized": messages_summarized,
            "fresh_tail_count": fresh_tail_count,
        },
    )


def append_context_ledger_record(
    record: ContextLedgerRecord | dict[str, Any],
    ledger_dir: Path | None = None,
) -> Path:
    payload = record.to_dict() if isinstance(record, ContextLedgerRecord) else dict(record)
    session_id = str(payload.get("session_id") or "unknown")
    target_dir = ledger_dir or CONTEXT_LEDGER_DIR
    path = target_dir / f"{_safe_session_id(session_id)}.jsonl"
    line = json.dumps(payload, ensure_ascii=False, sort_keys=True)

    with _LEDGER_LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    return path


def list_context_ledger_records(
    session_id: str | None = None,
    *,
    limit: int = 50,
    ledger_dir: Path | None = None,
) -> list[dict[str, Any]]:
    target_dir = ledger_dir or CONTEXT_LEDGER_DIR
    if limit <= 0:
        return []
    if session_id:
        paths = [target_dir / f"{_safe_session_id(session_id)}.jsonl"]
    else:
        paths = sorted(target_dir.glob("*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)

    records: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in reversed(lines):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
            if len(records) >= limit:
                break
        if len(records) >= limit:
            break
    return sorted(records, key=lambda item: str(item.get("created_at") or ""), reverse=True)[:limit]


def summarize_context_ledger_record(record: ContextLedgerRecord | dict[str, Any] | None) -> dict[str, Any] | None:
    if record is None:
        return None
    payload = record.to_dict() if isinstance(record, ContextLedgerRecord) else dict(record)
    entries = payload.get("entries", [])
    return {
        "id": payload.get("id"),
        "event": payload.get("event"),
        "trigger": payload.get("trigger"),
        "budget": payload.get("budget", {}),
        "totals": payload.get("totals", {}),
        "entries": [
            {
                "source_type": entry.get("source_type"),
                "action": entry.get("action"),
                "tokens_before": entry.get("tokens_before"),
                "tokens_after": entry.get("tokens_after"),
                "tokens_saved": entry.get("tokens_saved"),
                "reason": entry.get("reason"),
            }
            for entry in entries
            if isinstance(entry, dict)
        ],
    }


def _record(
    *,
    record_id: str | None,
    session_id: str,
    event: LedgerEvent,
    model: str,
    trigger: str,
    entries: list[ContextLedgerEntry],
    budget: dict[str, Any],
    metadata: dict[str, Any],
) -> ContextLedgerRecord:
    totals = {
        "tokens_before": sum(entry.tokens_before for entry in entries),
        "tokens_after": sum(entry.tokens_after for entry in entries),
        "tokens_saved": sum(max(0, entry.tokens_before - entry.tokens_after) for entry in entries),
        "entry_count": len(entries),
    }
    return ContextLedgerRecord(
        id=record_id or new_context_ledger_id(event),
        session_id=session_id or "unknown",
        event=event,
        created_at=datetime.now(timezone.utc).isoformat(),
        model=model or "unknown",
        trigger=trigger,
        entries=entries,
        budget=budget,
        totals=totals,
        metadata=_safe_metadata(metadata),
    )


def _budget_to_dict(budget: Any) -> dict[str, Any]:
    if budget is None:
        return {}
    if hasattr(budget, "to_dict"):
        try:
            payload = budget.to_dict()
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}
    return dict(budget) if isinstance(budget, dict) else {}


def _safe_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value
        elif isinstance(value, (list, tuple)):
            safe[key] = [item for item in value if isinstance(item, (str, int, float, bool))][:20]
        elif isinstance(value, dict):
            safe[key] = {
                str(k): v
                for k, v in value.items()
                if isinstance(v, (str, int, float, bool)) or v is None
            }
    return safe


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _safe_session_id(session_id: str) -> str:
    digest = _digest(session_id)
    visible = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in session_id)[:80]
    return f"{visible or 'unknown'}-{digest}"


def _default_reason(action: LedgerAction) -> str:
    if action == "trimmed":
        return "Source was shortened to stay within the context budget."
    if action == "compacted":
        return "Source was replaced by a summary."
    if action == "preserved":
        return "Source was preserved verbatim because it is recent or high-signal."
    if action == "omitted":
        return "Source was omitted because the budget did not allow it."
    return "Source was included in context."
