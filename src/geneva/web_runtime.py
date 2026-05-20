from __future__ import annotations

import json
import re
import sqlite3
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.memdir.brain_engine import DB_PATH, init_db, rebuild_index
from src.providers import PROVIDER_INFO
from src.geneva.agent_trace import append_research_trace, get_turn_trace, list_trace_records
from src.geneva.context_disclosure import find_context_summary
from src.geneva.events import TurnStreamEvent
from src.geneva.code_runner import run_code
from src.geneva.importer import GenevaImporter
from src.geneva.memory_manager import MemoryManager
from src.geneva.memory_write_review import (
    approve_memory_write_event,
    list_memory_write_events,
    record_memory_revision,
    undo_memory_write_event,
)
from src.geneva.project_sources import ProjectSourceStore, project_source_context_blocks
from src.geneva.project_store import ProjectStore
from src.geneva.research_engine import ResearchEngine
from src.geneva.research_runs import ResearchRunStore
from src.geneva.session import GenevaSession
from src.geneva.settings_manager import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    GenevaConfig,
    check_cli,
    get_redacted,
    load_settings,
    save_settings,
)
from src.geneva.slash_commands import (
    SlashCommand,
    list_slash_commands,
    parse_slash_command,
)
from src.geneva.skill_control_plane import SkillControlError, SkillStatus
from src.geneva.skill_engine import get_engine
from src.services.compact import list_context_ledger_records
from src.services.model_router import DEFAULT_MODE_ID, mode_profile_payloads, normalize_mode_id
from src.tool_system.defaults import build_default_registry
from src.tool_system.profiles import profile_catalog, resolve_tool_profile


@dataclass(frozen=True)
class ChatRequest:
    message: str
    session_id: str | None = None
    provider_name: str | None = None
    model: str | None = None
    mode_id: str | None = None
    max_turns: int = 100
    project_id: str | None = None
    ghost_mode: bool = False
    images: list[dict[str, str]] = field(default_factory=list)


@dataclass(frozen=True)
class CommandRequest:
    raw: str
    session_id: str | None = None
    provider_name: str | None = None
    model: str | None = None


