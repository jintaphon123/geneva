from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

DreamPhase = Literal["starting", "updating", "complete", "failed"]


@dataclass
class DreamTurn:
    content: str
    timestamp: str


@dataclass
class DreamTask:
    id: str
    phase: DreamPhase
    sessions_reviewed: list[str]
    files_touched: list[str]
    turns: list[DreamTurn] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str | None = None
    error: str | None = None


_dream_tasks: dict[str, DreamTask] = {}


def register_dream_task(task_id: str) -> DreamTask:
    task = DreamTask(
        id=task_id,
        phase="starting",
        sessions_reviewed=[],
        files_touched=[],
    )
    _dream_tasks[task_id] = task
    return task


def add_dream_turn(task_id: str, content: str) -> None:
    task = _dream_tasks.get(task_id)
    if task is None:
        task = register_dream_task(task_id)
    task.phase = "updating"
    task.turns.append(
        DreamTurn(
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
    if len(task.turns) > 30:
        task.turns = task.turns[-30:]


def complete_dream_task(task_id: str, files_touched: list[str]) -> None:
    task = _dream_tasks.get(task_id)
    if task is None:
        task = register_dream_task(task_id)
    task.phase = "complete"
    task.files_touched = list(dict.fromkeys(files_touched))
    task.completed_at = datetime.now(timezone.utc).isoformat()
    task.error = None


def fail_dream_task(task_id: str, error: str) -> None:
    task = _dream_tasks.get(task_id)
    if task is None:
        task = register_dream_task(task_id)
    task.phase = "failed"
    task.completed_at = datetime.now(timezone.utc).isoformat()
    task.error = error


def get_dream_task(task_id: str) -> DreamTask | None:
    return _dream_tasks.get(task_id)
