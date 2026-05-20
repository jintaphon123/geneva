"""Task decomposition and handoff summary generation."""
from __future__ import annotations

import json
from collections.abc import Awaitable
from typing import Any

from src.memdir.task_store import Task, create_task, get_active_tasks
from src.utils.asyncio_tools import run_awaitable_sync


DECOMPOSE_SYSTEM_PROMPT = """You are a task planner. Given a complex user request, decompose it into 3-7 concrete steps.
Respond ONLY with valid JSON:
{
  "title": "Short task title (max 60 chars)",
  "plan": "1-2 sentence overview of the approach",
  "steps": ["Step 1 description", "Step 2 description", ...]
}
No markdown, no explanation, only the JSON object."""


def decompose_intent(
    user_input: str,
    session_id: str,
    llm_caller: Any | None = None,
    project_id: str | None = None,
) -> Task | None:
    """Decompose a complex intent into a task graph. Returns None for simple requests."""
    if llm_caller is None:
        return None

    words = user_input.split()
    connectors = sum(
        1
        for word in words
        if word.lower() in {"then", "after", "and", "also", "next", "finally", "first"}
    )
    thai_complex_signals = (
        "และ",
        "แล้ว",
        "จากนั้น",
        "ต่อมา",
        "พร้อม",
        "ทั้งหมด",
        "ไล่",
        "ตั้งแต่",
        "จนถึง",
        "ละเอียด",
    )
    has_thai_complex_signal = any(signal in user_input for signal in thai_complex_signals)
    if len(words) < 20 and connectors == 0 and len(user_input) < 120 and not has_thai_complex_signal:
        return None

    try:
        prompt = f"User request: {user_input[:500]}"
        result = llm_caller(DECOMPOSE_SYSTEM_PROMPT + "\n\n" + prompt)
        if isinstance(result, Awaitable):
            result = run_awaitable_sync(result)
        parsed = json.loads(result) if isinstance(result, str) else result
        title = parsed.get("title", user_input[:60])
        plan = parsed.get("plan", "")
        steps = parsed.get("steps", [])
        if not steps:
            return None
        return create_task(session_id, title, steps, plan=plan, project_id=project_id)
    except Exception:
        return None


def build_task_context_block(session_id: str) -> str:
    """Build an active-task context block for injection into system prompt."""
    try:
        active = get_active_tasks(session_id)
        if not active:
            return ""
        lines = ["## Active Tasks"]
        for task in active[:3]:
            lines.append(f"\n### [{task.status.upper()}] {task.title}")
            if task.plan:
                lines.append(f"Plan: {task.plan}")
            for step in task.steps:
                marker = "[done]" if step.status == "done" else "[active]" if step.status == "active" else "[ ]"
                lines.append(f"  {marker} {step.description}")
        lines.append("\n> Resume and continue from the last incomplete step.")
        return "\n".join(lines)
    except Exception:
        return ""


def build_handoff_summary(task: Task) -> str:
    """Generate a structured handoff summary for a completed or interrupted task."""
    done_steps = [step for step in task.steps if step.status == "done"]
    pending_steps = [step for step in task.steps if step.status != "done"]
    lines = [
        f"## Task Handoff: {task.title}",
        f"Status: {task.status}",
        f"Completed steps ({len(done_steps)}/{len(task.steps)}):",
    ]
    for step in done_steps:
        suffix = f" -> {step.result[:80]}" if step.result else ""
        lines.append(f"  [done] {step.description}{suffix}")
    if pending_steps:
        lines.append("Remaining steps:")
        for step in pending_steps:
            lines.append(f"  [ ] {step.description}")
    return "\n".join(lines)
