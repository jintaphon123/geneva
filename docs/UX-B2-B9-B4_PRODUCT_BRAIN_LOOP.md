# UX-B2/B9/B4 Product Brain Loop Plan

> Created: 2026-05-20
> Status: UX-B2 backend source ingestion shipped for text / markdown / URL / PDF / DOCX. UX-B9 lean backend run/source/report model shipped. UX-B4 lean backend Full Brain Search shipped.

## Decision

Build the next product-brain layer in this order:

1. UX-B2 Project Sources v1: text / markdown / URL
2. UX-B2 Project Sources v2: PDF / DOCX
3. UX-B9 Deep Research Product Flow lean: research uses the same source/run model
4. UX-B4 Full Brain Search lean: search the new corpus after it exists

Do not build UX-B0, UX-B3 full, UX-B5, UX-B8, UX-B10, or UX-B11 in this slice.

## Source vs Memory Principle

Project sources are not personal memory.

Text files, markdown files, URLs, PDFs, and DOCX files should be treated as project/reference material that Geneva can cite, include, exclude, refresh, search, and inspect. They should not automatically become long-term memory.

Long-term memory should stay reserved for facts, preferences, decisions, project state, feedback, and identity/context items that Geneva should carry across sessions. If a source contains candidate facts worth remembering, those facts must go through the existing UX-B7 memory write/review path instead of being silently saved.

This distinction prevents source ingestion from polluting memory with large documents, stale URL snapshots, or temporary project notes.

## Storage Recommendation

Use a hybrid storage model:

- SQLite / memdir metadata for source records, parse status, include policy, hashes, project ownership, timestamps, and searchable result metadata.
- File snapshots for extracted content and chunks under a Geneva-managed data directory.

Recommended source record shape:

- `id`
- `project_id`
- `source_type`: `text`, `markdown`, `url`, later `pdf`, `docx`
- `title`
- `uri`
- `content_hash`
- `snapshot_path`
- `parse_status`: `ready`, `parsing`, `failed`, `excluded`, `stale`, `unsupported`
- `include_policy`: `include`, `exclude`
- `token_estimate`
- `last_indexed_at`
- `created_at`
- `updated_at`

For URL sources, cache a fetched snapshot by default, store `fetched_at`, and mark it stale when refresh is needed. Do not fetch live every time by default because live pages drift, disappear, or change without the user noticing. Refresh should be explicit or policy-driven.

## Phase Breakdown

### 1. UX-B2.1 Source Core

Goal: create the source contract before parser complexity.

Scope:

- Add source schema and source service.
- Support project-scoped CRUD.
- Support include/exclude.
- Support parse/index status.
- Ensure failed/unsupported/excluded sources are never injected silently.

Acceptance:

- A project can list, add, update, exclude, and delete source records.
- Source status is explicit.
- Backend tests prove excluded/failed sources do not enter project context.

Implementation result (2026-05-20):

- Added `src/geneva/project_sources.py`.
- Added `project_sources` SQLite table managed by `ProjectSourceStore`.
- Snapshots are stored outside memory under `GENEVA_DATA_DIR/sources/{project_id}`.
- Text/markdown sources are saved as snapshots with `content_hash`, `parse_status`, `include_policy`, and `token_estimate`.
- Source ingestion does not create rows in the `memories` table.

### 2. UX-B2.2 Text / Markdown / URL Parser

Goal: make the first useful source types work end to end.

Scope:

- Parse pasted text and uploaded/local markdown.
- Fetch URL content and save a snapshot outside long-term memory.
- Store extracted text/chunks as source snapshots.
- Add basic chunk/index metadata.
- Add project context preview.
- Emit source-used metadata into context disclosure.

Acceptance:

- A markdown source can be added to a project and used in a project chat response.
- A URL source can be fetched once, cached, and included in context when enabled.
- Context strip can show that sources were used.
- Source content does not become memory automatically.

Implementation result (2026-05-20):

- URL sources are fetched once at add time, cached as text snapshots, and keep `metadata.fetched_at`; context assembly does not fetch live URLs.
- Added project-source API routes:
  - `GET /api/projects/{project_id}/sources`
  - `POST /api/projects/{project_id}/sources`
  - `PUT /api/projects/{project_id}/sources/{source_id}`
  - `DELETE /api/projects/{project_id}/sources/{source_id}`
  - `GET /api/projects/{project_id}/sources/context-preview`
