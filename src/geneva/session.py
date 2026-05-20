"""Geneva headless backend session."""
from __future__ import annotations

import json
import logging
import os
import queue
import shlex
import sqlite3
from datetime import datetime, timezone
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from src.agent.conversation import Conversation
from src.agent.session import Session
from src.commands import lookup
from src.config import get_provider_config
from src.context_system import build_context_prompt
from src.cost_tracker import CostEntry, CostTracker
from src.outputStyles import resolve_output_style
from src.geneva.context_disclosure import build_context_summary
from src.geneva.events import ErrorInfo, MemoryActivity, TurnStreamEvent, public_error_info
from src.geneva.agent_trace import append_trace_record, hash_content, list_trace_records
from src.geneva.memory_write_review import record_memory_write_event
from src.geneva.settings_manager import DEFAULT_MODEL, DEFAULT_PROVIDER, load_settings
from src.geneva.slash_commands import parse_slash_command
from src.geneva.skill_engine import get_engine
from src.geneva.turn_state import TurnState
from src.memdir.brain_engine import DB_PATH, MemoryResult, init_db, refresh_context, remember
from src.memdir.memdir import load_memory_prompt
from src.memdir import transcript_store as _transcript_store
from src.providers import get_provider_class
from src.services.extract_memories.extract_memories import run_extraction
from src.services.auto_dream.auto_dream import init_auto_dream
from src.services.compact import (
    AutoCompact,
    ContextSourceBlock,
    append_context_ledger_record,
    build_turn_context_ledger,
    estimate_context_budget,
    list_context_ledger_records,
    summarize_context_ledger_record,
    trim_to_token_budget,
)
from src.services.model_router import DEFAULT_MODE_ID, RouteDecision, route, route_mode
from src.services.session_memory.session_memory import load_session_memory
from src.tool_system.agent_loop import AgentLoopResult, ToolEvent, run_agent_loop, summarize_tool_result
from src.tool_system.context import ToolContext
from src.tool_system.defaults import build_default_registry
from src.utils.asyncio_tools import run_awaitable_sync

logger = logging.getLogger(__name__)
EPISODIC_MEMORY_MAX_CHARS = 12_000


def _resolve_default_model(provider_name: str, configured_model: str, routed_model: str) -> str:
    if provider_name == "openrouter":
        return configured_model if configured_model.startswith("deepseek/deepseek-v4-") else DEFAULT_MODEL
    return configured_model or routed_model


@dataclass
class TurnResult:
    text: str
    tool_events: list[ToolEvent]
    usage: dict[str, int] | None
    num_turns: int
    error: str | None = None


@dataclass
class MemoryStats:
    total_active: int
    total_superseded: int
    total_archived: int
    total_expired: int
    last_indexed: str | None


@dataclass
class PermissionRequestState:
    request_id: str
    session_id: str
    tool_name: str
    message: str
    suggestion: str | None
    created_at: float
    timeout_seconds: float
    event: threading.Event
    approved: bool | None = None


def _format_bg_result(result: dict) -> str:
    lines = [f"[Background task {result.get('task_id', '?')} complete]"]
    lines.append(f"Command: {result.get('command', '')}")
    exit_code = result.get("exit_code", "?")
    lines.append(f"Exit code: {exit_code}")
    stdout = (result.get("stdout") or "").strip()
    if stdout:
        lines.append(f"stdout:\n{stdout}")
    stderr = (result.get("stderr") or "").strip()
    if stderr:
        lines.append(f"stderr:\n{stderr}")
    return "\n".join(lines)


