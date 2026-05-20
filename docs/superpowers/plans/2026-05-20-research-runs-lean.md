# UX-B9 Lean Research Runs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Deep Research produce durable run records, source records, and a reopenable report artifact.

**Architecture:** Add a focused `ResearchRunStore` alongside existing `ResearchEngine`. The web runtime creates a run for non-ghost research streams, observes stream completion/error events, and persists final text, sources, quality metadata, and a `research_report` artifact. API routes expose lean run create/list/get/complete/status operations for future UI.

**Tech Stack:** Python stdlib, SQLite via Geneva brain DB, existing `artifact_store`, existing `ResearchEngine` event stream, existing `web_api` dispatch pattern.

---

### Task 1: Research Run Store Tests

**Files:**
- Test: `tests/test_research_runs.py`

- [x] **Step 1: Write failing store tests**

Create tests that verify:

- `ResearchRunStore.create_run(...)` creates a `draft_plan` run.
- `complete_run(...)` stores final text, source rows, quality metadata, and a `research_report` artifact.
- `fail_run(...)` marks a run failed without creating a report artifact.

- [x] **Step 2: Run red**

Run: `pytest -q tests/test_research_runs.py`

Expected before implementation: import fails because `src.geneva.research_runs` does not exist.

Result: `pytest -q tests/test_research_runs.py` -> `5 failed` with missing module/routes.

### Task 2: Research Run Store Implementation

**Files:**
- Create: `src/geneva/research_runs.py`
- Modify: `src/geneva/artifact_store.py`

- [x] **Step 1: Create store tables**

Add `research_runs` and `research_sources` tables in the same brain DB with id, session/project/mode/query/plan/status/artifact/final/error timestamps, and source metadata.

- [x] **Step 2: Implement store methods**

Implement create/get/list/status/complete/fail and report artifact saving.

- [x] **Step 3: Run green**

Run: `pytest -q tests/test_research_runs.py`

Expected: store tests pass.

Result: covered by `pytest -q tests/test_research_runs.py` -> `5 passed`.

### Task 3: API + Stream Integration

**Files:**
- Modify: `src/geneva/web_runtime.py`
- Modify: `src/geneva/web_api.py`
- Test: `tests/test_research_runs.py`

- [x] **Step 1: Add failing API/runtime tests**

Verify:

- `POST /api/research/runs` creates a run.
- `GET /api/research/runs/{run_id}` returns it.
- `POST /api/research/runs/{run_id}/complete` creates report/source rows.
- `research_events(...)` persists a run for non-ghost streams and injects `run_id`/`artifact_id` into complete event data.
- ghost research does not persist a run.

- [x] **Step 2: Implement payload helpers and routes**

Add lean run payload helpers in `web_runtime.py`, route them in `web_api.py`, and extend `ResearchRequest` with optional `project_id`.

- [x] **Step 3: Run green**

Run: `pytest -q tests/test_research_runs.py tests/test_geneva_web.py`

Expected: all selected tests pass.

Result: `pytest -q tests/test_research_runs.py tests/test_research_engine_unit.py tests/test_geneva_web.py tests/test_artifact_store.py` -> `82 passed, 8 skipped`.

### Task 4: Verification + Docs

**Files:**
- Modify: `docs/UX-B2-B9-B4_PRODUCT_BRAIN_LOOP.md`
- Modify: `projects/second-brain/GENEVA_ROADMAP.md`
- Modify: `projects/second-brain/CURRENT_STATE.md`
- Modify: `projects/second-brain/Geneva Owner Manual.md`
- Modify: `decisions/log.md`

- [x] **Step 1: Run verification**

Run:

```bash
python -m compileall -q src/geneva/research_runs.py src/geneva/web_runtime.py src/geneva/web_api.py src/geneva/artifact_store.py
pytest -q tests/test_research_runs.py tests/test_research_engine_unit.py tests/test_geneva_web.py tests/test_artifact_store.py
pytest -q
```

Result:

- `python -m compileall -q src/geneva/research_runs.py src/geneva/web_runtime.py src/geneva/web_api.py src/geneva/artifact_store.py` -> passed
- `pytest -q tests/test_research_runs.py tests/test_research_engine_unit.py tests/test_geneva_web.py tests/test_artifact_store.py` -> `82 passed, 8 skipped`
- `pytest -q` -> `599 passed, 16 skipped, 1 warning`

- [x] **Step 2: Update status docs**

Record UX-B9 lean backend as shipped, with stop/resume UI, editable plan UI, and memory candidate review UI still deferred.
