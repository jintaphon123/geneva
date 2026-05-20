"""Phase 8.5 — Release Gates: Go/No-Go checklist for Layer 0.

Each test validates one Go/No-Go criterion from GENEVA_ROADMAP.md.
Run before any production release: python -m pytest tests/smoke/ -v
"""
from __future__ import annotations

import importlib
import os
import sqlite3
from pathlib import Path


# ── Gate 1: DNA/Soul context loads ───────────────────────────────────────────

def test_soul_context_loads():
    """DNA kernel loads without error."""
    from src.memdir.memdir import load_memory_prompt
    prompt = load_memory_prompt(Path.cwd())
    assert isinstance(prompt, str)


def test_memory_db_initialises():
    """Brain DB initialises without error; schema_migrations table exists."""
    from src.memdir.brain_engine import init_db, DB_PATH
    init_db()
    db_path = Path(os.environ.get("GENEVA_BRAIN_DB_PATH", "") or DB_PATH)
    assert db_path.exists(), "brain.db was not created"
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
    assert len(rows) >= 1, "no schema migrations found"


# ── Gate 2: Tool system ───────────────────────────────────────────────────────

def test_tool_spec_dataclass():
    """ToolSpec dataclass has required fields including new is_concurrency_safe."""
    from src.tool_system.registry import ToolSpec
    spec = ToolSpec(name="Test", description="test", input_schema={})
    assert spec.name == "Test"
    assert spec.timeout_seconds > 0
    assert hasattr(spec, "is_concurrency_safe")
    assert hasattr(spec, "is_read_only")
    assert hasattr(spec, "is_destructive")


def test_concurrency_safe_tools():
    """Read, Glob, Grep, WebFetch, WebSearch source files have is_concurrency_safe=True."""
    tools_dir = Path(__file__).parent.parent.parent / "src" / "tool_system" / "tools"
    for tool_name in ("read", "glob", "grep", "web_fetch", "web_search"):
        source = (tools_dir / f"{tool_name}.py").read_text()
        assert "is_concurrency_safe=True" in source, f"{tool_name}.py missing is_concurrency_safe=True"


# ── Gate 3: Memory substrate ──────────────────────────────────────────────────

def test_memory_evidence_fields_exist():
    """Memory dataclass has Phase 3 evidence fields."""
    from src.memdir.memory_models import Memory
    fields = {f for f in Memory.__dataclass_fields__}
    assert "evidence_quote" in fields
    assert "sensitivity" in fields
    assert "validity_window_days" in fields


def test_memory_schema_v3_migration():
    """Schema migration adds evidence columns to memories table."""
    from src.memdir.brain_engine import init_db, DB_PATH
    init_db()
    db_path = Path(os.environ.get("GENEVA_BRAIN_DB_PATH", "") or DB_PATH)
    with sqlite3.connect(str(db_path)) as conn:
        # PRAGMA returns tuples: (cid, name, type, notnull, dflt_value, pk)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(memories)").fetchall()}
    assert "evidence_quote" in cols, "missing evidence_quote column"
    assert "sensitivity" in cols, "missing sensitivity column"
    assert "validity_window_days" in cols, "missing validity_window_days column"


# ── Gate 4: Runtime safety ────────────────────────────────────────────────────

def test_wal_functions_exist():
    """GenevaSession has _write_turn_wal and _clear_turn_wal."""
    from src.geneva.session import GenevaSession
    assert hasattr(GenevaSession, "_write_turn_wal")
    assert hasattr(GenevaSession, "_clear_turn_wal")


def test_cancel_token_available():
    """GenevaSession exposes cancel_current_turn."""
    from src.geneva.session import GenevaSession
    assert hasattr(GenevaSession, "cancel_current_turn")


# ── Gate 5: Provider error handling ──────────────────────────────────────────

