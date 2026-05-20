from __future__ import annotations

import json
import os
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.memdir.brain_engine import DB_PATH, init_db


def auto_detect_project_name(message: str) -> str | None:
    """Extract a project name from a create_project intent message (Thai + English)."""
    import re

    _STOP = {"new", "a", "the", "ใหม่", "create", "start", "this", "that"}
    patterns = [
        # Thai: "project เรื่อง/ชื่อ/เกี่ยวกับ X"
        r"project\s+(?:เรื่อง|ชื่อ|เกี่ยวกับ|สำหรับ)\s+([\w\u0e00-\u0e7f][\w\u0e00-\u0e7f\s]{1,49}?)(?:\s*$|\s+(?:ได้เลย|หน่อย|นะ|ครับ|ค่ะ))",
        # English: "project: X", "project named X", "project about X"
        r"project\s*:\s*(.+?)(?:\s*$|\.)",
        r"project\s+(?:named?|about|for|called)\s+(.+?)(?:\s*$|\.|\s+(?:now|please|ok))",
        # Fallback: "project X" (1-3 words)
        r"project\s+([\w\u0e00-\u0e7f]{2,30}(?:\s+[\w\u0e00-\u0e7f]{2,20})?)",
    ]
    for pat in patterns:
        m = re.search(pat, message, re.IGNORECASE)
        if m:
            name = m.group(1).strip()[:50]
            if name.lower() not in _STOP:
                return name
    return None


def _project_db_path() -> Path:
    override = os.environ.get("GENEVA_BRAIN_DB_PATH")
    return Path(override).expanduser() if override else DB_PATH


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Todo:
    id: str
    project_id: str
    text: str
    done: bool = False
    position: int = 0
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass
class Project:
    id: str
    name: str
    description: str = ""
    context_md: str = ""
    color: str = "#6366f1"
    pinned: bool = False
    archived: bool = False
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    todos: list[Todo] = field(default_factory=list)
    session_count: int = 0


