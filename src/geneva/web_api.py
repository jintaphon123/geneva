from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import Any, Literal
from urllib.parse import parse_qs, unquote

from src.geneva.events import ErrorInfo, TurnStreamEvent
from src.agent.session import Session
from src.geneva.search_service import full_brain_search, search_suggestions
from src.geneva.web_security import (
    MAX_API_BODY_BYTES,
    REMOTE_BIND_OVERRIDE_ENV,
    GENEVA_REQUEST_HEADER,
    cors_headers,
    is_bind_host_allowed,
    is_host_allowed,
    is_origin_allowed,
    security_headers,
    validate_request_security,
)
from src.geneva.onboarding import current_onboarding_manager
from src.memdir.paths import get_auto_mem_path
from src.geneva.web_runtime import (
    ChatRequest,
    CommandRequest,
    ResearchRequest,
    SessionManager,
    add_skill_eval_payload,
    add_memory_payload,
    add_memory_revision_payload,
    add_project_session_payload,
    add_todo_payload,
    archive_memory_payload,
    archive_project_payload,
    activate_skill_payload,
    agent_trace_payload,
    available_modes,
    available_models,
    build_skill_payload,
    chat_events,
    command_catalog,
    context_ledger_payload,
    context_summary_payload,
    create_project_payload,
    create_project_source_payload,
    create_research_run_payload,
    create_skill_payload,
    delete_memory_payload,
    delete_project_payload,
    delete_project_source_payload,
    delete_skill_payload,
    delete_todo_payload,
    event_to_sse,
    execute_command,
    generate_conversation_title,
    get_conversation_title,
    activity_timeline_payload,
    get_memory_conflict_payload,
    get_memory_payload,
    get_turn_trace_payload,
    get_project_payload,
    get_research_run_payload,
    get_skill_payload,
    import_workspace_payload,
    is_validation_error,
    json_bytes,
    list_memory_conflicts_payload,
    list_memory_write_events_payload,
    list_memories_payload,
    list_project_sources_payload,
    list_projects_payload,
    list_research_runs_payload,
    list_skills_payload,
    memory_stats_payload,
    memory_timeline_payload,
    parse_json_bytes,
    project_source_context_preview_payload,
    rebuild_memory_index,
    reload_skills_payload,
    research_events,
    resolve_tool_permission_payload,
    resolve_memory_conflict_payload,
    approve_memory_write_event_payload,
    undo_memory_write_event_payload,
    rollback_skill_payload,
    run_code_payload,
    skill_file_content_payload,
    skill_files_payload,
    set_conversation_title,
    set_skill_status_payload,
    settings_payload,
    submit_skill_feedback_payload,
    system_status,
    tool_catalog_payload,
    update_memory_payload,
    update_project_payload,
    update_project_source_payload,
    update_research_run_status_payload,
    update_skill_eval_payload,
    update_settings,
    update_skill_payload,
    update_todo_payload,
    complete_research_run_payload,
    usage_payload,
)
from src.geneva.research_engine import normalize_research_mode

_ONBOARDING_COMPLETE_TOKEN = "[ONBOARDING_COMPLETE]"

WEB_ROOT = Path(__file__).resolve().parent / "web"
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JsonApiResult:
    payload: object
    status: HTTPStatus = HTTPStatus.OK

    @property
    def body(self) -> object:
        return self.payload


@dataclass(frozen=True)
class SseApiResult:
    kind: Literal["chat", "research"]
    request: ChatRequest | ResearchRequest


ApiResult = JsonApiResult | SseApiResult


def dispatch_api_request(
    manager: SessionManager,
    method: str,
    path: str,
    query_string: str = "",
    payload: dict[str, Any] | None = None,
) -> ApiResult:
    method = method.upper()
    payload = payload or {}
    if method == "GET":
        return _dispatch_get(manager, path, query_string)
    if method == "POST":
        return _dispatch_post(manager, path, payload)
    if method == "PUT":
        return _dispatch_put(path, payload)
    if method == "DELETE":
        return _dispatch_delete(path)
    return JsonApiResult({"error": "Method not allowed"}, HTTPStatus.METHOD_NOT_ALLOWED)


