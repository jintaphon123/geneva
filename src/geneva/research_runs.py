from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.geneva.artifact_store import save_artifact
from src.memdir.brain_engine import DB_PATH, init_db

RUN_STATUSES = {"draft_plan", "running", "stopped", "completed", "failed"}


def _db_path() -> Path:
    override = os.environ.get("GENEVA_BRAIN_DB_PATH")
    return Path(override).expanduser() if override else DB_PATH


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_dumps(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def _json_loads(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _source_id(source: dict[str, Any], index: int) -> str:
    return str(source.get("source_id") or source.get("id") or f"S{index + 1}")


class ResearchRunStore:
    def __init__(self) -> None:
        init_db()
        self._ensure_tables()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(_db_path())
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS research_runs (
                    id           TEXT PRIMARY KEY,
                    session_id   TEXT DEFAULT NULL,
                    project_id   TEXT DEFAULT NULL,
                    mode         TEXT NOT NULL DEFAULT 'deep',
                    query        TEXT NOT NULL,
                    plan_json    TEXT DEFAULT '{}',
                    status       TEXT NOT NULL DEFAULT 'draft_plan',
                    artifact_id  TEXT DEFAULT NULL,
                    final_text   TEXT DEFAULT '',
                    error        TEXT DEFAULT NULL,
                    metadata     TEXT DEFAULT '{}',
                    created_at   TEXT NOT NULL,
                    updated_at   TEXT NOT NULL,
                    started_at   TEXT DEFAULT NULL,
                    completed_at TEXT DEFAULT NULL
                );
                CREATE TABLE IF NOT EXISTS research_sources (
                    id                TEXT PRIMARY KEY,
                    run_id            TEXT NOT NULL,
                    source_id         TEXT NOT NULL,
                    project_source_id TEXT DEFAULT NULL,
                    title             TEXT NOT NULL,
                    url               TEXT DEFAULT '',
                    publisher         TEXT DEFAULT '',
                    credibility_score REAL DEFAULT NULL,
                    credibility_tier  INTEGER DEFAULT NULL,
                    used_in_report    INTEGER DEFAULT 1,
                    metadata          TEXT DEFAULT '{}',
                    created_at        TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_research_runs_project_updated
                    ON research_runs(project_id, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_research_runs_session_updated
                    ON research_runs(session_id, updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_research_sources_run
                    ON research_sources(run_id);
                """
            )

    def _row_to_run(self, row: sqlite3.Row, sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return {
            "id": str(row["id"]),
            "session_id": row["session_id"],
            "project_id": row["project_id"],
            "mode": str(row["mode"] or "deep"),
            "query": str(row["query"] or ""),
            "plan": _json_loads(row["plan_json"], {}),
            "status": str(row["status"] or "draft_plan"),
            "artifact_id": row["artifact_id"],
            "final_text": str(row["final_text"] or ""),
            "error": row["error"],
            "metadata": _json_loads(row["metadata"], {}),
            "created_at": str(row["created_at"] or ""),
            "updated_at": str(row["updated_at"] or ""),
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "sources": sources if sources is not None else [],
        }

    def _row_to_source(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": str(row["id"]),
            "run_id": str(row["run_id"]),
            "source_id": str(row["source_id"]),
            "project_source_id": row["project_source_id"],
            "title": str(row["title"] or ""),
            "url": str(row["url"] or ""),
            "publisher": str(row["publisher"] or ""),
            "credibility_score": row["credibility_score"],
            "credibility_tier": row["credibility_tier"],
            "used_in_report": bool(row["used_in_report"]),
            "metadata": _json_loads(row["metadata"], {}),
            "created_at": str(row["created_at"] or ""),
        }

    def create_run(
        self,
        *,
        query: str,
        session_id: str | None = None,
        project_id: str | None = None,
        mode: str = "deep",
        plan: dict[str, Any] | None = None,
        status: str = "draft_plan",
    ) -> dict[str, Any]:
        clean_query = query.strip()
        clean_status = status.strip().lower()
        if not clean_query:
            raise ValueError("Research query is required")
        if clean_status not in RUN_STATUSES:
            raise ValueError("Invalid research run status")
        run_id = str(uuid.uuid4())
        now = _now()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO research_runs(
                    id, session_id, project_id, mode, query, plan_json, status,
                    metadata, created_at, updated_at, started_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, '{}', ?, ?, ?)
                """,
                (
                    run_id,
                    session_id,
                    project_id,
                    mode or "deep",
                    clean_query,
                    _json_dumps(plan or {}),
                    clean_status,
                    now,
                    now,
                    now if clean_status == "running" else None,
                ),
            )
        run = self.get_run(run_id)
        return run or {}

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM research_runs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                return None
            sources = [
                self._row_to_source(source_row)
                for source_row in conn.execute(
                    "SELECT * FROM research_sources WHERE run_id=? ORDER BY created_at, source_id",
                    (run_id,),
                ).fetchall()
            ]
        return self._row_to_run(row, sources=sources)

    def list_runs(
        self,
        *,
        session_id: str | None = None,
        project_id: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        filters = ["1=1"]
        params: list[Any] = []
        if session_id:
            filters.append("session_id=?")
            params.append(session_id)
        if project_id:
            filters.append("project_id=?")
            params.append(project_id)
        safe_limit = max(1, min(int(limit), 100))
        params.append(safe_limit)
        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM research_runs WHERE {' AND '.join(filters)} ORDER BY updated_at DESC LIMIT ?",
                params,
            ).fetchall()
        runs = [self._row_to_run(row) for row in rows]
        return {"runs": runs, "count": len(runs)}

    def update_status(self, run_id: str, status: str) -> dict[str, Any] | None:
        clean_status = status.strip().lower()
        if clean_status not in RUN_STATUSES:
            raise ValueError("Invalid research run status")
        now = _now()
        fields = ["status=?", "updated_at=?"]
        params: list[Any] = [clean_status, now]
        if clean_status == "running":
            fields.append("started_at=COALESCE(started_at, ?)")
            params.append(now)
        if clean_status in {"completed", "failed"}:
            fields.append("completed_at=COALESCE(completed_at, ?)")
            params.append(now)
        params.append(run_id)
        with self._conn() as conn:
            cursor = conn.execute(
                f"UPDATE research_runs SET {', '.join(fields)} WHERE id=?",
                params,
            )
            if cursor.rowcount == 0:
                return None
        return self.get_run(run_id)

    def complete_run(
        self,
        run_id: str,
        *,
        final_text: str,
        sources: list[dict[str, Any]] | None = None,
        quality_score: dict[str, Any] | None = None,
        trace: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        existing = self.get_run(run_id)
        if existing is None:
            return None
        text = final_text.strip()
        report_payload = {
            "run_id": run_id,
            "query": existing["query"],
            "mode": existing["mode"],
            "project_id": existing["project_id"],
            "session_id": existing["session_id"],
            "text": text,
            "sources": sources or [],
            "quality_score": quality_score or {},
            "trace": trace or [],
        }
        artifact_id = save_artifact(
            "research_report",
            json.dumps(report_payload, ensure_ascii=False, indent=2),
            existing.get("session_id"),
            redact=True,
        )
        now = _now()
        merged_metadata = dict(metadata or {})
        merged_metadata["quality_score"] = quality_score or {}
        merged_metadata["trace"] = trace or []
        with self._conn() as conn:
            conn.execute("DELETE FROM research_sources WHERE run_id=?", (run_id,))
            for index, source in enumerate(sources or []):
                self._insert_source(conn, run_id, source, index)
            conn.execute(
                """
                UPDATE research_runs
                SET status='completed', artifact_id=?, final_text=?, error=NULL,
                    metadata=?, updated_at=?, completed_at=?
                WHERE id=?
                """,
                (artifact_id, text, _json_dumps(merged_metadata), now, now, run_id),
            )
        return self.get_run(run_id)

    def fail_run(self, run_id: str, error: str) -> dict[str, Any] | None:
        now = _now()
        with self._conn() as conn:
            cursor = conn.execute(
                """
                UPDATE research_runs
                SET status='failed', error=?, updated_at=?, completed_at=?
                WHERE id=?
                """,
                (error, now, now, run_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_run(run_id)

    def _insert_source(
        self,
        conn: sqlite3.Connection,
        run_id: str,
        source: dict[str, Any],
        index: int,
    ) -> None:
        source_ref = _source_id(source, index)
        metadata = {
            key: source.get(key)
            for key in ("query", "snippet", "fetched", "content_preview", "error")
            if key in source
        }
        conn.execute(
            """
            INSERT INTO research_sources(
                id, run_id, source_id, project_source_id, title, url, publisher,
                credibility_score, credibility_tier, used_in_report, metadata, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                run_id,
                source_ref,
                source.get("project_source_id"),
                str(source.get("title") or source_ref),
                str(source.get("url") or source.get("uri") or ""),
                str(source.get("publisher") or ""),
                source.get("credibility_score"),
                source.get("credibility_tier"),
                1 if source.get("used_in_report", True) else 0,
                _json_dumps(metadata),
                _now(),
            ),
        )
