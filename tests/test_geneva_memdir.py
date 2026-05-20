from __future__ import annotations

import asyncio
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.memdir.brain_engine import (
    get_memory_conflict,
    init_db,
    list_memory_conflicts,
    privacy_delete,
    rebuild_index,
    remember,
    refresh_context,
    resolve_memory_conflict,
    search,
)
from src.memdir.find_relevant_memories import find_relevant_memories
from src.memdir.memdir import (
    MAX_ENTRYPOINT_BYTES,
    MAX_ENTRYPOINT_LINES,
    load_memory_prompt,
    truncate_entrypoint_content,
)
from src.memdir.memory_scan import scan_memory_files


class BrainEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db_path = self.root / "brain.db"
        self.events_dir = self.root / "events"
        self.memory_dir = self.root / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _patch_env(self):
        return patch.dict(
            os.environ,
            {
                "GENEVA_BRAIN_DB_PATH": str(self.db_path),
                "GENEVA_MEMORY_EVENTS_DIR": str(self.events_dir),
                "GENEVA_AUTO_MEM_PATH": str(self.memory_dir),
            },
        )

    def test_init_db_creates_schema(self) -> None:
        init_db(self.db_path)
        with sqlite3.connect(self.db_path) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
                ).fetchall()
            }
        self.assertIn("schema_migrations", tables)
        self.assertIn("memories", tables)
        self.assertIn("memory_events", tables)
        self.assertIn("memory_edges", tables)
        self.assertIn("memory_conflicts", tables)
        self.assertIn("memory_fts", tables)

    def test_remember_add_noop_and_update(self) -> None:
        with self._patch_env():
            first = asyncio.run(remember("User prefers concise code reviews.", "user"))
            second = asyncio.run(remember("User prefers concise code reviews.", "user"))
            third = asyncio.run(remember("User prefers concise and direct code reviews.", "user"))

            self.assertEqual(first.operation, "add")
            self.assertEqual(second.operation, "noop")
            self.assertEqual(third.operation, "update")

            results = search("concise reviews", type="user")
            self.assertEqual(len(results), 1)
            self.assertIn("direct", results[0].content)

    def test_remember_supersede_and_search_include_archived(self) -> None:
        with self._patch_env():
            original = asyncio.run(remember("Original architectural choice.", "project"))
            replacement = asyncio.run(
                remember(f"Supersedes: {original.memory_id}\nReplacement architectural choice.", "project")
            )

            self.assertEqual(replacement.operation, "supersede")
            active = search("architectural", type="project")
            archived = search("architectural", type="project", include_archived=True)
            self.assertEqual(len(active), 1)
            self.assertEqual(active[0].id, replacement.memory_id)
            self.assertGreaterEqual(len(archived), 1)

    def test_episodic_memory_is_searchable_without_polluting_entrypoint(self) -> None:
        with self._patch_env():
            result = asyncio.run(
                remember(
                    "Session: s1\nUser: Bond asked about ปั๊มน้ำ thermodynamics.\nAssistant: Explained pump efficiency.",
                    "episodic",
                )
            )

            matches = search("ปั๊มน้ำ")
            entrypoint = self.memory_dir / "MEMORY.md"

        self.assertEqual(result.operation, "add")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].type, "episodic")
        self.assertFalse(entrypoint.exists())

    def test_episodic_memory_does_not_fuzzy_update_similar_chat_turns(self) -> None:
        with self._patch_env():
            first = asyncio.run(
                remember(
                    "Session: s1\nCaptured at: 2026-05-13T01:00:00Z\nUser: ตรวจ memory engine\nAssistant: Found one issue.",
                    "episodic",
                )
            )
            second = asyncio.run(
                remember(
                    "Session: s1\nCaptured at: 2026-05-13T01:01:00Z\nUser: ตรวจ memory engine\nAssistant: Found a different issue.",
                    "episodic",
                )
            )
            matches = search("memory engine", type="episodic")

        self.assertEqual(first.operation, "add")
        self.assertEqual(second.operation, "add")
        self.assertEqual(len(matches), 2)
        self.assertNotEqual(first.memory_id, second.memory_id)

    def test_memory_control_plane_assigns_policy_metadata(self) -> None:
        with self._patch_env():
            result = asyncio.run(
                remember(
                    "Decision: Geneva should use FastAPI as the production gateway.",
                    "decision",
                    source_type="assistant_inferred",
                    scope="project-1",
                    source_session_id="session-42",
                )
            )

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT * FROM memories WHERE id = ?", (result.memory_id,)).fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row["type"], "project")
        self.assertEqual(row["memory_kind"], "decision")
        self.assertEqual(row["scope"], "project-1")
        self.assertEqual(row["source_session_id"], "session-42")
        self.assertGreater(row["importance"], 0.8)
        self.assertIsNotNone(row["last_validated_at"])

    def test_project_context_retrieval_includes_global_and_scoped_memory(self) -> None:
        with self._patch_env():
            asyncio.run(
                remember(
                    "Bond prefers direct Thai explanations with production-grade critique.",
                    "user",
                    source_type="user_direct",
                )
            )
            asyncio.run(
                remember(
                    "Decision: Project Alpha must preserve closed chat recall.",
                    "project",
                    source_type="assistant_inferred",
                    scope="project-alpha",
                )
            )

            context = refresh_context("production critique recall", scope="project-alpha", max_tokens=6000)

        self.assertIn("Bond prefers direct Thai", context)
        self.assertIn("Project Alpha", context)
        self.assertIn("decision/project scope=project-alpha", context)

    def test_conflicting_memory_is_queued_until_explicit_resolution(self) -> None:
        with self._patch_env():
            original = asyncio.run(
                remember(
                    "Bond prefers concise code reviews.",
                    "user",
                    source_type="user_direct",
                    memory_kind="preference",
                )
            )
            conflict = asyncio.run(
                remember(
                    "Bond does not want concise code reviews anymore; Bond wants exhaustive reviews.",
                    "user",
                    source_type="user_direct",
                    memory_kind="preference",
                )
            )

            open_conflicts = list_memory_conflicts()
            conflict_detail = get_memory_conflict(str(conflict.conflict_id))
            active_before_resolution = search("exhaustive reviews", type="user")
            resolved = resolve_memory_conflict(
                str(conflict.conflict_id),
                "replace",
                "Bond prefers exhaustive code reviews.",
            )
            open_after_resolution = list_memory_conflicts()
            active_after_resolution = search("exhaustive reviews", type="user")

        self.assertEqual(original.operation, "add")
        self.assertEqual(conflict.operation, "conflict")
        self.assertEqual(conflict.memory_id, original.memory_id)
        self.assertIsNotNone(conflict.conflict_id)
        self.assertEqual(open_conflicts["total"], 1)
        self.assertIsNotNone(conflict_detail)
        self.assertEqual(conflict_detail["status"], "open")
        self.assertEqual(conflict_detail["existing_memory_id"], original.memory_id)
        self.assertFalse(any("exhaustive" in memory.content for memory in active_before_resolution))
        self.assertTrue(resolved.success)
        self.assertEqual(open_after_resolution["total"], 0)
        self.assertEqual(len(active_after_resolution), 1)
        self.assertIn("exhaustive", active_after_resolution[0].content)

    def test_rebuild_index_and_privacy_delete(self) -> None:
        vault = self.root / "vault"
        file_path = vault / "projects" / "decision.md"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(
            "---\n"
            "id: mem_20260512_001\n"
            "name: Build Decision\n"
            "description: Chosen build system\n"
            "type: project\n"
            "status: active\n"
            "confidence: 0.9\n"
            "importance: 0.5\n"
            "source_type: file_import\n"
            "created_at: 2026-05-12T10:00:00+00:00\n"
            "retention_days: 365\n"
            "---\n\n"
            "Use the new build chain.\n",
            encoding="utf-8",
        )

        with self._patch_env():
            result = rebuild_index(vault)
            self.assertEqual(result.files_scanned, 1)
            self.assertEqual(result.files_updated, 1)
            self.assertEqual(len(search("build chain", type="project")), 1)

            privacy_delete("mem_20260512_001", requester="tester", reason="cleanup")
            self.assertEqual(search("build chain", type="project"), [])
            self.assertIn("DELETED - privacy request", file_path.read_text(encoding="utf-8"))


class MemoryHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.memory_dir = self.root / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_load_memory_prompt_truncates(self) -> None:
        entrypoint = self.memory_dir / "MEMORY.md"
        long_lines = [f"- item {idx}" for idx in range(MAX_ENTRYPOINT_LINES + 20)]
        entrypoint.write_text("\n".join(long_lines), encoding="utf-8")

        with patch.dict(os.environ, {"GENEVA_AUTO_MEM_PATH": str(self.memory_dir)}):
            prompt = load_memory_prompt(self.root)
        self.assertIn("### MEMORY", prompt)
        self.assertLessEqual(len(prompt.encode("utf-8")), MAX_ENTRYPOINT_BYTES + 40)
        self.assertLessEqual(len(prompt.splitlines()), MAX_ENTRYPOINT_LINES + 2)

    def test_truncate_entrypoint_content_respects_limits(self) -> None:
        content = "\n".join("x" * 100 for _ in range(MAX_ENTRYPOINT_LINES + 50))
        truncated = truncate_entrypoint_content(content)
        self.assertLessEqual(len(truncated.splitlines()), MAX_ENTRYPOINT_LINES)
        self.assertLessEqual(len(truncated.encode("utf-8")), MAX_ENTRYPOINT_BYTES)

    def test_scan_and_find_relevant_memories(self) -> None:
        alpha = self.memory_dir / "alpha.md"
        beta = self.memory_dir / "beta.md"
        alpha.write_text(
            "---\nname: Bond Working Style\ndescription: Notes about concise collaboration\ntype: user\n---\nBody\n",
            encoding="utf-8",
        )
        beta.write_text(
            "---\nname: Deployment Playbook\ndescription: Release checklist\ntype: project\n---\nBody\n",
            encoding="utf-8",
        )

        headers = scan_memory_files(self.memory_dir)
        self.assertEqual(len(headers), 2)
        relevant = find_relevant_memories(headers, "Bond concise collaboration style")
        self.assertTrue(relevant)
        self.assertEqual(relevant[0].path.name, "alpha.md")
