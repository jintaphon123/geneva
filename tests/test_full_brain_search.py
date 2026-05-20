from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _patch_geneva_paths(monkeypatch: Any, tmp_path: Path) -> Path:
    db_path = tmp_path / "brain.db"
    monkeypatch.setenv("GENEVA_BRAIN_DB_PATH", str(db_path))
    monkeypatch.setenv("GENEVA_DATA_DIR", str(tmp_path / "data"))
    return db_path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seed_search_corpus(monkeypatch: Any, tmp_path: Path) -> dict[str, Any]:
    db_path = _patch_geneva_paths(monkeypatch, tmp_path)

    from src.geneva.project_sources import ProjectSourceStore
    from src.geneva.project_store import ProjectStore
    from src.geneva.research_runs import ResearchRunStore

    project_store = ProjectStore()
    alpha = project_store.create_project(
        "Orbit Alpha",
        description="Alpha project description contains searchable orbit material.",
    )
    beta = project_store.create_project(
        "Orbit Beta",
        description="Beta project should not appear in alpha scoped orbit search.",
    )
    source_store = ProjectSourceStore()
    alpha_source = source_store.add_text_source(
        project_id=alpha.id,
        title="Alpha Source Note",
        content="Project source snapshot with searchable orbit source context.",
        source_type="markdown",
    )
    beta_source = source_store.add_text_source(
        project_id=beta.id,
        title="Beta Source Note",
        content="Project source snapshot with beta-only orbit context.",
        source_type="text",
    )

    research_store = ResearchRunStore()
    alpha_run = research_store.create_run(
        query="Alpha orbit research",
        session_id="session-alpha",
        project_id=alpha.id,
        mode="deep",
        plan={"title": "Alpha plan"},
    )
    alpha_report = research_store.complete_run(
        alpha_run["id"],
        final_text="Completed alpha research report about searchable orbit evidence.",
        sources=[{"id": "S1", "title": "Alpha Evidence", "url": "https://example.com/a"}],
    )
    beta_run = research_store.create_run(
        query="Beta orbit research",
        session_id="session-beta",
        project_id=beta.id,
        mode="deep",
        plan={"title": "Beta plan"},
    )
    research_store.complete_run(
        beta_run["id"],
        final_text="Completed beta research report about orbit evidence.",
        sources=[{"id": "S1", "title": "Beta Evidence", "url": "https://example.com/b"}],
    )

    now = _now()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO session_transcripts(
                id, session_id, project_id, ghost_mode, turn_index, role, content, created_at
            )
            VALUES (?, ?, ?, 0, 1, 'user', ?, ?)
            """,
            (
                "turn-alpha",
                "session-alpha",
                alpha.id,
                "Chat transcript says searchable orbit chat context.",
                now,
            ),
        )
        conn.execute(
            """
            INSERT INTO session_transcripts(
                id, session_id, project_id, ghost_mode, turn_index, role, content, created_at
            )
            VALUES (?, ?, ?, 0, 1, 'user', ?, ?)
            """,
            (
                "turn-beta",
                "session-beta",
                beta.id,
                "Beta transcript says orbit but belongs elsewhere.",
                now,
            ),
        )
        conn.execute(
            """
            INSERT INTO memories(
                id, path, name, type, status, scope, content, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?)
            """,
            (
                "memory-alpha",
                "memory://alpha",
                "Alpha Memory",
                "project",
                alpha.id,
                "Long-term memory with searchable orbit memory context.",
                now,
                now,
            ),
        )
        conn.execute(
            """
            INSERT INTO memories(
                id, path, name, type, status, scope, content, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?)
            """,
            (
                "memory-beta",
                "memory://beta",
                "Beta Memory",
                "project",
                beta.id,
                "Long-term beta memory with orbit context.",
                now,
                now,
            ),
        )

    return {
        "project": alpha,
        "other_project": beta,
        "source": alpha_source,
        "other_source": beta_source,
        "report": alpha_report,
    }


def test_full_brain_search_groups_chats_projects_memories_sources_and_reports(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _seed_search_corpus(monkeypatch, tmp_path)

    from src.geneva.search_service import full_brain_search

    payload = full_brain_search("orbit", limit=20)

    assert payload["query"] == "orbit"
    assert payload["count"] >= 5
    for result_type in ("chat", "project", "memory", "source", "research_report"):
        assert result_type in payload["groups"]
        assert payload["groups"][result_type]["count"] >= 1

    for result in payload["results"]:
        assert result["id"]
        assert result["type"]
        assert result["title"]
        assert result["snippet"]
        assert result["actions"]
        assert "orbit" in result["snippet"].lower() or "orbit" in result["title"].lower()


def test_full_brain_search_respects_project_scope(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    seed = _seed_search_corpus(monkeypatch, tmp_path)

    from src.geneva.search_service import full_brain_search

    payload = full_brain_search("orbit", project_id=seed["project"].id, limit=30)

    assert payload["count"] >= 5
    assert {result["project_id"] for result in payload["results"] if result["type"] != "project"} == {
        seed["project"].id
    }
    assert seed["other_project"].id not in {
        result.get("project_id") for result in payload["results"]
    }
    assert all("beta" not in result["title"].lower() for result in payload["results"])
    assert all("beta" not in result["snippet"].lower() for result in payload["results"])


def test_api_search_uses_unified_grouped_contract(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    seed = _seed_search_corpus(monkeypatch, tmp_path)

    from src.geneva.web_api import JsonApiResult, dispatch_api_request
    from src.geneva.web_runtime import SessionManager

    manager = SessionManager.__new__(SessionManager)
    result = dispatch_api_request(
        manager,
        "GET",
        "/api/search",
        query_string=f"q=orbit&project_id={seed['project'].id}&limit=20",
    )

    assert isinstance(result, JsonApiResult)
    assert result.payload["query"] == "orbit"  # type: ignore[index]
    assert result.payload["count"] >= 5  # type: ignore[index]
    assert "groups" in result.payload  # type: ignore[operator]
    assert "source" in result.payload["groups"]  # type: ignore[index]
    assert "research_report" in result.payload["groups"]  # type: ignore[index]


def test_api_search_suggest_returns_lightweight_suggestions(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _seed_search_corpus(monkeypatch, tmp_path)

    from src.geneva.web_api import JsonApiResult, dispatch_api_request
    from src.geneva.web_runtime import SessionManager

    manager = SessionManager.__new__(SessionManager)
    result = dispatch_api_request(
        manager,
        "GET",
        "/api/search/suggest",
        query_string="q=orbit&limit=5",
    )

    assert isinstance(result, JsonApiResult)
    assert result.payload["query"] == "orbit"  # type: ignore[index]
    assert result.payload["suggestions"]  # type: ignore[index]
    assert {
        "id",
        "type",
        "title",
        "snippet",
    }.issubset(result.payload["suggestions"][0])  # type: ignore[index]