class ProjectStore:
    def __init__(self) -> None:
        init_db()
        self._ensure_tables()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(_project_db_path())
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _ensure_tables(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    context_md TEXT DEFAULT '',
                    color TEXT DEFAULT '#6366f1',
                    pinned INTEGER DEFAULT 0,
                    archived INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS project_todos (
                    id TEXT PRIMARY KEY,
                    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
                    text TEXT NOT NULL,
                    done INTEGER DEFAULT 0,
                    position INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS project_sessions (
                    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
                    session_id TEXT,
                    created_at TEXT,
                    PRIMARY KEY (project_id, session_id)
                );
                CREATE TABLE IF NOT EXISTS project_activity (
                    id         TEXT PRIMARY KEY,
                    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
                    event_type TEXT NOT NULL,
                    content    TEXT,
                    turn_id    TEXT DEFAULT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def _row_to_project(
        self,
        row: sqlite3.Row,
        todos: list[Todo] | None = None,
        session_count: int = 0,
    ) -> Project:
        return Project(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            context_md=row["context_md"] or "",
            color=row["color"] or "#6366f1",
            pinned=bool(row["pinned"]),
            archived=bool(row["archived"]),
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] or "",
            todos=todos or [],
            session_count=session_count,
        )

    def _get_todos(self, conn: sqlite3.Connection, project_id: str) -> list[Todo]:
        rows = conn.execute(
            "SELECT * FROM project_todos WHERE project_id=? ORDER BY position,created_at",
            (project_id,),
        ).fetchall()
        return [
            Todo(
                id=r["id"],
                project_id=r["project_id"],
                text=r["text"],
                done=bool(r["done"]),
                position=r["position"],
                created_at=r["created_at"] or "",
                updated_at=r["updated_at"] or "",
            )
            for r in rows
        ]

    def list_projects(self) -> list[Project]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT p.*, COUNT(ps.session_id) as sc FROM projects p "
                "LEFT JOIN project_sessions ps ON p.id=ps.project_id "
                "WHERE p.archived=0 GROUP BY p.id "
                "ORDER BY p.pinned DESC, p.updated_at DESC"
            ).fetchall()
            return [
                self._row_to_project(
                    r,
                    todos=self._get_todos(conn, r["id"]),
                    session_count=r["sc"],
                )
                for r in rows
            ]

    def get_project(self, project_id: str) -> Project | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
            if row is None:
                return None
            todos = self._get_todos(conn, project_id)
            sc = conn.execute(
                "SELECT COUNT(*) FROM project_sessions WHERE project_id=?",
                (project_id,),
            ).fetchone()[0]
            return self._row_to_project(row, todos=todos, session_count=sc)

    def create_project(self, name: str, description: str = "") -> Project:
        pid = str(uuid.uuid4())
        now = _now()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO projects (id,name,description,created_at,updated_at) VALUES (?,?,?,?,?)",
                (pid, name, description, now, now),
            )
        return self.get_project(pid)  # type: ignore[return-value]

    def update_project(self, project_id: str, **fields: Any) -> Project | None:
        allowed = {"name", "description", "context_md", "color", "pinned", "archived"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return self.get_project(project_id)
        updates["updated_at"] = _now()
        cols = ", ".join(f"{k}=?" for k in updates)
        with self._conn() as conn:
            conn.execute(f"UPDATE projects SET {cols} WHERE id=?", (*updates.values(), project_id))
        return self.get_project(project_id)

    def archive_project(self, project_id: str) -> bool:
        with self._conn() as conn:
            cursor = conn.execute(
                "UPDATE projects SET archived=1,updated_at=? WHERE id=?",
                (_now(), project_id),
            )
            return cursor.rowcount > 0

    def delete_project(self, project_id: str) -> bool:
        with self._conn() as conn:
            cursor = conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
            return cursor.rowcount > 0

    def add_todo(self, project_id: str, text: str) -> Todo | None:
        clean_text = text.strip()
        if not clean_text:
            return None
        tid = str(uuid.uuid4())
        now = _now()
        with self._conn() as conn:
            project = conn.execute("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone()
            if project is None:
                return None
            pos = conn.execute(
                "SELECT COALESCE(MAX(position),0)+1 FROM project_todos WHERE project_id=?",
                (project_id,),
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO project_todos (id,project_id,text,done,position,created_at,updated_at) VALUES (?,?,?,0,?,?,?)",
                (tid, project_id, clean_text, pos, now, now),
            )
        return Todo(id=tid, project_id=project_id, text=clean_text, position=pos, created_at=now, updated_at=now)

    def toggle_todo(self, project_id: str, todo_id: str) -> Todo | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM project_todos WHERE id=? AND project_id=?",
                (todo_id, project_id),
            ).fetchone()
            if row is None:
                return None
            new_done = 0 if row["done"] else 1
            now = _now()
            conn.execute(
                "UPDATE project_todos SET done=?,updated_at=? WHERE id=? AND project_id=?",
                (new_done, now, todo_id, project_id),
            )
            return Todo(
                id=todo_id,
                project_id=project_id,
                text=row["text"],
                done=bool(new_done),
                position=row["position"],
                created_at=row["created_at"],
                updated_at=now,
            )

    def set_todo_done(self, project_id: str, todo_id: str, done: bool) -> Todo | None:
        now = _now()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM project_todos WHERE id=? AND project_id=?",
                (todo_id, project_id),
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                "UPDATE project_todos SET done=?,updated_at=? WHERE id=? AND project_id=?",
                (1 if done else 0, now, todo_id, project_id),
            )
            return Todo(
                id=todo_id,
                project_id=project_id,
                text=row["text"],
                done=done,
                position=row["position"],
                created_at=row["created_at"],
                updated_at=now,
            )

    def update_todo_text(self, project_id: str, todo_id: str, text: str) -> Todo | None:
        clean_text = text.strip()
        if not clean_text:
            return None
        now = _now()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM project_todos WHERE id=? AND project_id=?",
                (todo_id, project_id),
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                "UPDATE project_todos SET text=?,updated_at=? WHERE id=? AND project_id=?",
                (clean_text, now, todo_id, project_id),
            )
            return Todo(
                id=todo_id,
                project_id=project_id,
                text=clean_text,
                done=bool(row["done"]),
                position=row["position"],
                created_at=row["created_at"],
                updated_at=now,
            )

    def delete_todo(self, project_id: str, todo_id: str) -> bool:
        with self._conn() as conn:
            cursor = conn.execute(
                "DELETE FROM project_todos WHERE id=? AND project_id=?",
                (todo_id, project_id),
            )
            return cursor.rowcount > 0

    def add_session(self, project_id: str, session_id: str) -> bool:
        clean_session_id = session_id.strip()
        if not clean_session_id:
            return False
        with self._conn() as conn:
            project = conn.execute("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone()
            if project is None:
                return False
            conn.execute(
                "INSERT OR IGNORE INTO project_sessions (project_id,session_id,created_at) VALUES (?,?,?)",
                (project_id, clean_session_id, _now()),
            )
            return True

    def list_session_ids(self, project_id: str) -> list[str]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT session_id
                FROM project_sessions
                WHERE project_id=?
                ORDER BY created_at DESC
                """,
                (project_id,),
            ).fetchall()
            return [str(row["session_id"]) for row in rows]

    def get_project_for_session(self, session_id: str) -> Project | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT p.* FROM projects p JOIN project_sessions ps ON p.id=ps.project_id WHERE ps.session_id=?",
                (session_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_project(row)

    def to_dict(self, project: Project) -> dict[str, Any]:
        return {**asdict(project), "todos": [asdict(t) for t in project.todos]}

    def auto_create_for_session(self, session_id: str, message: str) -> "Project | None":
        """Detect project name from message, create project if new, link session. Returns project or None."""
        name = auto_detect_project_name(message)
        if not name:
            return None
        # Check if project with this name already exists
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id FROM projects WHERE LOWER(name) = LOWER(?)", (name,)
            ).fetchone()
        if row:
            project_id = str(row["id"])
            self.add_session(project_id, session_id)
            return self.get_project(project_id)
        project = self.create_project(name)
        self.add_session(project.id, session_id)
        return project

    def add_activity(
        self,
        project_id: str,
        event_type: str,
        content: str,
        turn_id: str | None = None,
    ) -> bool:
        """Append an event to the project activity log. Returns True on success."""
        import uuid as _uuid

        with self._conn() as conn:
            exists = conn.execute(
                "SELECT 1 FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
            if not exists:
                return False
            conn.execute(
                """
                INSERT INTO project_activity(id, project_id, event_type, content, turn_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (_uuid.uuid4().hex[:16], project_id, event_type, content[:500], turn_id, _now()),
            )
        return True

    def list_activity(self, project_id: str, limit: int = 50) -> list[dict]:
        """Return project activity log in reverse-chronological order."""
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT id, project_id, event_type, content, turn_id, created_at
                FROM project_activity
                WHERE project_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (project_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]
