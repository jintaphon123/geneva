from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.geneva.web_api import dispatch_api_request
from src.geneva.web_runtime import SessionManager
from src.memdir.brain_engine import remember
from src.utils.asyncio_tools import run_awaitable_sync


def patch_memory_env(db_path: Path, events_dir: Path, memory_dir: Path):
    return patch.dict(
        os.environ,
        {
            "GENEVA_BRAIN_DB_PATH": str(db_path),
            "GENEVA_MEMORY_EVENTS_DIR": str(events_dir),
            "GENEVA_AUTO_MEM_PATH": str(memory_dir),
        },
    )


class MemoryWriteReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db_path = self.root / "brain.db"
        self.events_dir = self.root / "events"
        self.memory_dir = self.root / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _status_for_memory(self, memory_id: str) -> str:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT status FROM memories WHERE id = ?", (memory_id,)).fetchone()
        assert row is not None
        return str(row[0])

    def test_write_event_is_listable_and_undo_archives_memory(self) -> None:
        from src.geneva.memory_write_review import (
            list_memory_write_events,
            record_memory_write_event,
            undo_memory_write_event,
        )

        with patch_memory_env(self.db_path, self.events_dir, self.memory_dir):
            result = run_awaitable_sync(
                remember(
                    "Bond prefers Geneva architecture answers at architect level first.",
                    "user",
                    source_type="assistant_inferred",
                    source_session_id="session-1",
                    evidence_quote="architect level first",
                )
            )
            memory_id = str(result.memory_id)

            event = record_memory_write_event(
                memory_id=memory_id,
                session_id="session-1",
                turn_id="turn-1",
                project_id="project-1",
                write_type="auto_saved",
                confidence=0.92,
                sensitivity="private",
                user_visible_text="Bond prefers architect-level explanations.",
                source_excerpt="architect level first",
            )

            self.assertEqual(event["status"], "saved")
            self.assertEqual(event["memory_id"], memory_id)
            self.assertEqual(event["source_excerpt"], "architect level first")

            listed = list_memory_write_events(session_id="session-1")
            self.assertEqual(listed["total"], 1)
            self.assertEqual(listed["items"][0]["id"], event["id"])

            undone = undo_memory_write_event(str(event["id"]))

            self.assertEqual(undone["status"], "undone")
            self.assertEqual(self._status_for_memory(memory_id), "archived")

    def test_draft_write_is_archived_until_approved(self) -> None:
        from src.geneva.memory_write_review import (
            approve_memory_write_event,
            record_memory_write_event,
        )

        with patch_memory_env(self.db_path, self.events_dir, self.memory_dir):
            result = run_awaitable_sync(
                remember(
                    "Possibly sensitive Geneva trial note.",
                    "project",
                    source_type="assistant_inferred",
                    scope="project-1",
                    source_session_id="session-1",
                    sensitivity="restricted",
                )
            )
            memory_id = str(result.memory_id)

            event = record_memory_write_event(
                memory_id=memory_id,
                session_id="session-1",
                turn_id="turn-2",
                project_id="project-1",
                write_type="draft",
                confidence=0.41,
                sensitivity="restricted",
                user_visible_text="Possibly sensitive Geneva trial note.",
                source_excerpt="trial note",
            )

            self.assertEqual(event["status"], "draft")
            self.assertEqual(self._status_for_memory(memory_id), "archived")

            approved = approve_memory_write_event(str(event["id"]))

            self.assertEqual(approved["status"], "saved")
            self.assertEqual(self._status_for_memory(memory_id), "active")

    def test_api_lists_and_undoes_memory_write_events(self) -> None:
        from src.geneva.memory_write_review import record_memory_write_event

        manager = SessionManager.__new__(SessionManager)
        with patch_memory_env(self.db_path, self.events_dir, self.memory_dir):
            result = run_awaitable_sync(
                remember(
                    "Geneva should show Saved to memory with Undo.",
                    "reference",
                    source_type="assistant_inferred",
                    source_session_id="session-1",
                )
            )
            memory_id = str(result.memory_id)
            event = record_memory_write_event(
                memory_id=memory_id,
                session_id="session-1",
                turn_id="turn-3",
                write_type="auto_saved",
                confidence=0.9,
                sensitivity="private",
                user_visible_text="Geneva should show Saved to memory with Undo.",
                source_excerpt="Saved to memory with Undo",
            )

            listed = dispatch_api_request(
                manager,
                "GET",
                "/api/memory/write-events",
                "session_id=session-1",
            )
            self.assertEqual(listed.body["total"], 1)

            undone = dispatch_api_request(
                manager,
                "POST",
                f"/api/memory/write-events/{event['id']}/undo",
            )

            self.assertEqual(undone.body["event"]["status"], "undone")
            self.assertEqual(self._status_for_memory(memory_id), "archived")

