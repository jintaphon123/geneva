from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from src.agent.session import Session
from src.memdir.brain_engine import Memory, init_db, remember, search
from src.services.auto_dream.auto_dream import init_auto_dream
from src.services.auto_dream.consolidation_lock import (
    list_sessions_touched_since,
    mark_consolidated,
    read_last_consolidated_at,
    release_consolidation_lock,
    try_acquire_consolidation_lock,
)
from src.services.extract_memories.extract_memories import run_extraction
from src.services.session_memory.prompts import build_session_memory_cache_prompt
from src.services.session_memory.session_memory import (
    build_session_memory_context,
    get_current_session_memory,
    load_session_memory,
)
from src.services.session_memory.session_memory_utils import dedup_memories, truncate_to_budget
from src.services.team_memory_sync.secret_scanner import detect_secret_patterns
from src.services.team_memory_sync.team_mem_secret_guard import check_team_mem_secrets
from src.services.team_memory_sync.types import TeamMemoryContent
from src.memdir.team_mem_paths import PathTraversalError, get_team_mem_path


def patch_memory_env(db_path: Path, events_dir: Path, memory_dir: Path):
    return patch.dict(
        os.environ,
        {
            "GENEVA_BRAIN_DB_PATH": str(db_path),
            "GENEVA_MEMORY_EVENTS_DIR": str(events_dir),
            "GENEVA_AUTO_MEM_PATH": str(memory_dir),
        },
    )


class AutoDreamTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.memory_dir = self.root / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir = self.root / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_consolidation_lock_lifecycle(self) -> None:
        acquired = try_acquire_consolidation_lock(self.memory_dir)
        self.assertTrue(acquired)
        last = read_last_consolidated_at(self.memory_dir)
        self.assertIsNotNone(last)
        self.assertFalse(try_acquire_consolidation_lock(self.memory_dir))
        release_consolidation_lock(self.memory_dir)
        self.assertIsNone(read_last_consolidated_at(self.memory_dir))

    def test_mark_consolidated_survives_lock_release(self) -> None:
        self.assertTrue(try_acquire_consolidation_lock(self.memory_dir))
        mark_consolidated(self.memory_dir)
        release_consolidation_lock(self.memory_dir)

        self.assertIsNotNone(read_last_consolidated_at(self.memory_dir))

    def test_list_sessions_touched_since(self) -> None:
        older = self.sessions_dir / "older.json"
        newer = self.sessions_dir / "newer.json"
        older.write_text("{}", encoding="utf-8")
        newer.write_text("{}", encoding="utf-8")
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=1)
        os.utime(older, (cutoff.timestamp() - 10, cutoff.timestamp() - 10))
        touched = list_sessions_touched_since(self.sessions_dir, cutoff)
        self.assertEqual([path.name for path in touched], ["newer.json"])

    def test_init_auto_dream_invokes_agent(self) -> None:
        prompts: list[str] = []
        for idx in range(4):
            (self.sessions_dir / f"s{idx}.json").write_text("{}", encoding="utf-8")

        async def fake_agent(prompt: str) -> None:
            prompts.append(prompt)

        checker = init_auto_dream(
            memory_dir=self.memory_dir,
            time_gate_hours=0.0,
            session_gate_count=3,
            agent_caller=fake_agent,
        )
        with patch.dict(os.environ, {"GENEVA_AUTO_DREAM": "1"}), patch(
            "src.services.auto_dream.auto_dream._session_dir", return_value=self.sessions_dir
        ):
            asyncio.run(checker())
        self.assertEqual(len(prompts), 1)
        self.assertIn("Sessions to review", prompts[0])
        self.assertIsNotNone(read_last_consolidated_at(self.memory_dir))

    def test_auto_dream_agent_json_creates_durable_memory(self) -> None:
        (self.sessions_dir / "s1.json").write_text("{}", encoding="utf-8")

        async def fake_agent(_prompt: str) -> str:
            return '{"memories":[{"type":"project","content":"Decision: use Memory Control Plane first.","scope":"p1"}]}'

        checker = init_auto_dream(
            memory_dir=self.memory_dir,
            time_gate_hours=0.0,
            session_gate_count=1,
            agent_caller=fake_agent,
        )

        with patch.dict(os.environ, {"GENEVA_AUTO_DREAM": "1"}), patch(
            "src.services.auto_dream.auto_dream._session_dir", return_value=self.sessions_dir
        ), patch_memory_env(self.root / "brain.db", self.root / "events", self.memory_dir):
            asyncio.run(checker())
            results = search("Memory Control Plane", type="project", scope="p1")

        self.assertEqual(len(results), 1)

    def test_auto_dream_default_consolidates_touched_sessions(self) -> None:
        session_file = self.sessions_dir / "memory-session.json"
        session_file.write_text(
            '{"session_id":"memory-session","conversation":{"messages":[]}}',
            encoding="utf-8",
        )
        checker = init_auto_dream(
            memory_dir=self.memory_dir,
            time_gate_hours=0.0,
            session_gate_count=1,
        )

        with patch.dict(os.environ, {"GENEVA_AUTO_DREAM": "1"}), patch(
            "src.services.auto_dream.auto_dream._session_dir", return_value=self.sessions_dir
        ), patch_memory_env(self.root / "brain.db", self.root / "events", self.memory_dir):
            asyncio.run(
                remember(
                    "Session: memory-session\nUser: Please remember that I prefer Thai status updates.",
                    "episodic",
                )
            )
            asyncio.run(checker())
            results = search("Thai status updates", type="user")

        self.assertEqual(len(results), 1)
        self.assertIsNotNone(read_last_consolidated_at(self.memory_dir))

    def test_auto_dream_default_does_not_extract_raw_session_without_episode(self) -> None:
        session_file = self.sessions_dir / "ghost-session.json"
        session_file.write_text(
            '{"session_id":"ghost-session","conversation":{"messages":['
            '{"role":"user","content":"Please remember ghost private detail."}'
            ']}}',
            encoding="utf-8",
        )
        checker = init_auto_dream(
            memory_dir=self.memory_dir,
            time_gate_hours=0.0,
            session_gate_count=1,
        )

        with patch.dict(os.environ, {"GENEVA_AUTO_DREAM": "1"}), patch(
            "src.services.auto_dream.auto_dream._session_dir", return_value=self.sessions_dir
        ), patch_memory_env(self.root / "brain.db", self.root / "events", self.memory_dir):
            asyncio.run(checker())
            results = search("ghost private detail", type="user")

        self.assertEqual(results, [])


class ExtractionAndSessionMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db_path = self.root / "brain.db"
        self.events_dir = self.root / "events"
        self.memory_dir = self.root / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        init_db(self.db_path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_run_extraction_is_idempotent(self) -> None:
        context = {
            "messages": [
                {"role": "user", "content": "Please remember that I prefer concise updates."},
                {"role": "assistant", "content": "Noted. I will keep updates concise."},
            ]
        }
        with patch_memory_env(self.db_path, self.events_dir, self.memory_dir):
            asyncio.run(run_extraction(context, memory_dir=self.memory_dir))
            asyncio.run(run_extraction(context, memory_dir=self.memory_dir))
            results = search("concise updates", type="user")
        self.assertEqual(len(results), 1)

    def test_run_extraction_understands_thai_memory_signals(self) -> None:
        context = {
            "messages": [
                {"role": "user", "content": "ช่วยจำว่าฉันชอบให้สรุปสถานะเป็นภาษาไทยแบบสั้นและชัด"},
            ]
        }
        with patch_memory_env(self.db_path, self.events_dir, self.memory_dir):
            asyncio.run(run_extraction(context, memory_dir=self.memory_dir))
            results = search("ภาษาไทย", type="user")

        self.assertEqual(len(results), 1)

    def test_run_extraction_scopes_project_memory(self) -> None:
        context = {
            "scope": "project-1",
            "messages": [
                {"role": "user", "content": "Project decision: build Memory Inspector before compaction."},
            ],
        }
        with patch_memory_env(self.db_path, self.events_dir, self.memory_dir):
            asyncio.run(run_extraction(context, memory_dir=self.memory_dir))
            scoped = search("Memory Inspector", type="project", scope="project-1")
            wrong_scope = search("Memory Inspector", type="project", scope="project-2")

        self.assertEqual(len(scoped), 1)
        self.assertEqual(wrong_scope, [])

    def test_context_budget_reduces_memory_budget_under_pressure(self) -> None:
        from src.services.compact.context_budget import estimate_context_budget, trim_to_token_budget

        low = estimate_context_budget(
            messages=[{"role": "user", "content": "hello"}],
            model="gpt-4o",
        )
        high = estimate_context_budget(
            messages=[{"role": "user", "content": "x " * 110_000}],
            model="gpt-4o",
        )

        self.assertEqual(low.pressure, "low")
        self.assertIn(high.pressure, {"high", "critical"})
        self.assertLessEqual(high.memory_budget_tokens, low.memory_budget_tokens)
        self.assertLessEqual(len(trim_to_token_budget("word " * 1000, 60)), len("word " * 1000))

    def test_context_ledger_records_budget_without_raw_memory_text(self) -> None:
        from src.services.compact.context_budget import estimate_context_budget
        from src.services.compact.context_ledger import (
            ContextSourceBlock,
            append_context_ledger_record,
            build_turn_context_ledger,
            list_context_ledger_records,
        )

        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "src.services.compact.context_ledger.CONTEXT_LEDGER_DIR",
            Path(temp_dir),
        ):
            messages = [{"role": "user", "content": "hello"}]
            budget = estimate_context_budget(messages=messages, model="gpt-4o")
            record = build_turn_context_ledger(
                session_id="session/with/slash",
                model="gpt-4o",
                budget=budget,
                user_input="latest private request",
                messages=messages,
                source_blocks=[
                    ContextSourceBlock(
                        source_type="memory_context",
                        label="Memory context",
                        text="raw private durable memory " * 20,
                        rendered_text="raw private durable memory",
                        action="trimmed",
                        reason="Budget pressure",
                    )
                ],
                final_context="raw private durable memory",
                memory_budget_tokens=80,
            )
            append_context_ledger_record(record)
            loaded = list_context_ledger_records("session/with/slash")

        self.assertEqual(len(loaded), 1)
        payload_text = str(loaded[0])
        self.assertIn("context_window", loaded[0]["budget"])
        self.assertIn("trimmed", {entry["action"] for entry in loaded[0]["entries"]})
        self.assertNotIn("raw private durable memory raw private", payload_text)

    def test_session_memory_helpers(self) -> None:
        memory = Memory(
            id="m1",
            path="/tmp/m1.md",
            name="One",
            type="user",
            status="active",
            content="A" * 100,
            confidence=0.9,
            importance=0.5,
            source_type="assistant_inferred",
            created_at="2026-05-12T00:00:00+00:00",
            updated_at=None,
            retention_days=365,
            expires_at=None,
            superseded_by=None,
        )
        deduped = dedup_memories([memory, memory])
        self.assertEqual(len(deduped), 1)
        prompt = build_session_memory_cache_prompt([memory], max_tokens=10)
        self.assertLessEqual(len(prompt), 40)
        self.assertLessEqual(len(truncate_to_budget("x" * 100, max_tokens=5)), 20)

    def test_load_session_memory_and_context_builder(self) -> None:
        fake_memory = Memory(
            id="m2",
            path="/tmp/m2.md",
            name="Two",
            type="project",
            status="active",
            content="Project context",
            confidence=0.9,
            importance=0.5,
            source_type="assistant_inferred",
            created_at="2026-05-12T00:00:00+00:00",
            updated_at=None,
            retention_days=365,
            expires_at=None,
            superseded_by=None,
        )
        with patch("src.services.session_memory.session_memory.search", return_value=[fake_memory, fake_memory]):
            prompt = asyncio.run(load_session_memory(memory_dir=self.memory_dir, force_refresh=True))
            cached = get_current_session_memory()
        self.assertIn("Project context", prompt)
        self.assertEqual(len(cached["memories"]), 1)

        header = type("Header", (), {"path": Path("/tmp/m2.md"), "name": "Two", "type": "project"})()
        context = build_session_memory_context([header], {Path("/tmp/m2.md"): "Project context"})
        self.assertIn("Project context", context)