def _dispatch_get(
    manager: SessionManager,
    path: str,
    query_string: str | dict[str, Any],
) -> JsonApiResult:
    query = _normalize_query(query_string)
    segments = _path_segments(path)
    if path == "/api/modes":
        return JsonApiResult(available_modes())
    if path == "/api/models":
        return JsonApiResult({"models": available_models()})
    if path == "/api/commands":
        return JsonApiResult({"commands": command_catalog()})
    if path == "/api/tools":
        return JsonApiResult(tool_catalog_payload(_optional_str(_query_single(query, "profile"))))
    if path == "/api/onboarding/status":
        onboarding_manager = current_onboarding_manager()
        return JsonApiResult(
            {
                "needs_onboarding": onboarding_manager.needs_onboarding(),
                "complete": (onboarding_manager.completion_root / ".onboarding_complete").exists(),
            }
        )
    if path == "/api/settings":
        return JsonApiResult(settings_payload())
    if path == "/api/system/status":
        return JsonApiResult(system_status())
    if path == "/api/usage":
        return JsonApiResult(usage_payload())
    if path == "/api/bridge/status":
        from src.geneva.cli_bridge import get_bridge

        return JsonApiResult(get_bridge().status())
    if path == "/api/skills":
        return JsonApiResult(list_skills_payload())
    if len(segments) == 4 and segments[:2] == ["api", "skills"] and segments[3] == "files":
        return _result_or_not_found(skill_files_payload(segments[2]), "Skill not found")
    if len(segments) == 4 and segments[:2] == ["api", "skills"] and segments[3] == "file":
        rel_path = _optional_str(_query_single(query, "path")) or ""
        return _result_or_not_found(skill_file_content_payload(segments[2], rel_path), "File not found")
    if len(segments) == 3 and segments[:2] == ["api", "skills"]:
        return _result_or_not_found(get_skill_payload(segments[2]), "Skill not found")
    if path == "/api/projects":
        return JsonApiResult(list_projects_payload())
    if len(segments) == 4 and segments[:2] == ["api", "projects"] and segments[3] == "sources":
        return _result_or_not_found(list_project_sources_payload(segments[2]), "Project not found")
    if len(segments) == 5 and segments[:2] == ["api", "projects"] and segments[3] == "sources" and segments[4] == "context-preview":
        return _result_or_not_found(project_source_context_preview_payload(segments[2]), "Project not found")
    if len(segments) == 4 and segments[:2] == ["api", "projects"] and segments[3] == "sessions":
        return JsonApiResult({"sessions": manager.list_project_sessions(segments[2])})
    if len(segments) == 3 and segments[:2] == ["api", "projects"]:
        return _result_or_not_found(get_project_payload(segments[2]), "Project not found")
    if path == "/api/sessions":
        limit = _query_int(query, "limit", 50)
        offset = _query_int(query, "offset", 0)
        return JsonApiResult(manager.list_sessions_paged(limit=limit, offset=offset))
    if len(segments) == 4 and segments[:2] == ["api", "sessions"] and segments[3] == "messages":
        return JsonApiResult(manager.messages(segments[2]))
    if len(segments) == 4 and segments[:2] == ["api", "conversations"] and segments[3] == "title":
        return JsonApiResult(get_conversation_title(segments[2]))
    if path == "/api/memory/list":
        return JsonApiResult(
            list_memories_payload(
                memory_type=_optional_str(_query_single(query, "type")),
                status=_query_single(query, "status") or "active",
                query=_optional_str(_query_single(query, "q")),
                scope=_optional_str(_query_single(query, "scope")),
                limit=_query_int(query, "limit", 50),
                offset=_query_int(query, "offset", 0),
            )
        )
    if path == "/api/memory/search":
        return JsonApiResult(
            list_memories_payload(
                memory_type=_optional_str(_query_single(query, "type")),
                query=_optional_str(_query_single(query, "q")),
                limit=_query_int(query, "limit", 50),
                offset=_query_int(query, "offset", 0),
            )
        )
    if path == "/api/memory/timeline":
        return JsonApiResult(memory_timeline_payload())
    if path == "/api/memory/stats":
        return JsonApiResult(memory_stats_payload(manager, _optional_str(_query_single(query, "session_id"))))
    if path == "/api/memory/write-events":
        return JsonApiResult(
            list_memory_write_events_payload(
                session_id=_optional_str(_query_single(query, "session_id")),
                memory_id=_optional_str(_query_single(query, "memory_id")),
                status=_optional_str(_query_single(query, "status")),
                limit=_query_int(query, "limit", 50),
                offset=_query_int(query, "offset", 0),
            )
        )
    if path == "/api/context/ledger":
        return JsonApiResult(
            context_ledger_payload(
                manager,
                _optional_str(_query_single(query, "session_id")),
                _query_int(query, "limit", 50),
            )
        )
    if len(segments) == 4 and segments[:2] == ["api", "sessions"] and segments[3] == "context-ledger":
        return JsonApiResult(
            context_ledger_payload(
                manager,
                segments[2],
                _query_int(query, "limit", 50),
            )
        )
    if len(segments) == 6 and segments[:2] == ["api", "sessions"] and segments[3] == "turns" and segments[5] == "context-summary":
        return _result_or_not_found(
            context_summary_payload(manager, segments[2], segments[4]),
            "Context summary not found",
        )
    if len(segments) == 4 and segments[:2] == ["api", "sessions"] and segments[3] == "agent-traces":
        return JsonApiResult(
            agent_trace_payload(
                manager,
                segments[2],
                _query_int(query, "limit", 50),
            )
        )
    if len(segments) == 5 and segments[:2] == ["api", "sessions"] and segments[3] == "trace":
        return _result_or_not_found(
            get_turn_trace_payload(segments[2], segments[4]),
            "Trace record not found",
        )
    if len(segments) == 4 and segments[:2] == ["api", "sessions"] and segments[3] == "activity":
        return JsonApiResult(
            activity_timeline_payload(manager, segments[2], _query_int(query, "limit", 50))
        )
    if path == "/api/research/runs":
        return JsonApiResult(
            list_research_runs_payload(
                session_id=_optional_str(_query_single(query, "session_id")),
                project_id=_optional_str(_query_single(query, "project_id")),
                limit=_query_int(query, "limit", 50),
            )
        )
    if len(segments) == 4 and segments[:3] == ["api", "research", "runs"]:
        return _result_or_not_found(get_research_run_payload(segments[3]), "Research run not found")
    if path == "/api/memory/conflicts":
        return JsonApiResult(
            list_memory_conflicts_payload(
                status=_query_single(query, "status") or "open",
                limit=_query_int(query, "limit", 50),
                offset=_query_int(query, "offset", 0),
            )
        )
    if len(segments) == 4 and segments[:3] == ["api", "memory", "conflicts"]:
        return _result_or_not_found(get_memory_conflict_payload(segments[3]), "Memory conflict not found")
    if len(segments) == 3 and segments[:2] == ["api", "memory"]:
        payload = get_memory_payload(segments[2])
        if payload is None:
            return _not_found("Memory not found")
        return JsonApiResult({"memory": payload})
    if path == "/api/search/suggest":
        q = _query_single(query, "q") or ""
        return JsonApiResult(
            search_suggestions(
                q,
                project_id=_optional_str(_query_single(query, "project_id")),
                limit=_query_int(query, "limit", 8),
            )
        )
    if path == "/api/search":
        q = _query_single(query, "q") or ""
        return JsonApiResult(
            full_brain_search(
                q,
                types=_query_single(query, "types"),
                project_id=_optional_str(_query_single(query, "project_id")),
                limit=_query_int(query, "limit", 20),
            )
        )
    if path == "/api/health":
        return JsonApiResult(_health_check_payload())
    if path == "/api/artifacts":
        from src.geneva.artifact_store import list_artifacts

        return JsonApiResult(
            list_artifacts(
                session_id=_optional_str(_query_single(query, "session_id")),
                artifact_type=_optional_str(_query_single(query, "type")),
                limit=_query_int(query, "limit", 50),
            )
        )
    if len(segments) == 3 and segments[:2] == ["api", "artifacts"]:
        from src.geneva.artifact_store import get_artifact

        result = get_artifact(segments[2])
        if result is None:
            return _not_found("Artifact not found")
        return JsonApiResult(result)
    if len(segments) == 4 and segments[:2] == ["api", "projects"] and segments[3] == "activity":
        from src.geneva.project_store import ProjectStore

        store = ProjectStore()
        return JsonApiResult(store.list_activity(segments[2], _query_int(query, "limit", 50)))

    # ── Plugins ──────────────────────────────────────────────────────────
    if path == "/api/plugins":
        from src.geneva.plugin_runtime import PluginRuntime

        rt = PluginRuntime()
        include_builtin = _query_bool(query, "include_builtin", True)
        return JsonApiResult({"plugins": rt.list_manifest_dicts(include_builtin=include_builtin)})

    if len(segments) == 3 and segments[:2] == ["api", "plugins"]:
        from src.geneva.plugin_runtime import PluginRuntime

        rt = PluginRuntime()
        manifests = rt.list_manifest_dicts(include_builtin=True)
        match = next((m for m in manifests if m["name"] == segments[2]), None)
        if match is None:
            match = next((m for m in manifests if str(m.get("name") or "").rsplit(".", 1)[-1] == segments[2]), None)
            if match is not None:
                match = {**match, "qualified_name": match["name"], "name": segments[2]}
        if match is None:
            return _not_found(f"Plugin '{segments[2]}' not found")
        return JsonApiResult(match)

    # ── Connectors ───────────────────────────────────────────────────────
    if path == "/api/connectors":
        from src.services.mcp.connectors.google import GoogleConnector
        from src.services.mcp.connectors.notion import NotionConnector
        from src.services.mcp.connectors.github import GitHubConnector
        from src.services.mcp.trust_policy import list_trusted

        connectors = [
            GoogleConnector().get_connection_status(),
            NotionConnector().get_connection_status(),
            GitHubConnector().get_connection_status(),
        ]
        return JsonApiResult({"connectors": connectors, "trusted_servers": list_trusted()})

    if len(segments) == 4 and segments[:2] == ["api", "connectors"] and segments[3] == "status":
        name = segments[2]
        try:
            if name == "google":
                from src.services.mcp.connectors.google import GoogleConnector

                return JsonApiResult(GoogleConnector().get_connection_status())
            elif name == "notion":
                from src.services.mcp.connectors.notion import NotionConnector

                return JsonApiResult(NotionConnector().get_connection_status())
            elif name == "github":
                from src.services.mcp.connectors.github import GitHubConnector

                return JsonApiResult(GitHubConnector().get_connection_status())
            else:
                return _not_found(f"Connector '{name}' not found")
        except Exception as exc:
            return JsonApiResult({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    # ── Computer Use ─────────────────────────────────────────────────────
    if path == "/api/computer-use/log":
        session_id = _optional_str(_query_single(query, "session_id"))
        return JsonApiResult({"action_log": [], "session_id": session_id})
    return _not_found("Not found")


def _dispatch_post(
    manager: SessionManager,
    path: str,
    payload: dict[str, Any],
) -> ApiResult:
    segments = _path_segments(path)
    if path == "/api/code/run":
        return JsonApiResult(run_code_payload(payload))
    if path == "/api/bridge/codex":
        return JsonApiResult(run_code_payload(payload))
    if path == "/api/settings":
        return JsonApiResult(update_settings(payload))
    if path == "/api/onboarding/start":
        onboarding_manager = current_onboarding_manager()
        return JsonApiResult(
            {
                "session_id": manager.get().session_id,
                "first_message": (
                    "สวัสดีครับ! ผมชื่อ Geneva — ผู้ช่วย AI ส่วนตัวของคุณ 👋\n\n"
                    "ก่อนที่เราจะเริ่มทำงานด้วยกัน ผมอยากรู้จักคุณมากขึ้นสักหน่อย เพื่อให้ผมช่วยงานได้ตรงกับความต้องการของคุณมากที่สุด\n\n"
                    "มาเริ่มกันที่ข้อมูลพื้นฐานก่อนนะครับ — **ชื่อของคุณคืออะไร? คุณทำอะไรอยู่ในตอนนี้ (บอกสั้นๆ ประโยคเดียวพอ)?**"
                ),
            }
        )
    if path == "/api/memory/rebuild":
        return JsonApiResult(rebuild_memory_index())
    if path == "/api/bridge/gemini":
        from src.geneva.cli_bridge import get_bridge

        try:
            files = _bridge_files(payload.get("files"))
            result = get_bridge().gemini_query(str(payload.get("prompt") or ""), files)
            return JsonApiResult({"result": result})
        except Exception:
            logger.exception("Gemini bridge request failed")
            return JsonApiResult(
                {"ok": False, "error": "Gemini bridge request failed", "code": "runtime_error"},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
    if path == "/api/import/workspace":
        return JsonApiResult(import_workspace_payload(payload))
    if path == "/api/skills":
        return _result_or_bad_request(create_skill_payload(payload), "Invalid skill payload")
    if path == "/api/skills/reload":
        return JsonApiResult(reload_skills_payload())
    if path == "/api/skills/build":
        return _result_or_bad_request(build_skill_payload(manager, payload), "Invalid skill description")
    if len(segments) == 4 and segments[:2] == ["api", "skills"] and segments[3] == "activate":
        return _payload_result(activate_skill_payload(segments[2], payload), "Skill not found")
    if len(segments) == 4 and segments[:2] == ["api", "skills"] and segments[3] == "status":
        return _payload_result(set_skill_status_payload(segments[2], payload), "Skill not found")
    if len(segments) == 4 and segments[:2] == ["api", "skills"] and segments[3] == "evals":
        return _payload_result(add_skill_eval_payload(segments[2], payload), "Skill not found")
    if len(segments) == 5 and segments[:2] == ["api", "skills"] and segments[3] == "evals":
        return _payload_result(update_skill_eval_payload(segments[2], segments[4], payload), "Evaluation case not found")
    if len(segments) == 4 and segments[:2] == ["api", "skills"] and segments[3] == "rollback":
        return _payload_result(rollback_skill_payload(segments[2], payload), "Skill revision not found")
    if len(segments) == 4 and segments[:2] == ["api", "skills"] and segments[3] == "feedback":
        return _payload_result(submit_skill_feedback_payload(segments[2], payload), "Skill not found")
    if path == "/api/memory":
        return _payload_result(add_memory_payload(payload), "Memory not found")
    if len(segments) == 5 and segments[:3] == ["api", "memory", "write-events"] and segments[4] == "undo":
        return _payload_result(undo_memory_write_event_payload(segments[3]), "Memory write event not found")
    if len(segments) == 5 and segments[:3] == ["api", "memory", "write-events"] and segments[4] == "approve":
        return _payload_result(approve_memory_write_event_payload(segments[3]), "Memory write event not found")
    if len(segments) == 4 and segments[:2] == ["api", "memory"] and segments[3] == "revisions":
        return _payload_result(add_memory_revision_payload(segments[2], payload), "Memory not found")
    if len(segments) == 5 and segments[:3] == ["api", "memory", "conflicts"] and segments[4] == "resolve":
        return _payload_result(resolve_memory_conflict_payload(segments[3], payload), "Memory conflict not found")
    if len(segments) == 5 and segments[:3] == ["api", "memory", "conflicts"] and segments[4] == "dismiss":
        dismiss_payload = {**payload, "resolution": "keep_existing"}
        return _payload_result(resolve_memory_conflict_payload(segments[3], dismiss_payload), "Memory conflict not found")
    if len(segments) == 4 and segments[:2] == ["api", "memory"] and segments[3] == "archive":
        return _payload_result(archive_memory_payload(segments[2]), "Memory not found")
    if path == "/api/projects":
        return _result_or_bad_request(create_project_payload(payload), "Invalid project payload")
    if len(segments) == 4 and segments[:2] == ["api", "projects"] and segments[3] == "sources":
        return _payload_result(create_project_source_payload(segments[2], payload), "Project not found")
    if len(segments) == 4 and segments[:2] == ["api", "projects"] and segments[3] == "todos":
        return _payload_result(add_todo_payload(segments[2], payload), "Project not found")
    if len(segments) == 4 and segments[:2] == ["api", "projects"] and segments[3] == "sessions":
        return _payload_result(add_project_session_payload(segments[2], payload), "Project not found")
    if len(segments) == 4 and segments[:2] == ["api", "projects"] and segments[3] == "archive":
        return _payload_result(archive_project_payload(segments[2]), "Project not found")
    if len(segments) == 4 and segments[:2] == ["api", "conversations"] and segments[3] == "title":
        return JsonApiResult(set_conversation_title(segments[2], str(payload.get("title") or "")))
    if len(segments) == 4 and segments[:2] == ["api", "sessions"] and segments[3] == "pin":
        session_id = segments[2]
        session_path = Path.home() / ".geneva" / "sessions" / f"{session_id}.json"
        if not session_path.exists():
            return JsonApiResult({"ok": False, "error": "Session not found"}, status=404)
        try:
            data = json.loads(session_path.read_text(encoding="utf-8"))
            data["pinned"] = not bool(data.get("pinned", False))
            session_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            return JsonApiResult({"ok": True, "pinned": data["pinned"]})
        except Exception as exc:
            return JsonApiResult({"ok": False, "error": str(exc)}, status=500)
    if len(segments) == 5 and segments[:2] == ["api", "conversations"] and segments[3:5] == ["title", "generate"]:
        return JsonApiResult(
            generate_conversation_title(
                manager,
                segments[2],
                str(payload.get("first_message") or ""),
                _optional_str(payload.get("provider_name")),
                _optional_str(payload.get("model")),
            )
        )
    if len(segments) == 6 and segments[:2] == ["api", "sessions"] and segments[3] == "trace" and segments[5] == "replay":
        return JsonApiResult(
            {"error": "Execute replay requires Phase R4 (Permission & Safety Policy v2). Not yet available.", "phase_gate": "R4"},
            HTTPStatus.FORBIDDEN,
        )
    if len(segments) == 5 and segments[:2] == ["api", "sessions"] and segments[3] == "tool-permissions":
        return _payload_result(
            resolve_tool_permission_payload(manager, segments[2], segments[4], payload),
            "Permission request not found",
        )
    if len(segments) == 4 and segments[:2] == ["api", "sessions"] and segments[3] == "edit":
        session_id = segments[2]
        existing = manager.get_if_exists(session_id)
        if existing is None:
            return JsonApiResult({"error": "session not found"}, HTTPStatus.NOT_FOUND)
        raw_id = str(payload.get("message_id") or "")
        new_text = str(payload.get("new_text") or "").strip()
        if not raw_id or not new_text:
            return JsonApiResult({"error": "message_id and new_text are required"}, HTTPStatus.BAD_REQUEST)
        try:
            display_idx = int(raw_id.split("-", 1)[1]) if raw_id.startswith("msg-") else int(raw_id)
        except (ValueError, IndexError):
            return JsonApiResult({"error": "invalid message_id format"}, HTTPStatus.BAD_REQUEST)
        removed = existing.session.conversation.truncate_at_display_index(display_idx)
        if removed is None:
            return JsonApiResult({"error": "message not found"}, HTTPStatus.NOT_FOUND)
        existing.session.conversation.add_user_message(new_text)
        existing.save()
        return JsonApiResult({"ok": True, "session_id": session_id, "removed": removed})
    if len(segments) == 4 and segments[:2] == ["api", "sessions"] and segments[3] == "retry":
        session_id = segments[2]
        existing = manager.get_if_exists(session_id)
        if existing is None:
            return JsonApiResult({"error": "session not found"}, HTTPStatus.NOT_FOUND)
        last_user_text = existing.session.conversation.remove_last_assistant()
        if last_user_text is None:
            return JsonApiResult({"error": "no assistant message to retry"}, HTTPStatus.BAD_REQUEST)
        existing.save()
        return JsonApiResult({"ok": True, "session_id": session_id, "retry_text": last_user_text})
    if len(segments) == 4 and segments[:2] == ["api", "sessions"] and segments[3] == "stop":
        existing = manager.get_if_exists(segments[2])
        if existing is None:
            return JsonApiResult({"error": "session not found"}, HTTPStatus.NOT_FOUND)
        existing.cancel_current_turn()
        return JsonApiResult({"status": "cancelled"})
    if len(segments) == 4 and segments[:2] == ["api", "sessions"] and segments[3] == "amend":
        session_id = segments[2]
        existing = manager.get_if_exists(session_id)
        if existing is None:
            return JsonApiResult({"error": "session not found"}, HTTPStatus.NOT_FOUND)
        text = str(payload.get("text") or "").strip()
        if not text:
            return JsonApiResult({"error": "text is required"}, HTTPStatus.BAD_REQUEST)
        result = existing.amend_current_turn(text)
        status = HTTPStatus.OK if result["ok"] else HTTPStatus.CONFLICT
        return JsonApiResult(result, status)
    if path == "/api/command":
        request = CommandRequest(
            raw=str(payload.get("raw") or ""),
            session_id=_optional_str(payload.get("session_id")),
            provider_name=_optional_str(payload.get("provider_name")),
            model=_optional_str(payload.get("model")),
        )
        return JsonApiResult(execute_command(manager, request))
    if path == "/api/chat/stream":
        request, validation_error = chat_request_from_payload(payload)
        if validation_error is not None:
            return JsonApiResult(validation_error, HTTPStatus.BAD_REQUEST)
        return SseApiResult("chat", request)
    if path == "/api/research/stream":
        request, validation_error = research_request_from_payload(payload)
        if validation_error is not None:
            return JsonApiResult(validation_error, HTTPStatus.BAD_REQUEST)
        return SseApiResult("research", request)
    if path == "/api/research/runs":
        return _result_or_bad_request(create_research_run_payload(payload), "Invalid research run payload")
    if len(segments) == 5 and segments[:3] == ["api", "research", "runs"] and segments[4] == "complete":
        return _payload_result(complete_research_run_payload(segments[3], payload), "Research run not found")
    if len(segments) == 5 and segments[:3] == ["api", "research", "runs"] and segments[4] in {"stop", "resume", "fail"}:
        status = {"stop": "stopped", "resume": "running", "fail": "failed"}[segments[4]]
        return _payload_result(update_research_run_status_payload(segments[3], status, payload), "Research run not found")
    if path == "/api/research/plan":
        query = str(payload.get("query") or "").strip()
        session_id = payload.get("session_id") or None
        provider_name = payload.get("provider") or None
        model = payload.get("model") or None
        if not query:
            return JsonApiResult({"error": "query required"}, HTTPStatus.BAD_REQUEST)
        try:
            from src.geneva.research_engine import ResearchEngine

            engine = ResearchEngine(manager)
            plan = engine.generate_plan(query, session_id, provider_name, model)
            return JsonApiResult(plan)
        except Exception as exc:
            return JsonApiResult({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    # ── Plugins ──────────────────────────────────────────────────────────
    if len(segments) == 4 and segments[:2] == ["api", "plugins"] and segments[3] == "enable":
        name = segments[2]
        approved_scopes = payload.get("approved_scopes") or []
        if not isinstance(approved_scopes, list):
            approved_scopes = []
        try:
            from src.geneva.plugin_runtime import PluginRuntime

            PluginRuntime().enable(name, approved_scopes=approved_scopes)
            return JsonApiResult({"ok": True, "plugin": name, "action": "enabled"})
        except FileNotFoundError as exc:
            return _not_found(str(exc))
        except PermissionError as exc:
            return JsonApiResult({"error": str(exc)}, HTTPStatus.FORBIDDEN)
        except Exception as exc:
            return JsonApiResult({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    if len(segments) == 4 and segments[:2] == ["api", "plugins"] and segments[3] == "disable":
        name = segments[2]
        try:
            from src.geneva.plugin_runtime import PluginRuntime

            PluginRuntime().disable(name)
            return JsonApiResult({"ok": True, "plugin": name, "action": "disabled"})
        except FileNotFoundError as exc:
            return _not_found(str(exc))
        except Exception as exc:
            return JsonApiResult({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    if len(segments) == 4 and segments[:2] == ["api", "plugins"] and segments[3] == "rollback":
        name = segments[2]
        try:
            from src.geneva.plugin_runtime import PluginRuntime

            PluginRuntime().rollback(name)
            return JsonApiResult({"ok": True, "plugin": name, "action": "rolled_back"})
        except FileNotFoundError as exc:
            return _not_found(str(exc))
        except Exception as exc:
            return JsonApiResult({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    # ── Connectors ───────────────────────────────────────────────────────
    if len(segments) == 4 and segments[:2] == ["api", "connectors"] and segments[3] == "configure":
        name = segments[2]
        if name not in ("google", "notion", "github"):
            return _not_found(f"Connector '{name}' not found")
        try:
            if name == "google":
                from src.services.mcp.connectors.google import GoogleConnector

                GoogleConnector().configure(str(payload.get("api_key") or ""))
            elif name == "notion":
                from src.services.mcp.connectors.notion import NotionConnector

                NotionConnector().configure(str(payload.get("token") or ""))
            elif name == "github":
                from src.services.mcp.connectors.github import GitHubConnector

                GitHubConnector().configure(str(payload.get("token") or ""))
            return JsonApiResult({"ok": True, "connector": name, "action": "configured"})
        except Exception as exc:
            return JsonApiResult({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    if len(segments) == 4 and segments[:2] == ["api", "connectors"] and segments[3] == "trust":
        server_url = str(payload.get("url") or "").strip()
        label = str(payload.get("label") or "")
        if not server_url:
            return JsonApiResult(_validation_error("url is required"), HTTPStatus.BAD_REQUEST)
        from src.services.mcp.trust_policy import approve

        approve(server_url, label)
        return JsonApiResult({"ok": True, "url": server_url, "action": "trusted"})

    # ── Computer Use ─────────────────────────────────────────────────────
    if path == "/api/computer-use/execute":
        action_type = str(payload.get("action_type") or "").strip()
        target = str(payload.get("target") or "").strip()
        text = str(payload.get("text") or "")
        confirm_sensitive = bool(payload.get("confirm_sensitive", False))
        if not action_type:
            return JsonApiResult(_validation_error("action_type is required"), HTTPStatus.BAD_REQUEST)
        try:
            from src.geneva.computer_use_runtime import ComputerUseAction, ComputerUseRuntime, result_to_dict

            rt = ComputerUseRuntime()
            action = ComputerUseAction(
                action_type=action_type,
                target=target,
                text=text,
                confirm_sensitive=confirm_sensitive,
            )
            result = rt.execute(action)
            return JsonApiResult(result_to_dict(result))
        except Exception as exc:
            return JsonApiResult({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
    return _not_found("Not found")


def _dispatch_put(path: str, payload: dict[str, Any]) -> JsonApiResult:
    segments = _path_segments(path)
    if len(segments) == 3 and segments[:2] == ["api", "skills"]:
        return _payload_result(update_skill_payload(segments[2], payload), "Skill not found")
    if len(segments) == 3 and segments[:2] == ["api", "memory"]:
        return _payload_result(update_memory_payload(segments[2], payload), "Memory not found")
    if len(segments) == 3 and segments[:2] == ["api", "projects"]:
        return _payload_result(update_project_payload(segments[2], payload), "Project not found")
    if len(segments) == 5 and segments[:2] == ["api", "projects"] and segments[3] == "sources":
        return _payload_result(update_project_source_payload(segments[2], segments[4], payload), "Source not found")
    if len(segments) == 5 and segments[:2] == ["api", "projects"] and segments[3] == "todos":
        return _payload_result(update_todo_payload(segments[2], segments[4], payload), "Todo not found")
    return _not_found("Not found")


def _dispatch_delete(path: str) -> JsonApiResult:
    segments = _path_segments(path)
    if len(segments) == 3 and segments[:2] == ["api", "skills"]:
        payload = delete_skill_payload(segments[2])
        return JsonApiResult(payload) if payload.get("ok") else _not_found("Skill not found")
    if len(segments) == 3 and segments[:2] == ["api", "memory"]:
        return _payload_result(delete_memory_payload(segments[2]), "Memory not found")
    if len(segments) == 3 and segments[:2] == ["api", "projects"]:
        return _payload_result(delete_project_payload(segments[2]), "Project not found")
    if len(segments) == 5 and segments[:2] == ["api", "projects"] and segments[3] == "sources":
        return _payload_result(delete_project_source_payload(segments[2], segments[4]), "Source not found")
    if len(segments) == 5 and segments[:2] == ["api", "projects"] and segments[3] == "todos":
        return _payload_result(delete_todo_payload(segments[2], segments[4]), "Todo not found")
    if len(segments) == 3 and segments[:2] == ["api", "sessions"]:
        deleted = Session.delete(segments[2])
        if deleted:
            return JsonApiResult({"ok": True, "session_id": segments[2]})
        return _not_found("Session not found")
    if len(segments) == 3 and segments[:2] == ["api", "artifacts"]:
        from src.geneva.artifact_store import delete_artifact

        if delete_artifact(segments[2]):
            return JsonApiResult({"ok": True, "artifact_id": segments[2]})
        return _not_found("Artifact not found")

    # ── Plugins ──────────────────────────────────────────────────────────
    if len(segments) == 3 and segments[:2] == ["api", "plugins"]:
        name = segments[2]
        try:
            from src.geneva.plugin_runtime import PluginRuntime

            PluginRuntime().uninstall(name)
            return JsonApiResult({"ok": True, "plugin": name, "action": "uninstalled"})
        except FileNotFoundError as exc:
            return _not_found(str(exc))
        except ValueError as exc:
            return JsonApiResult({"error": str(exc)}, HTTPStatus.FORBIDDEN)
        except Exception as exc:
            return JsonApiResult({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    # ── Connectors ───────────────────────────────────────────────────────
    if len(segments) == 3 and segments[:2] == ["api", "connectors"]:
        name = segments[2]
        from src.services.mcp.credentials import delete_credential

        deleted = delete_credential(name)
        if not deleted:
            return _not_found(f"Connector '{name}' credentials not found")
        return JsonApiResult({"ok": True, "connector": name, "action": "credentials_deleted"})
    return _not_found("Not found")


def stream_sse_bytes(manager: SessionManager, result: SseApiResult):
    try:
        if result.kind == "chat":
            yield from _stream_chat(manager, result.request)
        else:
            yield from (event_to_sse(event) for event in research_events(manager, result.request))
    except Exception as exc:
        message = "Chat stream failed" if result.kind == "chat" else "Research stream failed"
        logger.error("%s SSE stream failed: %s", result.kind, type(exc).__name__)
        yield event_to_sse(stream_error_event(message))


def _stream_chat(manager: SessionManager, request: ChatRequest):
    onboarding_manager = current_onboarding_manager()
    completion_buffer = ""
    completed = False
    for event in chat_events(manager, request):
        if not completed:
            completion_buffer += _extract_text(event)
            payload = _extract_onboarding_payload(completion_buffer)
            if payload is not None:
                onboarding_manager.write_dna_files(payload)
                onboarding_manager.mark_complete()
                completed = True
        yield event_to_sse(event)


def stream_error_event(message: str) -> TurnStreamEvent:
    return TurnStreamEvent(
        turn_id="stream_error",
        event_seq=0,
        type="error",
        data={"message": message},
        timestamp=time.time(),
        error=ErrorInfo(
            code="internal_error",
            message=message,
            recoverable=True,
            suggestion="Retry the request.",
        ),
    )


def _extract_text(event: TurnStreamEvent | dict[str, Any]) -> str:
    data = event.data if isinstance(event, TurnStreamEvent) else event.get("data", {})
    if not isinstance(data, dict):
        return ""
    text = data.get("text")
    return str(text) if isinstance(text, str) else ""


def _extract_onboarding_payload(chunk: str) -> dict[str, Any] | None:
    marker = _ONBOARDING_COMPLETE_TOKEN
    marker_index = chunk.find(marker)
    if marker_index < 0:
        return None
    payload = chunk[marker_index + len(marker):].lstrip()
    if not payload:
        return None
    start = payload.find("{")
    if start < 0:
        return None
    json_candidate = _extract_json(payload[start:])
    if json_candidate is None:
        return None
    try:
        parsed = json.loads(json_candidate)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _extract_json(text: str) -> str | None:
    depth = 0
    in_string = False
    escape = False
    for index, char in enumerate(text):
        if in_string:
            if escape:
                escape = False
                continue
            if char == "\\":
                escape = True
                continue
            if char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[: index + 1]
    return None


def parse_json_request_body(raw: bytes) -> tuple[dict[str, Any], dict[str, Any] | None]:
    try:
        return parse_json_bytes(raw), None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}, _validation_error("Invalid JSON body")


def chat_request_from_payload(
    payload: dict[str, Any],
) -> tuple[ChatRequest | None, dict[str, Any] | None]:
    message = str(payload.get("message") or "").strip()
    if not message:
        return None, _validation_error("Chat message is required")
    raw_images = payload.get("images") or []
    images: list[dict[str, str]] = []
    if isinstance(raw_images, list):
        for img in raw_images:
            if isinstance(img, dict) and img.get("type") == "base64" and img.get("data"):
                images.append({
                    "type": "base64",
                    "media_type": str(img.get("media_type", "image/jpeg")),
                    "data": str(img["data"]),
                })
    return (
        ChatRequest(
            message=message,
            session_id=_optional_str(payload.get("session_id")),
            provider_name=_optional_str(payload.get("provider_name")),
            model=_optional_str(payload.get("model")),
            mode_id=_optional_str(payload.get("mode_id")),
            max_turns=_payload_int(payload, "max_turns", 100),
            project_id=_optional_str(payload.get("project_id")),
            ghost_mode=bool(payload.get("ghost_mode")),
            images=images,
        ),
        None,
    )


def research_request_from_payload(
    payload: dict[str, Any],
) -> tuple[ResearchRequest | None, dict[str, Any] | None]:
    query = str(payload.get("query") or "").strip()
    if not query:
        return None, _validation_error("Research query is required")
    return (
        ResearchRequest(
            query=query,
            session_id=_optional_str(payload.get("session_id")),
            provider_name=_optional_str(payload.get("provider_name")),
            model=_optional_str(payload.get("model")),
            project_id=_optional_str(payload.get("project_id")),
            ghost_mode=bool(payload.get("ghost_mode")),
            mode=normalize_research_mode(_optional_str(payload.get("mode"))),
        ),
        None,
    )



def _payload_result(payload: object | None, not_found_message: str) -> JsonApiResult:
    if payload is None:
        return _not_found(not_found_message)
    if is_validation_error(payload):
        return JsonApiResult(payload, HTTPStatus.BAD_REQUEST)
    return JsonApiResult(payload)


def _result_or_bad_request(payload: object | None, message: str) -> JsonApiResult:
    if payload is None:
        return JsonApiResult(_validation_error(message), HTTPStatus.BAD_REQUEST)
    if is_validation_error(payload):
        return JsonApiResult(payload, HTTPStatus.BAD_REQUEST)
    return JsonApiResult(payload)


def _result_or_not_found(payload: object | None, message: str) -> JsonApiResult:
    if payload is None:
        return _not_found(message)
    return JsonApiResult(payload)


def _not_found(message: str) -> JsonApiResult:
    return JsonApiResult({"ok": False, "error": message}, HTTPStatus.NOT_FOUND)


def _validation_error(message: str) -> dict[str, Any]:
    return {"ok": False, "error": message, "code": "validation_error"}


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _path_segments(path: str) -> list[str]:
    return [unquote(segment) for segment in path.strip("/").split("/") if segment]


def _normalize_query(query_string: str | dict[str, Any]) -> dict[str, list[str]]:
    if not isinstance(query_string, dict):
        return parse_qs(query_string, keep_blank_values=True)
    normalized: dict[str, list[str]] = {}
    for key, value in query_string.items():
        if isinstance(value, list):
            normalized[str(key)] = [str(item) for item in value]
        elif value is None:
            normalized[str(key)] = [""]
        else:
            normalized[str(key)] = [str(value)]
    return normalized


def _query_single(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    return values[0] if values else None


def _query_int(query: dict[str, list[str]], key: str, default: int) -> int:
    value = _query_single(query, key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _query_bool(query: dict[str, list[str]], key: str, default: bool = False) -> bool:
    value = _query_single(query, key)
    if value is None:
        return default
    val = value.lower()
    if val in ("1", "true", "yes"):
        return True
    if val in ("0", "false", "no"):
        return False
    return default


def _payload_int(payload: dict[str, Any], key: str, default: int) -> int:
    value = payload.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _bridge_files(value: object) -> list[tuple[str, str]] | None:
    if not isinstance(value, list):
        return None
    files: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "input.txt")
        content = str(item.get("content") or "")
        files.append((name, content))
    return files or None


def _health_check_payload() -> dict[str, Any]:
    import os
    import re
    import sqlite3

    from src.memdir.brain_engine import DB_PATH
    from src.geneva.settings_manager import load_settings

    checks: dict[str, str] = {}

    # Provider config
    try:
        cfg = load_settings()
        has_key = bool(
            cfg.anthropic_api_key
            or cfg.openrouter_api_key
            or os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("OPENROUTER_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
        )
        checks["provider"] = "ok" if has_key else "missing_api_key"
    except Exception as exc:
        checks["provider"] = f"error: {exc}"

    # DB
    schema_version: int | None = None
    try:
        db_path = Path(os.environ.get("GENEVA_BRAIN_DB_PATH", "") or DB_PATH)
        if db_path.exists():
            with sqlite3.connect(str(db_path)) as conn:
                conn.execute("SELECT 1").fetchone()
                row = conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()
                schema_version = int(row[0]) if row and row[0] is not None else 0
            checks["db"] = "ok"
        else:
            checks["db"] = "not_initialized"
    except Exception as exc:
        checks["db"] = f"error: {exc}"

    # Memory path
    try:
        memory_path = get_auto_mem_path(Path.cwd())
        checks["memory_path"] = "ok" if memory_path.exists() else "not_found"
    except Exception:
        checks["memory_path"] = "error"

    # Dream scheduler
    checks["dream_scheduler"] = "enabled" if os.environ.get("GENEVA_AUTO_DREAM") == "1" else "disabled"

    # Version from pyproject.toml
    try:
        toml = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
        match = re.search(r'version\s*=\s*"([^"]+)"', toml.read_text()) if toml.exists() else None
        version = match.group(1) if match else "unknown"
    except Exception:
        version = "unknown"

    bad = {k: v for k, v in checks.items() if not (v.startswith("ok") or v in ("enabled", "disabled"))}
    overall = "degraded" if bad else "ok"

    return {
        "status": overall,
        "version": version,
        "schema_version": schema_version,
        "checks": checks,
    }