@dataclass(frozen=True)
class ResearchRequest:
    query: str
    session_id: str | None = None
    provider_name: str | None = None
    model: str | None = None
    project_id: str | None = None
    ghost_mode: bool = False
    mode: str = "deep"


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, GenevaSession] = {}
        self._lock = threading.RLock()
        self._start_auto_dream_scheduler()

    def _start_auto_dream_scheduler(self) -> None:
        try:
            from src.services.auto_dream.auto_dream import start_dream_scheduler

            def agent_caller(prompt: str) -> str:
                session = self.get()
                return session._call_auto_dream_agent(prompt)

            start_dream_scheduler(agent_caller=agent_caller)
        except Exception:
            pass

    def get(
        self,
        session_id: str | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        mode_id: str | None = None,
        user_input: str = "",
    ) -> GenevaSession:
        with self._lock:
            if session_id and session_id in self._sessions:
                session = self._sessions[session_id]
                if provider_name or model or mode_id:
                    session.configure_mode(
                        mode_id,
                        provider_name=provider_name,
                        model=model,
                        user_input=user_input,
                    )
                return session
            session = GenevaSession(
                session_id=session_id,
                provider_name=provider_name,
                model=model,
                mode_id=mode_id,
            )
            self._sessions[session.session_id] = session
            return session

    def get_if_exists(self, session_id: str) -> GenevaSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def list_sessions(self) -> list[dict[str, str]]:
        session = self.get()
        sessions = session.list_sessions()
        for item in sessions:
            project = _project_store.get_project_for_session(item["session_id"])
            if project:
                item["project_id"] = project.id
                item["project_name"] = project.name
                item["project_color"] = project.color
        return sessions

    def list_sessions_paged(self, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        session = self.get()
        result = session.list_sessions_paged(limit=limit, offset=offset)
        for item in result["sessions"]:
            project = _project_store.get_project_for_session(item["session_id"])
            if project:
                item["project_id"] = project.id
                item["project_name"] = project.name
                item["project_color"] = project.color
        return result

    def list_project_sessions(self, project_id: str) -> list[dict[str, str]]:
        project = _project_store.get_project(project_id)
        session_ids = _project_store.list_session_ids(project_id)
        sessions_by_id = {item["session_id"]: item for item in self.list_sessions()}
        result: list[dict[str, str]] = []
        for session_id in session_ids:
            item = dict(sessions_by_id.get(session_id) or {"session_id": session_id})
            item["project_id"] = project_id
            if project:
                item["project_name"] = project.name
                item["project_color"] = project.color
            item.setdefault("title", "")
            item.setdefault("created_at", "")
            item.setdefault("updated_at", "")
            item.setdefault("message_count", "")
            result.append(item)
        return result

    def memory_snapshot(self, session_id: str | None = None) -> dict[str, Any]:
        session = self.get(session_id)
        return {
            "stats": session.get_memory_stats().__dict__,
            "recent": session.list_recent_memories(),
            "activity": session.get_memory_activity(),
        }

    def messages(self, session_id: str) -> dict[str, Any]:
        session = self.get(session_id)
        return {
            "session_id": session.session_id,
            "provider": session.provider_name,
            "model": session.provider.model,
            "messages": session.get_display_messages(),
            "message_count": session.message_count,
        }

    def context_ledger(self, session_id: str | None = None, limit: int = 50) -> dict[str, Any]:
        bounded_limit = max(1, min(int(limit), 100))
        with self._lock:
            loaded = self._sessions.get(session_id or "") if session_id else None
            if loaded is not None:
                return loaded.get_context_ledger(bounded_limit)
            if not session_id:
                session = self.get()
                return session.get_context_ledger(bounded_limit)
        return {
            "session_id": session_id or "",
            "latest": None,
            "history": [],
            "records": list_context_ledger_records(session_id, limit=bounded_limit),
        }

    def agent_traces(self, session_id: str, limit: int = 50) -> dict[str, Any]:
        bounded_limit = max(1, min(int(limit), 100))
        with self._lock:
            session = self._sessions.get(session_id)
        if session is not None:
            return session.get_agent_traces(bounded_limit)
        return {
            "session_id": session_id,
            "records": list_trace_records(session_id, limit=bounded_limit),
        }

    def resolve_tool_permission(self, session_id: str, request_id: str, approved: bool) -> dict[str, Any] | None:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            return None
        if not session.resolve_permission_request(request_id, approved):
            return None
        return {"ok": True, "session_id": session_id, "request_id": request_id, "approved": approved}


SETTINGS_FIELDS = {
    "anthropic_api_key",
    "openrouter_api_key",
    "google_api_key",
    "gemini_cli_path",
    "codex_cli_path",
    "default_provider",
    "default_model",
    "research_model",
    "fast_model",
    "default_mode",
    "workspace_dir",
    "dark_mode",
}

SECRET_SETTINGS_FIELDS = {"anthropic_api_key", "openrouter_api_key", "google_api_key"}

_memory_mgr = MemoryManager()
_project_store = ProjectStore()
_research_engine: ResearchEngine | None = None


def available_models() -> list[dict[str, Any]]:
    info = PROVIDER_INFO[DEFAULT_PROVIDER]
    return [
        {
            "provider": DEFAULT_PROVIDER,
            "provider_label": info["label"],
            "id": model_id,
            "name": _model_display_name(model_id),
            "default": model_id == DEFAULT_MODEL,
        }
        for model_id in info["available_models"]
    ]


def available_modes() -> dict[str, Any]:
    return {
        "default_mode_id": DEFAULT_MODE_ID,
        "modes": mode_profile_payloads(),
    }


def _model_display_name(model_id: str) -> str:
    if model_id == "deepseek/deepseek-v4-flash":
        return "DeepSeek V4"
    if model_id == "openrouter/free":
        return "OpenRouter Free"
    return model_id


def command_catalog() -> list[dict[str, object]]:
    return list_slash_commands()


def tool_catalog_payload(profile: str | None = None) -> dict[str, Any]:
    tool_profile = resolve_tool_profile(profile)
    registry = build_default_registry(profile=tool_profile.name)
    tools = []
    for spec in registry.list_specs():
        tools.append(
            {
                "name": spec.name,
                "description": spec.description,
                "input_schema": dict(spec.input_schema),
                "aliases": list(spec.aliases),
                "is_read_only": spec.is_read_only,
                "is_destructive": spec.is_destructive,
                "strict": spec.strict,
                "max_result_size_chars": spec.max_result_size_chars,
                "timeout_seconds": spec.timeout_seconds,
                "profile": tool_profile.name,
            }
        )
    return {
        "tools": tools,
        "count": len(tools),
        "profile": tool_profile.name,
        "profiles": profile_catalog(),
    }


def settings_payload() -> dict[str, Any]:
    cfg = load_settings()
    return {
        "config": get_redacted(cfg),
        "cli": {
            "gemini_ok": check_cli(cfg.gemini_cli_path),
            "codex_ok": check_cli(cfg.codex_cli_path),
        },
    }


def update_settings(payload: dict[str, Any]) -> dict[str, bool]:
    cfg = load_settings()
    openrouter_key_updated = False
    for field_name in SETTINGS_FIELDS:
        if field_name in payload:
            coerced = _coerce_setting_value(cfg, field_name, payload[field_name])
            if field_name in SECRET_SETTINGS_FIELDS and isinstance(coerced, str) and not coerced.strip():
                continue
            setattr(cfg, field_name, coerced)
            if field_name == "openrouter_api_key":
                openrouter_key_updated = True
    if openrouter_key_updated:
        cfg.default_provider = DEFAULT_PROVIDER
        cfg.default_model = DEFAULT_MODEL
        cfg.research_model = DEFAULT_MODEL
        cfg.fast_model = DEFAULT_MODEL
    save_settings(cfg)
    return {"ok": True}


def run_code_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return run_code(
        language=str(payload.get("language") or ""),
        code=str(payload.get("code") or ""),
    )


def system_status() -> dict[str, Any]:
    cfg = load_settings()
    return {
        "version": "0.3.0",
        "memory_count": _active_memory_count(),
        "skills_count": get_engine().count(),
        "gemini_ok": check_cli(cfg.gemini_cli_path),
        "codex_ok": check_cli(cfg.codex_cli_path),
        "geneva_dir": cfg.geneva_dir,
    }


def usage_payload() -> dict[str, Any]:
    cfg = load_settings()
    sessions_dir = Path(str(cfg.geneva_dir or GENEVA_DIR)) / "sessions"
    by_model: dict[str, dict[str, float | int | str]] = {}
    recent_sessions: list[dict[str, Any]] = []
    total_tokens = 0
    total_cost = 0.0
    entry_count = 0
    sessions_count = 0

    if sessions_dir.exists():
        for costs_path in sorted(sessions_dir.glob("*/costs.json")):
            try:
                payload = json.loads(costs_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            session_id = str(payload.get("session_id") or costs_path.parent.name)
            saved_at = str(payload.get("saved_at") or "")
            session_tokens = 0
            session_cost = 0.0
            valid_session = False

            for raw_entry in payload.get("entries", []):
                if not isinstance(raw_entry, dict):
                    continue
                model = str(raw_entry.get("model") or "unknown")
                tokens = (
                    _safe_int(raw_entry.get("input_tokens"))
                    + _safe_int(raw_entry.get("output_tokens"))
                    + _safe_int(raw_entry.get("cache_read_tokens"))
                    + _safe_int(raw_entry.get("cache_write_tokens"))
                )
                cost = _safe_float(raw_entry.get("cost_usd"))
                bucket = by_model.setdefault(model, {"model": model, "tokens": 0, "cost_usd": 0.0})
                bucket["tokens"] = int(bucket["tokens"]) + tokens
                bucket["cost_usd"] = float(bucket["cost_usd"]) + cost
                total_tokens += tokens
                total_cost += cost
                session_tokens += tokens
                session_cost += cost
                entry_count += 1
                valid_session = True

            if valid_session:
                sessions_count += 1
                recent_sessions.append(
                    {
                        "session_id": session_id,
                        "saved_at": saved_at,
                        "tokens": session_tokens,
                        "cost_usd": round(session_cost, 6),
                    }
                )

    recent_sessions.sort(key=lambda item: str(item.get("saved_at") or ""), reverse=True)
    model_rows = sorted(by_model.values(), key=lambda item: int(item["tokens"]), reverse=True)

    return {
        "sessions_count": sessions_count,
        "entry_count": entry_count,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 6),
        "by_model": [
            {"model": row["model"], "tokens": int(row["tokens"]), "cost_usd": round(float(row["cost_usd"]), 6)}
            for row in model_rows
        ],
        "recent_sessions": recent_sessions[:6],
    }


def rebuild_memory_index() -> dict[str, Any]:
    result = rebuild_index()
    return {
        "files_scanned": result.files_scanned,
        "files_updated": result.files_updated,
        "errors": result.errors,
    }


def list_memories_payload(
    memory_type: str | None = None,
    status: str = "active",
    query: str | None = None,
    scope: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    return _memory_mgr.list_memories(
        type=memory_type,
        status=status or "active",
        query=query,
        scope=scope,
        limit=max(1, min(int(limit), 100)),
        offset=max(0, int(offset)),
    )


def get_memory_payload(memory_id: str) -> dict[str, Any] | None:
    return _memory_mgr.get_memory_detail(memory_id)


def memory_timeline_payload() -> dict[str, Any]:
    return {"timeline": _memory_mgr.get_timeline()}


def memory_stats_payload(
    manager: SessionManager,
    session_id: str | None = None,
) -> dict[str, Any]:
    return {**manager.memory_snapshot(session_id), **_memory_mgr.get_stats()}


def context_ledger_payload(
    manager: SessionManager,
    session_id: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    return manager.context_ledger(session_id, limit)


def context_summary_payload(
    manager: SessionManager,
    session_id: str,
    turn_id: str,
) -> dict[str, Any] | None:
    ledger = manager.context_ledger(session_id, 500)
    records = ledger.get("records", [])
    if not isinstance(records, list):
        return None
    summary = find_context_summary(
        [record for record in records if isinstance(record, dict)],
        session_id=session_id,
        turn_id=turn_id,
    )
    return {"context_summary": summary} if summary else None


def list_memory_write_events_payload(
    session_id: str | None = None,
    memory_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    return list_memory_write_events(
        session_id=session_id,
        memory_id=memory_id,
        status=status,
        limit=limit,
        offset=offset,
    )


def undo_memory_write_event_payload(event_id: str) -> dict[str, Any] | None:
    event = undo_memory_write_event(event_id)
    return {"event": event} if event else None


def approve_memory_write_event_payload(event_id: str) -> dict[str, Any] | None:
    event = approve_memory_write_event(event_id)
    return {"event": event} if event else None


def agent_trace_payload(
    manager: SessionManager,
    session_id: str,
    limit: int = 50,
) -> dict[str, Any]:
    return manager.agent_traces(session_id, limit)


def get_turn_trace_payload(
    session_id: str,
    turn_id: str,
) -> dict[str, Any] | None:
    record = get_turn_trace(session_id, turn_id)
    if record is None:
        return None
    return {"session_id": session_id, "turn_id": turn_id, "trace": record}


def activity_timeline_payload(
    manager: SessionManager,
    session_id: str,
    limit: int = 50,
) -> dict[str, Any]:
    bounded_limit = max(1, min(int(limit), 200))
    with manager._lock:
        session = manager._sessions.get(session_id)
    if session is not None:
        raw_records = session.get_agent_traces(bounded_limit).get("records", [])
    else:
        raw_records = list_trace_records(session_id, limit=bounded_limit)
    activities = []
    for r in raw_records:
        activities.append({
            "turn_id": r.get("turn_id"),
            "created_at": r.get("created_at"),
            "user_preview": (r.get("user_preview") or "")[:100],
            "tool_names": [ev.get("tool_name") for ev in (r.get("events") or []) if ev.get("kind") == "tool_use"],
            "memory_action": r.get("memory_action"),
            "error_count": len(r.get("errors") or [ev for ev in (r.get("events") or []) if ev.get("is_error")]),
        })
    return {"session_id": session_id, "activities": activities}


def resolve_tool_permission_payload(
    manager: SessionManager,
    session_id: str,
    request_id: str,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    return manager.resolve_tool_permission(
        session_id,
        request_id,
        payload.get("approved") is True,
    )


def list_memory_conflicts_payload(
    status: str = "open",
    limit: int = 50,
    offset: int = 0,
) -> dict[str, object]:
    return _memory_mgr.list_conflicts(
        status=status or "open",
        limit=max(1, min(int(limit), 100)),
        offset=max(0, int(offset)),
    )


def get_memory_conflict_payload(conflict_id: str) -> dict[str, object] | None:
    return _memory_mgr.get_conflict(conflict_id)


def resolve_memory_conflict_payload(conflict_id: str, payload: dict[str, Any]) -> dict[str, object] | None:
    if _memory_mgr.get_conflict(conflict_id) is None:
        return None
    resolution = str(payload.get("resolution") or "replace").strip() or "replace"
    merged_content = _optional_text(payload.get("merged_content"))
    result = _memory_mgr.resolve_conflict(conflict_id, resolution, merged_content)
    if not result.get("success"):
        return _validation_error(str(result.get("message") or "Unable to resolve memory conflict"))
    return result


def add_memory_payload(payload: dict[str, Any]) -> dict[str, Any]:
    content = str(payload.get("content") or "").strip()
    if not content:
        return _validation_error("Memory content is required")
    result = _memory_mgr.add_memory(
        content=content,
        type=str(payload.get("type") or "user"),
        source_type=str(payload.get("source_type") or "user_direct"),
        scope=_optional_text(payload.get("scope")),
        memory_kind=_optional_text(payload.get("memory_kind")),
        confidence=_optional_float(payload.get("confidence")),
        importance=_optional_float(payload.get("importance")),
    )
    return {"result": result}


def update_memory_payload(memory_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    content = str(payload.get("content") or "").strip()
    if not content:
        return _validation_error("Memory content is required")
    if _memory_mgr.get_memory(memory_id) is None:
        return None
    result = _memory_mgr.update_memory(memory_id, content)
    return result if result.get("success") else None


def add_memory_revision_payload(memory_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    memory = _memory_mgr.get_memory(memory_id)
    if memory is None:
        return None
    new_content = str(payload.get("new_content") or payload.get("content") or "").strip()
    if not new_content:
        return _validation_error("Revision content is required")
    revision = record_memory_revision(
        memory_id=memory_id,
        previous_content=str(memory.get("content") or ""),
        new_content=new_content,
        edited_by=str(payload.get("edited_by") or "user"),
        reason=_optional_text(payload.get("reason")),
    )
    updated = _memory_mgr.update_memory(memory_id, new_content)
    if not updated.get("success"):
        return _validation_error(str(updated.get("message") or "Unable to update memory"))
    return {"revision": revision, "result": updated}


def archive_memory_payload(memory_id: str) -> dict[str, Any] | None:
    if _memory_mgr.get_memory(memory_id) is None:
        return None
    result = _memory_mgr.archive_memory(memory_id)
    return result if result.get("ok") else None


def delete_memory_payload(memory_id: str) -> dict[str, Any] | None:
    if _memory_mgr.get_memory(memory_id) is None:
        return None
    result = _memory_mgr.delete_memory(memory_id)
    return result if result.get("ok") else None


def list_skills_payload() -> dict[str, Any]:
    engine = get_engine()
    skills = engine.list_skills()
    return {
        "skills": skills,
        "count": len(skills),
        "active_count": engine.count(active_only=True),
        "review_count": sum(1 for skill in skills if skill.get("status") == "review"),
    }


def get_skill_payload(name: str) -> dict[str, Any] | None:
    skill = get_engine().describe_skill(name, include_prompt=True)
    if skill is None:
        return None
    return {"skill": skill}


def create_skill_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    name = str(payload.get("name") or "").strip()
    content = str(payload.get("content") or "").strip()
    if not name or not content:
        return None
    status = _skill_status_from_payload(payload.get("status"), default="active")
    try:
        skill = get_engine().create_skill_record(name, content, status=status, source="manual")
    except SkillControlError as exc:
        return _validation_error(str(exc))
    if skill is None:
        return None
    return {"skill": skill}


def update_skill_payload(name: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    content = str(payload.get("content") or "").strip()
    if not content:
        return _validation_error("Skill content is required")
    try:
        ok = get_engine().update_skill(name, content)
    except SkillControlError as exc:
        return _validation_error(str(exc))
    if not ok:
        return None
    skill = get_engine().describe_skill(name, include_prompt=True)
    return {"ok": True, "skill": skill}


def delete_skill_payload(name: str) -> dict[str, bool]:
    return {"ok": get_engine().delete_skill(name)}


def set_skill_status_payload(name: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    status = _skill_status_from_payload(payload.get("status"), default="review")
    note = _optional_text(payload.get("note"))
    try:
        skill = get_engine().set_status(name, status, note)
    except SkillControlError as exc:
        if "not found" in str(exc).lower():
            return None
        return _validation_error(str(exc))
    return {"ok": True, "skill": skill}


def activate_skill_payload(name: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        skill = get_engine().set_status(name, "active", _optional_text((payload or {}).get("note")))
    except SkillControlError as exc:
        if "not found" in str(exc).lower():
            return None
        return _validation_error(str(exc))
    return {"ok": True, "skill": skill}


def add_skill_eval_payload(name: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    input_text = str(payload.get("input") or payload.get("sample_input") or "").strip()
    expected = str(payload.get("expected") or payload.get("expected_behavior") or "").strip()
    status = _skill_eval_status_from_payload(payload.get("status"), default="pending")
    actual = str(payload.get("actual") or "").strip()
    notes = str(payload.get("notes") or "").strip()
    try:
        skill = get_engine().add_eval_case(
            name,
            input_text=input_text,
            expected=expected,
            status=status,
            actual=actual,
            notes=notes,
        )
    except SkillControlError as exc:
        if "not found" in str(exc).lower():
            return None
        return _validation_error(str(exc))
    return {"ok": True, "skill": skill}


def update_skill_eval_payload(name: str, eval_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    status = _skill_eval_status_from_payload(payload.get("status"), default="pending")
    actual = str(payload.get("actual") or "").strip()
    notes = str(payload.get("notes") or "").strip()
    try:
        skill = get_engine().update_eval_case(
            name,
            eval_id,
            status=status,
            actual=actual,
            notes=notes,
        )
    except SkillControlError as exc:
        if "not found" in str(exc).lower():
            return None
        return _validation_error(str(exc))
    return {"ok": True, "skill": skill}


def rollback_skill_payload(name: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    revision_id = str(payload.get("revision_id") or "").strip()
    if not revision_id:
        return _validation_error("revision_id is required")
    try:
        skill = get_engine().rollback(name, revision_id)
    except SkillControlError as exc:
        if "not found" in str(exc).lower():
            return None
        return _validation_error(str(exc))
    return {"ok": True, "skill": skill}


def submit_skill_feedback_payload(name: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    try:
        score = int(payload.get("score") or 3)
    except (TypeError, ValueError):
        return _validation_error("score must be an integer from 1 to 5")
    outcome = str(payload.get("outcome") or "").strip()
    if not outcome:
        return _validation_error("outcome is required")
    try:
        skill = get_engine().submit_feedback(
            name,
            score=score,
            outcome=outcome,
            note=str(payload.get("note") or "").strip(),
            suggested_change=str(payload.get("suggested_change") or "").strip(),
            source_session_id=_optional_text(payload.get("session_id")),
        )
    except SkillControlError as exc:
        if "not found" in str(exc).lower():
            return None
        return _validation_error(str(exc))
    return {"ok": True, "skill": skill}


def reload_skills_payload() -> dict[str, int]:
    return {"count": get_engine().reload()}


def import_workspace_payload(payload: dict[str, Any]) -> dict[str, Any]:
    workspace_path = _optional_text(payload.get("workspace_path"))
    importer = GenevaImporter(Path(workspace_path) if workspace_path else None)
    result = importer.import_all()
    get_engine().reload()
    return asdict(result)


def build_skill_payload(manager: SessionManager, payload: dict[str, Any]) -> dict[str, Any] | None:
    description = str(payload.get("description") or "").strip()
    if not description:
        return None

    name = _derive_skill_name(description)
    request = (
        "You are a skill author. Generate a SKILL.md file for this skill:\n"
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "---\n"
        "[skill instructions in markdown]\n\n"
        "Return only the complete SKILL.md content."
    )
    session = manager.get()
    result = session.chat(request, max_turns=8)
    raw = _extract_skill_markdown(result.text)
    if result.error or not _has_valid_skill_frontmatter(raw):
        raw = _fallback_skill_markdown(name, description)

    skill = get_engine().create_skill_record(
        name,
        raw,
        status="review",
        source="generated",
        generated_from=description,
        source_session_id=session.session_id,
    )
    if skill is None:
        return None
    return {"skill": skill, "raw": raw, "requires_review": True}


def list_projects_payload() -> dict[str, Any]:
    return {"projects": [_project_store.to_dict(project) for project in _project_store.list_projects()]}


def create_project_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    name = str(payload.get("name") or "").strip()
    if not name:
        return _validation_error("Project name is required")
    project = _project_store.create_project(
        name=name,
        description=str(payload.get("description") or ""),
    )
    extra_fields = {
        key: payload[key]
        for key in ("context_md", "color", "pinned")
        if key in payload
    }
    if extra_fields:
        project = _project_store.update_project(project.id, **extra_fields) or project
    return {"project": _project_store.to_dict(project)}


def get_project_payload(project_id: str) -> dict[str, Any] | None:
    project = _project_store.get_project(project_id)
    if project is None:
        return None
    return {"project": _project_store.to_dict(project)}


def update_project_payload(project_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    if "name" in payload and not str(payload.get("name") or "").strip():
        return _validation_error("Project name is required")
    updated = _project_store.update_project(project_id, **payload)
    if updated is None:
        return None
    return {"project": _project_store.to_dict(updated)}


def archive_project_payload(project_id: str) -> dict[str, bool] | None:
    return {"ok": True} if _project_store.archive_project(project_id) else None


def delete_project_payload(project_id: str) -> dict[str, bool] | None:
    return {"ok": True} if _project_store.delete_project(project_id) else None


def list_project_sources_payload(project_id: str) -> dict[str, Any] | None:
    if _project_store.get_project(project_id) is None:
        return None
    return ProjectSourceStore().list_sources(project_id)


def create_project_source_payload(project_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    if _project_store.get_project(project_id) is None:
        return None
    source_type = str(payload.get("source_type") or payload.get("type") or "text").strip().lower()
    title = str(payload.get("title") or "").strip()
    store = ProjectSourceStore()
    try:
        if source_type == "url":
            url = str(payload.get("url") or payload.get("uri") or "").strip()
            if not url:
                return _validation_error("URL is required")
            source = store.add_url_source(project_id=project_id, url=url, title=title)
        elif source_type in {"pdf", "docx"}:
            file_path = str(payload.get("file_path") or payload.get("path") or payload.get("uri") or "").strip()
            if not file_path:
                return _validation_error("file_path is required")
            source = store.add_document_source(project_id=project_id, path=Path(file_path), title=title)
        elif source_type in {"text", "markdown"}:
            content = str(payload.get("content") or "").strip()
            if not content:
                return _validation_error("Source content is required")
            source = store.add_text_source(
                project_id=project_id,
                title=title or "Untitled source",
                content=content,
                source_type=source_type,
            )
        else:
            return _validation_error("source_type must be text, markdown, url, pdf, or docx")
    except ValueError as exc:
        return _validation_error(str(exc))
    return {"source": source}


def update_project_source_payload(project_id: str, source_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    if _project_store.get_project(project_id) is None:
        return None
    kwargs: dict[str, Any] = {}
    for key in ("title", "include_policy", "parse_status", "parse_error"):
        if key in payload:
            kwargs[key] = payload.get(key)
    try:
        source = ProjectSourceStore().update_source(project_id, source_id, **kwargs)
    except ValueError as exc:
        return _validation_error(str(exc))
    if source is None:
        return None
    return {"source": source}


def delete_project_source_payload(project_id: str, source_id: str) -> dict[str, bool] | None:
    if _project_store.get_project(project_id) is None:
        return None
    return {"ok": True} if ProjectSourceStore().delete_source(project_id, source_id) else None


def project_source_context_preview_payload(project_id: str) -> dict[str, Any] | None:
    if _project_store.get_project(project_id) is None:
        return None
    return ProjectSourceStore().context_preview(project_id)


def create_research_run_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    query = str(payload.get("query") or "").strip()
    if not query:
        return _validation_error("Research query is required")
    try:
        run = ResearchRunStore().create_run(
            query=query,
            session_id=_optional_text(payload.get("session_id")),
            project_id=_optional_text(payload.get("project_id")),
            mode=str(payload.get("mode") or "deep"),
            plan=payload.get("plan") if isinstance(payload.get("plan"), dict) else None,
            status=str(payload.get("status") or "draft_plan"),
        )
    except ValueError as exc:
        return _validation_error(str(exc))
    return {"run": run}


def list_research_runs_payload(
    *,
    session_id: str | None = None,
    project_id: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    return ResearchRunStore().list_runs(session_id=session_id, project_id=project_id, limit=limit)


def get_research_run_payload(run_id: str) -> dict[str, Any] | None:
    run = ResearchRunStore().get_run(run_id)
    return {"run": run} if run is not None else None


def complete_research_run_payload(run_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    text = str(payload.get("text") or payload.get("final_text") or "").strip()
    if not text:
        return _validation_error("Research final text is required")
    sources = payload.get("sources")
    if not isinstance(sources, list):
        sources = []
    trace = payload.get("research_trace") or payload.get("trace")
    if not isinstance(trace, list):
        trace = []
    quality_score = payload.get("quality_score")
    if not isinstance(quality_score, dict):
        quality_score = {}
    run = ResearchRunStore().complete_run(
        run_id,
        final_text=text,
        sources=[item for item in sources if isinstance(item, dict)],
        quality_score=quality_score,
        trace=[item for item in trace if isinstance(item, dict)],
    )
    return {"run": run} if run is not None else None


def update_research_run_status_payload(run_id: str, status: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        if status == "failed":
            run = ResearchRunStore().fail_run(run_id, str((payload or {}).get("error") or "Research failed"))
        else:
            run = ResearchRunStore().update_status(run_id, status)
    except ValueError as exc:
        return _validation_error(str(exc))
    return {"run": run} if run is not None else None


def add_todo_payload(project_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    text = str(payload.get("text") or "").strip()
    if not text:
        return _validation_error("Todo text is required")
    todo = _project_store.add_todo(project_id, text)
    if todo is None:
        return None
    return {"todo": asdict(todo)}


def update_todo_payload(project_id: str, todo_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    changed = False
    updated_todo = None
    text: str | None = None
    if "text" in payload:
        text = str(payload.get("text") or "").strip()
        if not text:
            return _validation_error("Todo text is required")
    if "done" in payload:
        updated_todo = _project_store.set_todo_done(project_id, todo_id, bool(payload.get("done")))
        if updated_todo is None:
            return None
        changed = True
    elif payload.get("toggle"):
        updated_todo = _project_store.toggle_todo(project_id, todo_id)
        if updated_todo is None:
            return None
        changed = True
    if "text" in payload:
        updated_todo = _project_store.update_todo_text(project_id, todo_id, text or "")
        if updated_todo is None:
            return None
        changed = True
    if not changed:
        return _validation_error("Todo update payload is required")
    return {"ok": True, "todo": asdict(updated_todo)} if updated_todo is not None else {"ok": True}


def delete_todo_payload(project_id: str, todo_id: str) -> dict[str, bool] | None:
    return {"ok": True} if _project_store.delete_todo(project_id, todo_id) else None


def add_project_session_payload(project_id: str, payload: dict[str, Any]) -> dict[str, bool] | None:
    session_id = str(payload.get("session_id") or "").strip()
    if not session_id:
        return _validation_error("Session id is required")
    return {"ok": True} if _project_store.add_session(project_id, session_id) else None


def get_conversation_title(session_id: str) -> dict[str, str]:
    path = _session_path(session_id)
    if not path.exists():
        return {"title": ""}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"title": ""}
    title = data.get("title", "") if isinstance(data, dict) else ""
    return {"title": str(title)}


def set_conversation_title(session_id: str, title: str) -> dict[str, str | bool]:
    path = _session_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    data["session_id"] = str(data.get("session_id") or session_id)
    data["title"] = title
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "session_id": session_id, "title": title}


def generate_conversation_title(
    manager: SessionManager,
    session_id: str,
    first_message: str,
    provider_name: str | None = None,
    model: str | None = None,
) -> dict[str, str]:
    """Use a lightweight LLM call to produce a 4-6 word conversation title."""
    import re as _re

    text = first_message.strip()
    if not text:
        return {"title": ""}

    words = text.split()
    if _is_likely_title(text):
        title = text[:60]
        set_conversation_title(session_id, title)
        _pool_session = manager.get_if_exists(session_id)
        if _pool_session is not None:
            _pool_session.session.title = title
        return {"title": title}

    try:
        # Reuse an existing session's provider — cheapest path, avoids re-auth
        session = manager.get(session_id, provider_name, model)

        prompt = (
            f"Generate a concise 4-6 word title for a conversation that starts with:\n\n{text[:400]}\n\n"
            "Reply with ONLY the title — no quotes, no punctuation at the end, no explanation."
        )
        msgs = [{"role": "user", "content": prompt}]
        response = session.provider.chat(msgs)
        raw = str(response.content or "").strip().strip('"\'').strip()
        # Clean up: first line only, max 70 chars
        title = _re.sub(r"[\n\r]+.*", "", raw)[:70].strip()
        if not title:
            raise ValueError("empty title")
    except Exception:
        # Fallback: extract first 8 words, title-case
        title = (" ".join(words[:8]) or text)[:70].strip()

    set_conversation_title(session_id, title)
    _pool_session = manager.get_if_exists(session_id)
    if _pool_session is not None:
        _pool_session.session.title = title
    return {"title": title}


def execute_command(manager: SessionManager, request: CommandRequest) -> dict[str, Any]:
    command, args = parse_slash_command(request.raw)
    if command is None:
        return {"type": "error", "error": "Unknown command"}
    if command.level == "client":
        return {"type": "client", "command": command.to_dict(), "args": args}
    if command.level == "skill":
        skill = get_engine().get(command.name)
        return {
            "type": "skill",
            "command": command.to_dict(),
            "message": _skill_message(command, args),
            "system_prompt": skill.system_prompt if skill else "",
        }
    session = manager.get(request.session_id, request.provider_name, request.model)
    output = session.execute_command(request.raw)
    return {
        "type": "server",
        "command": command.to_dict(),
        "session_id": session.session_id,
        "output": output,
    }


def chat_events(manager: SessionManager, request: ChatRequest):
    if not request.message.strip():
        raise ValueError("Chat message is required")
    session = manager.get(
        request.session_id,
        request.provider_name,
        request.model,
        mode_id=request.mode_id,
        user_input=request.message,
    )
    if request.project_id:
        project = _project_store.get_project(request.project_id)
        if project:
            session.set_project_context(_project_context_payload(project), project_id=project.id)
            try:
                blocks = project_source_context_blocks(project.id)
            except Exception:
                logger.exception("Failed to attach project sources for project %s", project.id)
                blocks = []
            setter = getattr(session, "set_project_source_context_blocks", None)
            if callable(setter):
                setter(blocks)
            _project_store.add_session(request.project_id, session.session_id)
    yield from session.chat_stream(
        request.message,
        max_turns=request.max_turns,
        memory_enabled=not request.ghost_mode,
        ghost_mode=request.ghost_mode,
        images=request.images or [],
    )


def get_research_engine(manager: SessionManager) -> ResearchEngine:
    global _research_engine
    if _research_engine is None:
        _research_engine = ResearchEngine(manager)
    return _research_engine


def research_events(manager: SessionManager, request: ResearchRequest):
    if not request.query.strip():
        raise ValueError("Research query is required")
    engine = get_research_engine(manager)
    run_id: str | None = None
    run_store: ResearchRunStore | None = None
    if not request.ghost_mode:
        try:
            run_store = ResearchRunStore()
            run = run_store.create_run(
                query=request.query,
                session_id=request.session_id,
                project_id=request.project_id,
                mode=request.mode,
                status="running",
            )
            run_id = str(run["id"])
        except Exception:
            run_store = None
            run_id = None
    for event in engine.research_stream(
        request.query,
        request.session_id,
        request.provider_name,
        request.model,
        save_memory=not request.ghost_mode,
        mode=request.mode,
    ):
        if isinstance(event, dict) and run_id:
            event = dict(event)
            data = dict(event.get("data") or {})
            data.setdefault("run_id", run_id)
            event["data"] = data
            if event.get("type") == "research_complete" and run_store is not None:
                completed = run_store.complete_run(
                    run_id,
                    final_text=str(data.get("text") or ""),
                    sources=[item for item in (data.get("sources") or []) if isinstance(item, dict)],
                    quality_score=data.get("quality_score") if isinstance(data.get("quality_score"), dict) else {},
                    trace=[item for item in (data.get("research_trace") or []) if isinstance(item, dict)],
                )
                if completed is not None:
                    data["artifact_id"] = completed.get("artifact_id")
                    event["data"] = data
            elif event.get("type") == "research_error" and run_store is not None:
                run_store.fail_run(run_id, str(data.get("error") or "Research failed"))
        if (
            isinstance(event, dict)
            and event.get("type") == "research_complete"
            and request.session_id
            and not request.ghost_mode
        ):
            try:
                data = event.get("data") or {}
                append_research_trace(
                    session_id=request.session_id,
                    sources=data.get("sources") or [],
                    query=request.query,
                    mode=request.mode,
                )
            except Exception:
                pass
        yield event


def event_to_sse(event: TurnStreamEvent | dict[str, Any]) -> bytes:
    if isinstance(event, dict):
        event_type = str(event.get("type") or "message")
        payload = json.dumps(event.get("data", {}), ensure_ascii=False)
        return f"event: {event_type}\ndata: {payload}\n\n".encode("utf-8")
    payload = json.dumps(event.to_dict(), ensure_ascii=False)
    return f"event: {event.type}\ndata: {payload}\n\n".encode("utf-8")


def json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def parse_json_bytes(raw: bytes) -> dict[str, Any]:
    if not raw:
        return {}
    data = json.loads(raw.decode("utf-8"))
    return data if isinstance(data, dict) else {}


def is_validation_error(payload: object) -> bool:
    return isinstance(payload, dict) and payload.get("ok") is False and payload.get("code") == "validation_error"


def _validation_error(message: str) -> dict[str, Any]:
    return {"ok": False, "error": message, "code": "validation_error"}


def _skill_message(command: SlashCommand, args: str) -> str:
    return f"{command.command} {args}".strip()


def _is_likely_title(text: str) -> bool:
    if len(text) > 60:
        return False
    ascii_ratio = sum(1 for char in text if ord(char) < 128) / max(len(text), 1)
    if ascii_ratio > 0.7:
        return True
    import unicodedata

    letter_ratio = sum(1 for char in text if unicodedata.category(char).startswith("L")) / max(len(text), 1)
    return letter_ratio > 0.6


def _project_context_payload(project: Any) -> str:
    context_parts: list[str] = []
    project_lines = [f"## Project: {project.name}"]
    if str(project.description or "").strip():
        project_lines.append(str(project.description).strip())
    if str(project.context_md or "").strip():
        project_lines.append(str(project.context_md).strip())
    context_parts.append("\n\n".join(project_lines))
    context_parts.append(
        "## Project Operating Mode\n"
        "Treat this project as a durable workspace, not a one-off chat. "
        "Use the project goals below as the main direction for the answer, "
        "continue unfinished goals across conversations, and explicitly call out "
        "goal changes when the user reveals new direction."
    )

    pending_todos = [todo for todo in project.todos if not todo.done]
    if pending_todos:
        todo_text = "\n".join(f"- [ ] {todo.text}" for todo in pending_todos[:10])
        context_parts.append(f"## Project Goals\n{todo_text}")

    scoped_memories = list_memories_payload(
        scope=project.id,
        status="active",
        limit=8,
        offset=0,
    ).get("items", [])
    if isinstance(scoped_memories, list) and scoped_memories:
        rendered = []
        for memory in scoped_memories[:8]:
            if not isinstance(memory, dict):
                continue
            content = str(memory.get("content") or memory.get("name") or "").strip()
            if content:
                rendered.append(f"- {content[:500]}")
        if rendered:
            context_parts.append("## Project Memory\n" + "\n".join(rendered))

    return "\n\n".join(context_parts)


def _derive_skill_name(description: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", description.lower())
    useful = [word for word in words if len(word) > 2 and word not in {"the", "and", "for", "with"}]
    return "-".join(useful[:4]) or "new-skill"


def _skill_status_from_payload(value: Any, *, default: SkillStatus) -> SkillStatus:
    text = str(value or default).strip().lower()
    if text in {"review", "active", "disabled", "archived"}:
        return text  # type: ignore[return-value]
    return default


def _skill_eval_status_from_payload(value: Any, *, default: str) -> Any:
    text = str(value or default).strip().lower()
    if text in {"pending", "passed", "failed"}:
        return text
    return default


def _extract_skill_markdown(raw: str) -> str:
    text = raw.strip()
    match = re.search(r"```(?:markdown|md)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text


def _has_valid_skill_frontmatter(raw: str) -> bool:
    try:
        from src.skills.frontmatter import parse_frontmatter

        parsed = parse_frontmatter(raw)
        frontmatter = getattr(parsed, "frontmatter", parsed[0] if isinstance(parsed, tuple) else {})
        return bool(frontmatter.get("name") and frontmatter.get("description"))
    except Exception:
        return False


def _fallback_skill_markdown(name: str, description: str) -> str:
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "---\n\n"
        f"# {name.replace('-', ' ').title()}\n\n"
        "Use this skill when the user asks for the capability described above.\n\n"
        "## Workflow\n\n"
        "1. Clarify the desired outcome when the request is ambiguous.\n"
        "2. Gather the relevant context from the conversation and available files.\n"
        "3. Produce a concise, actionable answer with explicit assumptions.\n"
        "4. Name any risks, tradeoffs, or follow-up checks that matter.\n"
    )


def _active_memory_count() -> int:
    try:
        init_db()
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM memories WHERE status = 'active'"
            ).fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0


def _coerce_setting_value(
    config: GenevaConfig,
    field_name: str,
    value: Any,
) -> str | bool:
    if field_name == "default_mode":
        return normalize_mode_id(str(value))
    current = getattr(config, field_name)
    if isinstance(current, bool):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)
    return str(value)


def _safe_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: object) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _session_path(session_id: str) -> Path:
    safe_session_id = Path(session_id).name
    return Path.home() / ".geneva" / "sessions" / f"{safe_session_id}.json"


def skill_files_payload(name: str) -> "dict[str, Any] | None":
    """Return recursive file tree of a skill directory."""
    import os

    engine = get_engine()
    safe_name = name.strip().replace("/", "").replace("..", "")
    if not safe_name:
        return None
    skill_dir = (engine._dir / safe_name).resolve()
    # Security: must be inside skills_dir
    try:
        skill_dir.relative_to(engine._dir.resolve())
    except ValueError:
        return None
    if not skill_dir.exists() or not skill_dir.is_dir():
        return None

    def _build(path: "Path") -> "list[dict[str, Any]]":
        entries: "list[dict[str, Any]]" = []
        try:
            items = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return entries
        for item in items:
            if item.name.startswith(".") or item.name == ".skill-control-plane.json":
                continue
            rel = str(item.relative_to(skill_dir))
            if item.is_dir():
                entries.append({"type": "dir", "name": item.name, "path": rel, "children": _build(item)})
            else:
                entries.append({"type": "file", "name": item.name, "path": rel})
        return entries

    return {"files": _build(skill_dir)}


def skill_file_content_payload(name: str, rel_path: str) -> "dict[str, Any] | None":
    """Return content of a specific file inside a skill directory."""
    engine = get_engine()
    safe_name = name.strip().replace("/", "").replace("..", "")
    if not safe_name or not rel_path:
        return None
    skill_dir = (engine._dir / safe_name).resolve()
    try:
        skill_dir.relative_to(engine._dir.resolve())
        target = (skill_dir / rel_path).resolve()
        target.relative_to(skill_dir)
    except ValueError:
        return None
    if not target.exists() or not target.is_file():
        return None
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return {"content": content, "path": rel_path, "name": target.name}
