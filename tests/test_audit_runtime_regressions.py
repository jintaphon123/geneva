from __future__ import annotations

import asyncio
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Generator

from src.geneva.events import MemoryActivity
from src.memdir.brain_engine import remember, search
from src.agent.conversation import Conversation
from src.providers.base import BaseProvider, ChatResponse, MessageInput
from src.tool_system.agent_loop import run_agent_loop
from src.tool_system.context import ToolContext
from src.tool_system.protocol import ToolCall
from src.tool_system.registry import ToolRegistry
from src.tool_system.tools import FileReadTool


class _FakeProvider(BaseProvider):
    def __init__(self) -> None:
        super().__init__(api_key="", model="fake-model")
        self.messages: list[list[MessageInput]] = []

    def chat(
        self,
        messages: list[MessageInput],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        self.messages.append(messages)
        return ChatResponse(
            content="ghost answer",
            model=self.model or "fake-model",
            usage={"input_tokens": 1, "output_tokens": 1},
            finish_reason="stop",
            tool_uses=[],
        )

    def chat_stream(
        self,
        messages: list[MessageInput],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        yield "ghost answer"

    def chat_stream_response(
        self,
        messages: list[MessageInput],
        tools: list[dict[str, Any]] | None = None,
        on_text_chunk: Any | None = None,
        on_tool_ready: Any | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        self.messages.append(messages)
        if on_text_chunk is not None:
            on_text_chunk("ghost answer")
        return ChatResponse(
            content="ghost answer",
            model=self.model or "fake-model",
            usage={"input_tokens": 1, "output_tokens": 1},
            finish_reason="stop",
            tool_uses=[],
        )

    def get_available_models(self) -> list[str]:
        return [self.model or "fake-model"]


def _patch_runtime_env(monkeypatch: Any, tmp_path: Path) -> Path:
    root = tmp_path / "runtime"
    data_dir = root / "geneva"
    monkeypatch.setenv("HOME", str(root / "home"))
    monkeypatch.setenv("GENEVA_DATA_DIR", str(data_dir))
    monkeypatch.setenv("GENEVA_BRAIN_DB_PATH", str(root / "brain.db"))
    monkeypatch.setenv("GENEVA_MEMORY_EVENTS_DIR", str(root / "events"))
    monkeypatch.setenv("GENEVA_AUTO_MEM_PATH", str(data_dir / "memory"))
    monkeypatch.setenv("GENEVA_AGENT_TRACE_DIR", str(root / "agent-traces"))
    monkeypatch.setenv("GENEVA_AUDIT_LOG", str(root / "audit.jsonl"))
    monkeypatch.setenv("GENEVA_TOOL_PROFILE", "web_safe")
    return root


def test_soul_dna_and_brain_are_injected_into_turn_context(monkeypatch: Any, tmp_path: Path) -> None:
    root = _patch_runtime_env(monkeypatch, tmp_path)
    data_dir = root / "geneva"
    context_dir = data_dir / "context"
    context_dir.mkdir(parents=True)
    (data_dir / "soul.md").write_text(
        "---\nversion: 1\n---\n\n# Soul\nBond is the owner of Geneva.\n",
        encoding="utf-8",
    )
    (data_dir / "BRAIN.md").write_text(
        "# BRAIN\nGeneva must behave as Bond's co-founder brain.\n",
        encoding="utf-8",
    )
    (context_dir / "me.md").write_text("# me\nname: Bond\nrole: KU ME student\n", encoding="utf-8")
    (context_dir / "team.md").write_text("# team\n- Mother handles condo ops\n", encoding="utf-8")

    from src.geneva.session import GenevaSession

    session = GenevaSession(provider_name="openrouter", model="openrouter/free", workspace_root=tmp_path)
    session.provider = _FakeProvider()

    block = session._build_memory_block("ฉันชื่ออะไร", persist_ledger=False)

    assert "Soul — Identity Contract" in block
    assert "Bond is the owner of Geneva" in block
    assert "BRAIN" in block
    assert "co-founder brain" in block
    assert "name: Bond" in block
    assert "Mother handles condo ops" in block

    latest = session.get_context_ledger()["latest"]
    labels = {entry["label"] for entry in latest["entries"]}
    assert "Soul — Identity Contract" in labels
    assert "BRAIN — Runtime Contract" in labels
    assert "DNA — Owner Context" in labels


def test_identity_extraction_saves_short_user_name_but_not_assistant_claim(monkeypatch: Any, tmp_path: Path) -> None:
    _patch_runtime_env(monkeypatch, tmp_path)
    from src.services.extract_memories.extract_memories import run_extraction

    asyncio.run(
        run_extraction(
            {
                "session_id": "identity-session",
                "user_request": "ฉันชื่อ Bond",
                "messages": [
                    {"role": "user", "content": "ฉันชื่อ Bond"},
                    {"role": "assistant", "content": "ฉันชื่อ Geneva"},
                ],
            }
        )
    )

    bond = search("Bond", type="user")
    geneva = search("Geneva", type="user")

    assert any("Bond" in memory.content and memory.memory_kind == "identity" for memory in bond)
    assert not any("Geneva" in memory.content and memory.memory_kind == "identity" for memory in geneva)


def test_session_memory_extraction_path_saves_short_identity(monkeypatch: Any, tmp_path: Path) -> None:
    _patch_runtime_env(monkeypatch, tmp_path)
    from src.geneva.session import GenevaSession

    session = GenevaSession(provider_name="openrouter", model="openrouter/free", workspace_root=tmp_path)
    session.provider = _FakeProvider()
    session.session.conversation.add_user_message("ฉันชื่อ Bond")

    session._run_memory_extraction("ฉันชื่อ Bond", turn_id="turn_identity")

    results = search("Bond", type="user")
    assert any(memory.memory_kind == "identity" and "Bond" in memory.content for memory in results)


def test_stream_turn_complete_does_not_wait_for_post_turn_memory(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    _patch_runtime_env(monkeypatch, tmp_path)
    from src.geneva.session import GenevaSession

    session = GenevaSession(provider_name="openrouter", model="openrouter/free", workspace_root=tmp_path)
    session.provider = _FakeProvider()
    memory_started = threading.Event()
    memory_finished = threading.Event()

    def slow_capture(**_kwargs: Any) -> tuple[MemoryActivity, None]:
        memory_started.set()
        time.sleep(0.45)
        memory_finished.set()
        return (
            MemoryActivity(
                session_id=session.session_id,
                timestamp=time.time(),
                action="NOOP",
                title="Auto memory extraction",
            ),
            None,
        )

    monkeypatch.setattr(session, "_capture_memory_after_turn", slow_capture)
    monkeypatch.setattr(session, "_persist_agent_trace", lambda **_kwargs: None)
    monkeypatch.setattr(session, "_run_auto_dream_check", lambda: None)

    started = time.perf_counter()
    events = list(session.chat_stream("ตอบเร็วๆ", memory_enabled=True))
    elapsed = time.perf_counter() - started

    event_types = [event.type for event in events]
    assert "turn_complete" in event_types
    assert event_types.index("turn_complete") < event_types.index("memory_update") if "memory_update" in event_types else True
    assert elapsed < 0.35
    assert memory_started.wait(timeout=0.2)
    assert memory_finished.wait(timeout=1.0)


def test_thai_identity_question_retrieves_identity_memory(monkeypatch: Any, tmp_path: Path) -> None:
    _patch_runtime_env(monkeypatch, tmp_path)

    asyncio.run(
        remember(
            "ผู้ใช้ชื่อ Bond และเป็นนักศึกษา KU",
            "user",
            source_type="user_direct",
            memory_kind="identity",
        )
    )

    results = search("ฉันชื่ออะไร", type="user")

    assert any("Bond" in memory.content for memory in results)


def test_ghost_mode_does_not_persist_session_transcript_or_trace(monkeypatch: Any, tmp_path: Path) -> None:
    root = _patch_runtime_env(monkeypatch, tmp_path)
    from src.geneva.session import GenevaSession

    session = GenevaSession(provider_name="openrouter", model="openrouter/free", workspace_root=tmp_path)
    session.provider = _FakeProvider()
    session_id = session.session_id

    events = list(session.chat_stream("secret ghost turn", memory_enabled=False, ghost_mode=True))

    assert events[-1].type == "turn_complete"
    assert session.session.conversation.messages == []
    latest = session.get_context_ledger()["latest"]
    assert any(entry["source_type"] == "ghost_privacy_contract" for entry in latest["entries"])
    assert not (root / "home" / ".geneva" / "sessions" / f"{session_id}.json").exists()
    assert not (root / "agent-traces" / f"{session_id}.jsonl").exists()

    with sqlite3.connect(root / "brain.db") as conn:
        rows = conn.execute(
            "SELECT content FROM session_transcripts WHERE session_id = ?",
            (session_id,),
        ).fetchall()
    assert rows == []


def test_read_tool_prefixes_text_as_untrusted(tmp_path: Path) -> None:
    p = tmp_path / "notes.txt"
    p.write_text("name: Bond\n", encoding="utf-8")
    result = FileReadTool().run({"file_path": str(p), "limit": 10}, ToolContext(workspace_root=tmp_path))

    assert result.output["file"]["content"].startswith("[UNTRUSTED SOURCE]")
    assert "1\tname: Bond" in result.output["file"]["content"]


def test_lsp_tool_is_not_registered_without_a_client() -> None:
    from src.tool_system.defaults import build_default_registry

    registry = build_default_registry(profile="power_harness")

    assert registry.spec_for("LSP") is None


def test_onboarding_does_not_overwrite_existing_dna_by_default(tmp_path: Path) -> None:
    from src.geneva.onboarding import OnboardingManager

    memory_root = tmp_path / "memory"
    memory_root.mkdir()
    (memory_root / "me.md").write_text("# me\nname: Existing Bond\n", encoding="utf-8")

    OnboardingManager(memory_root).write_dna_files({"name": "New Name", "role": "New Role"})

    assert (memory_root / "me.md").read_text(encoding="utf-8") == "# me\nname: Existing Bond\n"


def test_onboarding_uses_canonical_data_dir_for_soul_and_context_dna(monkeypatch: Any, tmp_path: Path) -> None:
    root = _patch_runtime_env(monkeypatch, tmp_path)
    data_dir = root / "geneva"

    from src.geneva.onboarding import current_onboarding_manager

    manager = current_onboarding_manager()
    manager.write_dna_files({"name": "Bond", "role": "Founder", "timezone": "ICT"})

    assert (data_dir / "soul.md").exists()
    assert (data_dir / "context" / "me.md").exists()
    assert not (data_dir / "memory" / "me.md").exists()


def test_onboarding_status_reads_existing_canonical_context_dna(monkeypatch: Any, tmp_path: Path) -> None:
    root = _patch_runtime_env(monkeypatch, tmp_path)
    context_dir = root / "geneva" / "context"
    context_dir.mkdir(parents=True)
    (context_dir / "me.md").write_text("\n".join(f"line {i}" for i in range(12)), encoding="utf-8")

    from src.geneva.onboarding import current_onboarding_manager

    assert current_onboarding_manager().needs_onboarding() is False


def test_refresh_context_uses_runtime_identity_loader(monkeypatch: Any, tmp_path: Path) -> None:
    _patch_runtime_env(monkeypatch, tmp_path)
    from src.geneva.runtime_identity import RuntimeIdentityBlock
    from src.memdir.brain_engine import refresh_context

    def fake_identity_blocks() -> list[RuntimeIdentityBlock]:
        return [
            RuntimeIdentityBlock(
                source_type="soul_identity",
                label="Soul — Identity Contract",
                text="## Soul — Identity Contract\nCANONICAL_IDENTITY_BLOCK",
                reason="test",
                metadata={"path": "test"},
            )
        ]

    monkeypatch.setattr("src.geneva.runtime_identity.load_runtime_identity_blocks", fake_identity_blocks)

    context = refresh_context("who is Bond?", max_tokens=1000, include_identity_files=True)

    assert "CANONICAL_IDENTITY_BLOCK" in context


def test_query_engine_uses_llm_memory_extraction_when_available(monkeypatch: Any, tmp_path: Path) -> None:
    _patch_runtime_env(monkeypatch, tmp_path)
    from src.query_engine import QueryEnginePort
    from src.port_manifest import build_port_manifest

    calls: list[str] = []

    async def fake_agent(prompt: str) -> str:
        calls.append(prompt)
        return (
            '[{"type":"user","content":"User preference: Bond wants calm memory UX.",'
            '"memory_kind":"preference","evidence_quote":"memory UX",'
            '"sensitivity":"private"}]'
        )

    engine = QueryEnginePort(manifest=build_port_manifest(), extraction_agent_caller=fake_agent)
    engine.submit_message("บันทึกไว้ว่า memory UX ต้องนิ่งและไม่ลืม")

    assert calls
    assert any("calm memory UX" in memory.content for memory in search("calm memory UX", type="user"))


def test_repl_memory_extraction_uses_llm_agent_caller(monkeypatch: Any, tmp_path: Path) -> None:
    _patch_runtime_env(monkeypatch, tmp_path)
    from src.agent.conversation import Conversation
    from src.repl.core import GenevaREPL
    from src.utils.asyncio_tools import run_awaitable_sync

    calls: list[str] = []

    def fake_agent(prompt: str) -> str:
        calls.append(prompt)
        return (
            '[{"type":"user","content":"User preference: Bond wants durable context parity.",'
            '"memory_kind":"preference","evidence_quote":"context parity",'
            '"sensitivity":"private"}]'
        )

    repl = object.__new__(GenevaREPL)
    repl.session = type(
        "FakeSession",
        (),
        {"session_id": "repl-memory", "conversation": Conversation()},
    )()
    repl.session.conversation.add_user_message("จำไว้ว่า context parity ต้องแข็ง")
    repl._run_async_blocking = run_awaitable_sync
    repl._call_memory_extraction_agent = fake_agent

    GenevaREPL._run_memory_extraction(repl, "จำไว้ว่า context parity ต้องแข็ง")

    assert calls
    assert any("durable context parity" in memory.content for memory in search("durable context parity", type="user"))


def test_high_confidence_user_correction_supersedes_lower_confidence_memory(monkeypatch: Any, tmp_path: Path) -> None:
    _patch_runtime_env(monkeypatch, tmp_path)

    original = asyncio.run(
        remember(
            "User preference: Bond prefers dark blue dashboards.",
            "user",
            source_type="assistant_inferred",
            memory_kind="preference",
            confidence=0.55,
            evidence_quote="inferred from prior UI work",
        )
    )
    correction = asyncio.run(
        remember(
            "Correction: User preference: Bond prefers calm neutral dashboards instead of dark blue dashboards.",
            "user",
            source_type="user_direct",
            memory_kind="preference",
            confidence=0.95,
            evidence_quote="Actually use calm neutral dashboards",
        )
    )

    assert correction.operation == "supersede"
    assert correction.memory_id != original.memory_id
    active = search("calm neutral dashboards", type="user")
    old = search("dark blue dashboards", type="user", include_archived=True)
    assert any(memory.id == correction.memory_id and memory.status == "active" for memory in active)
    assert any(memory.id == original.memory_id and memory.status == "superseded" for memory in old)


def test_restricted_memory_conflict_still_requires_review(monkeypatch: Any, tmp_path: Path) -> None:
    _patch_runtime_env(monkeypatch, tmp_path)

    asyncio.run(
        remember(
            "User identity: Bond's private legal name is Alpha.",
            "user",
            source_type="user_direct",
            memory_kind="identity",
            confidence=0.55,
            sensitivity="restricted",
            evidence_quote="private legal name is Alpha",
        )
    )
    correction = asyncio.run(
        remember(
            "Correction: User identity: Bond's private legal name is Beta, not Alpha.",
            "user",
            source_type="user_direct",
            memory_kind="identity",
            confidence=0.95,
            sensitivity="restricted",
            evidence_quote="private legal name is Beta",
        )
    )

    assert correction.operation == "conflict"


def test_tool_audit_logs_start_and_result(monkeypatch: Any, tmp_path: Path) -> None:
    from src.geneva import audit_log

    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(audit_log, "AUDIT_LOG_PATH", audit_path)
    p = tmp_path / "notes.txt"
    p.write_text("hello\n", encoding="utf-8")

    registry = ToolRegistry([FileReadTool()])
    registry.dispatch(ToolCall(name="Read", input={"file_path": str(p), "limit": 10}), ToolContext(workspace_root=tmp_path))

    entries = audit_log.search_audit_log(tool_name="Read")
    outcomes = [entry["outcome"] for entry in entries]
    assert "start" in outcomes
    assert "allow" in outcomes


def test_active_project_turn_updates_blast_progress_and_decisions(monkeypatch: Any, tmp_path: Path) -> None:
    root = _patch_runtime_env(monkeypatch, tmp_path)
    from src.geneva.blast_writer import create_blast_docs
    from src.geneva.project_store import ProjectStore
    from src.geneva.session import GenevaSession

    store = ProjectStore()
    project = store.create_project("Runtime BLAST")
    create_blast_docs(project.id, project.name)

    session = GenevaSession(provider_name="openrouter", model="openrouter/free", workspace_root=tmp_path)
    session.set_project_context("# Runtime BLAST", project.id)
    session._log_project_activity(
        user_input="ตัดสินใจใช้ SQLite เป็น memory backend",
        assistant_text="รับทราบ",
    )

    blast_root = root / "projects" / project.id
    assert "ตัดสินใจใช้ SQLite" in (blast_root / "progress.md").read_text(encoding="utf-8")
    assert "ตัดสินใจใช้ SQLite" in (blast_root / "decisions.md").read_text(encoding="utf-8")


def test_intent_routing_add_todo_writes_project_todo(monkeypatch: Any, tmp_path: Path) -> None:
    _patch_runtime_env(monkeypatch, tmp_path)
    from src.geneva.project_store import ProjectStore
    from src.geneva.session import GenevaSession

    store = ProjectStore()
    project = store.create_project("Todo Project")
    session = GenevaSession(provider_name="openrouter", model="openrouter/free", workspace_root=tmp_path)
    session.set_project_context("# Todo Project", project.id)

    session._handle_intent_routing("อย่าลืม deploy staging")

    updated = ProjectStore().get_project(project.id)
    assert updated is not None
    assert any("deploy staging" in todo.text for todo in updated.todos)


def test_session_manager_starts_auto_dream_scheduler(monkeypatch: Any, tmp_path: Path) -> None:
    _patch_runtime_env(monkeypatch, tmp_path)
    calls: list[Any] = []

    from src.services.auto_dream import auto_dream

    def fake_start_dream_scheduler(*, agent_caller: Any, memory_dir: Path | None = None) -> None:
        calls.append(agent_caller)

    monkeypatch.setattr(auto_dream, "start_dream_scheduler", fake_start_dream_scheduler)
    from src.geneva.web_runtime import SessionManager

    SessionManager()

    assert calls


def test_agent_loop_records_tool_outcome(monkeypatch: Any, tmp_path: Path) -> None:
    p = tmp_path / "notes.txt"
    p.write_text("hello\n", encoding="utf-8")
    outcomes: list[tuple[str, bool]] = []

    class ToolUseProvider(_FakeProvider):
        def __init__(self) -> None:
            super().__init__()
            self.calls = 0
            self.model = "fake-outcome-model"

        def chat(
            self,
            messages: list[MessageInput],
            tools: list[dict[str, Any]] | None = None,
            **kwargs: Any,
        ) -> ChatResponse:
            self.calls += 1
            if self.calls == 1:
                return ChatResponse(
                    content="",
                    model=self.model or "fake-outcome-model",
                    usage={},
                    finish_reason="tool_use",
                    tool_uses=[{"id": "toolu_1", "name": "Read", "input": {"file_path": str(p), "limit": 10}}],
                )
            return ChatResponse(content="done", model=self.model or "fake-outcome-model", usage={}, finish_reason="stop")

    monkeypatch.setattr(
        "src.tool_system.agent_loop.record_outcome",
        lambda model, success: outcomes.append((model, success)),
    )
    conversation = Conversation()
    conversation.add_user_message("read notes")

    result = run_agent_loop(
        conversation=conversation,
        provider=ToolUseProvider(),
        tool_registry=ToolRegistry([FileReadTool()]),
        tool_context=ToolContext(workspace_root=tmp_path),
        max_turns=3,
    )

    assert result.response_text == "done"
    assert ("fake-outcome-model", True) in outcomes


def test_llm_extraction_preserves_memory_metadata(monkeypatch: Any, tmp_path: Path) -> None:
    _patch_runtime_env(monkeypatch, tmp_path)
    from src.services.extract_memories.extract_memories import run_extraction

    async def fake_agent(_prompt: str) -> str:
        return (
            '[{"type":"user","content":"User identity: name is Bond.",'
            '"memory_kind":"identity","evidence_quote":"ฉันชื่อ Bond",'
            '"sensitivity":"restricted","validity_window_days":30}]'
        )

    asyncio.run(
        run_extraction(
            {"session_id": "meta-session", "messages": [{"role": "user", "content": "ฉันชื่อ Bond"}]},
            agent_caller=fake_agent,
        )
    )

    results = search("Bond", type="user", include_archived=True)
    assert results
    memory = results[0]
    assert memory.memory_kind == "identity"
    assert memory.evidence_quote == "ฉันชื่อ Bond"
    assert memory.sensitivity == "restricted"
    assert memory.validity_window_days == 30


def test_memory_block_decomposes_complex_thai_intent(monkeypatch: Any, tmp_path: Path) -> None:
    _patch_runtime_env(monkeypatch, tmp_path)
    calls: list[dict[str, Any]] = []

    def fake_decompose_intent(user_input: str, session_id: str, llm_caller: Any | None = None, project_id: str | None = None) -> None:
        calls.append({"user_input": user_input, "session_id": session_id, "project_id": project_id})

    monkeypatch.setattr("src.geneva.task_planner.decompose_intent", fake_decompose_intent)
    from src.geneva.session import GenevaSession

    session = GenevaSession(provider_name="openrouter", model="openrouter/free", workspace_root=tmp_path)
    session.provider = _FakeProvider()

    session._build_memory_block("ช่วยไล่แก้ตั้งแต่ phase 0 จนถึงปัจจุบันทั้งหมดอย่างละเอียด", persist_ledger=False)

    assert calls
