from __future__ import annotations

from src.geneva.web_api import JsonApiResult, dispatch_api_request


def _ledger_record(*, turn_id: str = "turn_1", ghost_mode: bool = False) -> dict[str, object]:
    return {
        "id": "ctx_1",
        "session_id": "session_1",
        "event": "turn_context",
        "model": "haiku-test",
        "created_at": "2026-05-20T00:00:00+00:00",
        "metadata": {"turn_id": turn_id, "ghost_mode": ghost_mode},
        "budget": {"percent_used": 0.12},
        "entries": [
            {
                "source_type": "project_context",
                "action": "included",
                "label": "Active project context",
                "tokens_before": 120,
                "tokens_after": 120,
                "metadata": {"project_id": "project_1", "project_name": "Geneva"},
            },
            {
                "source_type": "memory_context",
                "action": "included",
                "label": "Memory context",
                "tokens_before": 340,
                "tokens_after": 340,
                "metadata": {"memory_count": 3},
            },
            {
                "source_type": "skill_context",
                "action": "included",
                "label": "Active skill: consult",
                "tokens_before": 80,
                "tokens_after": 80,
                "metadata": {"skill_name": "consult"},
            },
            {
                "source_type": "assembled_extra_system_prompt",
                "action": "included",
                "label": "Final injected context block",
                "tokens_before": 540,
                "tokens_after": 540,
            },
        ],
    }


def test_context_summary_turns_ledger_into_user_facing_counts() -> None:
    from src.geneva.context_disclosure import build_context_summary

    summary = build_context_summary(
        _ledger_record(),
        tool_events=[{"tool_name": "WebSearch", "status": "complete"}],
    )

    assert summary["turn_id"] == "turn_1"
    assert summary["summary"] == "Used Geneva project · 3 memories · /consult · 1 tool"
    assert summary["counts"]["projects"] == 1
    assert summary["counts"]["memories"] == 3
    assert summary["counts"]["skills"] == 1
    assert summary["counts"]["tools"] == 1
    assert summary["ghost_mode"] is False
    assert summary["no_memory_write"] is False


def test_context_summary_proves_ghost_mode_no_memory_write() -> None:
    from src.geneva.context_disclosure import build_context_summary

    record = _ledger_record(ghost_mode=True)
    record["entries"] = [
        *record["entries"],
        {
            "source_type": "ghost_privacy_contract",
            "action": "included",
            "label": "Ghost Mode Privacy Contract",
            "tokens_before": 40,
            "tokens_after": 40,
        },
    ]
    summary = build_context_summary(record)

    assert summary["ghost_mode"] is True
    assert summary["no_memory_write"] is True
    assert "Ghost mode" in summary["summary"]


def test_api_dispatcher_exposes_turn_context_summary() -> None:
    class _Manager:
        def context_ledger(self, session_id: str | None = None, limit: int = 50) -> dict[str, object]:
            return {"session_id": session_id, "records": [_ledger_record(turn_id="turn_api")]}

    result = dispatch_api_request(
        _Manager(),  # type: ignore[arg-type]
        "GET",
        "/api/sessions/session_1/turns/turn_api/context-summary",
    )

    assert isinstance(result, JsonApiResult)
    assert result.payload["context_summary"]["turn_id"] == "turn_api"  # type: ignore[index]
    assert result.payload["context_summary"]["counts"]["memories"] == 3  # type: ignore[index]
