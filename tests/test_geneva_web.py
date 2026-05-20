from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
import asyncio
import importlib.util
import queue
import threading
from http import HTTPStatus
from pathlib import Path
from unittest.mock import patch

from src.memdir.brain_engine import rebuild_index, remember, search
from src.geneva.code_runner import run_code
from src.geneva.agent_trace import append_trace_record, list_trace_records
from src.geneva.events import ErrorInfo, MemoryActivity, TurnStreamEvent, public_error_info
from src.geneva.memory_manager import MemoryManager
from src.geneva.project_store import ProjectStore
from src.geneva.session import GenevaSession
from src.geneva import settings_manager
from src.geneva.settings_manager import GenevaConfig, save_settings
from src.geneva.skill_engine import reset_engine
from src.geneva.slash_commands import lookup_slash_command, parse_slash_command
from src.geneva.web_server import (
    GenevaRequestHandler,
    chat_request_from_payload,
    parse_json_request_body,
    research_request_from_payload,
)
from src.geneva.web_runtime import (
    ChatRequest,
    ResearchRequest,
    add_memory_payload,
    add_todo_payload,
    chat_events,
    create_project_payload,
    delete_todo_payload,
    event_to_sse,
    get_memory_payload,
    is_validation_error,
    parse_json_bytes,
    research_events,
    settings_payload,
    update_memory_payload,
    update_settings,
    update_todo_payload,
    usage_payload,
)


def patch_memory_env(db_path: Path, events_dir: Path, memory_dir: Path):
    return patch.dict(
        os.environ,
        {
            "GENEVA_BRAIN_DB_PATH": str(db_path),
            "GENEVA_MEMORY_EVENTS_DIR": str(events_dir),
            "GENEVA_AUTO_MEM_PATH": str(memory_dir),
        },
    )
from src.geneva.web_api import (
    JsonApiResult,
    MAX_API_BODY_BYTES,
    REMOTE_BIND_OVERRIDE_ENV,
    GENEVA_REQUEST_HEADER,
    SseApiResult,
    dispatch_api_request,
    is_bind_host_allowed,
    is_host_allowed,
    security_headers,
    stream_sse_bytes,
    validate_request_security,
)
from src.skills.frontmatter import parse_frontmatter


class _FakeManager:
    def __init__(self, session: "_FakeSession") -> None:
        self.session = session
        self.resolved_permissions: list[dict[str, object]] = []

    def get(
        self,
        session_id: str | None = None,
        provider_name: str | None = None,
        model: str | None = None,
    ) -> "_FakeSession":
        return self.session

    def context_ledger(self, session_id: str | None = None, limit: int = 50) -> dict[str, object]:
        return {
            "session_id": session_id or self.session.session_id,
            "latest": None,
            "history": [],
            "records": [{"id": "ctx_1", "event": "turn_context"}],
        }

    def agent_traces(self, session_id: str, limit: int = 50) -> dict[str, object]:
        return {
            "session_id": session_id,
            "records": [
                {
                    "turn_id": "turn_1",
                    "session_id": session_id,
                    "events": [
                        {
                            "kind": "tool_result",
                            "tool_name": "WebSearch",
                            "tool_call_id": "toolu_1",
                            "status": "complete",
                            "summary": "searched production agent UX",
                        }
                    ],
                }
            ],
        }

    def resolve_tool_permission(self, session_id: str, request_id: str, approved: bool) -> dict[str, object] | None:
        if request_id != "req_1":
            return None
        payload = {"ok": True, "session_id": session_id, "request_id": request_id, "approved": approved}
        self.resolved_permissions.append(payload)
        return payload


class _FakeSession:
    def __init__(self) -> None:
        self.session_id = "fake-session"
        self.chat_calls: list[dict[str, object]] = []

    def set_project_context(self, _context: str, project_id: str | None = None) -> None:
        return None

    def execute_command(self, raw: str) -> str:
        if raw == "/context":
            return "used_tokens=0\nmax_tokens=200000\npercent_used=0\ncontext_files_loaded=0"
        return "ok"

    def chat_stream(
        self,
        message: str,
        max_turns: int = 100,
        memory_enabled: bool = True,
        ghost_mode: bool = False,
        images: list[dict[str, str]] | None = None,
    ):
        self.chat_calls.append(
            {
                "message": message,
                "max_turns": max_turns,
                "memory_enabled": memory_enabled,
                "ghost_mode": ghost_mode,
                "images": images or [],
            }
        )
        yield TurnStreamEvent(
            turn_id="turn_1",
            event_seq=0,
            type="turn_complete",
            data={"session_id": self.session_id},
            timestamp=1.0,
        )


class _FakeResearchEngine:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def research_stream(
        self,
        query: str,
        session_id: str | None,
        provider_name: str | None,
        model: str | None,
        save_memory: bool = True,
        mode: str = "deep",
    ):
        self.calls.append(
            {
                "query": query,
                "session_id": session_id,
                "provider_name": provider_name,
                "model": model,
                "save_memory": save_memory,
                "mode": mode,
            }
        )
        yield {"type": "research_complete", "data": {"query": query, "saved": save_memory}}


