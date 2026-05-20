# UX-B4 Lean Full Brain Search Plan

> Created: 2026-05-20
> Status: Implemented and verified — `603 passed, 16 skipped, 1 warning`.

## Goal

Make Geneva search the real Product Brain corpus instead of only chat transcripts:

- chats / session transcripts
- projects
- long-term memories
- project sources from UX-B2
- completed research reports from UX-B9

This is backend lean only. The full `SearchOverlay` UI remains deferred unless Bond asks for UI next.

## Contract

Add `src/geneva/search_service.py` with a unified result shape:

- `id`
- `type`: `chat`, `project`, `memory`, `source`, `research_report`
- `title`
- `snippet`
- `matched_fields`
- `score`
- `scope`
- `project_id`
- `session_id`
- `source_id`
- `artifact_id`
- `badges`
- `actions`
- `created_at`
- `metadata`

`GET /api/search?q=...&types=...&project_id=...&limit=...` should return:

- `query`
- `results`
- `groups`
- `count`
- `limit`

`GET /api/search/suggest?q=...` should return lightweight suggestions using the same backend.

## Scope Rules

When `project_id` is set, search should only return items owned by that project. It should not mix other project or global results unless a later UI explicitly asks for global-in-project search.

This protects the user's mental model: project search means "inside this project", not "everything Geneva knows plus maybe this project."

## Non-Goals

- No vector index yet.
- No frontend overlay in this slice.
- No skill/artifact full model search beyond UX-B9 `research_report`.
- No advanced ranking beyond deterministic lexical matching.

## Tests First

Add `tests/test_full_brain_search.py`:

- grouped result contract across chat/project/memory/source/research report
- project scoped search excludes another project's matches
- `/api/search` uses the new grouped contract
- `/api/search/suggest` returns lightweight suggestions

## Implementation Steps

1. ✅ Write failing tests against `full_brain_search(...)` and the API contract.
2. ✅ Implement `SearchResult` helpers and `full_brain_search(...)`.
3. ✅ Search sources by metadata plus source snapshot content.
4. ✅ Search reports through `research_runs.final_text` and linked `artifact_id`.
5. ✅ Replace old `/api/search` transcript-only route.
6. ✅ Run targeted tests, then full `pytest -q`.
7. ✅ Update roadmap/current docs and decision log.

## Implementation Result

- Added `src/geneva/search_service.py`.
- Added `tests/test_full_brain_search.py`.
- Replaced `/api/search` transcript-only behavior with grouped full-brain search.
- Added `/api/search/suggest`.
- Strict project-scoped search shipped for the lean backend.

## Verification

- `python -m pytest tests/test_full_brain_search.py -q` -> `4 passed`
- `python -m pytest tests/test_full_brain_search.py tests/test_project_sources.py tests/test_research_runs.py tests/test_geneva_web.py tests/test_web_api_new_endpoints.py -q` -> `69 passed, 8 skipped`
- `python -m pytest -q` -> `603 passed, 16 skipped, 1 warning`
