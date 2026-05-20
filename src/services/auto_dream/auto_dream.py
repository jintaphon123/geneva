from __future__ import annotations

import inspect
import json
import logging
import re
import threading
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ...memdir.brain_engine import remember, search
from ...memdir.memory_types import MemoryType
from ...memdir.paths import get_auto_mem_path
from ...utils.asyncio_tools import run_awaitable_sync
from ..extract_memories.extract_memories import run_extraction
from .config import is_auto_dream_enabled
from .consolidation_lock import (
    list_sessions_touched_since,
    mark_consolidated,
    read_last_consolidated_at,
    release_consolidation_lock,
    try_acquire_consolidation_lock,
)
from .consolidation_prompt import build_consolidation_prompt

logger = logging.getLogger(__name__)

_workflow_counter: dict[str, int] = {}
_workflow_lock = threading.Lock()
_latest_dream_report: dict | None = None
_dream_scheduler_lock = threading.Lock()
_dream_scheduler_started = False


def _session_dir() -> Path:
    return Path.home() / ".geneva" / "sessions"


async def _maybe_await(result: object) -> object:
    if inspect.isawaitable(result):
        return await result  # type: ignore[no-any-return]
    return result


async def _run_default_consolidation(_sessions: list[Path], memory_dir: Path) -> None:
    episodes = search("", type=MemoryType.episodic.value, min_confidence=0.0)
    if not episodes:
        return
    for episode in episodes:
        await run_extraction(
            {"messages": [{"role": "user", "content": episode.content}], "scope": episode.scope},
            memory_dir=memory_dir,
        )


def _json_from_agent_result(result: object) -> dict[str, object] | list[object] | None:
    text = getattr(result, "content", result)
    if text is None:
        return None
    raw = str(text).strip()
    if not raw:
        return None
    fenced = re.search(r"```(?:json)?\s*(.*?)```", raw, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        raw = fenced.group(1).strip()
    else:
        start_candidates = [idx for idx in (raw.find("{"), raw.find("[")) if idx >= 0]
        if start_candidates:
            raw = raw[min(start_candidates):]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, (dict, list)) else None


async def _store_agent_memories(result: object) -> int:
    global _latest_dream_report

    parsed = _json_from_agent_result(result)
    if isinstance(parsed, dict):
        memories = parsed.get("memories")
    else:
        memories = parsed
    stored = 0
    allowed = {"user", "feedback", "project", "reference"}
    if isinstance(memories, list):
        for item in memories:
            if not isinstance(item, dict):
                continue
            memory_type = str(item.get("type") or "reference").strip().lower()
            content = str(item.get("content") or "").strip()
            scope_raw = item.get("scope")
            scope = str(scope_raw).strip() if scope_raw is not None and str(scope_raw).strip() else None
            if memory_type not in allowed or not content:
                continue
            result = await remember(
                content=content,
                type=memory_type,
                source_type="system_consolidation",
                scope=scope,
            )
            if result.success and result.operation != "noop":
                stored += 1
    if isinstance(parsed, dict):
        dream_report = parsed.get("dream_report")
        if isinstance(dream_report, dict):
            _latest_dream_report = dream_report
    return stored


def record_workflow_pattern(tool_names: list[str]) -> None:
    try:
        names = sorted({str(name).strip() for name in tool_names if str(name).strip()})
        if not names:
            return
        key = ",".join(names)
        with _workflow_lock:
            _workflow_counter[key] = _workflow_counter.get(key, 0) + 1
    except Exception:
        logger.exception("Failed to record workflow pattern")


def get_skill_nudge_suggestions() -> list[str]:
    try:
        with _workflow_lock:
            repeated = [
                (key, count)
                for key, count in _workflow_counter.items()
                if count >= 3
            ]
        repeated.sort(key=lambda item: (-item[1], item[0]))
        suggestions = []
        for key, _count in repeated[:3]:
            tools = " + ".join(part for part in key.split(",") if part)
            suggestions.append(
                f"Workflow pattern repeated 3+ times: {tools} → consider creating a skill"
            )
        return suggestions
    except Exception:
        logger.exception("Failed to get skill nudge suggestions")
        return []


def get_latest_dream_report() -> dict | None:
    try:
        return _latest_dream_report
    except Exception:
        logger.exception("Failed to get latest dream report")
        return None


def start_dream_scheduler(agent_caller: Callable, memory_dir: Path | None = None) -> None:
    global _dream_scheduler_started

    try:
        if not is_auto_dream_enabled():
            return

        check_and_dream_fn = init_auto_dream(memory_dir=memory_dir, agent_caller=agent_caller)

        def scheduler_loop() -> None:
            while True:
                try:
                    now = datetime.now()
                    next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
                    if next_run <= now:
                        next_run += timedelta(days=1)
                    sleep_seconds = max((next_run - now).total_seconds(), 0.0)
                    time.sleep(sleep_seconds)
                    try:
                        run_awaitable_sync(check_and_dream_fn())
                    except Exception:
                        logger.exception("Auto Dream scheduled check failed")
                except Exception:
                    logger.exception("Auto Dream scheduler loop failed")
                    time.sleep(60)

        with _dream_scheduler_lock:
            if _dream_scheduler_started:
                return
            thread = threading.Thread(target=scheduler_loop, name="geneva-dream-scheduler", daemon=True)
            thread.start()
            _dream_scheduler_started = True
    except Exception:
        logger.exception("Failed to start Auto Dream scheduler")


def init_auto_dream(
    memory_dir: Path | None = None,
    time_gate_hours: float = 2.0,
    session_gate_count: int = 3,
    agent_caller: Callable | None = None,
) -> Callable[[], Awaitable[None]]:
    target_memory_dir = (memory_dir or get_auto_mem_path(Path.cwd())).expanduser()

    async def check_and_dream() -> None:
        if not is_auto_dream_enabled():
            return

        sessions_dir = _session_dir()
        last = read_last_consolidated_at(target_memory_dir)
        since = last or (datetime.now(timezone.utc) - timedelta(days=3650))
        if last is not None and datetime.now(timezone.utc) - last < timedelta(hours=time_gate_hours):
            return

        sessions = list_sessions_touched_since(sessions_dir, since)
        if len(sessions) < session_gate_count:
            return
        if not try_acquire_consolidation_lock(target_memory_dir):
            return

        try:
            try:
                episodes = search("", type=MemoryType.episodic.value, min_confidence=0.0)
            except Exception:
                logger.exception("Auto Dream episode search failed")
                episodes = []
            if agent_caller is not None:
                prompt = build_consolidation_prompt(
                    sessions,
                    target_memory_dir,
                    episodes=episodes,
                    skill_suggestions=get_skill_nudge_suggestions(),
                )
                result = await _maybe_await(agent_caller(prompt))
                await _store_agent_memories(result)
            else:
                await _run_default_consolidation(sessions, target_memory_dir)
            mark_consolidated(target_memory_dir)
        finally:
            release_consolidation_lock(target_memory_dir)

    return check_and_dream