class GenevaWebEventTests(unittest.TestCase):
    def test_turn_stream_event_serializes_error(self) -> None:
        event = TurnStreamEvent(
            turn_id="turn_1",
            event_seq=3,
            type="error",
            data={},
            timestamp=1.0,
            error=ErrorInfo(
                code="tool_error",
                message="search failed",
                recoverable=True,
                suggestion="Retry",
            ),
        )

        payload = event.to_dict()

        self.assertEqual(payload["event_seq"], 3)
        self.assertEqual(payload["error"]["code"], "tool_error")
        self.assertTrue(payload["error"]["recoverable"])

    def test_public_error_info_classifies_openrouter_max_tokens_as_budget_error(self) -> None:
        raw = (
            'OpenRouter stream failed (402): {"error":{"message":"This request requires more credits, '
            'or fewer max_tokens. You requested up to 65536 tokens, but can only afford 15967."},'
            '"user_id":"user_secret"}'
        )

        error = public_error_info(RuntimeError(raw))

        self.assertEqual(error.code, "token_budget_error")
        self.assertIn("model budget", error.message)
        self.assertNotIn("user_secret", error.message)
        self.assertNotIn("65536", error.message)
        self.assertNotIn("OpenRouter", error.message)

    def test_public_error_info_sanitizes_openrouter_never_purchased_credit_errors(self) -> None:
        raw = (
            'OpenRouter stream failed (402): {"error":{"message":"Insufficient credits. '
            'This account never purchased credits. Make sure your key is on the correct account or org."},'
            '"user_id":"user_secret"}'
        )

        error = public_error_info(RuntimeError(raw))

        self.assertEqual(error.code, "quota_error")
        self.assertIn("paid model", error.message)
        self.assertNotIn("user_secret", error.message)
        self.assertNotIn("OpenRouter", error.message)

    def test_event_to_sse_uses_event_type(self) -> None:
        event = TurnStreamEvent(
            turn_id="turn_1",
            event_seq=0,
            type="text_delta",
            data={"text": "hello"},
            timestamp=1.0,
        )

        frame = event_to_sse(event).decode("utf-8")

        self.assertIn("event: text_delta", frame)
        self.assertIn('"text": "hello"', frame)
        event_line, data_line = frame.strip().splitlines()
        self.assertEqual(event_line, "event: text_delta")
        self.assertEqual(json.loads(data_line.removeprefix("data: "))["data"]["text"], "hello")

    def test_memory_activity_serializes(self) -> None:
        activity = MemoryActivity(
            session_id="s1",
            timestamp=1.0,
            action="ADD",
            title="New preference",
            confidence=0.9,
            after={"total_active": 2},
        )

        payload = activity.to_dict()

        self.assertEqual(payload["action"], "ADD")
        self.assertEqual(payload["after"]["total_active"], 2)


