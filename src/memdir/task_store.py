"""Task state persistence - stores task graph in brain.db alongside memories."""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Literal

from .brain_engine import _resolve_db_path

TaskStatus = Literal["todo", "active", "blocked", "done", "failed"]


@dataclass
class TaskStep:
    id: str
    description: str
    status: TaskStatus = "todo"
    result: str | None = None


@dataclass
class Task:
    id: str
    session_id: str
    title: str
    plan: str
    steps: list[TaskStep]
    status: TaskStatus
    created_at: str
    updated_at: str
    project_id: str | None = None
    handoff_summary: str | None = None


def _connect() -> sqlite3.Connection:
    db_path = _resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_tasks_table() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                title TEXT NOT NULL,
                plan TEXT NOT NULL DEFAULT '',
                steps TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'todo',
                project_id TEXT,
                handoff_summary TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_session ON tasks(session_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        conn.commit()


def create_task(
    session_id: str,
    title: str,
    steps: list[str],
    plan: str = "",
    project_id: str | None = None,
) -> Task:
    init_tasks_table()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    task_id = uuid.uuid4().hex
    step_objects = [TaskStep(id=uuid.uuid4().hex[:8], description=s) for s in steps]
    task = Task(
        id=task_id,
        session_id=session_id,
        title=title,
        plan=plan,
        steps=step_objects,
        status="active",
        created_at=now,
        updated_at=now,
        project_id=project_id,
    )
    with _connect() as conn:
        conn.execute(
            "INSERT INTO tasks(id, session_id, title, plan, steps, status, project_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                task.id,
                session_id,
                title,
                plan,
                json.dumps([asdict(s) for s in step_objects]),
                "active",
                project_id,
                now,
                now,
            ),
        )
        conn.commit()
    return task


def get_active_tasks(session_id: str) -> list[Task]:
    """Return active/todo tasks for a session."""
    init_tasks_table()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks "
            "WHERE session_id = ? AND status IN ('active', 'todo', 'blocked') "
            "ORDER BY created_at DESC",
            (session_id,),
        ).fetchall()
    return [_row_to_task(row) for row in rows]


def list_tasks(session_id: str, limit: int = 20) -> list[Task]:
    """List all tasks for a session."""
    init_tasks_table()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
    return [_row_to_task(row) for row in rows]


def update_task_status(task_id: str, status: TaskStatus, handoff_summary: str | None = None) -> bool:
    init_tasks_table()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with _connect() as conn:
        conn.execute(
            "UPDATE tasks "
            "SET status = ?, updated_at = ?, handoff_summary = COALESCE(?, handoff_summary) "
            "WHERE id = ?",
            (status, now, handoff_summary, task_id),
        )
        conn.commit()
    return True


def update_step_status(task_id: str, step_id: str, status: TaskStatus, result: str | None = None) -> bool:
    init_tasks_table()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with _connect() as conn:
        row = conn.execute("SELECT steps FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            return False
        steps = json.loads(row["steps"])
        for step in steps:
            if step["id"] == step_id:
                step["status"] = status
                if result is not None:
                    step["result"] = result
                break
        conn.execute(
            "UPDATE tasks SET steps = ?, updated_at = ? WHERE id = ?",
            (json.dumps(steps), now, task_id),
        )
        conn.commit()
    return True


def _row_to_task(row: sqlite3.Row) -> Task:
    steps_raw = json.loads(row["steps"] or "[]")
    steps = [TaskStep(**s) for s in steps_raw]
    return Task(
        id=row["id"],
        session_id=row["session_id"],
        title=row["title"],
        plan=row["plan"] or "",
        steps=steps,
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        project_id=row["project_id"],
        handoff_summary=row["handoff_summary"],
    )
