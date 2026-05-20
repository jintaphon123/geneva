"""R9 - Artifact store tests. All acceptance criteria from GENEVA_ROADMAP.md R9."""
from __future__ import annotations

import os
import unittest


class TestArtifactStore(unittest.TestCase):

    def setUp(self) -> None:
        # conftest sets GENEVA_BRAIN_DB_PATH to a temp dir - init_db() will use it
        from src.memdir.brain_engine import init_db

        init_db()

    # -- R9.2: save / get -------------------------------------------------------

    def test_save_artifact_returns_id(self) -> None:
        from src.geneva.artifact_store import save_artifact

        aid = save_artifact("research_trace", '{"query": "test", "results": []}', "sess_01")
        self.assertIsNotNone(aid)
        self.assertIsInstance(aid, str)
        self.assertGreater(len(aid), 0)

    def test_get_artifact_by_id(self) -> None:
        from src.geneva.artifact_store import get_artifact, save_artifact

        payload = '{"citation": "Bond 2026", "score": 0.9}'
        aid = save_artifact("citation_map", payload, "sess_02")
        self.assertIsNotNone(aid)
        result = get_artifact(aid)
        self.assertIsNotNone(result)
        self.assertEqual(result["artifact_id"], aid)
        self.assertEqual(result["type"], "citation_map")
        self.assertEqual(result["session_id"], "sess_02")
        self.assertIn(result["content"], [payload, None])  # inline or file

    def test_get_nonexistent_returns_none(self) -> None:
        from src.geneva.artifact_store import get_artifact

        self.assertIsNone(get_artifact("nonexistent-id-xyz"))

    # -- R9.2: list -------------------------------------------------------------

    def test_list_artifacts_by_session(self) -> None:
        from src.geneva.artifact_store import list_artifacts, save_artifact

        sid = "sess_list_test"
        save_artifact("tool_output", "output A", sid)
        save_artifact("tool_output", "output B", sid)
        results = list_artifacts(session_id=sid)
        self.assertGreaterEqual(len(results), 2)
        for r in results:
            self.assertEqual(r["session_id"], sid)

    def test_list_artifacts_by_type(self) -> None:
        from src.geneva.artifact_store import list_artifacts, save_artifact

        save_artifact("screenshot", "screenshot data here", "sess_type_test")
        save_artifact("research_trace", '{"q": "test"}', "sess_type_test")
        screenshots = list_artifacts(artifact_type="screenshot")
        for r in screenshots:
            self.assertEqual(r["type"], "screenshot")

    # -- R9.2: ghost mode -------------------------------------------------------

    def test_ghost_mode_returns_none(self) -> None:
        from src.geneva.artifact_store import save_artifact

        os.environ["GENEVA_GHOST"] = "1"
        try:
            aid = save_artifact("tool_output", "should not persist", "sess_ghost")
            self.assertIsNone(aid)
        finally:
            del os.environ["GENEVA_GHOST"]

    def test_ghost_mode_does_not_persist(self) -> None:
        from src.geneva.artifact_store import list_artifacts, save_artifact

        os.environ["GENEVA_GHOST"] = "1"
        try:
            save_artifact("tool_output", "ghost content xyz", "sess_ghost_check")
        finally:
            del os.environ["GENEVA_GHOST"]
        results = list_artifacts(session_id="sess_ghost_check")
        self.assertEqual(len(results), 0, "Ghost mode should not write to DB")

    # -- R9.5: redaction --------------------------------------------------------

    def test_redaction_strips_api_key(self) -> None:
        from src.geneva.artifact_store import get_artifact, save_artifact

        sensitive = '{"api_key": "sk-secret1234567890abcdef", "result": "ok"}'
        aid = save_artifact("tool_output", sensitive, "sess_redact", redact=True)
        self.assertIsNotNone(aid)
        result = get_artifact(aid)
        content = result.get("content") or ""
        self.assertNotIn("sk-secret1234567890abcdef", content)
        self.assertIn("[REDACTED]", content)

    def test_redaction_strips_password(self) -> None:
        from src.geneva.artifact_store import get_artifact, save_artifact

        sensitive = "password=super_secret_value data follows"
        aid = save_artifact("tool_output", sensitive, "sess_redact2", redact=True)
        result = get_artifact(aid)
        content = result.get("content") or ""
        self.assertNotIn("super_secret_value", content)

    def test_redact_flag_false_preserves_content(self) -> None:
        from src.geneva.artifact_store import get_artifact, save_artifact

        data = "no secrets here, plain content"
        aid = save_artifact("citation_map", data, "sess_plain")
        result = get_artifact(aid)
        self.assertEqual(result["content"], data)

    # -- R9.4: retention TTL ----------------------------------------------------

    def test_ttl_screenshot_is_7_days(self) -> None:
        from src.geneva.artifact_store import TTL_DAYS

        self.assertEqual(TTL_DAYS["screenshot"], 7)

    def test_ttl_research_trace_is_30_days(self) -> None:
        from src.geneva.artifact_store import TTL_DAYS

        self.assertEqual(TTL_DAYS["research_trace"], 30)

    def test_ttl_document_preview_is_permanent(self) -> None:
        from src.geneva.artifact_store import TTL_DAYS

        self.assertIsNone(TTL_DAYS["document_preview"])

    def test_ttl_citation_map_is_permanent(self) -> None:
        from src.geneva.artifact_store import TTL_DAYS

        self.assertIsNone(TTL_DAYS["citation_map"])

    def test_expire_artifacts_removes_expired(self) -> None:
        from src.geneva.artifact_store import _connect, expire_artifacts, get_artifact, save_artifact

        # Save an artifact, then manually set expires_at to the past.
        aid = save_artifact("screenshot", "expired content", "sess_expire")
        self.assertIsNotNone(aid)
        # Backdate expires_at.
        from src.memdir.brain_engine import init_db as _init_db

        _init_db()
        with _connect() as conn:
            conn.execute(
                "UPDATE artifacts SET expires_at = ? WHERE artifact_id = ?",
                ("2000-01-01T00:00:00+00:00", aid),
            )
            conn.commit()
        count = expire_artifacts()
        self.assertGreaterEqual(count, 1)
        self.assertIsNone(get_artifact(aid), "Expired artifact should be gone")

    def test_expire_artifacts_keeps_permanent(self) -> None:
        from src.geneva.artifact_store import expire_artifacts, get_artifact, save_artifact

        aid = save_artifact("document_preview", "permanent content", "sess_perm")
        self.assertIsNotNone(aid)
        count = expire_artifacts()
        # The permanent artifact should still exist.
        self.assertIsNotNone(get_artifact(aid), "Permanent artifact should survive expire_artifacts()")

    # -- R9.2: delete -----------------------------------------------------------

    def test_delete_artifact_returns_true(self) -> None:
        from src.geneva.artifact_store import delete_artifact, get_artifact, save_artifact

        aid = save_artifact("tool_output", "to be deleted", "sess_del")
        self.assertTrue(delete_artifact(aid))
        self.assertIsNone(get_artifact(aid))

    def test_delete_nonexistent_returns_false(self) -> None:
        from src.geneva.artifact_store import delete_artifact

        self.assertFalse(delete_artifact("does-not-exist"))