class GenevaSession:
    """Headless wrapper around the agent loop for Phase 2 Geneva."""

    def __init__(
        self,
        provider_name: str | None = None,
        model: str | None = None,
        mode_id: str | None = None,
        session_id: str | None = None,
        workspace_root: Path | None = None,
    ) -> None:
        decision: RouteDecision = route_mode(mode_id, "") if mode_id else route("")
        _cfg = load_settings()
        if provider_name:
            resolved_provider = provider_name
        elif mode_id:
            resolved_provider = decision.provider_name
        elif _cfg.openrouter_api_key:
            resolved_provider = "openrouter"
        elif _cfg.default_provider:
            resolved_provider = _cfg.default_provider
        else:
            resolved_provider = decision.provider_name or DEFAULT_PROVIDER
        resolved_model = model or (decision.model if mode_id else _resolve_default_model(resolved_provider, _cfg.default_model, decision.model))

        provider = self._build_provider(resolved_provider, resolved_model)
        self.provider_name = resolved_provider
        self.provider = provider
        self.mode_id = decision.mode_id or (DEFAULT_MODE_ID if mode_id else None)
        self.mode_label = decision.mode_label
        self.route_decision = decision

        loaded_session = Session.load(session_id) if session_id else None
        if session_id and loaded_session is None:
            logger.warning("Requested session_id was not found: %s", session_id)
        self.session = loaded_session or Session.create(resolved_provider, self.provider.model)
        # R3.4: detect incomplete tasks for resume prompt
        self._has_pending_tasks = False
        try:
            from src.memdir.task_store import get_active_tasks
            self._has_pending_tasks = bool(get_active_tasks(self.session_id or ""))
        except Exception:
            pass
        if loaded_session is not None:
            self._skill_context = loaded_session.skill_context or ""
            self._active_skill_name = loaded_session.active_skill_name or None
            self._ghost_mode = bool(loaded_session.ghost_mode)
        else:
            self._skill_context = ""
            self._active_skill_name = None
            self._ghost_mode = False
        self.session.provider = resolved_provider
        self.session.model = self.provider.model

        self.tool_profile = os.environ.get("GENEVA_TOOL_PROFILE", "web_safe")
        self.tool_registry = build_default_registry(profile=self.tool_profile)
        self.tool_context = ToolContext(workspace_root=workspace_root or Path.cwd())
        self.tool_context.bg_task_notify = self._on_bg_task_done
        self.tool_context.permission_handler = self._headless_permission_handler
        self.cost_tracker = CostTracker()
        self._last_tool_events: list[ToolEvent] = []
        self._memory_activity: list[MemoryActivity] = []
        self._project_context = ""
        self._project_context_external = False
        self._active_project_id: str | None = None
        self._project_source_context_blocks: list[ContextSourceBlock] = []
        self._auto_compact = AutoCompact(threshold=0.75, cooldown_seconds=45.0)
        self._auto_dream_check = init_auto_dream(agent_caller=self._call_auto_dream_agent)
        self._latest_context_ledger: dict[str, Any] | None = None
        self._context_ledger_history: list[dict[str, Any]] = []
        self._permission_requests: dict[str, PermissionRequestState] = {}
        self._permission_lock = threading.RLock()
        self._turn_lock = threading.Lock()
        self._cancel_token: threading.Event = threading.Event()
        self._turn_state: TurnState = TurnState.IDLE
        self._amendment_queue: queue.Queue[str] = queue.Queue()
        self._pending_bg_results: list[dict] = []
        self._pending_bg_lock = threading.Lock()
        self._active_put_event: Any = None
        init_db()

    def _build_provider(self, provider_name: str, model: str):
        _cfg = load_settings()
        config = get_provider_config(provider_name)
        provider_class = get_provider_class(provider_name)
        if provider_name == "anthropic":
            api_key = _cfg.anthropic_api_key or str(config.get("api_key", ""))
        elif provider_name == "openrouter":
            api_key = (
                _cfg.openrouter_api_key
                or os.environ.get("OPENROUTER_API_KEY", "")
                or str(config.get("api_key", ""))
            )
        else:
            api_key = str(config.get("api_key", ""))
        return provider_class(
            api_key=api_key,
            base_url=config.get("base_url"),
            model=model,
        )

    def configure_mode(
        self,
        mode_id: str | None,
        *,
        provider_name: str | None = None,
        model: str | None = None,
        user_input: str = "",
    ) -> None:
        if not mode_id and not provider_name and not model:
            return
        decision = route_mode(mode_id or self.mode_id or DEFAULT_MODE_ID, user_input)
        resolved_provider = provider_name or decision.provider_name
        resolved_model = model or decision.model
        if self.provider_name == resolved_provider and self.provider.model == resolved_model:
            self.mode_id = decision.mode_id
            self.mode_label = decision.mode_label
            self.route_decision = decision
            self.session.provider = resolved_provider
            self.session.model = resolved_model
            return
        self.provider_name = resolved_provider
        self.provider = self._build_provider(resolved_provider, resolved_model)
        self.mode_id = decision.mode_id
        self.mode_label = decision.mode_label
        self.route_decision = decision
        self.session.provider = resolved_provider
        self.session.model = self.provider.model

    def cancel_current_turn(self) -> None:
        self._cancel_token.set()

    def inject_amendment(self, text: str) -> None:
        self._amendment_queue.put(text)

    _AMENDABLE_STATES: frozenset = frozenset({
        TurnState.RECEIVED,
        TurnState.CONTEXT_BUILT,
        TurnState.MODEL_STARTED,
        TurnState.TOOL_PENDING,
    })

    def amend_current_turn(self, text: str) -> dict:
        """Push text into the amendment queue if a turn is currently active.

        Returns a dict with:
          ok=True, status="queued", turn_state=<current state value>  -> amendment accepted
          ok=False, status="idle", reason=<str>                       -> no active turn (caller falls back to normal chat)
          ok=False, status="empty", reason=<str>                      -> text was blank
        """
        text = text.strip()
        if not text:
            return {"ok": False, "status": "empty", "reason": "text must not be empty"}
        if self._turn_state not in self._AMENDABLE_STATES:
            return {"ok": False, "status": "idle", "reason": "no active turn to amend"}
        self.inject_amendment(text)
        return {"ok": True, "status": "queued", "turn_state": self._turn_state.value}

    def _on_bg_task_done(self, task_id: str, command: str, result: dict) -> None:
        put_fn = None
        with self._pending_bg_lock:
            self._pending_bg_results.append(result)
            put_fn = self._active_put_event
        if put_fn is not None:
            try:
                put_fn(
                    "background_task_done",
                    {
                        "task_id": result.get("task_id"),
                        "command": result.get("command"),
                        "exit_code": result.get("exit_code"),
                        "stdout": (result.get("stdout") or "")[:2000],
                        "stderr": (result.get("stderr") or "")[:500],
                        "completed_at": result.get("completed_at"),
                    },
                )
            except Exception:
                logger.exception("Failed to emit realtime bg_task_done SSE")

    def _make_fallback_provider(self):
        """Return a fallback provider instance if GENEVA_FALLBACK_PROVIDER is set, else None."""
        from src.services.model_router.router import route_fallback
        decision = route_fallback()
        if decision is None:
            return None
        _cfg = load_settings()
        config = get_provider_config(decision.provider_name)
        provider_class = get_provider_class(decision.provider_name)
        if decision.provider_name == "anthropic":
            api_key = _cfg.anthropic_api_key or str(config.get("api_key", ""))
        elif decision.provider_name == "openrouter":
            api_key = (
                _cfg.openrouter_api_key
                or os.environ.get("OPENROUTER_API_KEY", "")
                or str(config.get("api_key", ""))
            )
        else:
            api_key = str(config.get("api_key", ""))
        if not api_key:
            return None
        return provider_class(
            api_key=api_key,
            base_url=config.get("base_url"),
            model=decision.model,
        )

    def chat(self, user_input: str, max_turns: int = 100) -> TurnResult:
        self._last_tool_events.clear()
        turn_id = uuid.uuid4().hex
        previous_extra = getattr(self.tool_context, "extra_system_prompt", "")
        self._handle_intent_routing(user_input)
        self._apply_skill_context(user_input)
        try:
            memory_block = self._build_memory_block(user_input, turn_id=turn_id)
            self.tool_context.extra_system_prompt = memory_block
            self.session.conversation.add_user_message(user_input)
            self._maybe_auto_compact(memory_block)
            result = run_agent_loop(
                conversation=self.session.conversation,
                provider=self.provider,
                tool_registry=self.tool_registry,
                tool_context=self.tool_context,
                max_turns=max_turns,
                stream=False,
                verbose=False,
                on_event=self._collect_tool_event,
            )
            usage = self._normalize_usage(result.usage)
            self._track_cost(result)
            self._capture_memory_after_turn(
                user_input=user_input,
                assistant_text=result.response_text,
                tool_events=list(self._last_tool_events),
                turn_id=turn_id,
            )
            self.session.save()
            self._write_transcript_turn(user_input, result.response_text)
            self._run_auto_dream_check()
            return TurnResult(
                text=result.response_text,
                tool_events=list(self._last_tool_events),
                usage=usage,
                num_turns=result.num_turns,
            )
        except Exception as exc:
            logger.exception("GenevaSession chat failed")
            error = public_error_info(exc)
            return TurnResult(
                text="",
                tool_events=list(self._last_tool_events),
                usage=None,
                num_turns=0,
                error=error.message,
            )
        finally:
            self.tool_context.extra_system_prompt = previous_extra

    def chat_stream(
        self,
        user_input: str,
        max_turns: int = 100,
        memory_enabled: bool = True,
        ghost_mode: bool = False,
        images: list[dict[str, str]] | None = None,
    ) -> Iterator[TurnStreamEvent]:
        turn_id = uuid.uuid4().hex
        event_seq = 0
        event_queue: queue.Queue[TurnStreamEvent | None] = queue.Queue()
        if not ghost_mode:
            self._handle_intent_routing(user_input)
        self._apply_skill_context(user_input)

        def next_event(
            event_type: str,
            data: dict[str, Any],
            tool_call_id: str | None = None,
            error: ErrorInfo | None = None,
        ) -> TurnStreamEvent:
            nonlocal event_seq
            event = TurnStreamEvent(
                turn_id=turn_id,
                event_seq=event_seq,
                type=event_type,  # type: ignore[arg-type]
                data=data,
                timestamp=time.time(),
                tool_call_id=tool_call_id,
                error=error,
            )
            event_seq += 1
            return event

        def put_event(
            event_type: str,
            data: dict[str, Any],
            tool_call_id: str | None = None,
            error: ErrorInfo | None = None,
        ) -> None:
            event_queue.put(next_event(event_type, data, tool_call_id, error))

        yield next_event(
            "memory_load_start",
            {"session_id": self.session_id, "query": user_input},
        )
        previous_ghost = getattr(self, "_ghost_mode", False)
        previous_session_ghost = bool(getattr(self.session, "ghost_mode", False))
        if ghost_mode:
            self._ghost_mode = True
            self.session.ghost_mode = True
        try:
            memory_block = self._build_memory_block(
                user_input,
                persist_ledger=memory_enabled and not ghost_mode,
                turn_id=turn_id,
            )
        finally:
            self._ghost_mode = previous_ghost
            self.session.ghost_mode = previous_session_ghost
        if os.environ.get("GENEVA_DEBUG") == "1":
            _dbg_ledger = self._latest_context_ledger or {}
            for _i, _e in enumerate(_dbg_ledger.get("entries", [])):
                logger.debug("[GENEVA_DEBUG] context[%d] label=%r tokens=%d action=%s", _i, _e.get("label"), _e.get("tokens_after", 0), _e.get("action"))
        context_budget = self._estimate_context_budget(
            user_input=user_input,
            extra_prompt=memory_block,
        )
        context_ledger = summarize_context_ledger_record(self._latest_context_ledger)
        memory_stats = self.get_memory_stats()
        yield next_event(
            "memory_load_complete",
            {
                "session_id": self.session_id,
                "chars": len(memory_block),
                "context_budget": context_budget.to_dict(),
                "context_ledger": context_ledger,
                "stats": memory_stats.__dict__,
            },
        )

        slash_command, _ = parse_slash_command(user_input)
        if slash_command is not None and slash_command.level == "server":
            slash_pre_turn_messages = list(self.session.conversation.messages)
            self.session.conversation.add_user_message(user_input)
            output = self.execute_command(user_input)
            if output:
                self.session.conversation.add_assistant_message(output)
                yield next_event("text_delta", {"text": output})
            if memory_enabled and not ghost_mode:
                self._emit_memory_activity(
                    user_input=user_input,
                    assistant_text=output,
                    tool_events=[],
                    put_event=put_event,
                )
            context_summary = build_context_summary(
                self._latest_context_ledger,
                tool_events=[],
                ghost_mode=ghost_mode,
            )
            if not ghost_mode:
                self.session.save()
            if memory_enabled and not ghost_mode:
                self._run_auto_dream_check()
            if ghost_mode:
                self.session.conversation.messages = slash_pre_turn_messages
            yield next_event(
                "turn_complete",
                {
                    "session_id": self.session_id,
                    "usage": None,
                    "num_turns": 0,
                    "command": slash_command.name,
                    "context_summary": context_summary,
                },
            )
            return

        worker = threading.Thread(
            target=self._run_stream_worker,
            kwargs={
                "turn_id": turn_id,
                "user_input": user_input,
                "memory_block": memory_block,
                "memory_enabled": memory_enabled,
                "ghost_mode": ghost_mode,
                "images": images or [],
                "max_turns": max_turns,
                "put_event": put_event,
                "event_queue": event_queue,
            },
            daemon=True,
        )
        worker.start()
        while True:
            try:
                event = event_queue.get(timeout=15.0)
            except queue.Empty:
                yield next_event(
                    "heartbeat",
                    {"session_id": self.session_id, "status": "working"},
                )
                continue
            if event is None:
                break
            yield event
        worker.join(timeout=1.0)

    def execute_command(self, raw: str) -> str:
        text = raw.strip()
        if not text.startswith("/"):
            return "Commands must start with '/'."
        command_text = text[1:].strip()
        if not command_text:
            return "No command provided."

        parts = command_text.split(maxsplit=1)
        cmd_name = parts[0].lower()
        args_str = parts[1] if len(parts) > 1 else ""
        meta = lookup(cmd_name)
        if meta is None:
            return f"Unknown command: /{cmd_name}"

        try:
            parsed_args = shlex.split(args_str) if args_str.strip() else []
            result = run_awaitable_sync(meta.run(parsed_args))
        except ValueError as exc:
            return f"Invalid command arguments: {exc}"
        except Exception as exc:
            logger.exception("Command failed: %s", raw)
            return f"Command failed: {exc}"
        return str(result) if result else ""

    def get_memory_stats(self) -> MemoryStats:
        try:
            init_db()
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT status, COUNT(*) as cnt FROM memories GROUP BY status"
                ).fetchall()
                status_counts = {str(row["status"]): int(row["cnt"]) for row in rows}
                last_row = conn.execute(
                    "SELECT MAX(updated_at) as last FROM memories"
                ).fetchone()
            return MemoryStats(
                total_active=status_counts.get("active", 0),
                total_superseded=status_counts.get("superseded", 0),
                total_archived=status_counts.get("archived", 0),
                total_expired=status_counts.get("expired", 0),
                last_indexed=last_row["last"] if last_row else None,
            )
        except Exception:
            logger.exception("Failed to load memory stats")
            return MemoryStats(0, 0, 0, 0, None)

    def list_recent_memories(self, limit: int = 6) -> list[dict[str, Any]]:
        try:
            init_db()
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT id, name, type, status, content, confidence, importance,
                           memory_kind, scope, source_session_id, captured_at,
                           last_validated_at, updated_at, created_at
                    FROM memories
                    WHERE status = 'active'
                    ORDER BY COALESCE(updated_at, created_at) DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            return [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "type": row["type"],
                    "status": row["status"],
                    "content": row["content"],
                    "confidence": row["confidence"],
                    "importance": row["importance"],
                    "memory_kind": row["memory_kind"],
                    "scope": row["scope"],
                    "source_session_id": row["source_session_id"],
                    "captured_at": row["captured_at"],
                    "last_validated_at": row["last_validated_at"],
                    "updated_at": row["updated_at"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
        except Exception:
            logger.exception("Failed to load recent memories")
            return []

    def get_memory_activity(self) -> list[dict[str, Any]]:
        return [activity.to_dict() for activity in self._memory_activity[-20:]]

    def get_messages(self) -> list[dict[str, Any]]:
        return self.session.conversation.get_messages()

    def get_display_messages(self) -> list[dict[str, Any]]:
        return self.session.conversation.get_display_messages()

    def get_context_ledger(self, limit: int = 50) -> dict[str, Any]:
        persisted = list_context_ledger_records(self.session_id, limit=max(1, min(limit, 100)))
        return {
            "session_id": self.session_id,
            "latest": self._latest_context_ledger,
            "history": list(self._context_ledger_history[-limit:]),
            "records": persisted,
        }

    def get_agent_traces(self, limit: int = 50) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "records": list_trace_records(self.session_id, limit=limit),
        }

    def resolve_permission_request(self, request_id: str, approved: bool) -> bool:
        with self._permission_lock:
            pending = self._permission_requests.get(request_id)
            if pending is None:
                return False
            pending.approved = bool(approved)
            pending.event.set()
            return True

    @staticmethod
    def _date_bucket(iso_str: str, ref: datetime | None = None) -> str:
        """Return date bucket for a session given its updated_at ISO string."""
        today = datetime.now().date()
        try:
            session_date = datetime.fromisoformat(iso_str).date()
        except (ValueError, TypeError):
            if ref is None:
                return "older"
            session_date = ref.date()

        delta = (today - session_date).days
        if delta == 0:
            return "today"
        if delta == 1:
            return "yesterday"
        if delta <= 3:
            return "three_days_ago"
        if delta <= 6:
            return "this_week"
        if delta <= 13:
            return "two_weeks_ago"
        if delta <= 20:
            return "three_weeks_ago"
        if delta <= 30:
            return "one_month"
        return "older"

    def list_sessions(self) -> list[dict[str, str]]:
        session_dir = Path.home() / ".geneva" / "sessions"
        if not session_dir.exists():
            return []

        sessions: list[dict[str, str]] = []
        for path in sorted(session_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)[:50]:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                conversation = data.get("conversation", {})
                messages = conversation.get("messages", []) if isinstance(conversation, dict) else []
                updated_at_str = str(data.get("updated_at") or "")
                try:
                    file_mtime = datetime.fromtimestamp(path.stat().st_mtime)
                except (OSError, OverflowError, ValueError):
                    file_mtime = None
                sessions.append(
                    {
                        "session_id": str(data.get("session_id") or path.stem),
                        "created_at": str(data.get("created_at") or ""),
                        "updated_at": updated_at_str,
                        "provider": str(data.get("provider") or ""),
                        "model": str(data.get("model") or ""),
                        "title": str(data.get("title") or ""),
                        "message_count": str(len(messages) if isinstance(messages, list) else 0),
                        "date_bucket": GenevaSession._date_bucket(updated_at_str, file_mtime),
                        "pinned": bool(data.get("pinned", False)),
                    }
                )
            except Exception:
                logger.exception("Failed to parse session file: %s", path)
        return sessions

    def list_sessions_paged(self, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """Return paginated session list with total count."""
        session_dir = Path.home() / ".geneva" / "sessions"
        if not session_dir.exists():
            return {"sessions": [], "total": 0, "limit": limit, "offset": offset}

        safe_limit = max(1, min(int(limit), 200))
        safe_offset = max(0, int(offset))

        all_paths = sorted(session_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        total = len(all_paths)
        page_paths = all_paths[safe_offset : safe_offset + safe_limit]

        sessions: list[dict[str, str]] = []
        for path in page_paths:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                conversation = data.get("conversation", {})
                messages = conversation.get("messages", []) if isinstance(conversation, dict) else []
                updated_at_str = str(data.get("updated_at") or "")
                try:
                    file_mtime = datetime.fromtimestamp(path.stat().st_mtime)
                except (OSError, OverflowError, ValueError):
                    file_mtime = None
                sessions.append(
                    {
                        "session_id": str(data.get("session_id") or path.stem),
                        "created_at": str(data.get("created_at") or ""),
                        "updated_at": updated_at_str,
                        "provider": str(data.get("provider") or ""),
                        "model": str(data.get("model") or ""),
                        "title": str(data.get("title") or ""),
                        "message_count": str(len(messages) if isinstance(messages, list) else 0),
                        "date_bucket": GenevaSession._date_bucket(updated_at_str, file_mtime),
                        "pinned": bool(data.get("pinned", False)),
                    }
                )
            except Exception:
                logger.exception("Failed to parse session file: %s", path)

        sessions.sort(key=lambda s: (not s.get("pinned", False),))
        return {"sessions": sessions, "total": total, "limit": safe_limit, "offset": safe_offset}

    def save(self) -> None:
        self.session.save()

    def new_conversation(self) -> None:
        self.session.conversation = Conversation()

    def switch_session(self, session_id: str) -> bool:
        loaded = Session.load(session_id)
        if loaded is None:
            return False
        self.session = loaded
        return True

    def set_project_context(self, context_md: str, project_id: str | None = None) -> None:
        self._project_context = context_md
        self._project_context_external = bool(context_md)
        self._active_project_id = project_id if context_md else None
        if not context_md:
            self._project_source_context_blocks = []

    def set_project_source_context_blocks(self, blocks: list[ContextSourceBlock]) -> None:
        self._project_source_context_blocks = list(blocks)

    def clear_skill_context(self) -> None:
        """Explicitly exit the active skill."""
        self._skill_context = ""
        self._active_skill_name = None
        self.session.skill_context = ""
        self.session.active_skill_name = None

    def _handle_intent_routing(self, user_input: str) -> None:
        """R10.3c / R10.6: Route semantic intents into real project/skill state."""
        try:
            from src.geneva.intent_router import classify_intent
            from src.geneva.blast_writer import append_to_blast, create_blast_docs
            from src.geneva.project_store import ProjectStore

            result = classify_intent(user_input)
            if result.confidence < 0.6 or result.intent == "normal_chat":
                return
            store = ProjectStore()
            if result.intent == "create_project":
                name = result.params.get("project_name") or "Untitled Project"
                project = store.auto_create_for_session(self.session_id, f"new project: {name}") or store.create_project(name)
                store.add_session(project.id, self.session_id)
                create_blast_docs(project.id, project.name, project.description)
                context_md = f"# {project.name}\n{project.description}"
                self.set_project_context(context_md, project.id)
            elif result.intent == "attach_project":
                name = result.params.get("project_name", "")
                if name:
                    for p in store.list_projects():
                        if name.lower() in p.name.lower() or p.name.lower() in name.lower():
                            store.add_session(p.id, self.session_id)
                            self.set_project_context(p.context_md or f"# {p.name}", p.id)
                            break
            elif result.intent == "add_todo" and self._active_project_id:
                todo = store.add_todo(self._active_project_id, user_input)
                if todo is not None:
                    store.add_activity(self._active_project_id, "todo", todo.text)
                    project = store.get_project(self._active_project_id)
                    if project is not None:
                        create_blast_docs(project.id, project.name, project.description)
                    append_to_blast(self._active_project_id, "task-plan.md", f"- [ ] {todo.text}")
            elif result.intent == "add_project_log" and self._active_project_id:
                store.add_activity(self._active_project_id, "log", user_input)
                project = store.get_project(self._active_project_id)
                if project is not None:
                    create_blast_docs(project.id, project.name, project.description)
                append_to_blast(self._active_project_id, "progress.md", f"- {user_input[:500]}")
            elif result.intent == "create_skill":
                self._skill_context = (
                    "[Skill Builder Mode]\n\n"
                    "Help the user create a new Geneva skill. "
                    "Ask for: skill name, description, trigger phrases. "
                    "Then generate SKILL.md content with frontmatter and system prompt."
                )
                self.session.skill_context = self._skill_context
                self._active_skill_name = "skill-builder"
                self.session.active_skill_name = self._active_skill_name
            elif result.intent == "update_skill":
                self._skill_context = (
                    "[Skill Editor Mode]\n\n"
                    "Help the user update an existing Geneva skill. Locate the skill file first, "
                    "preserve its trigger contract, and make the smallest safe edit."
                )
                self.session.skill_context = self._skill_context
                self._active_skill_name = "skill-editor"
                self.session.active_skill_name = self._active_skill_name
            elif result.intent == "deep_research":
                self._skill_context = (
                    "[Deep Research Mode]\n\n"
                    "Use search/fetch tools when current external evidence is required, compare sources, "
                    "and cite URLs in the answer."
                )
                self.session.skill_context = self._skill_context
                self._active_skill_name = "deep-research"
                self.session.active_skill_name = self._active_skill_name
            elif result.intent == "document_workflow":
                self._skill_context = (
                    "[Document Workflow Mode]\n\n"
                    "Use document parsing and verification tools for files, keep findings grounded in the source, "
                    "and identify missing pages or unreadable sections."
                )
                self.session.skill_context = self._skill_context
                self._active_skill_name = "document-workflow"
                self.session.active_skill_name = self._active_skill_name
            elif result.intent == "computer_use":
                self._skill_context = (
                    "[Computer Use Mode]\n\n"
                    "Use browser or computer tools only when they are available and appropriate. "
                    "Narrate state changes concisely."
                )
                self.session.skill_context = self._skill_context
                self._active_skill_name = "computer-use"
                self.session.active_skill_name = self._active_skill_name
        except Exception:
            logger.exception("Intent routing failed")

    def _maybe_decompose_intent(self, user_input: str) -> None:
        try:
            from src.geneva.task_planner import decompose_intent

            decompose_intent(
                user_input,
                self.session_id,
                llm_caller=self._call_auto_dream_agent,
                project_id=self._active_project_id,
            )
        except Exception:
            logger.exception("Task decomposition failed")

    def _log_project_activity(self, *, user_input: str, assistant_text: str) -> None:
        """R10.5b: Log turn to project activity log when a project is active."""
        if self._ghost_mode or not self._active_project_id:
            return
        try:
            from datetime import datetime, timezone

            from src.geneva.blast_writer import append_to_blast, create_blast_docs
            from src.geneva.project_store import ProjectStore
            store = ProjectStore()
            store.add_activity(
                self._active_project_id,
                "user_goal",
                user_input[:200],
            )
            project = store.get_project(self._active_project_id)
            if project is not None:
                create_blast_docs(project.id, project.name, project.description)
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            progress_line = f"- {timestamp}: {user_input[:500]}"
            append_to_blast(self._active_project_id, "progress.md", progress_line)
            if self._looks_like_decision(user_input):
                store.add_activity(self._active_project_id, "decision", user_input[:500])
                append_to_blast(self._active_project_id, "decisions.md", f"- {timestamp}: {user_input[:500]}")
        except Exception:
            pass

    @staticmethod
    def _looks_like_decision(text: str) -> bool:
        lowered = text.lower()
        return any(
            token in lowered
            for token in (
                "decision",
                "decided",
                "ตัดสินใจ",
                "สรุปว่า",
                "เลือกใช้",
            )
        )

    def _apply_skill_context(self, user_input: str) -> None:
        try:
            engine = get_engine()
            skill_name = engine.detect_trigger(user_input)
            if not skill_name:
                return
            skill = engine.get(skill_name)
            if skill is None or not skill.system_prompt:
                return
            self._active_skill_name = skill.name
            self._skill_context = (
                f"[Skill: /{skill.name}]\n\n"
                f"{skill.system_prompt}"
            )
            engine.record_invocation(skill.name)
            self.session.skill_context = self._skill_context
            self.session.active_skill_name = self._active_skill_name
        except Exception:
            logger.exception("Failed to apply skill context")

    @property
    def session_id(self) -> str:
        return self.session.session_id

    @property
    def message_count(self) -> int:
        return len(self.session.conversation.messages)

    def _collect_tool_event(self, event: ToolEvent) -> None:
        self._last_tool_events.append(event)

    def _stream_tool_event_payload(self, event: ToolEvent) -> dict[str, Any]:
        return {
            "tool_name": event.tool_name,
            "tool_input": event.tool_input if self._fits_event_payload(event.tool_input) else None,
            "tool_input_preview": self._event_preview(event.tool_input),
            "tool_output": event.tool_output if self._fits_event_payload(event.tool_output) else None,
            "tool_output_preview": self._event_preview(event.tool_output),
            "is_error": event.is_error,
            "error": event.error,
            "status": event.status,
            "summary": event.summary,
            "turn_index": event.turn_index,
            "started_at": event.started_at,
            "completed_at": event.completed_at,
            "duration_ms": event.duration_ms,
            "timeout_seconds": event.timeout_seconds,
        }

    @staticmethod
    def _fits_event_payload(value: Any, max_chars: int = 2_000) -> bool:
        if value is None:
            return True
        try:
            rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        except Exception:
            rendered = str(value)
        return len(rendered) <= max_chars

    @staticmethod
    def _event_preview(value: Any, max_chars: int = 1_200) -> str:
        if value is None:
            return ""
        try:
            rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        except Exception:
            rendered = str(value)
        rendered = rendered.replace("\x00", "").strip()
        if len(rendered) <= max_chars:
            return rendered
        return rendered[: max_chars - 18].rstrip() + "\n[truncated]"

    def _run_stream_worker(
        self,
        *,
        turn_id: str,
        user_input: str,
        memory_block: str,
        memory_enabled: bool,
        ghost_mode: bool = False,
        images: list[dict[str, str]] | None = None,
        max_turns: int = 100,
        put_event: Any,
        event_queue: queue.Queue[TurnStreamEvent | None],
    ) -> None:
        self._last_tool_events.clear()
        self._turn_state = TurnState.RECEIVED
        previous_extra = getattr(self.tool_context, "extra_system_prompt", "")
        previous_permission_handler = self.tool_context.permission_handler
        previous_ghost = getattr(self, "_ghost_mode", False)
        previous_session_ghost = bool(getattr(self.session, "ghost_mode", False))
        conversation = getattr(self.session, "conversation", None)
        pre_turn_messages = list(getattr(conversation, "messages", []))
        if ghost_mode:
            self._ghost_mode = True
            self.session.ghost_mode = True
        else:
            self._ghost_mode = previous_ghost
        effective_memory_enabled = memory_enabled and not self._ghost_mode
        with self._pending_bg_lock:
            self._active_put_event = put_event
        if not self._turn_lock.acquire(blocking=False):
            self._amendment_queue.put(user_input)
            put_event(
                "amendment_accepted",
                {
                    "session_id": self.session_id,
                    "status": "incorporated",
                    "message": "ข้อความของคุณจะถูกรวมเข้ากับการตอบกลับปัจจุบัน",
                },
            )
            event_queue.put(None)
            self.session.ghost_mode = previous_session_ghost
            self._ghost_mode = previous_ghost
            return

        # Drain amendments that may have leaked from the previous turn's race window.
        # Lock is now held - we own this turn. Any queue entry from before this
        # acquisition belongs to a different (now-finished) turn.
        while True:
            try:
                self._amendment_queue.get_nowait()
            except queue.Empty:
                break

        # Drain pending background task results: emit SSE + inject as amendments.
        with self._pending_bg_lock:
            pending_bg = list(self._pending_bg_results)
            self._pending_bg_results.clear()
        for bg_result in pending_bg:
            put_event(
                "background_task_done",
                {
                    "task_id": bg_result.get("task_id"),
                    "command": bg_result.get("command"),
                    "exit_code": bg_result.get("exit_code"),
                    "stdout": (bg_result.get("stdout") or "")[:2000],
                    "stderr": (bg_result.get("stderr") or "")[:500],
                    "completed_at": bg_result.get("completed_at"),
                },
            )
            self._amendment_queue.put(_format_bg_result(bg_result))

        def on_text_chunk(chunk: str) -> None:
            if chunk:
                put_event("text_delta", {"text": chunk})

        def permission_handler(
            tool_name: str,
            message: str,
            suggestion: str | None,
        ) -> tuple[bool, bool]:
            return self._wait_for_web_permission(
                tool_name=tool_name,
                message=message,
                suggestion=suggestion,
                put_event=put_event,
            )

        def on_tool_event(event: ToolEvent) -> None:
            self._collect_tool_event(event)
            payload = self._stream_tool_event_payload(event)
            if event.kind == "agent_turn_start":
                put_event("agent_turn_start", payload)
                return
            if event.kind == "agent_turn_complete":
                put_event("agent_turn_complete", payload)
                return
            if event.kind == "agent_loop_limit":
                put_event(
                    "agent_loop_limit",
                    payload,
                    error=ErrorInfo(
                        code="internal_error",
                        message=event.error or "Max tool turns reached",
                        recoverable=True,
                        suggestion="Narrow the request or raise the turn limit for this run.",
                    ),
                )
                return
            if event.kind == "tool_use":
                put_event("tool_call_start", payload, event.tool_use_id)
                put_event("tool_executing", payload, event.tool_use_id)
            elif event.kind == "tool_timeout":
                put_event(
                    "tool_timeout",
                    payload,
                    event.tool_use_id,
                    ErrorInfo(
                        code="timeout",
                        message=event.error or f"{event.tool_name} timed out",
                        recoverable=True,
                        suggestion="Retry with a narrower request or use a faster tool path.",
                    ),
                )
            elif event.kind == "tool_result":
                if event.is_error:
                    put_event(
                        "tool_error",
                        payload,
                        event.tool_use_id,
                        ErrorInfo(
                            code="tool_error",
                            message=event.error or f"{event.tool_name} failed",
                            recoverable=True,
                            suggestion="Try again or simplify the request.",
                        ),
                    )
                else:
                    put_event("tool_complete", payload, event.tool_use_id)
            elif event.kind == "tool_error":
                put_event(
                    "tool_error",
                    payload,
                    event.tool_use_id,
                    ErrorInfo(
                        code="tool_error",
                        message=event.error or f"{event.tool_name} failed",
                        recoverable=True,
                        suggestion="Try again or simplify the request.",
                    ),
                )

        try:
            self.tool_context.extra_system_prompt = memory_block
            self.tool_context.permission_handler = permission_handler
            setattr(self.tool_context, "session_id", self.session_id)
            setattr(self.tool_context, "turn_id", turn_id)
            if images:
                self.session.conversation.add_user_message_with_images(user_input, images)
            else:
                self.session.conversation.add_user_message(user_input)
            self._maybe_auto_compact(memory_block)
            self._turn_state = TurnState.MODEL_STARTED
            if not self._ghost_mode:
                self._write_turn_wal(turn_id, user_input)
            def _try_run(provider_for_run):
                return run_agent_loop(
                    conversation=self.session.conversation,
                    provider=provider_for_run,
                    tool_registry=self.tool_registry,
                    tool_context=self.tool_context,
                    max_turns=max_turns,
                    stream=True,
                    verbose=False,
                    on_event=on_tool_event,
                    on_text_chunk=on_text_chunk,
                    cancel_token=self._cancel_token,
                    amendment_queue=self._amendment_queue,
                )

            _RETRYABLE = {"rate_limit", "network_error", "timeout"}
            try:
                result = _try_run(self.provider)
            except Exception as _primary_exc:
                _primary_info = public_error_info(_primary_exc)
                _fallback_provider = (
                    self._make_fallback_provider()
                    if _primary_info.code in _RETRYABLE
                    else None
                )
                if _fallback_provider is not None:
                    logger.warning(
                        "Primary provider failed (%s), retrying with fallback provider",
                        _primary_info.code,
                    )
                    result = _try_run(_fallback_provider)
                else:
                    raise
            self._turn_state = (
                TurnState.CANCELLED if result.cancelled else TurnState.ASSISTANT_DONE
            )
            if result.cancelled:
                put_event("turn_cancelled", {"session_id": self.session_id, "turn_id": turn_id})
            self._track_cost(result)
            _ledger = self._latest_context_ledger or {}
            _ctx_names = [
                e.get("label", "")
                for e in _ledger.get("entries", [])
                if e.get("action") in ("included", "trimmed") and e.get("label")
            ]
            _tool_events = list(self._last_tool_events)
            _errors = [ev.error for ev in _tool_events if ev.is_error and ev.error]
            _system_prompt_hash = hash_content(self.tool_context.extra_system_prompt)
            _context_summary = build_context_summary(
                self._latest_context_ledger,
                tool_events=_tool_events,
                ghost_mode=self._ghost_mode,
            )
            put_event(
                "turn_complete",
                {
                    "session_id": self.session_id,
                    "usage": self._normalize_usage(result.usage),
                    "num_turns": result.num_turns,
                    "cancelled": result.cancelled,
                    "context_summary": _context_summary,
                },
            )

            if not result.cancelled and not self._ghost_mode:
                def _finalize_turn() -> None:
                    try:
                        memory_action: str | None = None
                        memory_active_chars: int | None = None
                        episode_result: MemoryResult | None = None
                        if effective_memory_enabled:
                            activity, episode_result = self._capture_memory_after_turn(
                                user_input=user_input,
                                assistant_text=result.response_text,
                                tool_events=_tool_events,
                                turn_id=turn_id,
                            )
                            memory_action = str(activity.action)
                            memory_active_chars = (
                                int(activity.after.get("active_chars", 0) or 0) if activity.after else None
                            )

                        _mem_ids = [episode_result.memory_id] if episode_result and episode_result.memory_id else []
                        self._persist_agent_trace(
                            turn_id=turn_id,
                            user_input=user_input,
                            assistant_text=result.response_text,
                            tool_events=_tool_events,
                            memory_action=memory_action,
                            memory_active_chars=memory_active_chars,
                            system_prompt_hash=_system_prompt_hash,
                            context_block_names=_ctx_names,
                            memory_write_ids=_mem_ids,
                            errors=_errors,
                        )
                        self.session.save()
                        self._write_transcript_turn(user_input, result.response_text)
                        if effective_memory_enabled:
                            self._run_auto_dream_check()
                    except Exception:
                        logger.exception("Post-turn finalization failed")

                threading.Thread(
                    target=_finalize_turn,
                    daemon=True,
                    name="geneva-post-turn-finalize",
                ).start()
        except Exception as exc:
            logger.exception("GenevaSession streaming chat failed")
            error = public_error_info(exc)
            put_event(
                "error",
                {},
                error=error,
            )
        finally:
            if not self._ghost_mode:
                self._clear_turn_wal(turn_id)
            with self._pending_bg_lock:
                self._active_put_event = None
            self._cancel_token.clear()
            self.tool_context.extra_system_prompt = previous_extra
            self.tool_context.permission_handler = previous_permission_handler
            if hasattr(self.tool_context, "session_id"):
                delattr(self.tool_context, "session_id")
            if hasattr(self.tool_context, "turn_id"):
                delattr(self.tool_context, "turn_id")
            if ghost_mode and hasattr(self.session, "conversation"):
                self.session.conversation.messages = pre_turn_messages
            self.session.ghost_mode = previous_session_ghost
            self._ghost_mode = previous_ghost
            self._turn_lock.release()
            self._turn_state = TurnState.IDLE
            event_queue.put(None)

    def _headless_permission_handler(
        self,
        tool_name: str,
        message: str,
        suggestion: str | None,
    ) -> tuple[bool, bool]:
        logger.warning(
            "Auto-denied headless permission request for %s: %s %s",
            tool_name,
            message,
            suggestion or "",
        )
        return False, False

    def _wait_for_web_permission(
        self,
        *,
        tool_name: str,
        message: str,
        suggestion: str | None,
        put_event: Any,
        timeout_seconds: float = 60.0,
    ) -> tuple[bool, bool]:
        request_id = uuid.uuid4().hex
        state = PermissionRequestState(
            request_id=request_id,
            session_id=self.session_id,
            tool_name=tool_name,
            message=message,
            suggestion=suggestion,
            created_at=time.time(),
            timeout_seconds=timeout_seconds,
            event=threading.Event(),
        )
        with self._permission_lock:
            self._permission_requests[request_id] = state
        put_event(
            "tool_permission_request",
            {
                "request_id": request_id,
                "session_id": self.session_id,
                "tool_name": tool_name,
                "message": message,
                "suggestion": suggestion,
                "timeout_seconds": timeout_seconds,
                "status": "pending",
            },
        )
        approved = False
        try:
            if state.event.wait(timeout_seconds):
                approved = bool(state.approved)
            else:
                approved = False
            put_event(
                "tool_permission_resolved",
                {
                    "request_id": request_id,
                    "session_id": self.session_id,
                    "tool_name": tool_name,
                    "approved": approved,
                    "status": "approved" if approved else "denied",
                },
            )
            return approved, False
        finally:
            with self._permission_lock:
                self._permission_requests.pop(request_id, None)

    def _build_memory_block(
        self,
        user_input: str,
        *,
        persist_ledger: bool = True,
        turn_id: str | None = None,
    ) -> str:
        blocks: list[str] = []
        source_blocks: list[ContextSourceBlock] = []
        seen: set[str] = set()
        runtime_base_prompt = self._build_runtime_base_prompt()
        if runtime_base_prompt:
            source_blocks.append(
                ContextSourceBlock(
                    source_type="runtime_base_context",
                    label="Runtime base prompt and tool schemas",
                    text=runtime_base_prompt,
                    reason="The agent loop sends output style, workspace context, and tool schemas in addition to memory.",
                )
            )

        if self._ghost_mode:
            ghost_block = (
                "## Ghost Mode Privacy Contract\n"
                "This turn is private. Do not save transcript, agent trace, memory extraction, "
                "project activity, or dream consolidation output for this turn."
            )
            blocks.append(ghost_block)
            source_blocks.append(
                ContextSourceBlock(
                    source_type="ghost_privacy_contract",
                    label="Ghost Mode Privacy Contract",
                    text=ghost_block,
                    reason="Ghost mode is active, so the runtime must prove privacy safeguards in the context ledger.",
                )
            )

        # Inject cognition block first — inject order contract: cognition before soul/project/skill/memory
        try:
            from src.geneva.cognition import build_cognition_block
            _cognition = build_cognition_block(self.provider.model).strip()
            if _cognition:
                blocks.append(_cognition)
        except Exception:
            logger.exception("Failed to inject cognition block into memory block")

        try:
            from src.geneva.runtime_identity import load_runtime_identity_blocks

            for identity_block in load_runtime_identity_blocks():
                normalized = identity_block.text.strip()
                if not normalized or normalized in seen:
                    continue
                blocks.append(normalized)
                source_blocks.append(
                    ContextSourceBlock(
                        source_type=identity_block.source_type,
                        label=identity_block.label,
                        text=normalized,
                        reason=identity_block.reason,
                        metadata=identity_block.metadata,
                    )
                )
                seen.add(normalized)
        except Exception:
            logger.exception("Failed to inject runtime identity blocks")

        if not self._ghost_mode:
            self._maybe_decompose_intent(user_input)

        # R3.3: inject active task context
        try:
            from src.geneva.task_planner import build_task_context_block
            _task_block = build_task_context_block(self.session_id)
            if _task_block:
                blocks.append(_task_block)
        except Exception:
            pass

        if user_input.strip().lower().startswith("[web-search]"):
            web_search_block = (
                "## Web Search Requested\n"
                "The user enabled web search for this turn. Use the WebSearch and WebFetch tools "
                "when current external information would improve the answer, and cite useful URLs."
            )
            blocks.append(web_search_block)
            source_blocks.append(
                ContextSourceBlock(
                    source_type="web_search_instruction",
                    label="Web search instruction",
                    text=web_search_block,
                    reason="User explicitly requested current external information.",
                )
            )
        if self._project_context:
            project_block = f"## Active Project Context\n{self._project_context}"
            blocks.append(project_block)
            source_blocks.append(
                ContextSourceBlock(
                    source_type="project_context",
                    label="Active project context",
                    text=project_block,
                    reason="Project context is pinned while the session is scoped to a project.",
                    metadata={"project_id": self._active_project_id},
                )
            )
        for source_block in self._project_source_context_blocks:
            if not source_block.text.strip():
                continue
            blocks.append(source_block.text)
            source_blocks.append(source_block)
        if self._skill_context:
            blocks.append(self._skill_context)
            source_blocks.append(
                ContextSourceBlock(
                    source_type="skill_context",
                    label=f"Active skill: {self._active_skill_name or 'unknown'}",
                    text=self._skill_context,
                    reason="Detected skill trigger injects workflow instructions for this turn.",
                    metadata={"skill_name": self._active_skill_name},
                )
            )

        static_prompt = "\n\n".join(blocks)
        budget = self._estimate_context_budget(
            user_input=user_input,
            extra_prompt=static_prompt,
            runtime_base_prompt=runtime_base_prompt,
        )

        memory_budget = budget.memory_budget_tokens
        memory_context = ""
        memory_source_type = "memory_context"
        memory_reason = "Durable memories matched the current user request."
        if memory_budget > 0:
            memory_context = self._safe_refresh_context(user_input, max_tokens=memory_budget)
        if not memory_context and memory_budget > 0:
            fallback_parts = [self._safe_session_memory(), self._safe_memory_prompt()]
            memory_context = "\n\n".join(part.strip() for part in fallback_parts if part.strip())
            memory_source_type = "fallback_memory_context"
            memory_reason = "Primary semantic memory lookup returned nothing, so session/static memory was used."

        for block in (memory_context,):
            normalized = block.strip()
            if normalized and normalized not in seen:
                rendered = trim_to_token_budget(normalized, memory_budget)
                blocks.append(rendered)
                source_blocks.append(
                    ContextSourceBlock(
                        source_type=memory_source_type,
                        label="Memory context",
                        text=normalized,
                        rendered_text=rendered,
                        action="trimmed" if rendered != normalized else "included",
                        reason=memory_reason,
                        metadata={
                            "memory_budget_tokens": memory_budget,
                            "memory_count": self._count_context_memory_items(normalized),
                        },
                    )
                )
                seen.add(normalized)
        final_context = "\n\n".join(blocks)
        self._write_turn_context_ledger(
            user_input=user_input,
            budget=budget,
            source_blocks=source_blocks,
            final_context=final_context,
            memory_budget_tokens=memory_budget,
            persist=persist_ledger,
            turn_id=turn_id,
        )
        return final_context

    @staticmethod
    def _count_context_memory_items(memory_context: str) -> int:
        count = sum(1 for line in memory_context.splitlines() if line.lstrip().startswith("- ["))
        return count if count > 0 else 1

    def _estimate_context_budget(
        self,
        *,
        user_input: str = "",
        extra_prompt: str = "",
        runtime_base_prompt: str | None = None,
    ):
        messages = self.session.conversation.get_messages()
        if user_input.strip():
            messages = [*messages, {"role": "user", "content": user_input}]
        return estimate_context_budget(
            messages=messages,
            model=self.provider.model,
            system_prompt=runtime_base_prompt if runtime_base_prompt is not None else self._build_runtime_base_prompt(),
            projected_extra_prompt=extra_prompt,
        )

    def _build_runtime_base_prompt(self) -> str:
        parts: list[str] = []
        try:
            from src.geneva.cognition import build_cognition_block

            cognition = build_cognition_block(self.provider.model)
            if cognition.strip():
                parts.append(cognition.strip())
        except Exception:
            logger.exception("Failed to build cognition block")
        try:
            style_name = getattr(self.tool_context, "output_style_name", None)
            style_dir = getattr(self.tool_context, "output_style_dir", None)
            style_prompt = resolve_output_style(style_name, style_dir).prompt
            if style_prompt.strip():
                parts.append(style_prompt.strip())
        except Exception:
            logger.exception("Failed to estimate output style prompt")
        try:
            context_prompt = build_context_prompt(
                self.tool_context.workspace_root,
                cwd=self.tool_context.cwd,
            )
            if context_prompt.strip():
                parts.append(context_prompt.strip())
        except Exception:
            logger.exception("Failed to estimate workspace context prompt")
        try:
            tool_schemas = [
                {
                    "name": spec.name,
                    "description": spec.description,
                    "input_schema": spec.input_schema,
                }
                for spec in self.tool_registry.list_specs()
            ]
            if tool_schemas:
                parts.append(
                    "## Available Tool Schemas\n"
                    + json.dumps(tool_schemas, ensure_ascii=False, sort_keys=True)
                )
        except Exception:
            logger.exception("Failed to estimate tool schema tokens")
        return "\n\n".join(parts)

    def _maybe_auto_compact(self, memory_block: str) -> None:
        budget = self._estimate_context_budget(extra_prompt=memory_block)
        if not budget.should_compact:
            return
        try:
            compact_result = run_awaitable_sync(
                self._auto_compact.maybe_compact(
                    conversation=self.session.conversation,
                    provider=self.provider,
                    model=self.provider.model,
                    system_prompt=memory_block,
                    session_id=self.session_id,
                )
            )
            if compact_result and compact_result.ledger_record:
                self._remember_context_ledger(compact_result.ledger_record, persist=False)
        except Exception:
            logger.exception("Auto context compaction failed")

    def _write_turn_context_ledger(
        self,
        *,
        user_input: str,
        budget: Any,
        source_blocks: list[ContextSourceBlock],
        final_context: str,
        memory_budget_tokens: int,
        persist: bool,
        turn_id: str | None = None,
    ) -> None:
        try:
            record = build_turn_context_ledger(
                session_id=self.session_id,
                model=self.provider.model,
                budget=budget,
                user_input=user_input,
                messages=self.session.conversation.get_messages(),
                source_blocks=source_blocks,
                final_context=final_context,
                memory_budget_tokens=memory_budget_tokens,
                turn_id=turn_id,
                ghost_mode=self._ghost_mode,
                mode_id=self.mode_id,
                mode_label=self.mode_label,
                route_reason=getattr(self.route_decision, "reason", None),
                cost_tier=getattr(self.route_decision, "cost_tier", None),
            )
            self._remember_context_ledger(record, persist=persist)
        except Exception:
            logger.exception("Context ledger write failed")

    def _remember_context_ledger(self, record: Any, *, persist: bool) -> None:
        payload = record.to_dict() if hasattr(record, "to_dict") else dict(record)
        self._latest_context_ledger = payload
        self._context_ledger_history.append(payload)
        self._context_ledger_history = self._context_ledger_history[-20:]
        if not persist:
            return
        try:
            append_context_ledger_record(payload)
        except Exception:
            logger.exception("Failed to persist context ledger")

    def _write_turn_wal(self, turn_id: str, user_input: str) -> None:
        try:
            wal_path = Path.home() / ".geneva" / "wal" / "turns.jsonl"
            wal_path.parent.mkdir(parents=True, exist_ok=True)
            record = json.dumps({
                "turn_id": turn_id,
                "session_id": self.session_id,
                "user_input": user_input[:500],
                "model": self.provider.model,
                "provider": self.provider_name,
                "mode_id": self.mode_id,
                "mode_label": self.mode_label,
                "route_reason": getattr(self.route_decision, "reason", None),
                "cost_tier": getattr(self.route_decision, "cost_tier", None),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, ensure_ascii=False)
            with open(wal_path, "a", encoding="utf-8") as f:
                f.write(record + "\n")
        except Exception:
            logger.exception("Failed to write turn WAL")

    def _clear_turn_wal(self, turn_id: str) -> None:
        try:
            wal_path = Path.home() / ".geneva" / "wal" / "turns.jsonl"
            if not wal_path.exists():
                return
            lines = []
            with open(wal_path, encoding="utf-8") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                        if rec.get("turn_id") != turn_id:
                            lines.append(line)
                    except Exception:
                        lines.append(line)
            with open(wal_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception:
            logger.exception("Failed to clear turn WAL")

    def _run_memory_extraction(self, user_input: str, turn_id: str | None = None) -> None:
        try:
            run_awaitable_sync(
                run_extraction(
                    {
                        "user_request": user_input,
                        "session_id": self.session_id,
                        "turn_id": turn_id,
                        "scope": self._active_project_id,
                        "messages": self.session.conversation.get_messages(),
                    },
                    agent_caller=self._call_auto_dream_agent,
                )
            )
        except Exception:
            logger.exception("Memory extraction failed")

    def _run_auto_dream_check(self) -> None:
        try:
            run_awaitable_sync(self._auto_dream_check())
        except Exception:
            logger.exception("Auto Dream check failed")

    def _call_auto_dream_agent(self, prompt: str) -> str:
        response = self.provider.chat([{"role": "user", "content": prompt}], max_tokens=800)
        return str(response.content or "")

    def _write_transcript_turn(self, user_input: str, assistant_text: str) -> None:
        ghost = getattr(self, "_ghost_mode", False)
        msgs = self.session.conversation.messages
        base_idx = max(0, len(msgs) - 2)
        try:
            run_awaitable_sync(
                _transcript_store.write_turn(
                    self.session_id,
                    base_idx,
                    "user",
                    user_input,
                    project_id=self._active_project_id,
                    ghost_mode=ghost,
                )
            )
            run_awaitable_sync(
                _transcript_store.write_turn(
                    self.session_id,
                    base_idx + 1,
                    "assistant",
                    assistant_text,
                    project_id=self._active_project_id,
                    ghost_mode=ghost,
                )
            )
        except Exception:
            pass

    def _capture_memory_after_turn(
        self,
        *,
        user_input: str,
        assistant_text: str,
        tool_events: list[ToolEvent],
        turn_id: str | None = None,
    ) -> tuple[MemoryActivity, MemoryResult | None]:
        before = self.get_memory_stats()
        episode_result = self._persist_episode_memory(user_input, assistant_text, tool_events)
        write_event: dict[str, Any] | None = None
        if episode_result and episode_result.memory_id and episode_result.operation not in {"noop", "conflict"}:
            try:
                write_event = record_memory_write_event(
                    memory_id=episode_result.memory_id,
                    session_id=self.session_id,
                    turn_id=turn_id,
                    project_id=self._active_project_id,
                    write_type="auto_saved",
                    confidence=0.82,
                    sensitivity="private",
                    user_visible_text=self._truncate_memory_text(user_input.strip() or "Conversation memory", 320),
                    source_excerpt=self._truncate_memory_text(user_input.strip(), 240),
                )
            except Exception:
                logger.exception("Memory write event recording failed")
        # 7.1: LLM extraction runs in background — fire and don't block turn return
        if not self._ghost_mode:
            t = threading.Thread(
                target=self._run_memory_extraction,
                args=(user_input, turn_id),
                daemon=True,
                name="geneva-mem-extract",
            )
            t.start()
        after = self.get_memory_stats()
        action = "NOOP"
        if after.total_active > before.total_active:
            action = "ADD"
        elif after.last_indexed and after.last_indexed != before.last_indexed:
            action = "UPDATE"
        activity = MemoryActivity(
            session_id=self.session_id,
            timestamp=time.time(),
            action=action,  # type: ignore[arg-type]
            title="Auto memory extraction",
            memory_id=episode_result.memory_id if episode_result else None,
            write_event=write_event,
            content=user_input[:240],
            before=before.__dict__,
            after=after.__dict__,
        )
        self._memory_activity.append(activity)
        self._log_project_activity(user_input=user_input, assistant_text=assistant_text)
        return activity, episode_result

    def _emit_memory_activity(
        self,
        *,
        user_input: str,
        assistant_text: str,
        tool_events: list[ToolEvent],
        put_event: Any,
        turn_id: str | None = None,
    ) -> None:
        activity, episode_result = self._capture_memory_after_turn(
            user_input=user_input,
            assistant_text=assistant_text,
            tool_events=tool_events,
            turn_id=turn_id,
        )
        payload = activity.to_dict()
        if episode_result and episode_result.memory_id:
            payload["episode_memory_id"] = episode_result.memory_id
        put_event("memory_update", payload)

    def _persist_agent_trace(
        self,
        *,
        turn_id: str,
        user_input: str,
        assistant_text: str,
        tool_events: list[ToolEvent],
        memory_action: str | None = None,
        memory_active_chars: int | None = None,
        system_prompt_hash: str | None = None,
        context_block_names: list[str] | None = None,
        memory_write_ids: list[str] | None = None,
        errors: list[str] | None = None,
    ) -> None:
        if self._ghost_mode or os.environ.get("GENEVA_GHOST") == "1":
            return
        record = {
            "turn_id": turn_id,
            "trace_id": turn_id,
            "session_id": self.session_id,
            "model": self.provider.model,
            "provider": self.provider_name,
            "mode_id": self.mode_id,
            "mode_label": self.mode_label,
            "route_reason": getattr(self.route_decision, "reason", None),
            "cost_tier": getattr(self.route_decision, "cost_tier", None),
            "created_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "user_preview": self._truncate_memory_text(user_input.strip(), 500),
            "assistant_preview": self._truncate_memory_text((assistant_text or "").strip(), 700),
            "events": [self._trace_event_payload(event) for event in tool_events],
            "memory_action": memory_action,
            "memory_active_chars": memory_active_chars,
            "system_prompt_hash": system_prompt_hash,
            "context_block_names": context_block_names or [],
            "memory_write_ids": memory_write_ids or [],
            "errors": errors or [],
        }
        try:
            append_trace_record(record)
        except Exception:
            logger.exception("Agent trace persistence failed")

    def _trace_event_payload(self, event: ToolEvent) -> dict[str, Any]:
        input_str = self._event_preview(event.tool_input)
        output_str = self._event_preview(event.tool_output)
        return {
            "kind": event.kind,
            "tool_name": event.tool_name,
            "tool_call_id": event.tool_use_id,
            "status": event.status,
            "summary": event.summary,
            "is_error": event.is_error,
            "error": event.error,
            "turn_index": event.turn_index,
            "started_at": event.started_at,
            "completed_at": event.completed_at,
            "duration_ms": event.duration_ms,
            "timeout_seconds": event.timeout_seconds,
            "input_preview": input_str,
            "output_preview": output_str,
            "args_hash": hash_content(input_str),
            "result_hash": hash_content(output_str),
        }

    def _persist_episode_memory(
        self,
        user_input: str,
        assistant_text: str,
        tool_events: list[ToolEvent],
    ) -> MemoryResult | None:
        content = self._render_episode_memory(user_input, assistant_text, tool_events)
        if not content:
            return None
        try:
            captured_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            return run_awaitable_sync(
                remember(
                    content=content,
                    type="episodic",
                    source_type="assistant_inferred",
                    scope=self._active_project_id,
                    memory_kind="episode",
                    source_session_id=self.session_id,
                    captured_at=captured_at,
                )
            )
        except Exception:
            logger.exception("Episodic memory capture failed")
            return None

    def _render_episode_memory(
        self,
        user_input: str,
        assistant_text: str,
        tool_events: list[ToolEvent],
    ) -> str:
        user_text = user_input.strip()
        assistant = (assistant_text or "").strip()
        if not user_text and not assistant:
            return ""

        tool_lines: list[str] = []
        for event in tool_events:
            if event.kind not in {"tool_result", "tool_timeout", "tool_error"}:
                continue
            summary = event.summary or summarize_tool_result(event.tool_name, event.tool_output)
            if event.status in {"timeout", "error"} and event.error:
                summary = f"{summary} · {event.status}: {event.error}"
            if summary:
                tool_lines.append(f"- {summary}")

        sections = [
            f"Session: {self.session_id}",
            f"Captured at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
            "",
            "User:",
            self._truncate_memory_text(user_text, 4_000),
            "",
            "Assistant:",
            self._truncate_memory_text(assistant, 6_000),
        ]
        if tool_lines:
            sections.extend(["", "Tools:", *tool_lines[:12]])
        return self._truncate_memory_text("\n".join(sections).strip(), EPISODIC_MEMORY_MAX_CHARS)

    @staticmethod
    def _truncate_memory_text(text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        return text[: max(0, max_chars - 24)].rstrip() + "\n[truncated]"

    def _safe_refresh_context(self, user_input: str, max_tokens: int = 3000) -> str:
        try:
            return refresh_context(
                session_query=user_input,
                max_tokens=max_tokens,
                scope=self._active_project_id,
                include_identity_files=False,
            )
        except Exception:
            logger.exception("Failed to refresh memory context")
            return ""

    def _safe_session_memory(self) -> str:
        try:
            return str(run_awaitable_sync(load_session_memory()))
        except Exception:
            logger.exception("Failed to load session memory")
            return ""

    def _safe_memory_prompt(self) -> str:
        try:
            return load_memory_prompt(cwd=self.tool_context.workspace_root)
        except Exception:
            logger.exception("Failed to load memory prompt")
            return ""

    def _track_cost(self, result: AgentLoopResult) -> None:
        usage = self._normalize_usage(result.usage)
        if usage is None:
            return
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        if input_tokens <= 0 and output_tokens <= 0:
            return
        self.cost_tracker.add_cost(
            CostEntry(
                model=self.provider.model or self.provider_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=0,
                cache_write_tokens=0,
                cost_usd=0.0,
                timestamp="",
            )
        )

    def _normalize_usage(self, usage: dict[str, Any] | None) -> dict[str, int] | None:
        if not usage:
            return None
        return {
            "input_tokens": int(usage.get("input_tokens", 0) or 0),
            "output_tokens": int(usage.get("output_tokens", 0) or 0),
        }

    def _classify_error(self, exc: Exception) -> str:
        return public_error_info(exc).code