class GenevaWebSecurityTests(unittest.TestCase):
    def test_local_host_policy_blocks_dns_rebinding_hosts(self) -> None:
        self.assertTrue(is_host_allowed("127.0.0.1:8765"))
        self.assertTrue(is_host_allowed("localhost:5173"))
        self.assertTrue(is_host_allowed("[::1]:8765"))
        self.assertFalse(is_host_allowed(None))
        self.assertFalse(is_host_allowed("evil.example"))
        self.assertFalse(is_host_allowed("0.0.0.0:8765"))

    def test_remote_bind_requires_explicit_override(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(REMOTE_BIND_OVERRIDE_ENV, None)
            self.assertTrue(is_bind_host_allowed("127.0.0.1"))
            self.assertFalse(is_bind_host_allowed("0.0.0.0"))
        with patch.dict(os.environ, {REMOTE_BIND_OVERRIDE_ENV: "1"}):
            self.assertTrue(is_bind_host_allowed("0.0.0.0"))

    def test_security_policy_rejects_cross_origin_and_simple_mutations(self) -> None:
        forbidden_origin = validate_request_security(
            "POST",
            origin="https://evil.example",
            host="127.0.0.1:8765",
            content_type="application/json",
            content_length=2,
            client_host="127.0.0.1",
            geneva_header="1",
        )
        self.assertIsNotNone(forbidden_origin)
        self.assertEqual(forbidden_origin.status, HTTPStatus.FORBIDDEN)

        simple_form = validate_request_security(
            "POST",
            origin="http://localhost:5173",
            host="127.0.0.1:8765",
            content_type="text/plain",
            content_length=2,
            client_host="127.0.0.1",
            geneva_header=None,
        )
        self.assertIsNotNone(simple_form)
        self.assertEqual(simple_form.status, HTTPStatus.FORBIDDEN)

        non_browser_mutation = validate_request_security(
            "DELETE",
            origin=None,
            host="127.0.0.1:8765",
            client_host="127.0.0.1",
            geneva_header=None,
        )
        self.assertIsNotNone(non_browser_mutation)
        self.assertEqual(non_browser_mutation.status, HTTPStatus.FORBIDDEN)

        wrong_content_type = validate_request_security(
            "POST",
            origin="http://localhost:5173",
            host="127.0.0.1:8765",
            content_type="text/plain",
            content_length=2,
            client_host="127.0.0.1",
            geneva_header="1",
        )
        self.assertIsNotNone(wrong_content_type)
        self.assertEqual(wrong_content_type.status, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

        too_large = validate_request_security(
            "PUT",
            origin=None,
            host="127.0.0.1:8765",
            content_type="application/json",
            content_length=MAX_API_BODY_BYTES + 1,
            client_host="127.0.0.1",
            geneva_header=None,
        )
        self.assertIsNotNone(too_large)
        self.assertEqual(too_large.status, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)

    def test_security_policy_allows_same_origin_json_mutation_with_header(self) -> None:
        failure = validate_request_security(
            "POST",
            origin="http://localhost:5173",
            host="localhost:8765",
            content_type="application/json; charset=utf-8",
            content_length=2,
            client_host="127.0.0.1",
            geneva_header="1",
        )
        self.assertIsNone(failure)

    def test_security_headers_include_frame_and_content_guards(self) -> None:
        headers = security_headers()

        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        self.assertIn("connect-src 'self'", headers["Content-Security-Policy"])


class GenevaSlashCommandTests(unittest.TestCase):
    def test_parse_server_command(self) -> None:
        command, args = parse_slash_command("/memory search Bond")

        self.assertIsNotNone(command)
        self.assertEqual(command.name, "memory")
        self.assertEqual(command.level, "server")
        self.assertEqual(args, "search Bond")

    def test_lookup_skill_command(self) -> None:
        command = lookup_slash_command("consult")

        self.assertIsNotNone(command)
        self.assertEqual(command.level, "skill")

    def test_parse_json_bytes_requires_dict(self) -> None:
        payload = parse_json_bytes(json.dumps({"message": "hi"}).encode("utf-8"))

        self.assertEqual(payload["message"], "hi")
        self.assertEqual(parse_json_bytes(b"[]"), {})

    def test_invalid_json_helper_returns_controlled_error(self) -> None:
        payload, error = parse_json_request_body(b'{"message":')

        self.assertEqual(payload, {})
        self.assertIsNotNone(error)
        self.assertEqual(error["code"], "validation_error")
        self.assertIn("Invalid JSON", error["error"])

    def test_empty_stream_requests_are_rejected_before_sse(self) -> None:
        chat_request, chat_error = chat_request_from_payload({"message": "  "})
        research_request, research_error = research_request_from_payload({"query": ""})

        self.assertIsNone(chat_request)
        self.assertTrue(is_validation_error(chat_error))
        self.assertIsNone(research_request)
        self.assertTrue(is_validation_error(research_error))

        chat_request, chat_error = chat_request_from_payload({"message": "hi", "ghost_mode": True})
        research_request, research_error = research_request_from_payload({"query": "memory", "ghost_mode": True})

        self.assertIsNone(chat_error)
        self.assertIsNotNone(chat_request)
        self.assertTrue(chat_request.ghost_mode)
        self.assertIsNone(research_error)
        self.assertIsNotNone(research_request)
        self.assertTrue(research_request.ghost_mode)

    def test_api_dispatcher_is_single_stream_validation_contract(self) -> None:
        manager = _FakeManager(_FakeSession())

        rejected = dispatch_api_request(
            manager,
            "POST",
            "/api/chat/stream",
            payload={"message": "  "},
        )
        self.assertIsInstance(rejected, JsonApiResult)
        self.assertEqual(rejected.status, HTTPStatus.BAD_REQUEST)
        self.assertTrue(is_validation_error(rejected.payload))

        accepted = dispatch_api_request(
            manager,
            "POST",
            "/api/chat/stream",
            payload={"message": "hi", "ghost_mode": True, "max_turns": "not-an-int"},
        )
        self.assertIsInstance(accepted, SseApiResult)
        self.assertEqual(accepted.kind, "chat")
        self.assertTrue(accepted.request.ghost_mode)
        self.assertEqual(accepted.request.max_turns, 100)

    def test_skill_control_plane_requires_review_before_activation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"GENEVA_SKILLS_DIR": str(Path(temp_dir) / "skills")}):
                reset_engine()
                manager = _FakeManager(_FakeSession())
                created = dispatch_api_request(
                    manager,
                    "POST",
                    "/api/skills",
                    payload={
                        "name": "review-demo",
                        "status": "review",
                        "content": _skill_markdown("review-demo", "Review first"),
                    },
                )

                self.assertIsInstance(created, JsonApiResult)
                self.assertEqual(created.payload["skill"]["status"], "review")

                commands_before = dispatch_api_request(manager, "GET", "/api/commands")
                self.assertIsInstance(commands_before, JsonApiResult)
                self.assertNotIn(
                    "review-demo",
                    {command["name"] for command in commands_before.payload["commands"]},
                )

                activated = dispatch_api_request(
                    manager,
                    "POST",
                    "/api/skills/review-demo/activate",
                    payload={},
                )

                self.assertIsInstance(activated, JsonApiResult)
                self.assertEqual(activated.payload["skill"]["status"], "active")
                commands_after = dispatch_api_request(manager, "GET", "/api/commands")
                self.assertIsInstance(commands_after, JsonApiResult)
                self.assertIn(
                    "review-demo",
                    {command["name"] for command in commands_after.payload["commands"]},
                )
                reset_engine()

    def test_blocked_skill_activation_returns_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"GENEVA_SKILLS_DIR": str(Path(temp_dir) / "skills")}):
                reset_engine()
                manager = _FakeManager(_FakeSession())
                dispatch_api_request(
                    manager,
                    "POST",
                    "/api/skills",
                    payload={
                        "name": "blocked-demo",
                        "status": "review",
                        "content": "---\nname: blocked-demo\n---\n\nBody\n",
                    },
                )

                result = dispatch_api_request(
                    manager,
                    "POST",
                    "/api/skills/blocked-demo/activate",
                    payload={},
                )

                self.assertIsInstance(result, JsonApiResult)
                self.assertEqual(result.status, HTTPStatus.BAD_REQUEST)
                self.assertTrue(is_validation_error(result.payload))
                reset_engine()

    def test_context_command_is_cataloged_for_slash_access(self) -> None:
        manager = _FakeManager(_FakeSession())

        catalog = dispatch_api_request(manager, "GET", "/api/commands")
        self.assertIsInstance(catalog, JsonApiResult)
        self.assertIn("/context", {command["command"] for command in catalog.payload["commands"]})

        result = dispatch_api_request(
            manager,
            "POST",
            "/api/command",
            payload={"raw": "/context", "session_id": "context-session"},
        )

        self.assertIsInstance(result, JsonApiResult)
        self.assertEqual(result.payload["type"], "server")
        self.assertIn("used_tokens=", result.payload["output"])

    def test_skill_eval_feedback_and_rollback_api_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"GENEVA_SKILLS_DIR": str(Path(temp_dir) / "skills")}):
                reset_engine()
                manager = _FakeManager(_FakeSession())
                created = dispatch_api_request(
                    manager,
                    "POST",
                    "/api/skills",
                    payload={
                        "name": "quality-demo",
                        "content": _skill_markdown("quality-demo", "First version"),
                    },
                )
                self.assertIsInstance(created, JsonApiResult)

                updated = dispatch_api_request(
                    manager,
                    "PUT",
                    "/api/skills/quality-demo",
                    payload={"content": _skill_markdown("quality-demo", "Second version")},
                )
                self.assertIsInstance(updated, JsonApiResult)
                revision_id = updated.payload["skill"]["revisions"][0]["id"]

                eval_result = dispatch_api_request(
                    manager,
                    "POST",
                    "/api/skills/quality-demo/evals",
                    payload={
                        "input": "Review this plan",
                        "expected": "Should identify risks",
                        "status": "passed",
                    },
                )
                self.assertIsInstance(eval_result, JsonApiResult)
                self.assertEqual(eval_result.payload["skill"]["eval_cases"][0]["status"], "passed")

                feedback = dispatch_api_request(
                    manager,
                    "POST",
                    "/api/skills/quality-demo/feedback",
                    payload={
                        "score": 1,
                        "outcome": "failed",
                        "suggested_change": "Add an explicit risk checklist.",
                    },
                )
                self.assertIsInstance(feedback, JsonApiResult)
                self.assertEqual(feedback.payload["skill"]["status"], "review")
                self.assertIn("Feedback-Driven Review Backlog", feedback.payload["skill"]["system_prompt"])

                rollback = dispatch_api_request(
                    manager,
                    "POST",
                    "/api/skills/quality-demo/rollback",
                    payload={"revision_id": revision_id},
                )
                self.assertIsInstance(rollback, JsonApiResult)
                self.assertIn("First version", rollback.payload["skill"]["system_prompt"])
                reset_engine()

    def test_api_dispatcher_maps_mutation_failures_to_http_status(self) -> None:
        manager = _FakeManager(_FakeSession())

        missing = dispatch_api_request(
            manager,
            "PUT",
            "/api/memory/missing-memory",
            payload={"content": "canonical update"},
        )
        self.assertIsInstance(missing, JsonApiResult)
        self.assertEqual(missing.status, HTTPStatus.NOT_FOUND)

        invalid = dispatch_api_request(
            manager,
            "PUT",
            "/api/memory/missing-memory",
            payload={"content": "   "},
        )
        self.assertIsInstance(invalid, JsonApiResult)
        self.assertEqual(invalid.status, HTTPStatus.BAD_REQUEST)
        self.assertTrue(is_validation_error(invalid.payload))

    def test_sse_contract_emits_structured_error_frame_on_runtime_failure(self) -> None:
        manager = _FakeManager(_FakeSession())
        result = SseApiResult("chat", ChatRequest("hi"))

        with patch("src.geneva.web_api.chat_events", side_effect=RuntimeError("provider exploded")):
            frame = b"".join(stream_sse_bytes(manager, result)).decode("utf-8")

        self.assertIn("event: error", frame)
        payload = json.loads(frame.strip().splitlines()[1].removeprefix("data: "))
        self.assertEqual(payload["error"]["code"], "internal_error")
        self.assertNotIn("provider exploded", frame)

    def test_api_dispatcher_exposes_memory_conflict_queue(self) -> None:
        manager = _FakeManager(_FakeSession())
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            db_path = root / "brain.db"
            memory_dir = root / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            with patch_memory_env(db_path, root / "events", memory_dir), patch(
                "src.geneva.memory_manager.DB_PATH",
                db_path,
            ):
                asyncio.run(
                    remember(
                        "Bond prefers concise code reviews.",
                        "user",
                        source_type="user_direct",
                        memory_kind="preference",
                    )
                )
                queued = dispatch_api_request(
                    manager,
                    "POST",
                    "/api/memory",
                    payload={
                        "content": "Bond does not want concise code reviews anymore; Bond wants exhaustive reviews.",
                        "type": "user",
                        "memory_kind": "preference",
                    },
                )
                self.assertIsInstance(queued, JsonApiResult)
                conflict_id = queued.payload["result"]["conflict_id"]

                listed = dispatch_api_request(manager, "GET", "/api/memory/conflicts")
                self.assertIsInstance(listed, JsonApiResult)
                resolved = dispatch_api_request(
                    manager,
                    "POST",
                    f"/api/memory/conflicts/{conflict_id}/resolve",
                    payload={
                        "resolution": "replace",
                        "merged_content": "Bond prefers exhaustive code reviews.",
                    },
                )

        self.assertEqual(queued.payload["result"]["operation"], "conflict")
        self.assertEqual(listed.payload["total"], 1)
        self.assertEqual(listed.payload["items"][0]["id"], conflict_id)
        self.assertIsInstance(resolved, JsonApiResult)
        self.assertTrue(resolved.payload["success"])

    def test_api_dispatcher_exposes_context_ledger(self) -> None:
        manager = _FakeManager(_FakeSession())

        result = dispatch_api_request(
            manager,
            "GET",
            "/api/sessions/fake-session/context-ledger",
            "limit=5",
        )

        self.assertIsInstance(result, JsonApiResult)
        self.assertEqual(result.payload["session_id"], "fake-session")
        self.assertEqual(result.payload["records"][0]["event"], "turn_context")

    def test_api_dispatcher_exposes_agent_traces(self) -> None:
        manager = _FakeManager(_FakeSession())

        result = dispatch_api_request(
            manager,
            "GET",
            "/api/sessions/fake-session/agent-traces",
            "limit=5",
        )

        self.assertIsInstance(result, JsonApiResult)
        self.assertEqual(result.payload["session_id"], "fake-session")
        event = result.payload["records"][0]["events"][0]
        self.assertEqual(event["tool_call_id"], "toolu_1")
        self.assertEqual(event["status"], "complete")

    def test_api_dispatcher_resolves_pending_tool_permission(self) -> None:
        manager = _FakeManager(_FakeSession())

        result = dispatch_api_request(
            manager,
            "POST",
            "/api/sessions/fake-session/tool-permissions/req_1",
            payload={"approved": True},
        )

        self.assertIsInstance(result, JsonApiResult)
        self.assertTrue(result.payload["approved"])
        self.assertEqual(manager.resolved_permissions[0]["request_id"], "req_1")

        string_false = dispatch_api_request(
            manager,
            "POST",
            "/api/sessions/fake-session/tool-permissions/req_1",
            payload={"approved": "false"},
        )
        self.assertIsInstance(string_false, JsonApiResult)
        self.assertFalse(string_false.payload["approved"])

        missing = dispatch_api_request(
            manager,
            "POST",
            "/api/sessions/fake-session/tool-permissions/missing",
            payload={"approved": True},
        )
        self.assertIsInstance(missing, JsonApiResult)
        self.assertEqual(missing.status, HTTPStatus.NOT_FOUND)

    def test_api_dispatcher_exposes_tool_catalog(self) -> None:
        result = dispatch_api_request(_FakeManager(_FakeSession()), "GET", "/api/tools")

        self.assertIsInstance(result, JsonApiResult)
        payload = result.payload
        self.assertGreater(payload["count"], 0)
        self.assertEqual(payload["profile"], "web_safe")
        first_tool = payload["tools"][0]
        self.assertIn("input_schema", first_tool)
        self.assertIn("timeout_seconds", first_tool)
        tool_names = {tool["name"] for tool in payload["tools"]}
        self.assertIn("WebSearch", tool_names)
        self.assertNotIn("Bash", tool_names)

        developer = dispatch_api_request(_FakeManager(_FakeSession()), "GET", "/api/tools", "profile=developer")
        self.assertIsInstance(developer, JsonApiResult)
        developer_names = {tool["name"] for tool in developer.payload["tools"]}
        self.assertEqual(developer.payload["profile"], "developer")
        self.assertIn("Bash", developer_names)
        self.assertIn("Read", developer_names)
        self.assertNotIn("RemoteTrigger", developer_names)
        self.assertNotIn("NotebookEdit", developer_names)
        self.assertNotIn("REPL", developer_names)


