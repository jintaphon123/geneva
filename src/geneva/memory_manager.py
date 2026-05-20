from __future__ import annotations

import sqlite3
import json
import os
import re
from pathlib import Path
from typing import Any

from src.memdir.brain_engine import (
    DB_PATH,
    Memory,
    get_memory_conflict,
    init_db,
    list_memory_conflicts,
    remember,
    resolve_memory_conflict,
    search,
    set_memory_status,
    update_memory as update_memory_record,
)
from src.utils.asyncio_tools import run_awaitable_sync


class MemoryManager:
    """Direct SQLite queries for memory CRUD; wraps brain_engine functions."""

    def __init__(self) -> None:
        init_db()

    def _conn(self) -> sqlite3.Connection:
        override = os.environ.get("GENEVA_BRAIN_DB_PATH")
        db_path = Path(override).expanduser() if override else DB_PATH
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        data = {key: row[key] for key in row.keys()}
        data.setdefault("fts_score", 0.0)
        parsed = self._provenance_from_content(str(data.get("content") or ""))
        data["source_session_id"] = data.get("source_session_id") or parsed["source_session_id"]
        data["captured_at"] = data.get("captured_at") or parsed["captured_at"]
        data.setdefault("memory_kind", data.get("type") or "reference")
        return data

    @staticmethod
    def _provenance_from_content(content: str) -> dict[str, Any]:
        session_match = re.search(
            r"(?:^|\s)Session:\s*(.+?)(?=\s+Captured at:|\s+User:|\s+Assistant:|$)",
            content,
            flags=re.MULTILINE,
        )
        captured_match = re.search(
            r"(?:^|\s)Captured at:\s*(.+?)(?=\s+User:|\s+Assistant:|$)",
            content,
            flags=re.MULTILINE,
        )
        return {
            "source_session_id": session_match.group(1).strip() if session_match else None,
            "captured_at": captured_match.group(1).strip() if captured_match else None,
        }

    def _events_for_memory(self, memory_id: str) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT id, event_type, payload, created_at
                FROM memory_events
                WHERE memory_id = ?
                ORDER BY created_at DESC
                LIMIT 20
                """,
                (memory_id,),
            ).fetchall()
        events: list[dict[str, Any]] = []
        for row in rows:
            payload: Any = {}
            try:
                payload = json.loads(row["payload"] or "{}")
            except json.JSONDecodeError:
                payload = row["payload"]
            events.append(
                {
                    "id": row["id"],
                    "event_type": row["event_type"],
                    "payload": payload,
                    "created_at": row["created_at"],
                }
            )
        return events

    def list_memories(
        self,
        type: str | None = None,
        status: str = "active",
        query: str | None = None,
        scope: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List memories with optional filters. Returns {items, total, has_more}."""
        if query and query.strip():
            results = search(
                query.strip(),
                type=type,
                scope=scope,
                min_confidence=0.0,
                include_archived=(status == "archived"),
            )
            items = [self._memory_to_dict(memory) for memory in results]
            if type:
                items = [item for item in items if item["type"] == type]
            if status and status != "all":
                items = [item for item in items if item["status"] == status]
            total = len(items)
            return {
                "items": items[offset : offset + limit],
                "total": total,
                "has_more": offset + limit < total,
            }

        conditions = []
        params: list[Any] = []
        if status and status != "all":
            conditions.append("status = ?")
            params.append(status)
        if type:
            conditions.append("type = ?")
            params.append(type)
        if scope:
            conditions.append("scope = ?")
            params.append(scope)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        with self._conn() as conn:
            total = conn.execute(f"SELECT COUNT(*) FROM memories {where}", params).fetchone()[0]
            rows = conn.execute(
                f"SELECT * FROM memories {where} ORDER BY COALESCE(updated_at, created_at) DESC LIMIT ? OFFSET ?",
                [*params, limit, offset],
            ).fetchall()

        items = [self._row_to_dict(row) for row in rows]
        return {"items": items, "total": total, "has_more": offset + limit < total}

    def get_memory(self, memory_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM memories WHERE id=?", (memory_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def get_memory_detail(self, memory_id: str) -> dict[str, Any] | None:
        memory = self.get_memory(memory_id)
        if memory is None:
            return None
        memory["events"] = self._events_for_memory(memory_id)
        return memory

    def add_memory(
        self,
        content: str,
        type: str,
        source_type: str = "user_direct",
        scope: str | None = None,
        memory_kind: str | None = None,
        confidence: float | None = None,
        importance: float | None = None,
    ) -> dict[str, Any]:
        """Add memory via remember(); returns MemoryResult as dict."""
        result = run_awaitable_sync(
            remember(
                content=content,
                type=type,
                source_type=source_type,
                scope=scope,
                memory_kind=memory_kind,
                confidence=confidence,
                importance=importance,
            )
        )
        return {
            "operation": result.operation,
            "memory_id": result.memory_id,
            "conflict_id": result.conflict_id,
            "success": result.success,
            "message": result.message,
        }

    def update_memory(self, memory_id: str, content: str) -> dict[str, Any]:
        """Update one memory row and its Markdown file without creating a duplicate."""
        result = update_memory_record(memory_id, content, source_type="user_direct")
        return {
            "operation": result.operation,
            "memory_id": result.memory_id,
            "conflict_id": result.conflict_id,
            "success": result.success,
            "message": result.message,
        }

    def list_conflicts(
        self,
        status: str = "open",
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, object]:
        return list_memory_conflicts(status=status, limit=limit, offset=offset)

    def get_conflict(self, conflict_id: str) -> dict[str, object] | None:
        return get_memory_conflict(conflict_id)

    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: str,
        merged_content: str | None = None,
    ) -> dict[str, object]:
        result = resolve_memory_conflict(conflict_id, resolution, merged_content)
        return {
            "operation": result.operation,
            "memory_id": result.memory_id,
            "conflict_id": result.conflict_id,
            "success": result.success,
            "message": result.message,
        }

    def archive_memory(self, memory_id: str) -> dict[str, Any]:
        result = set_memory_status(memory_id, "archived", reason="web_archive")
        return {
            "ok": result.success,
            "memory_id": result.memory_id,
            "status": "archived",
            "message": result.message,
        }

    def delete_memory(self, memory_id: str) -> dict[str, Any]:
        """Soft delete; sets status=deleted."""
        result = set_memory_status(memory_id, "deleted", reason="web_delete")
        return {
            "ok": result.success,
            "memory_id": result.memory_id,
            "status": "deleted",
            "message": result.message,
        }

    def get_timeline(self) -> list[dict[str, Any]]:
        """Memories grouped by day, active only, newest first, max 7 days."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT DATE(created_at) as day, COUNT(*) as count, "
                "GROUP_CONCAT(id, ',') as ids "
                "FROM memories WHERE status='active' "
                "GROUP BY day ORDER BY day DESC LIMIT 7"
            ).fetchall()
        return [
            {"day": row["day"], "count": row["count"], "ids": (row["ids"] or "").split(",")[:5]}
            for row in rows
        ]

    def get_stats(self) -> dict[str, Any]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) as cnt FROM memories GROUP BY status"
            ).fetchall()
            type_rows = conn.execute(
                "SELECT type, COUNT(*) as cnt FROM memories WHERE status='active' GROUP BY type"
            ).fetchall()
            conflict_rows = conn.execute(
                "SELECT status, COUNT(*) as cnt FROM memory_conflicts GROUP BY status"
            ).fetchall()
        return {
            "by_status": {row["status"]: row["cnt"] for row in rows},
            "by_type": {row["type"]: row["cnt"] for row in type_rows},
            "conflicts_by_status": {row["status"]: row["cnt"] for row in conflict_rows},
        }

    @staticmethod
    def _memory_to_dict(memory: Memory) -> dict[str, Any]:
        return {
            field: getattr(memory, field)
            for field in [
                "id",
                "path",
                "name",
                "type",
                "status",
                "content",
                "confidence",
                "importance",
                "memory_kind",
                "source_type",
                "source_session_id",
                "captured_at",
                "last_validated_at",
                "created_at",
                "updated_at",
                "retention_days",
                "expires_at",
                "superseded_by",
                "scope",
                "fts_score",
            ]
        }