def test_public_error_info_maps_common_errors():
    """public_error_info produces user-safe error envelopes."""
    from src.geneva.events import public_error_info
    for msg in ("rate limit", "authentication", "network", "timeout"):
        info = public_error_info(msg)
        assert info.code in {
            "rate_limit", "auth_error", "quota_error",
            "network_error", "timeout", "internal_error",
        }
        assert info.message
        assert isinstance(info.recoverable, bool)


def test_model_normalizer_imports():
    """Model normalizer + router export all required symbols."""
    from src.services.model_normalizer import (
        get_capability,
        get_compensation_config,
        adapt_tool_schemas,
        repair_tool_call_json,
        extract_json_from_response,
    )
    from src.services.model_router import classify_model_tier
    # Haiku → medium tier
    assert classify_model_tier("claude-haiku-4-5") == "medium"
    # Sonnet → strong tier
    assert classify_model_tier("claude-sonnet-4-6") == "strong"


# ── Gate 6: Trace + observability ────────────────────────────────────────────

def test_health_endpoint_returns_ok():
    """_health_check_payload returns status=ok or status=degraded (never crashes)."""
    from src.geneva.web_api import _health_check_payload
    payload = _health_check_payload()
    assert payload["status"] in ("ok", "degraded")
    assert "checks" in payload
    assert "version" in payload


def test_agent_trace_append_and_read():
    """Agent trace append + read round-trip works."""
    import tempfile
    from src.geneva.agent_trace import append_trace_record, list_trace_records, trace_path
    session_id = "smoke-test-trace-001"
    record = {"session_id": session_id, "turn_id": "t1", "trace_id": "t1", "test": True}
    old_dir = os.environ.get("GENEVA_AGENT_TRACE_DIR")
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["GENEVA_AGENT_TRACE_DIR"] = tmp
        try:
            append_trace_record(record)
            records = list_trace_records(session_id)
            assert len(records) >= 1
            assert records[-1].get("trace_id") == "t1"
        finally:
            if old_dir is None:
                os.environ.pop("GENEVA_AGENT_TRACE_DIR", None)
            else:
                os.environ["GENEVA_AGENT_TRACE_DIR"] = old_dir


# ── Gate 7: Background brain ─────────────────────────────────────────────────

def test_skill_nudge_tracks_patterns():
    """record_workflow_pattern triggers nudge after 3+ repeats."""
    from src.services.auto_dream.auto_dream import record_workflow_pattern, get_skill_nudge_suggestions
    for _ in range(3):
        record_workflow_pattern(["smoke_tool_a", "smoke_tool_b"])
    suggestions = get_skill_nudge_suggestions()
    assert any("smoke_tool_a" in s or "smoke_tool_b" in s for s in suggestions)


def test_dream_report_in_consolidation_prompt():
    """build_consolidation_prompt includes dream_report format when skill suggestions provided."""
    from src.services.auto_dream.consolidation_prompt import build_consolidation_prompt
    prompt = build_consolidation_prompt([], Path.home(), skill_suggestions=["bash + read x3"])
    assert "dream_report" in prompt
    assert "recommendations" in prompt


# ── Gate 8: Observability ────────────────────────────────────────────────────

def test_structured_log_json_formatter():
    """JsonFormatter emits valid JSON with required fields."""
    import json
    import logging
    from src.geneva.structured_log import JsonFormatter
    fmt = JsonFormatter()
    record = logging.LogRecord("test.logger", logging.WARNING, "", 0, "test msg", [], None)
    output = fmt.format(record)
    parsed = json.loads(output)
    assert parsed["level"] == "WARNING"
    assert parsed["message"] == "test msg"
    assert "timestamp" in parsed
    assert "logger" in parsed


def test_backup_command_importable():
    """backup.py registers the /backup command."""
    import importlib
    mod = importlib.import_module("src.commands.backup")
    assert hasattr(mod, "run")
    assert hasattr(mod, "_create")
    assert hasattr(mod, "_list")
    assert hasattr(mod, "_restore")