class PersistentSessionTests(unittest.TestCase):
    def test_session_save_load_preserves_closed_chat_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(os.environ, {"HOME": temp_dir}):
            session = Session.create("test-provider", "test-model")
            session.conversation.add_user_message("จำแชทนี้ไว้หลังปิดหน้า")
            session.conversation.add_assistant_message("ได้ ฉันจะโหลดกลับมาได้")
            session.save()

            loaded = Session.load(session.session_id)

        self.assertIsNotNone(loaded)
        messages = loaded.conversation.get_messages()
        self.assertEqual(messages[0]["content"], "จำแชทนี้ไว้หลังปิดหน้า")
        self.assertEqual(messages[1]["content"], "ได้ ฉันจะโหลดกลับมาได้")

    def test_session_ids_include_subsecond_entropy(self) -> None:
        first = Session.create("provider", "model")
        second = Session.create("provider", "model")

        self.assertNotEqual(first.session_id, second.session_id)


class WebSkillEngineTests(unittest.TestCase):
    def test_default_compact_skill_is_seeded(self) -> None:
        from src.geneva.skill_engine import SkillEngine

        with tempfile.TemporaryDirectory() as temp_dir:
            engine = SkillEngine(Path(temp_dir) / "skills")
            skill = engine.get("compact")

        self.assertIsNotNone(skill)
        self.assertIn("context", skill.description.lower())


class TeamMemoryTests(unittest.TestCase):
    def test_secret_detection_and_guard(self) -> None:
        findings = detect_secret_patterns("token=abcdefghijklmnopqrstuvwxyz123456")
        self.assertTrue(findings)
        payload = TeamMemoryContent(
            name="team",
            description="desc",
            type="reference",
            content="AKIA1234567890ABCDEF",
        )
        guarded = check_team_mem_secrets(payload)
        self.assertTrue(guarded)
        self.assertEqual(len(payload.compute_hash()), 16)

    def test_team_memory_path_guard(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            safe = get_team_mem_path(base, "notes/example.md")
            self.assertTrue(str(safe).startswith(str(base.resolve())))
            with self.assertRaises(PathTraversalError):
                get_team_mem_path(base, "../escape.md")