@unittest.skipUnless(
    importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
    "FastAPI TestClient dependencies are not installed",
)
class GenevaFastApiGatewayTests(unittest.TestCase):
    def _client(self):
        from fastapi.testclient import TestClient
        from src.geneva.fastapi_app import create_app

        return TestClient(create_app(), base_url="http://127.0.0.1")

    def test_fastapi_gateway_uses_shared_json_and_status_contract(self) -> None:
        client = self._client()

        models = client.get("/api/models")
        self.assertEqual(models.status_code, 200)
        self.assertIn("models", models.json())

        blank_chat = client.post(
            "/api/chat/stream",
            json={"message": "  "},
            headers={GENEVA_REQUEST_HEADER: "1"},
        )
        self.assertEqual(blank_chat.status_code, 400)
        self.assertEqual(blank_chat.json()["code"], "validation_error")

        invalid_json = client.post(
            "/api/settings",
            data='{"broken":',
            headers={"content-type": "application/json", GENEVA_REQUEST_HEADER: "1"},
        )
        self.assertEqual(invalid_json.status_code, 400)
        self.assertEqual(invalid_json.json()["error"], "Invalid JSON body")

        missing_memory = client.get("/api/memory/not-a-real-memory-id")
        self.assertEqual(missing_memory.status_code, 404)
        self.assertEqual(missing_memory.json()["error"], "Memory not found")

    def test_fastapi_gateway_applies_cors_and_sse_contracts(self) -> None:
        client = self._client()

        forbidden = client.get("/api/models", headers={"Origin": "https://evil.example"})
        self.assertEqual(forbidden.status_code, 403)

        preflight = client.options("/api/models", headers={"Origin": "http://localhost:5173"})
        self.assertEqual(preflight.status_code, 204)
        self.assertEqual(preflight.headers["access-control-allow-origin"], "http://localhost:5173")
        self.assertIn(GENEVA_REQUEST_HEADER, preflight.headers["access-control-allow-headers"])

        def fake_chat_events(manager, request):
            self.assertEqual(request.message, "hello")
            self.assertTrue(request.ghost_mode)
            yield TurnStreamEvent(
                turn_id="t1",
                event_seq=0,
                type="turn_complete",
                data={"session_id": "s1"},
                timestamp=1.0,
            )

        with patch("src.geneva.web_api.chat_events", fake_chat_events):
            with client.stream(
                "POST",
                "/api/chat/stream",
                json={"message": "hello", "ghost_mode": True},
                headers={GENEVA_REQUEST_HEADER: "1"},
            ) as response:
                body = "".join(response.iter_text())

        self.assertEqual(response.status_code, 200)
        self.assertIn("event: turn_complete", body)
        self.assertEqual(response.headers["x-frame-options"], "DENY")

    def test_fastapi_gateway_blocks_bad_host_and_simple_mutation(self) -> None:
        client = self._client()

        bad_host = client.get("/api/models", headers={"Host": "evil.example"})
        self.assertEqual(bad_host.status_code, 403)

        simple_mutation = client.post(
            "/api/settings",
            data='{"openrouter_api_key":"sk-test"}',
            headers={
                "Origin": "http://localhost:5173",
                "Content-Type": "text/plain",
            },
        )
        self.assertEqual(simple_mutation.status_code, 403)

        oversized = client.post(
            "/api/settings",
            content=b'{"payload":"' + (b"x" * (MAX_API_BODY_BYTES + 1)) + b'"}',
            headers={
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(oversized.status_code, 413)

    def test_blank_memory_content_is_rejected(self) -> None:
        self.assertTrue(is_validation_error(add_memory_payload({"content": " "})))
        self.assertTrue(is_validation_error(update_memory_payload("missing", {"content": "\n"})))

    def test_ghost_mode_disables_stream_memory_writes(self) -> None:
        session = _FakeSession()
        events = list(chat_events(_FakeManager(session), ChatRequest("hi", ghost_mode=True)))

        self.assertEqual(events[-1].type, "turn_complete")
        self.assertEqual(session.chat_calls[0]["message"], "hi")
        self.assertFalse(session.chat_calls[0]["memory_enabled"])

    def test_ghost_mode_disables_research_memory_save(self) -> None:
        engine = _FakeResearchEngine()

        with patch("src.geneva.web_runtime.get_research_engine", return_value=engine):
            events = list(
                research_events(
                    _FakeManager(_FakeSession()),
                    ResearchRequest("memory", ghost_mode=True, mode="max"),
                )
            )

        self.assertEqual(events[-1]["type"], "research_complete")
        self.assertFalse(engine.calls[0]["save_memory"])
        self.assertEqual(engine.calls[0]["mode"], "max")

    def test_blank_secret_setting_update_does_not_clear_stored_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(settings_manager, "GENEVA_DIR", Path(temp_dir)):
                save_settings(GenevaConfig(openrouter_api_key="sk-test-secret-123456"))

                result = update_settings({"openrouter_api_key": "   "})

                self.assertEqual(result, {"ok": True})
                payload = settings_payload()
                self.assertEqual(payload["config"]["openrouter_api_key"], "sk-***...3456")
                self.assertFalse((Path(temp_dir) / "settings.json.tmp").exists())

    def test_nonblank_secret_setting_update_replaces_stored_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(settings_manager, "GENEVA_DIR", Path(temp_dir)):
                save_settings(GenevaConfig(openrouter_api_key="sk-test-secret-123456"))

                update_settings({"openrouter_api_key": "sk-test-secret-abcdef"})

                payload = settings_payload()
                self.assertEqual(payload["config"]["openrouter_api_key"], "sk-***...cdef")

class GenevaSettingsRuntimeTests(unittest.TestCase):
    def test_default_mode_setting_persists_for_frontend_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(settings_manager, "GENEVA_DIR", Path(temp_dir)):
                result = update_settings({"default_mode": "high"})

                self.assertEqual(result, {"ok": True})
                payload = settings_payload()
                self.assertEqual(payload["config"]["default_mode"], "high")

    def test_usage_payload_summarizes_local_session_cost_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            costs_path = root / "sessions" / "session-1" / "costs.json"
            costs_path.parent.mkdir(parents=True)
            costs_path.write_text(
                json.dumps(
                    {
                        "session_id": "session-1",
                        "saved_at": "2026-05-20T09:00:00+00:00",
                        "entries": [
                            {
                                "model": "deepseek/deepseek-v4-flash",
                                "input_tokens": 120,
                                "output_tokens": 80,
                                "cache_read_tokens": 10,
                                "cache_write_tokens": 5,
                                "cost_usd": 0.0123,
                                "timestamp": "2026-05-20T09:00:01+00:00",
                            }
                        ],
                    }
                )
            )

            with patch.object(settings_manager, "GENEVA_DIR", root):
                save_settings(GenevaConfig(geneva_dir=str(root)))
                payload = usage_payload()

            self.assertEqual(payload["sessions_count"], 1)
            self.assertEqual(payload["entry_count"], 1)
            self.assertEqual(payload["total_tokens"], 215)
            self.assertAlmostEqual(payload["total_cost_usd"], 0.0123)
            self.assertEqual(payload["by_model"][0]["model"], "deepseek/deepseek-v4-flash")


class GenevaSafetyTests(unittest.TestCase):
    def test_web_permission_wait_emits_request_and_resolution_events(self) -> None:
        session = object.__new__(GenevaSession)
        session.session = type("FakeSession", (), {"session_id": "permission-session"})()
        session._permission_lock = threading.RLock()
        session._permission_requests = {}
        events: list[tuple[str, dict[str, object]]] = []

        def put_event(event_type: str, data: dict[str, object], *args, **kwargs) -> None:
            events.append((event_type, data))
            if event_type == "tool_permission_request":
                session.resolve_permission_request(str(data["request_id"]), True)

        approved, permanent = session._wait_for_web_permission(
            tool_name="Write",
            message="Allow markdown write?",
            suggestion="Approve only if this edit is expected.",
            put_event=put_event,
            timeout_seconds=0.2,
        )

        self.assertTrue(approved)
        self.assertFalse(permanent)
        self.assertEqual(events[0][0], "tool_permission_request")
        self.assertEqual(events[1][0], "tool_permission_resolved")
        self.assertEqual(events[1][1]["status"], "approved")

    def test_stream_worker_rejects_concurrent_turn_for_same_session(self) -> None:
        session = object.__new__(GenevaSession)
        session.session = type("FakePersistedSession", (), {"session_id": "session_1"})()
        session._last_tool_events = []
        session._turn_lock = threading.Lock()
        session._turn_lock.acquire()
        session._amendment_queue = queue.Queue()
        session._pending_bg_lock = threading.Lock()
        session._active_put_event = None
        session.tool_context = type(
            "FakeToolContext",
            (),
            {"extra_system_prompt": "", "permission_handler": None},
        )()
        events: list[tuple[str, dict[str, object], ErrorInfo | None]] = []
        event_queue: queue.Queue[TurnStreamEvent | None] = queue.Queue()

        def put_event(
            event_type: str,
            data: dict[str, object],
            tool_call_id: str | None = None,
            error: ErrorInfo | None = None,
        ) -> None:
            events.append((event_type, data, error))

        try:
            session._run_stream_worker(
                turn_id="turn_1",
                user_input="hi",
                memory_block="",
                memory_enabled=True,
                max_turns=1,
                put_event=put_event,
                event_queue=event_queue,
            )
        finally:
            session._turn_lock.release()

        self.assertEqual(events[0][0], "amendment_accepted")
        self.assertEqual(events[0][1]["status"], "incorporated")
        self.assertEqual(session._amendment_queue.get_nowait(), "hi")
        self.assertIsNone(event_queue.get_nowait())

    def test_agent_trace_store_is_bounded_per_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(
                os.environ,
                {
                    "GENEVA_AGENT_TRACE_DIR": str(Path(temp_dir) / "traces"),
                    "GENEVA_AGENT_TRACE_MAX_RECORDS": "50",
                },
            ):
                for index in range(55):
                    append_trace_record(
                        {
                            "turn_id": f"turn_{index}",
                            "session_id": "bounded-session",
                            "events": [{"tool_call_id": f"toolu_{index}", "status": "complete"}],
                        }
                    )

                records = list_trace_records("bounded-session", limit=100)

        self.assertEqual(len(records), 50)
        self.assertEqual(records[0]["turn_id"], "turn_5")
        self.assertEqual(records[-1]["turn_id"], "turn_54")

    def test_code_runner_blocks_process_languages_by_default(self) -> None:
        result = run_code("python", "print('hi')")

        self.assertFalse(result["ok"])
        self.assertIn("disabled", result["error"])

    def test_project_todo_done_update_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "brain.db"
            with patch.multiple(
                "src.geneva.project_store",
                DB_PATH=db_path,
                init_db=lambda: None,
            ):
                store = ProjectStore()
                project = store.create_project("Pilot")
                todo = store.add_todo(project.id, "Validate Day-3 retention")

                first = store.set_todo_done(project.id, todo.id, True)
                second = store.set_todo_done(project.id, todo.id, True)

        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertTrue(first.done)
        self.assertTrue(second.done)

    def test_web_server_rejects_non_local_origins(self) -> None:
        handler = object.__new__(GenevaRequestHandler)

        handler.headers = {"Origin": "https://evil.example"}  # type: ignore[assignment]
        self.assertFalse(handler._origin_allowed())

        handler.headers = {"Origin": "http://localhost:5173"}  # type: ignore[assignment]
        self.assertTrue(handler._origin_allowed())

    def test_project_and_todo_validation_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "brain.db"
            with patch.multiple(
                "src.geneva.project_store",
                DB_PATH=db_path,
                init_db=lambda: None,
            ):
                store = ProjectStore()
                with patch("src.geneva.web_runtime._project_store", store):
                    blank_project = create_project_payload({"name": "   "})
                    self.assertTrue(is_validation_error(blank_project))

                    project_payload = create_project_payload({"name": "Pilot"})
                    self.assertIsNotNone(project_payload)
                    project_id = project_payload["project"]["id"]

                    blank_todo = add_todo_payload(project_id, {"text": "  "})
                    self.assertTrue(is_validation_error(blank_todo))
                    self.assertFalse(store.add_session("missing-project", "session-1"))
                    self.assertIsNone(add_todo_payload("missing-project", {"text": "Ship memory"}))
                    self.assertIsNone(update_todo_payload(project_id, "missing-todo", {"done": True}))
                    self.assertIsNone(delete_todo_payload(project_id, "missing-todo"))
                    self.assertTrue(is_validation_error(update_todo_payload(project_id, "missing-todo", {"text": ""})))

                    todo = add_todo_payload(project_id, {"text": "Keep backend truthful"})
                    self.assertIsNotNone(todo)
                    todo_id = todo["todo"]["id"]
                    done_update = update_todo_payload(project_id, todo_id, {"done": True})
                    self.assertEqual(done_update["todo"]["id"], todo_id)
                    self.assertTrue(done_update["todo"]["done"])
                    text_update = update_todo_payload(project_id, todo_id, {"text": "Keep backend truthful, visibly"})
                    self.assertEqual(text_update["todo"]["text"], "Keep backend truthful, visibly")
                    mixed_update = update_todo_payload(project_id, todo_id, {"done": True, "text": "  "})
                    self.assertTrue(is_validation_error(mixed_update))
                    persisted = store.get_project(project_id)
                    self.assertIsNotNone(persisted)
                    persisted_todo = next(item for item in persisted.todos if item.id == todo_id)
                    self.assertTrue(persisted_todo.done)
                    self.assertEqual(persisted_todo.text, "Keep backend truthful, visibly")

    def test_memory_detail_includes_provenance_and_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            db_path = root / "brain.db"
            memory_dir = root / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            with patch_memory_env(db_path, root / "events", memory_dir), patch(
                "src.geneva.memory_manager.DB_PATH",
                db_path,
            ):
                result = asyncio.run(
                    remember(
                        "Session: s1\nCaptured at: 2026-05-13T00:00:00Z\nUser: remember provenance.",
                        "episodic",
                    )
                )
                payload = get_memory_payload(result.memory_id or "")

        self.assertIsNotNone(payload)
        self.assertEqual(payload["source_session_id"], "s1")
        self.assertEqual(payload["captured_at"], "2026-05-13T00:00:00Z")
        self.assertEqual(payload["events"][0]["event_type"], "add")

    def test_project_store_foreign_keys_prevent_orphan_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "brain.db"
            with patch.multiple(
                "src.geneva.project_store",
                DB_PATH=db_path,
                init_db=lambda: None,
            ):
                store = ProjectStore()
                with store._conn() as conn:
                    with self.assertRaises(sqlite3.IntegrityError):
                        conn.execute(
                            "INSERT INTO project_sessions (project_id,session_id,created_at) VALUES (?,?,?)",
                            ("missing-project", "session-1", "now"),
                        )

    def test_project_store_honors_brain_db_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "isolated-brain.db"
            with patch_memory_env(db_path, Path(temp_dir) / "events", Path(temp_dir) / "memory"):
                store = ProjectStore()
                project = store.create_project("Env isolated project")

            self.assertEqual(project.name, "Env isolated project")
            self.assertTrue(db_path.exists())


class GenevaMemoryManagerTests(unittest.TestCase):
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
        return patch_memory_env(self.db_path, self.events_dir, self.memory_dir)

    def _frontmatter(self, path: Path) -> dict[str, object]:
        return parse_frontmatter(path.read_text(encoding="utf-8")).frontmatter

    def test_memory_manager_lists_project_scoped_memories_from_env_db(self) -> None:
        project_id = "project-visual-qa"
        with self._patch_env():
            manager = MemoryManager()
            added = manager.add_memory(
                "Project rail must show this scoped decision.",
                "project",
                scope=project_id,
                source_type="test",
            )
            self.assertTrue(added["success"])

            scoped = manager.list_memories(scope=project_id, status="active")
            global_items = manager.list_memories(scope="other-project", status="active")

        self.assertTrue(self.db_path.exists())
        self.assertEqual(scoped["total"], 1)
        self.assertEqual(scoped["items"][0]["scope"], project_id)
        self.assertEqual(scoped["items"][0]["type"], "project")
        self.assertEqual(global_items["items"], [])

    def test_memory_crud_keeps_markdown_and_rebuild_index_consistent(self) -> None:
        with self._patch_env(), patch("src.geneva.memory_manager.DB_PATH", self.db_path):
            manager = MemoryManager()
            added = manager.add_memory("Keep one canonical preference.", "user")
            memory_id = added["memory_id"]
            self.assertIsNotNone(memory_id)
            original_hash = manager.get_memory(str(memory_id))["content_hash"]

            updated = manager.update_memory(str(memory_id), "Keep one edited canonical preference.")
            self.assertTrue(updated["success"])
            self.assertEqual(updated["memory_id"], memory_id)

            with sqlite3.connect(self.db_path) as conn:
                count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            self.assertEqual(count, 1)

            memory = manager.get_memory(str(memory_id))
            self.assertIsNotNone(memory)
            self.assertNotEqual(memory["content_hash"], original_hash)
            self.assertIsNotNone(memory["updated_at"])
            memory_path = Path(str(memory["path"]))
            frontmatter = self._frontmatter(memory_path)
            self.assertEqual(frontmatter["id"], memory_id)
            self.assertEqual(frontmatter["status"], "active")
            self.assertIn("edited canonical", memory_path.read_text(encoding="utf-8"))
            self.assertEqual(search("edited canonical", type="user")[0].id, memory_id)

            archived = manager.archive_memory(str(memory_id))
            self.assertTrue(archived["ok"])
            self.assertEqual(manager.get_memory(str(memory_id))["status"], "archived")
            self.assertEqual(self._frontmatter(memory_path)["status"], "archived")
            self.assertEqual(search("edited canonical", type="user"), [])
            self.assertNotIn(str(memory_id), (self.memory_dir / "MEMORY.md").read_text(encoding="utf-8"))

            rebuild_index(self.memory_dir, force=True)
            self.assertEqual(manager.get_memory(str(memory_id))["status"], "archived")
            self.assertEqual(manager.list_memories(status="active")["items"], [])

            added_deleted = manager.add_memory("Temporary delete target.", "reference")
            deleted_id = str(added_deleted["memory_id"])
            deleted_path = Path(str(manager.get_memory(deleted_id)["path"]))
            deleted = manager.delete_memory(deleted_id)
            self.assertTrue(deleted["ok"])
            self.assertEqual(manager.get_memory(deleted_id)["status"], "deleted")
            self.assertEqual(self._frontmatter(deleted_path)["status"], "deleted")
            self.assertEqual(search("temporary delete", type="reference"), [])
            self.assertNotIn(deleted_id, (self.memory_dir / "MEMORY.md").read_text(encoding="utf-8"))

            rebuild_index(self.memory_dir, force=True)
            self.assertEqual(manager.get_memory(str(memory_id))["status"], "archived")
            self.assertEqual(manager.get_memory(deleted_id)["status"], "deleted")
            active_ids = {item["id"] for item in manager.list_memories(status="active")["items"]}
            self.assertNotIn(str(memory_id), active_ids)
            self.assertNotIn(deleted_id, active_ids)

    def test_rebuild_preserves_legacy_inactive_status_when_markdown_is_stale(self) -> None:
        with self._patch_env(), patch("src.geneva.memory_manager.DB_PATH", self.db_path):
            manager = MemoryManager()
            added = manager.add_memory("Legacy inactive memory should stay archived.", "user")
            memory_id = str(added["memory_id"])
            memory_path = Path(str(manager.get_memory(memory_id)["path"]))

            self.assertEqual(self._frontmatter(memory_path)["status"], "active")
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE memories SET status = 'archived' WHERE id = ?", (memory_id,))
                conn.commit()

            rebuild_index(self.memory_dir, force=True)

            self.assertEqual(manager.get_memory(memory_id)["status"], "archived")
            self.assertEqual(self._frontmatter(memory_path)["status"], "archived")
            self.assertEqual(search("legacy inactive", type="user"), [])
            entrypoint = self.memory_dir / "MEMORY.md"
            entrypoint_text = entrypoint.read_text(encoding="utf-8") if entrypoint.exists() else ""
            self.assertNotIn(memory_id, entrypoint_text)


def _skill_markdown(name: str, description: str) -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\nRun the workflow.\n"


if __name__ == "__main__":
    unittest.main()