- `chat_events` now attaches included ready project sources as `ContextSourceBlock(source_type="project_source")`.
- `GenevaSession` now injects those source blocks into the static context and context ledger path.
- UX-B6 can count these as sources because they use `project_source`, not `project_context` or `memory_context`.

### 3. UX-B2.3 Project Sources UI

Goal: make source management visible and controllable.

Scope:

- Add Sources tab/surface in Project view.
- Add text/markdown/URL source creation.
- Show status labels.
- Add include/exclude toggle.
- Show source preview and parse errors.

Acceptance:

- User can inspect which sources are available for a project.
- User can exclude a source and verify it is not used.
- UI does not claim a source is ready if parse/fetch failed.

### 4. UX-B2.4 PDF / DOCX Parser

Goal: add heavier document types after the source contract is stable.

Scope:

- Add PDF parser.
- Add DOCX parser.
- Preserve basic metadata: file name, page/section hints where possible, parse warnings.
- Use the same source schema and snapshot/chunk pipeline.

Non-goals:

- No full DOCX style-preserving editing.
- No advanced citation trace yet beyond basic source/chunk provenance.

Acceptance:

- Failed PDF/DOCX parsing is explicit and never silently injected.
- Parsed PDF/DOCX sources can be included/excluded like text/markdown/URL.

Implementation result (2026-05-20):

- `ProjectSourceStore.add_document_source(...)` supports `pdf` and `docx` paths.
- DOCX parsing uses stdlib zip/XML extraction from `word/document.xml` plus headers/footers when present.
- PDF parsing tries optional installed parsers (`pypdf`, `PyPDF2`, `pdfminer`) and falls back to a conservative stdlib text-stream extractor.
- Successful document parses create ready project-source snapshots with parser/file metadata.
- Failed document parses create explicit `parse_status="failed"` source records with `parse_error`.
- Failed document sources are listed for inspection but never enter context preview or chat context injection.
- Document source ingestion does not write to the `memories` table.

### 5. UX-B9.1 Research Run Core

Goal: make Deep Research a durable run, not only a long chat answer.

Scope:

- Add `research_runs`.
- Add `research_sources`.
- Store plan, mode, status, query, project/session links, progress trace, and final text.
- Reuse Project Sources where appropriate.

Acceptance:

- Deep Research creates a run id.
- The run has status transitions such as `draft_plan`, `running`, `completed`, `failed`.
- Used sources are preserved with the run.

Implementation result (2026-05-20):

- Added `src/geneva/research_runs.py` with `ResearchRunStore`.
- Added `research_runs` and `research_sources` tables in the Geneva brain DB.
- Non-ghost `research_events(...)` creates a running research run and adds `run_id` to stream events.
- On `research_complete`, Geneva persists final text, sources, quality score, trace metadata, and source rows.
- Ghost research does not create durable research runs.

### 6. UX-B9.2 Research Report Object

Goal: make completed research reopenable and searchable.

Scope:

- Create a lightweight report object when a run completes.
- Link report to run, project, sources, and originating session.
- This is B3-lite only; do not implement the full Product Artifact Model yet.

Acceptance:

- A completed research run creates an openable report record.
- Report source trace is visible.
- Report can later be indexed by UX-B4.

Implementation result (2026-05-20):

- Added `research_report` artifact type with permanent retention.
- Completed runs save a redacted JSON report artifact containing run id, query, mode, project/session links, final text, sources, quality score, and trace.
- `research_complete` events now include `artifact_id` when a non-ghost run is persisted.
- Verification: `pytest -q` -> `599 passed, 16 skipped, 1 warning`

API result (2026-05-20):

- `POST /api/research/runs`
- `GET /api/research/runs`
- `GET /api/research/runs/{run_id}`
- `POST /api/research/runs/{run_id}/complete`
- `POST /api/research/runs/{run_id}/stop`
- `POST /api/research/runs/{run_id}/resume`
- `POST /api/research/runs/{run_id}/fail`

### 7. UX-B9.3 Memory Candidates

Goal: let research produce memory candidates without silently polluting memory.

Scope:

- Extract candidate findings from research output.
- Send candidates through UX-B7 memory write/review flow.
- User can approve/undo/review.

Acceptance:

