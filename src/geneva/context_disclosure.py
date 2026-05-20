from __future__ import annotations

from typing import Any


_INTERNAL_SOURCE_TYPES = {
    "assembled_extra_system_prompt",
    "conversation_history",
    "pending_user_input",
    "runtime_base_context",
    "ghost_privacy_contract",
}
_MEMORY_SOURCE_TYPES = {"memory_context", "fallback_memory_context"}


def build_context_summary(
    ledger_record: dict[str, Any] | None,
    *,
    tool_events: list[Any] | None = None,
    ghost_mode: bool | None = None,
) -> dict[str, Any]:
    """Build a small user-facing summary from a turn context ledger."""
    record = ledger_record or {}
    metadata = _as_dict(record.get("metadata"))
    entries = [entry for entry in record.get("entries", []) or [] if isinstance(entry, dict)]
    included = [
        entry
        for entry in entries
        if str(entry.get("action") or "") in {"included", "trimmed", "preserved"}
        and int(entry.get("tokens_after") or 0) > 0
    ]

    project_entries = [entry for entry in included if entry.get("source_type") == "project_context"]
    memory_entries = [entry for entry in included if entry.get("source_type") in _MEMORY_SOURCE_TYPES]
    skill_entries = [entry for entry in included if entry.get("source_type") == "skill_context"]
    source_entries = [
        entry
        for entry in included
        if str(entry.get("source_type") or "")
        not in {*_INTERNAL_SOURCE_TYPES, *_MEMORY_SOURCE_TYPES, "project_context", "skill_context"}
    ]
    tools = _tool_names(tool_events or [])
    memory_count = sum(_memory_count(entry) for entry in memory_entries)
    skill_names = _skill_names(skill_entries)
    project_name = _project_name(project_entries)
    is_ghost = bool(ghost_mode if ghost_mode is not None else metadata.get("ghost_mode"))
    mode_id = _optional_text(metadata.get("mode_id"))
    mode_label = _optional_text(metadata.get("mode_label"))

    parts: list[str] = []
    if is_ghost:
        parts.append("Ghost mode: no memory write")
    if mode_label:
        parts.append(f"{mode_label} mode")
    if project_entries:
        parts.append(f"Used {project_name} project")
    if memory_count:
        parts.append(f"{memory_count} memor{'y' if memory_count == 1 else 'ies'}")
    if source_entries:
        count = len(source_entries)
        parts.append(f"{count} source{'s' if count != 1 else ''}")
    if skill_names:
        parts.append(" / ".join(f"/{name}" for name in skill_names))
    if tools:
        count = len(tools)
        parts.append(f"{count} tool{'s' if count != 1 else ''}")

    if not parts:
        parts.append("No extra context used")

    return {
        "session_id": record.get("session_id"),
        "turn_id": metadata.get("turn_id"),
        "ledger_id": record.get("id"),
        "summary": " · ".join(parts),
        "counts": {
            "projects": len(project_entries),
            "memories": memory_count,
            "sources": len(source_entries),
            "skills": len(skill_names),
            "tools": len(tools),
        },
        "projects": [_entry_label(entry) for entry in project_entries],
        "skills": skill_names,
        "tools": tools,
        "mode": {"id": mode_id, "label": mode_label} if mode_id or mode_label else None,
        "mode_id": mode_id,
        "mode_label": mode_label,
        "route_reason": _optional_text(metadata.get("route_reason")),
        "cost_tier": _optional_text(metadata.get("cost_tier")),
        "model": record.get("model"),
        "ghost_mode": is_ghost,
        "no_memory_write": is_ghost,
        "trimmed": any(str(entry.get("action") or "") == "trimmed" for entry in entries),
        "budget": record.get("budget") if isinstance(record.get("budget"), dict) else {},
        "created_at": record.get("created_at"),
    }


def find_context_summary(
    records: list[dict[str, Any]],
    *,
    session_id: str,
    turn_id: str,
) -> dict[str, Any] | None:
    for record in records:
        if str(record.get("session_id") or "") != session_id:
            continue
        metadata = _as_dict(record.get("metadata"))
        if str(metadata.get("turn_id") or "") == turn_id:
            return build_context_summary(record)
    return None


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _entry_label(entry: dict[str, Any]) -> str:
    metadata = _as_dict(entry.get("metadata"))
    label = metadata.get("project_name") or entry.get("label") or entry.get("source_type") or "context"
    return str(label)


def _project_name(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "current"
    metadata = _as_dict(entries[0].get("metadata"))
    raw = metadata.get("project_name")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return "current"


def _memory_count(entry: dict[str, Any]) -> int:
    metadata = _as_dict(entry.get("metadata"))
    raw = metadata.get("memory_count")
    if isinstance(raw, int) and raw > 0:
        return raw
    if isinstance(raw, float) and raw > 0:
        return int(raw)
    return 1


def _skill_names(entries: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for entry in entries:
        metadata = _as_dict(entry.get("metadata"))
        raw = metadata.get("skill_name") or str(entry.get("label") or "").removeprefix("Active skill:")
        name = str(raw or "").strip().lstrip("/")
        if name and name not in names:
            names.append(name)
    return names


def _tool_names(tool_events: list[Any]) -> list[str]:
    names: list[str] = []
    for event in tool_events:
        if isinstance(event, dict):
            name = event.get("tool_name") or event.get("toolName")
            status = event.get("status")
        else:
            name = getattr(event, "tool_name", None) or getattr(event, "toolName", None)
            status = getattr(event, "status", None)
        if not name or str(status or "") in {"queued", "running"}:
            continue
        rendered = str(name)
        if rendered not in names:
            names.append(rendered)
    return names
