"""R10 project autopilot + BLAST writer + activity log tests."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class TestAutoDetectProjectName(unittest.TestCase):

    def test_thai_project_name_reuang(self) -> None:
        from src.geneva.project_store import auto_detect_project_name
        name = auto_detect_project_name("อันนี้คือ project ใหม่เรื่อง Geneva")
        self.assertIsNotNone(name)
        self.assertIn("Geneva", name)

    def test_thai_project_name_chue(self) -> None:
        from src.geneva.project_store import auto_detect_project_name
        name = auto_detect_project_name("สร้าง project ชื่อ AI Router")
        self.assertIsNotNone(name)

    def test_english_colon_format(self) -> None:
        from src.geneva.project_store import auto_detect_project_name
        name = auto_detect_project_name("new project: Second Brain")
        self.assertIsNotNone(name)
        self.assertIn("Second", name)

    def test_english_about_format(self) -> None:
        from src.geneva.project_store import auto_detect_project_name
        name = auto_detect_project_name("start project about AI Router")
        self.assertIsNotNone(name)

    def test_no_project_keyword_returns_none(self) -> None:
        from src.geneva.project_store import auto_detect_project_name
        self.assertIsNone(auto_detect_project_name("how are you today?"))
        self.assertIsNone(auto_detect_project_name("สวัสดีครับ"))


class TestAutoCreateForSession(unittest.TestCase):

    def test_creates_project_and_links_session(self) -> None:
        from src.geneva.project_store import ProjectStore
        store = ProjectStore()
        project = store.auto_create_for_session("sess_r10_test", "new project: AutoTest R10")
        self.assertIsNotNone(project)
        self.assertIn("AutoTest", project.name)
        # session should be linked
        sessions = store.list_session_ids(project.id)
        self.assertIn("sess_r10_test", sessions)

    def test_returns_none_for_no_project_name(self) -> None:
        from src.geneva.project_store import ProjectStore
        store = ProjectStore()
        result = store.auto_create_for_session("sess_r10_none", "just a normal message")
        self.assertIsNone(result)

    def test_reuses_existing_project(self) -> None:
        from src.geneva.project_store import ProjectStore
        store = ProjectStore()
        # Create project first
        p = store.create_project("ReusableProject")
        # Auto-create with same name
        result = store.auto_create_for_session("sess_r10_reuse", "new project: ReusableProject")
        self.assertIsNotNone(result)
        self.assertEqual(result.id, p.id)


class TestProjectActivityLog(unittest.TestCase):

    def _make_project(self):
        from src.geneva.project_store import ProjectStore
        return ProjectStore(), ProjectStore().create_project("ActivityTestProject")

    def test_add_activity_returns_true(self) -> None:
        from src.geneva.project_store import ProjectStore
        store = ProjectStore()
        p = store.create_project("ActivityTest1")
        self.assertTrue(store.add_activity(p.id, "user_goal", "Starting work on Geneva R10"))

    def test_list_activity_returns_logged_events(self) -> None:
        from src.geneva.project_store import ProjectStore
        store = ProjectStore()
        p = store.create_project("ActivityTest2")
        store.add_activity(p.id, "user_goal", "First turn content")
        store.add_activity(p.id, "decision", "Decided to use SQLite")
        activities = store.list_activity(p.id)
        self.assertGreaterEqual(len(activities), 2)
        event_types = [a["event_type"] for a in activities]
        self.assertIn("decision", event_types)

    def test_add_activity_nonexistent_project_returns_false(self) -> None:
        from src.geneva.project_store import ProjectStore
        self.assertFalse(ProjectStore().add_activity("nonexistent-id", "user_goal", "test"))

    def test_list_activity_empty_for_new_project(self) -> None:
        from src.geneva.project_store import ProjectStore
        store = ProjectStore()
        p = store.create_project("EmptyActivityProject")
        self.assertEqual(store.list_activity(p.id), [])


class TestBlastWriter(unittest.TestCase):

    def test_create_blast_docs_creates_5_files(self) -> None:
        from src.geneva.blast_writer import create_blast_docs
        with tempfile.TemporaryDirectory() as tmp:
            result = create_blast_docs("proj_test", "Test Project", "Build something cool", folder_path=tmp)
            self.assertEqual(len(result), 5)
            for filename, path in result.items():
                self.assertTrue(path.exists(), f"{filename} was not created")

    def test_blast_docs_contain_project_name(self) -> None:
        from src.geneva.blast_writer import create_blast_docs
        with tempfile.TemporaryDirectory() as tmp:
            result = create_blast_docs("proj_n", "MyProjectName", folder_path=tmp)
            claude_md = (Path(tmp) / "CLAUDE.md").read_text()
            self.assertIn("MyProjectName", claude_md)

    def test_blast_docs_no_overwrite(self) -> None:
        from src.geneva.blast_writer import create_blast_docs
        with tempfile.TemporaryDirectory() as tmp:
            create_blast_docs("proj_ow", "OriginalName", folder_path=tmp)
            (Path(tmp) / "CLAUDE.md").write_text("# Custom Content")
            create_blast_docs("proj_ow", "NewName", folder_path=tmp)
            content = (Path(tmp) / "CLAUDE.md").read_text()
            self.assertEqual(content, "# Custom Content")

    def test_append_to_blast_appends_content(self) -> None:
        from src.geneva.blast_writer import create_blast_docs, append_to_blast
        with tempfile.TemporaryDirectory() as tmp:
            create_blast_docs("proj_ap", "AppendTest", folder_path=tmp)
            ok = append_to_blast("proj_ap", "decisions.md", "Decided to use SQLite", folder_path=tmp)
            self.assertTrue(ok)
            content = (Path(tmp) / "decisions.md").read_text()
            self.assertIn("Decided to use SQLite", content)

    def test_append_to_blast_nonexistent_file_returns_false(self) -> None:
        from src.geneva.blast_writer import append_to_blast
        with tempfile.TemporaryDirectory() as tmp:
            result = append_to_blast("proj_na", "missing.md", "content", folder_path=tmp)
            self.assertFalse(result)

    def test_get_blast_paths_returns_all_5(self) -> None:
        from src.geneva.blast_writer import get_blast_paths
        paths = get_blast_paths("proj_paths", folder_path="/tmp/test_blast")
        self.assertEqual(len(paths), 5)
        self.assertIn("CLAUDE.md", paths)
        self.assertIn("decisions.md", paths)