- Research findings are not automatically saved as active memory without policy/review.
- Accepted candidates become memory records with source/run trace.

Implementation note:

- Memory candidate extraction/review UI is still deferred. Current UX-B9 lean does not silently create memory candidates; existing research memory save behavior remains controlled by `ghost_mode` and existing memory policy.

### 8. UX-B4.1 Unified Search Backend

Goal: search the corpus after sources and research reports exist.

Scope:

- Search chats, projects, memories, project sources, and research reports.
- Return grouped results by type.
- Support project-scoped search.
- Provide actions: open chat, open project, open memory, open source, open report.

Acceptance:

- Search results are grouped and typed.
- Project-scoped search does not mix global results unless requested.
- Source and research report results include snippets and source/project badges.

Implementation result (2026-05-20):

- Added `src/geneva/search_service.py`.
- `full_brain_search(...)` searches chat transcripts, projects, active memories, ready project-source snapshots, and completed research reports.
- `SearchResult` includes id/type/title/snippet/matched_fields/score/scope/badges/actions plus project/session/source/artifact links.
- `/api/search` now returns the grouped full-brain contract instead of transcript-only results.
- `/api/search/suggest` returns lightweight suggestions from the same backend.
- Project-scoped search is strict: only records owned by that project are returned; global mixing is deferred until a UI control explicitly asks for it.
- Current lean search uses deterministic lexical matching, not vector search.

### 9. UX-B4.2 Search UI

Goal: make Cmd+K / SearchOverlay use the unified backend.

Scope:

- Replace client-only chat/project filtering with backend search.
- Show grouped result sections.
- Add source/report/memory result rows.
- Add open actions.

Acceptance:

- User can search one term and see matching chat, project, memory, source, and research report results.
- Results can be opened from the overlay.

## Open Questions

Resolved:

- v1 source types: text / markdown / URL only.
- PDF/DOCX backend parser: shipped after source core; UI upload/sources tab still pending.
- Source ingestion: source/reference layer, not long-term memory.
- Exact file storage root for source snapshots: `GENEVA_DATA_DIR/sources/{project_id}`, falling back to the normal Geneva data directory.
- URL sources: cached snapshot at add time; no live fetch during context assembly.

Default recommendation unless Bond changes it:

- URL sources should be cached as snapshots outside memory, with explicit refresh/stale handling.
- Markdown/text sources should be indexed as project sources, not remembered as memory.

Still to decide:

- Whether URL fetch requires user confirmation for every domain or uses the existing web/tool trust policy.
- Whether local markdown sources are copied into Geneva snapshots or referenced by path plus content hash.
- Whether UX-B4 UI should be the next slice, replacing the current client-only `SearchOverlay`.

## Verification

2026-05-20:

- `pytest -q tests/test_project_sources.py` -> `5 passed`
- `pytest -q tests/test_project_sources.py tests/test_geneva_web.py` -> `45 passed, 8 skipped`
- `python -m compileall -q src/geneva/project_sources.py src/geneva/session.py src/geneva/web_runtime.py src/geneva/web_api.py` -> passed
- `pytest -q` -> `591 passed, 16 skipped, 1 warning`

2026-05-20 document source update:

- `pytest -q tests/test_project_sources.py` -> `8 passed`
- `pytest -q tests/test_project_sources.py tests/test_geneva_web.py` -> `48 passed, 8 skipped`
- `python -m compileall -q src/geneva/project_sources.py src/geneva/web_runtime.py src/geneva/web_api.py` -> passed
- `pytest -q` -> `594 passed, 16 skipped, 1 warning`

2026-05-20 Full Brain Search update:

- `pytest -q tests/test_full_brain_search.py` -> `4 passed`
- `pytest -q tests/test_full_brain_search.py tests/test_project_sources.py tests/test_research_runs.py tests/test_geneva_web.py tests/test_web_api_new_endpoints.py` -> `69 passed, 8 skipped`
- `pytest -q` -> `603 passed, 16 skipped, 1 warning`

## Why This Order

UX-B2 must come first because sources create the grounded corpus.

UX-B9 should come after sources because Deep Research needs durable source/run/report records instead of emitting only chat text.

UX-B4 should come after B2 and B9 because full brain search needs real source and report objects to search. Building B4 first would only search the old corpus and would look finished without increasing Geneva's brain capability.
