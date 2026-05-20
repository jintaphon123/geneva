# UX-B2 Document Sources Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add PDF and DOCX ingestion to Project Sources without turning document content into long-term memory.

**Architecture:** Extend `ProjectSourceStore` with document parsing and source creation on the same `project_sources` contract. DOCX uses stdlib zip/XML parsing; PDF uses optional installed parsers when available and a conservative stdlib fallback, with explicit failed source records when extraction cannot produce readable text.

**Tech Stack:** Python stdlib (`zipfile`, `xml.etree.ElementTree`, `zlib`, `re`), existing SQLite source metadata, existing project-source API routing.

---

### Task 1: Document Source Tests

**Files:**
- Modify: `tests/test_project_sources.py`

- [x] **Step 1: Write failing tests**

Add tests that create a minimal DOCX zip, a minimal uncompressed PDF, and a broken PDF. Verify ready documents create source snapshots, broken documents are recorded as failed, failed documents are not injected into context preview, and no document content is written into `memories`.

- [x] **Step 2: Run tests to verify red**

Run: `pytest -q tests/test_project_sources.py`

Expected before implementation: fail because `ProjectSourceStore.add_document_source` and PDF/DOCX API handling do not exist.

### Task 2: Document Parser + Store Integration

**Files:**
- Modify: `src/geneva/project_sources.py`

- [x] **Step 1: Implement document parsing**

Add DOCX zip/XML text extraction and PDF extraction with optional parser hooks plus stdlib fallback.

- [x] **Step 2: Implement `add_document_source`**

Create ready source records for extracted text and failed source records with `parse_error` for unreadable/unsupported documents.

- [x] **Step 3: Verify green**

Run: `pytest -q tests/test_project_sources.py`

Expected after implementation: all project source tests pass.

Result: `pytest -q tests/test_project_sources.py` -> `8 passed`

### Task 3: API Integration

**Files:**
- Modify: `src/geneva/web_runtime.py`
- Modify: `src/geneva/web_api.py`
- Test: `tests/test_project_sources.py`

- [x] **Step 1: Wire JSON API document source creation**

Accept `source_type` of `pdf` or `docx` with `file_path`/`path`/`uri`, route to `ProjectSourceStore.add_document_source`, and return the same source payload shape.

- [x] **Step 2: Verify API test green**

Run: `pytest -q tests/test_project_sources.py::test_api_creates_pdf_source_from_file_path`

Expected: API creates a ready PDF source and context preview includes extracted text.

Result: covered by `pytest -q tests/test_project_sources.py` -> `8 passed`

### Task 4: Regression + Docs

**Files:**
- Modify: `docs/UX-B2-B9-B4_PRODUCT_BRAIN_LOOP.md`
- Modify: `projects/second-brain/GENEVA_ROADMAP.md`
- Modify: `projects/second-brain/CURRENT_STATE.md`
- Modify: `projects/second-brain/Geneva Owner Manual.md`
- Modify: `decisions/log.md`

- [x] **Step 1: Run targeted and full verification**

Run:

```bash
pytest -q tests/test_project_sources.py tests/test_geneva_web.py
python -m compileall -q src/geneva/project_sources.py src/geneva/web_runtime.py src/geneva/web_api.py
pytest -q
```

Current result:

- `pytest -q tests/test_project_sources.py tests/test_geneva_web.py` -> `48 passed, 8 skipped`
- `python -m compileall -q src/geneva/project_sources.py src/geneva/web_runtime.py src/geneva/web_api.py` -> passed
- `pytest -q` -> `594 passed, 16 skipped, 1 warning`

- [x] **Step 2: Update status docs**

Record that UX-B2 PDF/DOCX backend parser is shipped, while frontend Sources tab, lifecycle events, reindex/refresh/stale, and URL trust policy remain pending.
