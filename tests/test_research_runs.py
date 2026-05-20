from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch


def _patch_geneva_paths(monkeypatch: Any, tmp_path: Path) -> Path:
    db_path = tmp_path / "brain.db"
    monkeypatch.setenv("GENEVA_BRAIN_DB_PATH", str(db_path))
    monkeypatch.setenv("GENEVA_DATA_DIR", str(tmp_path / "data"))
    return db_path


def _source_payload() -> list[dict[str, Any]]:
    return [
        {
            "id": "S1",
            "title": "Primary Source",
            "url": "https://example.com/source",
            "query": "geneva source",
            "credibility_tier": 1,
            "fetched": True,
            "content_preview": "Source evidence text",
        }
    ]


def test_research_run_store_completes_with_sources_and_report_artifact(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _patch_geneva_paths(monkeypatch, tmp_path)

    from src.geneva.artifact_store import get_artifact
    from src.geneva.research_runs import ResearchRunStore

    store = ResearchRunStore()
    run = store.create_run(
        query="Geneva source model",
        session_id="session-1",
        project_id="project-1",
        mode="deep",
        plan={"title": "Plan", "steps": ["Search", "Synthesize"]},
    )

    assert run["status"] == "draft_plan"
    assert run["artifact_id"] is None

    completed = store.complete_run(
        run["id"],
        final_text="Final research report with [S1].",
        sources=_source_payload(),
        quality_score={"label": "high", "value": 88},
        trace=[{"label": "Synthesis", "done": True}],
    )

    assert completed is not None
    assert completed["status"] == "completed"
    assert completed["artifact_id"]
    assert completed["final_text"] == "Final research report with [S1]."
    assert completed["metadata"]["quality_score"]["label"] == "high"
    assert completed["sources"][0]["title"] == "Primary Source"
    assert completed["sources"][0]["used_in_report"] is True

    artifact = get_artifact(completed["artifact_id"])
    assert artifact is not None
    assert artifact["type"] == "research_report"
    assert "Final research report" in str(artifact.get("content") or "")


def test_failed_research_run_does_not_create_report_artifact(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _patch_geneva_paths(monkeypatch, tmp_path)

    from src.geneva.research_runs import ResearchRunStore

    store = ResearchRunStore()
    run = store.create_run(query="broken research", session_id="session-1", mode="quick")
    failed = store.fail_run(run["id"], "search failed")

    assert failed is not None
    assert failed["status"] == "failed"
    assert failed["error"] == "search failed"
    assert failed["artifact_id"] is None
    assert failed["sources"] == []


def test_research_run_api_creates_gets_and_completes_run(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _patch_geneva_paths(monkeypatch, tmp_path)

    from src.geneva.web_api import JsonApiResult, dispatch_api_request
    from src.geneva.web_runtime import SessionManager

    manager = SessionManager.__new__(SessionManager)
    created = dispatch_api_request(
        manager,
        "POST",
        "/api/research/runs",
        payload={
            "query": "Geneva research runs",
            "session_id": "session-1",
            "project_id": "project-1",
            "mode": "deep",
            "plan": {"title": "Plan", "steps": ["Search"]},
        },
    )

    assert isinstance(created, JsonApiResult)
    run_id = created.payload["run"]["id"]  # type: ignore[index]
    assert created.payload["run"]["status"] == "draft_plan"  # type: ignore[index]

    fetched = dispatch_api_request(manager, "GET", f"/api/research/runs/{run_id}")
    assert fetched.payload["run"]["query"] == "Geneva research runs"  # type: ignore[index]

    completed = dispatch_api_request(
        manager,
        "POST",
        f"/api/research/runs/{run_id}/complete",
        payload={
            "text": "Completed report with [S1].",
            "sources": _source_payload(),
            "quality_score": {"label": "medium", "value": 64},
        },
    )
    assert completed.payload["run"]["status"] == "completed"  # type: ignore[index]
    assert completed.payload["run"]["artifact_id"]  # type: ignore[index]
    assert completed.payload["run"]["sources"][0]["source_id"] == "S1"  # type: ignore[index]


class _FakeResearchEngine:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

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
        yield {"type": "research_start", "data": {"query": query, "mode": mode}}
        yield {
            "type": "research_complete",
            "data": {
                "query": query,
                "mode": mode,
                "text": "Streamed report with [S1].",
                "sources": _source_payload(),
                "quality_score": {"label": "high", "value": 90},
                "research_trace": [{"label": "Done", "done": True}],
                "saved": save_memory,
            },
        }


def test_research_events_persists_run_and_augments_complete_event(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _patch_geneva_paths(monkeypatch, tmp_path)

    from src.geneva.research_runs import ResearchRunStore
    from src.geneva.web_runtime import ResearchRequest, research_events

    engine = _FakeResearchEngine()
    with patch("src.geneva.web_runtime.get_research_engine", return_value=engine):
        events = list(research_events(object(), ResearchRequest("research topic", session_id="session-1", mode="deep")))

    complete = events[-1]
    assert complete["type"] == "research_complete"
    assert complete["data"]["run_id"]
    assert complete["data"]["artifact_id"]

    stored = ResearchRunStore().get_run(complete["data"]["run_id"])
    assert stored is not None
    assert stored["status"] == "completed"
    assert stored["final_text"] == "Streamed report with [S1]."
    assert stored["sources"][0]["title"] == "Primary Source"


def test_ghost_research_events_do_not_persist_run(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _patch_geneva_paths(monkeypatch, tmp_path)

    from src.geneva.research_runs import ResearchRunStore
    from src.geneva.web_runtime import ResearchRequest, research_events

    engine = _FakeResearchEngine()
    with patch("src.geneva.web_runtime.get_research_engine", return_value=engine):
        events = list(
            research_events(
                object(),
                ResearchRequest("private research", session_id="session-1", ghost_mode=True),
            )
        )

    complete = events[-1]
    assert complete["type"] == "research_complete"
    assert "run_id" not in complete["data"]
    assert ResearchRunStore().list_runs()["count"] == 0
