# Project Sources v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build UX-B2 Project Sources v1 so Geneva can store project-scoped text, markdown, and URL sources as reference material without silently converting them into long-term memory.

**Architecture:** Add a focused `src/geneva/project_sources.py` service backed by SQLite metadata and file snapshots under the Geneva data directory. Wire the service into project context assembly, context disclosure, and REST endpoints while keeping source content out of the memory tables unless UX-B7 explicitly accepts a derived memory candidate later.

**Tech Stack:** Python 3.11+, SQLite, existing `src.memdir.brain_engine` DB initialization, existing `web_api.py` dispatcher, pytest.

---

### Task 1: Source Service And Parser

**Files:**
- Create: `src/geneva/project_sources.py`
- Test: `tests/test_project_sources.py`

- [ ] **Step 1: Write failing tests**

```python
def test_text_source_is_snapshotted_without_creating_memory(tmp_path, monkeypatch):
    monkeypatch.setenv("GENEVA_BRAIN_DB_PATH", str(tmp_path / "brain.db"))
    monkeypatch.setenv("GENEVA_DATA_DIR", str(tmp_path / "data"))

    from src.geneva.project_sources import ProjectSourceStore

    store = ProjectSourceStore()
    source = store.add_text_source(
        project_id="project-1",
        title="Roadmap note",
        content="# Plan\n\nGeneva source text",
        source_type="markdown",
    )

    assert source["parse_status"] == "ready"
    assert source["source_type"] == "markdown"
    assert source["snapshot_path"]
    assert "Geneva source text" in store.read_snapshot(source["id"])
    assert store.list_sources("project-1")["count"] == 1
```

- [ ] **Step 2: Verify red**

Run: `pytest -q tests/test_project_sources.py`

Expected before implementation: import failure for `src.geneva.project_sources`.

- [ ] **Step 3: Implement minimal service**

Create `ProjectSourceStore` with schema creation, text/markdown source insertion, snapshot writes, list/get/update/delete, include/exclude, and context preview helpers.

- [ ] **Step 4: Verify green**

Run: `pytest -q tests/test_project_sources.py`

Expected after implementation: project source service tests pass.

### Task 2: URL Source Snapshot

**Files:**
- Modify: `src/geneva/project_sources.py`
- Test: `tests/test_project_sources.py`

- [ ] **Step 1: Write failing tests**

```python
def test_url_source_uses_fetcher_and_caches_snapshot(tmp_path, monkeypatch):
    monkeypatch.setenv("GENEVA_BRAIN_DB_PATH", str(tmp_path / "brain.db"))
    monkeypatch.setenv("GENEVA_DATA_DIR", str(tmp_path / "data"))

    from src.geneva.project_sources import ProjectSourceStore

    store = ProjectSourceStore()
    source = store.add_url_source(
        project_id="project-1",
        url="https://example.com/post",
        title="Example",
        fetcher=lambda url: "Fetched page body",
    )

    assert source["parse_status"] == "ready"
    assert source["uri"] == "https://example.com/post"
    assert "Fetched page body" in store.read_snapshot(source["id"])
```

- [ ] **Step 2: Verify red**

Run: `pytest -q tests/test_project_sources.py::test_url_source_uses_fetcher_and_caches_snapshot`

Expected before implementation: `add_url_source` missing.

- [ ] **Step 3: Implement URL source support**

Add URL validation, fetcher injection for tests, cache fetched content as a snapshot, and set `fetched_at` metadata. Do not fetch live during context assembly.

- [ ] **Step 4: Verify green**

Run: `pytest -q tests/test_project_sources.py`

Expected after implementation: text/markdown/URL tests pass.

### Task 3: API And Project Context Integration

**Files:**
- Modify: `src/geneva/web_runtime.py`
- Modify: `src/geneva/web_api.py`
- Test: `tests/test_project_sources.py`

- [ ] **Step 1: Write failing tests**

```python
def test_api_creates_lists_excludes_and_previews_project_sources(tmp_path, monkeypatch):
    monkeypatch.setenv("GENEVA_BRAIN_DB_PATH", str(tmp_path / "brain.db"))
    monkeypatch.setenv("GENEVA_DATA_DIR", str(tmp_path / "data"))

    from src.geneva.project_store import ProjectStore
    from src.geneva.web_api import dispatch_api_request
    from src.geneva.web_runtime import SessionManager

    manager = SessionManager.__new__(SessionManager)
    project = ProjectStore().create_project("Source Project")
    created = dispatch_api_request(
        manager,
        "POST",
        f"/api/projects/{project.id}/sources",
        payload={"source_type": "markdown", "title": "Spec", "content": "# Spec\nUseful context"},
    )

    assert created.payload["source"]["parse_status"] == "ready"
    listed = dispatch_api_request(manager, "GET", f"/api/projects/{project.id}/sources")
    assert listed.payload["count"] == 1
    preview = dispatch_api_request(manager, "GET", f"/api/projects/{project.id}/sources/context-preview")
    assert "Useful context" in preview.payload["preview"]
```

- [ ] **Step 2: Verify red**

Run: `pytest -q tests/test_project_sources.py::test_api_creates_lists_excludes_and_previews_project_sources`

Expected before implementation: 404 for new source endpoints.

- [ ] **Step 3: Implement API and context preview**

Add source payload helpers to `web_runtime.py` and route project source endpoints in `web_api.py`. Extend project context payload with included ready source previews.

- [ ] **Step 4: Verify green**

Run: `pytest -q tests/test_project_sources.py`

Expected after implementation: API and context integration tests pass.

### Task 4: Regression Coverage

**Files:**
- Test: `tests/test_project_sources.py`

- [ ] **Step 1: Add regression tests**

Add tests proving excluded/failed sources are not included in context preview and source content is not inserted into the `memories` table.

- [ ] **Step 2: Run targeted tests**

Run: `pytest -q tests/test_project_sources.py tests/test_geneva_web.py tests/test_context_disclosure.py`

Expected: all selected tests pass.

- [ ] **Step 3: Run broad verification**

Run: `pytest -q`

Expected: full suite passes or any unrelated pre-existing failures are explicitly identified.

## Implementation Result

Completed on 2026-05-20.

What shipped:

- `src/geneva/project_sources.py` adds `ProjectSourceStore` with source metadata, snapshot storage, text/markdown ingestion, URL snapshot ingestion, include/exclude policy, parse status, context preview, and context source blocks.
- `src/geneva/web_runtime.py` adds project-source payload helpers and attaches included ready project sources to project-scoped chat turns.
- `src/geneva/web_api.py` routes source CRUD and context preview endpoints under `/api/projects/{project_id}/sources`.
- `src/geneva/session.py` accepts project source context blocks and injects them as source ledger blocks.
- `tests/test_project_sources.py` covers memory non-pollution, URL snapshot caching, exclude/failed filtering, API CRUD/preview, and chat context attachment.

Verification:

- `pytest -q tests/test_project_sources.py` -> `5 passed`
- `pytest -q tests/test_project_sources.py tests/test_geneva_web.py` -> `45 passed, 8 skipped`
- `python -m compileall -q src/geneva/project_sources.py src/geneva/session.py src/geneva/web_runtime.py src/geneva/web_api.py` -> passed
- `pytest -q` -> `591 passed, 16 skipped, 1 warning`

Still pending:

- UX-B2 PDF/DOCX parser.
- UX-B2 frontend Sources tab.
- Source usage events beyond context ledger source blocks.
- Reindex/refresh/stale flow.
- URL trust/permission policy.
