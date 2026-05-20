# Geneva — Phase Runtime Audit

> Updated: 2026-05-20
> Scope: backend/runtime, memory, DNA, safety, routing, project/skill/autopilot, and backend contracts.
> Excluded: visual polish and frontend-only UI defects.
> Purpose: this file is the working source of truth for what still needs to be fixed before Geneva can be called "Layer 0/DNA completeสุดๆ".

---

## Executive Verdict

Geneva is much stronger than the previous audit state, but it is not honest to say "everything is completeสุดๆ" yet.

What is now verified:

- `~/.geneva/soul.md` exists and is loadable.
- `~/.geneva/BRAIN.md` exists and is loadable.
- `~/.geneva/context/me.md`, `work.md`, `team.md`, `current-priorities.md`, and `goals.md` exist and are loadable.
- `src/geneva/runtime_identity.py` returns three runtime identity blocks:
  - `soul_identity`
  - `brain_runtime_contract`
  - `owner_dna_context`

Smoke result from this audit:

```text
soul_exists= True
soul_path= /Users/jintaphon/.geneva/soul.md
block_count= 3
soul_identity          Soul — Identity Contract   /Users/jintaphon/.geneva/soul.md
brain_runtime_contract BRAIN — Runtime Contract   /Users/jintaphon/.geneva/BRAIN.md
owner_dna_context      DNA — Owner Context        /Users/jintaphon/.geneva/context/*.md
```

Fix update from this pass:

- Canonical onboarding now writes Soul to `~/.geneva/soul.md` and owner DNA to `~/.geneva/context/*.md`, not `~/.geneva/memory/*.md`.
- `refresh_context(..., include_identity_files=True)` now uses the same `runtime_identity` loader as the web session path.
- Web, QueryEngine, and REPL memory extraction can all use an LLM `agent_caller` instead of silently falling back to heuristic-only extraction.
- High-confidence user-direct memory corrections can safely supersede lower-confidence non-restricted memories; restricted conflicts still require review.
- Verification: `pytest -q` -> `581 passed, 16 skipped, 1 warning`.

The most important remaining gap:

Roadmap/status docs say many layers are complete, but several acceptance criteria are only partially implemented. The biggest remaining runtime issues are not cosmetic:

1. There is still no single full system prompt/context builder across every runtime path.
2. Phase R3 says pre-done verification exists, but task completion is not actually gated by a mandatory verification transition.
3. UX-B6 Context Disclosure backend is not implemented yet.
4. UX-B1 Mode Router contract is not implemented yet; settings currently normalize back to one default model.
5. Product Alignment backend backlog (UX-B0, B2, B3, B4, B5, B8, B9, B10, B11) is mostly absent/deferred by design.

---

## Severity Legend

| Severity | Meaning |
|---|---|
| P0 | Blocks trust, memory correctness, privacy, or "Geneva knows Bond" promise |
| P1 | Important production gap; should fix before KU trial/open-source handoff if possible |
| P2 | Real gap, but can wait until after trust gate if documented honestly |
| DEFERRED | Roadmap explicitly defers it; not a bug unless docs claim it is already usable |

---

## Phase 0 — Scope Lock + Path Normalization

### AUD-00-01 — Onboarding/DNA Root Mismatch

**Status:** FIXED — canonical manager writes Soul/DNA to `GENEVA_DATA_DIR`
**Severity:** P0
**Files:**

- `src/geneva/web_api.py`
- `src/geneva/onboarding.py`
- `src/memdir/paths.py`
- local runtime files under `~/.geneva/`

**What was wrong:**

`web_api.py` constructs onboarding with:

```python
OnboardingManager(get_auto_mem_path(Path.cwd()))
```

`get_auto_mem_path()` resolves to `~/.geneva/memory`, so onboarding status and onboarding writes use `~/.geneva/memory/me.md`, `~/.geneva/memory/work.md`, and `~/.geneva/memory/soul.md`.

But the real owner DNA currently lives here:

```text
~/.geneva/BRAIN.md
~/.geneva/soul.md
~/.geneva/context/me.md
~/.geneva/context/work.md
~/.geneva/context/team.md
~/.geneva/context/current-priorities.md
~/.geneva/context/goals.md
```

**Impact:**

- `/api/onboarding/status` can say onboarding is needed even when owner DNA already exists.
- Re-running onboarding may create a second, lower-quality DNA set in `~/.geneva/memory/`.
- Runtime identity loading is currently resilient because `runtime_identity.py` checks multiple paths, but onboarding UX/API still points at the wrong canonical root.

**Root cause:**

Path normalization solved `GENEVA_DATA_DIR`, but onboarding still uses the memory markdown directory as its DNA root.

**Fix applied:**

- Added `current_onboarding_manager()` as the canonical manager.
- Canonical writes:
  - Soul: `get_data_dir() / "soul.md"`
  - DNA: `get_data_dir() / "context" / "*.md"`
  - completion marker and decisions: `get_data_dir()`
- Web onboarding status/start/stream completion now use the canonical manager.
- Legacy `~/.geneva/memory/*.md` remains read fallback for status detection, but new canonical writes do not go there.

**Acceptance:**

- Covered by `test_onboarding_uses_canonical_data_dir_for_soul_and_context_dna`.
- Covered by `test_onboarding_status_reads_existing_canonical_context_dna`.
- Existing DNA no-overwrite remains covered by `test_onboarding_does_not_overwrite_existing_dna_by_default`.

---

### AUD-00-02 — Python Import Foot-Gun: `PYTHONPATH=src` Shadows Stdlib `types`

**Status:** OPEN
**Severity:** P2
**Files:**

- `src/types/__init__.py`
- project test/run docs

**What is wrong:**

Running this from inside `projects/second-brain/Geneva` fails:

```bash
PYTHONPATH=src python -c "from src.geneva.runtime_identity import load_runtime_identity_blocks"
```

Failure:

```text
ImportError: cannot import name 'MappingProxyType' from partially initialized module 'types'
```

**Root cause:**

The local package `src/types` shadows Python's standard library module `types` when `src` is placed directly on `PYTHONPATH`.

**Impact:**

Normal `pytest` paths can still work, but ad-hoc smoke commands and external agents can fail in a confusing way.

**Fix:**

- Preferred: run with `PYTHONPATH=/Users/jintaphon/Documents/Code/MyBrain/projects/second-brain/Geneva`, not `PYTHONPATH=src`.
- Stronger fix: rename local `src/types` if feasible, or document the correct import path in developer docs.

**Acceptance:**

- Local smoke command for `src.geneva.*` works from repo root without stdlib shadowing.

---

## Phase 1 — DNA Kernel

### AUD-01-01 — `soul.md` Physical File Was Missing

**Status:** FIXED IN THIS AUDIT
**Severity:** P0
**Files:**

- `/Users/jintaphon/.geneva/soul.md`
- `src/geneva/soul.py`
- `src/geneva/runtime_identity.py`

**What happened:**

The code could load `soul.md`, but the actual local file did not exist. That meant `SoulLoader` returned an empty block and Geneva had no pinned identity contract from Soul.

**Fix applied:**

Created:

```text
/Users/jintaphon/.geneva/soul.md
```

It contains:

- Bond identity
- Geneva identity
- voice contract
- memory contract
- Layer 0 priorities
- hard nos

**Verification:**

`SoulLoader().exists()` returns `True`, and `load_runtime_identity_blocks()` returns `soul_identity`.

**Remaining risk:**

This fixes the local machine and canonical onboarding writes. Future import/migration flows still need to preserve the same canonical paths.

---

### AUD-01-02 — Soul/BRAIN/DNA Injection Is Implemented, But Not Centralized

**Status:** FIXED — `refresh_context()` now uses `runtime_identity`
**Severity:** P1
**Files:**

- `src/geneva/runtime_identity.py`
- `src/geneva/session.py`
- `src/memdir/brain_engine.py`
- `src/context_system/builder.py`

**What was wrong:**

There were two separate identity-loading paths:

1. `src/geneva/runtime_identity.py`
2. `src/memdir/brain_engine.py::refresh_context(include_identity_files=True)`

`GenevaSession` disables identity in `refresh_context()` and injects identity via `runtime_identity.py`, which is good. But direct callers of `refresh_context()` still had their own identity logic.

**Impact:**

- Web session path and direct memory/context path can drift.
- Future changes to Soul/BRAIN/DNA path rules may be fixed in one place but missed in another.
- This violates the later R1 "single context assembly contract" promise.

**Fix applied:**

- `brain_engine.refresh_context()` now calls `load_runtime_identity_blocks()` instead of hand-rolling Soul/BRAIN/DNA loading.
- `include_identity_files=False` remains available for session path to prevent duplicate identity blocks.
- Test added: `test_refresh_context_uses_runtime_identity_loader`.

**Acceptance:**

- `test_soul_dna_and_brain_are_injected_into_turn_context`
- `test_refresh_context_uses_runtime_identity_loader`

---

## Phase 2 — Context Contract

### AUD-02-01 — No Single System Prompt / Context Builder Across Runtimes

**Status:** OPEN
**Severity:** P0
**Files:**

- `src/context_system/builder.py`
- `src/geneva/session.py`
- `src/tool_system/agent_loop.py`
- `src/query_engine.py`
- `src/repl/core.py`

**What is wrong:**

Roadmap R1 says there should be a single context assembly contract, but current code still assembles prompt/context in multiple places:

- `GenevaSession._build_memory_block()`
- `brain_engine.refresh_context()`
- `context_system.builder.build_context_prompt()`
- `tool_system.agent_loop`
- `QueryEnginePort.submit_message()`
- `REPLSession`

`context_system/builder.py` only renders workspace/git/CLAUDE.md context. It does not own the full runtime prompt contract: cognition, Soul, BRAIN, DNA, project, skill, memory, task, tools, privacy, and ledger.

**Impact:**

- "Geneva knows Bond" can be true in Web but weaker in REPL/QueryEngine.
- Context disclosure cannot be made reliable until there is one object/list of context blocks.
- Debugging memory bugs is harder because each runtime can inject in a different order.

**Fix:**

- Create one context assembly API, for example:

```python
build_system_context(
    user_input: str,
    session_id: str,
    project_id: str | None,
    ghost_mode: bool,
    include_tools: bool,
) -> ContextAssembly
```

- `ContextAssembly` should include:
  - final system prompt text
  - ordered context blocks
  - token estimates
  - source ids/labels
  - privacy flags
  - disclosure summary inputs
- Refactor Web, REPL, QueryEngine, and agent loop to call the same API.

**Acceptance:**

- One test asserts identical top-order blocks across Web/REPL/QueryEngine:
  1. cognition
  2. ghost contract if active
  3. soul
  4. BRAIN
  5. DNA
  6. active project/task/skill
  7. relevant memory
  8. tool/runtime rules

---

### AUD-02-02 — Context Ledger Exists, But UX-B6 Disclosure Inputs Are Missing

**Status:** OPEN
**Severity:** P0 for KU trust gate
**Files:**

- missing: `src/geneva/context_disclosure.py`
- `src/geneva/session.py`
- `src/services/compact/context_ledger.py`
- `src/geneva/web_api.py`

**What is wrong:**

The roadmap says UX-B6 is the next trust gate: a context strip showing what was used under each response.

But there is no `context_disclosure.py`, no `/context-summary` endpoint, and no per-turn `turn_context_summary` object.

**Impact:**

The user can still ask "why didn't Geneva know my name?" and the system cannot show a simple answer like:

```text
Used Soul · BRAIN · 5 DNA files · 3 memories · Geneva project · 2 tools
```

**Fix:**

- Implement backend-only summary first.
- Use existing context ledger where possible.
- Store per-turn summary with source ids, not raw prompt chunks.
- Ghost mode summary must show privacy proof without persisting private content.

**Acceptance:**

- After a chat turn, API can return:

```json
{
  "turn_id": "...",
  "used": {
    "soul": true,
    "brain": true,
    "dna_files": ["me.md", "work.md", "team.md", "current-priorities.md", "goals.md"],
    "project_id": "...",
    "memory_count": 4,
    "tools": ["Read"]
  }
}
```

---

## Phase 3 — Memory Substrate

### AUD-03-01 — Memory Extraction LLM Path Must Work Across Active Entrypoints

**Status:** FIXED — Web, QueryEngine, and REPL can use `agent_caller`
**Severity:** P1
**Files:**

- `src/geneva/session.py`
- `src/query_engine.py`
- `src/repl/core.py`
- `src/services/extract_memories/extract_memories.py`

**What was already fixed:**

`GenevaSession._run_memory_extraction()` now passes:

```python
agent_caller=self._call_auto_dream_agent
```

So the main web session can use LLM-backed memory extraction.

**What was still wrong:**

Legacy/direct paths still called:

```python
run_extraction(context)
```

without `agent_caller`:

- `src/query_engine.py`
- `src/repl/core.py`

**Impact:**

- Web path can remember short identity facts such as "ฉันชื่อ Bond".
- REPL/QueryEngine path falls back to heuristic extraction and may miss normal human phrasing.
- Memory behavior differs by entrypoint.

**Fix applied:**

- `QueryEnginePort` accepts `extraction_agent_caller` and passes it into `run_extraction()`.
- `GenevaREPL._run_memory_extraction()` now passes `_call_memory_extraction_agent`.
- `GenevaREPL._call_memory_extraction_agent()` calls the configured provider with the extraction prompt.

**Acceptance:**

- `test_session_memory_extraction_path_saves_short_identity`
- `test_query_engine_uses_llm_memory_extraction_when_available`
- `test_repl_memory_extraction_uses_llm_agent_caller`

---

### AUD-03-02 — Memory Visibility Exists, But Needs End-to-End Trust Pairing With Context Disclosure

**Status:** PARTIAL
**Severity:** P1
**Files:**

- `src/geneva/memory_write_review.py`
- `src/services/extract_memories/extract_memories.py`
- `src/geneva/web_api.py`
- `src/geneva/session.py`
- missing: `src/geneva/context_disclosure.py`

**What is working:**

UX-B7 lean backend exists:

- `memory_write_events`
- `memory_revisions`
- undo/approve endpoints
- extraction hook records write events

**What is incomplete:**

Memory write visibility alone does not answer "what did Geneva use to answer this turn?" That belongs to UX-B6 and is still missing.

**Fix:**

- Link `memory_write_events` and `turn_context_summary` by `turn_id`.
- Show both directions:
  - this turn wrote these memories
  - this answer used these memories

**Acceptance:**

- For a memory recall answer, backend can show memory IDs used.
- For a memory write, backend can show source turn and allow undo.

---

## Phase 4 — Runtime Safety

### AUD-04-01 — Ghost Mode Main Web Path Is Covered; Keep It In Regression Gate

**Status:** VERIFIED, WATCH
**Severity:** P1 watch item
**Files:**

- `src/geneva/session.py`
- `src/geneva/web_runtime.py`
- `src/memdir/transcript_store.py`
- `src/geneva/agent_trace.py`

**What is working:**

The main `chat_stream(..., ghost_mode=True)` path now gates transcript, trace, memory extraction, project activity, and dream consolidation.

**Why keep it in audit:**

Ghost privacy is a trust-killer if it regresses. It must remain in the always-run regression set.

**Acceptance:**

- Ghost turn writes no transcript rows.
- Ghost turn writes no agent trace file.
- Ghost turn runs no memory extraction.
- Ghost turn shows privacy proof in context ledger/disclosure.

---

## Phase 5 — Tool & Permission Boundary

### AUD-05-01 — UNTRUSTED Read Boundary Is Fixed; Keep It Cross-Tool

**Status:** VERIFIED, WATCH
**Severity:** P1 watch item
**Files:**

- `src/tool_system/tools/read.py`
- `src/tool_system/tools/web_fetch.py`
- `src/services/mcp/`

**What is working:**

`read.py` now prefixes file content with `[UNTRUSTED SOURCE]`.

**Remaining risk:**

Any new external-content tool can reintroduce prompt-injection risk if it returns raw content without the trust boundary label.

**Fix:**

- Add a shared helper for untrusted external content formatting.
- Require tests for every tool that returns file/web/MCP/user-provided document content.

**Acceptance:**

- All external content tools share the same prefix and wording.

---

## Phase 5B / 5BX — Async Intelligence

### AUD-5B-01 — Async/Parallel Runtime Needs A Single Capability Matrix

**Status:** OPEN
**Severity:** P2
**Files:**

- `src/tool_system/agent_loop.py`
- `src/tool_system/defaults.py`
- tool classes under `src/tool_system/tools/`

**What is wrong:**

Concurrent safety now exists for important tools, but the guarantee is distributed across tool specs and implementation details.

**Impact:**

It is hard to audit which tools are safe for parallel execution, background execution, or mid-turn execution.

**Fix:**

- Generate or expose a tool capability matrix:
  - read-only
  - concurrency-safe
  - requires confirmation
  - writes disk
  - network
  - destructive

**Acceptance:**

- One test asserts every registered tool declares capability fields.
- `/api/tools` exposes the same safe fields for UI/debug.

---

## Phase 6 / 6C / 6D — Model Reliability + Cognition

### AUD-06-01 — Cognition Exists, But Prompt Assembly Drift Still Weakens The Contract

**Status:** OPEN
**Severity:** P1
**Files:**

- `src/geneva/cognition/`
- `src/geneva/session.py`
- `src/tool_system/agent_loop.py`
- `src/context_system/builder.py`

**What is wrong:**

Cognition is injected in `GenevaSession._build_memory_block()`, but because prompt assembly is not centralized, the guarantee "cognition is always first" is only as strong as each entrypoint.

**Fix:**

Same fix as `AUD-02-01`: one context assembly API.

**Acceptance:**

- Provider payload tests assert cognition/Soul/BRAIN/DNA order on every active runtime path.

---

## Phase 7 — Background Brain

### AUD-07-01 — Dream Scheduler Is Web-App Wired, But Not Runtime-Universal

**Status:** OPEN
**Severity:** P2
**Files:**

- `src/geneva/web_runtime.py`
- `src/services/auto_dream/auto_dream.py`
- `src/repl/core.py`
- `src/query_engine.py`

**What is working:**

`SessionManager` starts the dream scheduler for the web app runtime.

**What is incomplete:**

REPL/QueryEngine paths do not appear to start the same scheduler. If those paths remain supported, background brain behavior differs by entrypoint.

**Fix:**

- Decide which entrypoints are first-class.
- If REPL/QueryEngine remain first-class, start or explicitly disable dream scheduler there with a visible status.

**Acceptance:**

- `/api/system/status` or equivalent reports dream scheduler state.
- Non-web entrypoints either start it or clearly say it is unavailable.

---

## Phase 8 — Observability + Release

### AUD-08-01 — Status Docs Drift From Runtime Truth

**Status:** OPEN
**Severity:** P1
**Files:**

- `projects/second-brain/CURRENT_STATE.md`
- `projects/second-brain/GENEVA_ROADMAP.md`
- `projects/second-brain/Geneva Owner Manual.md`
- `projects/second-brain/Geneva/AUDIT.md`

**What is wrong:**

Current docs say Layer 0 and many production phases are complete, but this audit found partial acceptance in context assembly, onboarding path, memory extraction parity, context disclosure, and mode contracts.

**Impact:**

The project can accidentally treat "tests pass" as equivalent to "product promise is true".

**Fix:**

- Do not mark a phase complete unless its acceptance is verified end-to-end.
- Add a "partial / lean / deferred" distinction to roadmap tables.
- Link this audit from Current State while trust-gate work is active.

**Acceptance:**

- Roadmap, Owner Manual, Current State, and AUDIT agree on what is complete, lean-complete, partial, and deferred.

---

## Phase H — Release Hardening

### AUD-H-01 — Regression Tests Are Strong, But They Do Not Cover Every Claimed Runtime Path

**Status:** OPEN
**Severity:** P1
**Files:**

- `tests/test_audit_runtime_regressions.py`
- `tests/test_geneva_services.py`
- `tests/test_geneva_web.py`
- missing/needed: tests for REPL/QueryEngine parity

**What is working:**

Regression coverage now catches the previous P0 bugs:

- Soul/BRAIN/DNA injection
- ghost privacy
- identity extraction
- Thai identity recall fallback
- read untrusted prefix
- dream scheduler startup
- LSP removal
- model outcome recording
- task decomposition
- B.L.A.S.T. append
- onboarding no-overwrite

**What is incomplete:**

The tests focus mostly on session/web/runtime services. They do not prove parity across every runtime entrypoint.

**Fix:**

- Add parity tests for Web, REPL, and QueryEngine:
  - identity context injection
  - memory extraction mode
  - context block order
  - ghost or explicit no-ghost support

**Acceptance:**

- One test suite fails if any active runtime path cannot answer "what is my name?" after DNA/memory setup.

---

## Phase R1 — Context Assembly Contract v2

### AUD-R1-01 — R1.2 "Single Context Builder" Is Not Actually Done

**Status:** OPEN
**Severity:** P0
**Files:**

- `src/context_system/builder.py`
- `src/geneva/session.py`
- `src/tool_system/agent_loop.py`
- `src/repl/core.py`
- `src/query_engine.py`

**What is wrong:**

The roadmap says R1 is done and includes "Single context builder". The codebase still has separate builders and prompt composition paths.

**Impact:**

This is the architectural root of several memory/context trust bugs. UX-B6 also depends on this.

**Fix:**

Implement the single context assembly API described in `AUD-02-01`.

**Acceptance:**

- All provider calls receive system context from one assembly object.
- Context ledger/disclosure is derived from the same object, not reconstructed later.

---

## Phase R2 — Memory Quality Engine v2

### AUD-R2-01 — Conflict Auto-SUPERSEDE Is Overstated

**Status:** FIXED — conservative auto-supersede implemented
**Severity:** P1
**Files:**

- `src/memdir/memory_conflicts.py`
- `src/memdir/brain_engine.py`

**What was wrong:**

`memory_conflicts.py` can set:

```python
candidate.suggested_action = "supersede"
```

But `brain_engine.remember()` still queued the conflict and returned:

```python
MemoryResult(operation="conflict", ...)
```

It did not automatically supersede based on the suggested action.

**Impact:**

Roadmap wording said evidence/conflict/trust score auto-resolution was complete, but runtime behavior was "queue for review".

**Fix applied:**

- Implemented safe auto-supersede only when all of these are true:
  - `conflict.suggested_action == "supersede"`
  - new source is `user_direct`
  - memory is not `restricted`
  - existing memory is not `restricted`
  - evidence quote is present
  - new confidence is at least `0.85`
  - memory kind is one of identity/preference/project/decision/feedback
- Restricted conflicts still queue review.
- `search(..., include_archived=True)` now includes `superseded` and `expired` historical memories, not only archived.

**Acceptance:**

- `test_high_confidence_user_correction_supersedes_lower_confidence_memory`
- `test_restricted_memory_conflict_still_requires_review`

---

## Phase R3 — Task & Planning Runtime

### AUD-R3-01 — Pre-Done Verification Is Not A Real Gate Yet

**Status:** OPEN
**Severity:** P1
**Files:**

- `src/geneva/task_planner.py`
- `src/memdir/task_store.py`
- `src/tool_system/agent_loop.py`
- `src/geneva/session.py`

**What is working:**

- Complex intent can create task plans.
- Active task context can be injected.
- Handoff summary helper exists.

**What is wrong:**

Roadmap R3.5 says "Before task marked done -> mandatory verify step." There is no clear task-state transition that forces verification before `done`.

**Impact:**

Geneva can look like it has a planning runtime, but it cannot yet guarantee that planned work is verified before completion.

**Fix:**

- Add task state transition API:
  - `request_done`
  - `verify`
  - `done`
  - `failed`
- Require verification evidence before final `done`.

**Acceptance:**

- Attempting to mark a task done without verification fails.
- Verified task stores evidence command/output or manual verification note.

---

## Phase R4 — Permission & Safety Policy v2

### AUD-R4-01 — Plugin Permission Model Is Still A Deferred/Partial Area

**Status:** PARTIAL
**Severity:** P2
**Files:**

- `src/services/plugins/` or current plugin runtime files
- `src/geneva/plugin_runtime.py`
- `src/geneva/skill_control_plane.py`
- `src/tool_system/registry.py`

**What is working:**

Tool registry and audit logging are stronger now.

**What is incomplete:**

The roadmap describes a full plugin permission model. Current plugin/skill runtime exists, but the permission model should be re-audited before third-party/open-source plugin usage.

**Fix:**

- Add a plugin manifest permission review path.
- Enforce dangerous scope combinations.
- Show first-use approval for sensitive plugin scopes.

**Acceptance:**

- Installing/enabling a plugin with `network + write + destructive` requires explicit approval or is denied.

---

## Phase R5 — Provider Router + Model Calibration v2

### AUD-R5-01 — Route Outcomes Are Recorded In Agent Loop, But Product Mode Contract Is Missing

**Status:** PARTIAL
**Severity:** P1
**Files:**

- `src/services/model_router/router.py`
- `src/services/model_normalizer/capability_registry.py`
- `src/geneva/settings_manager.py`
- missing: `src/services/model_router/modes.py`

**What is working:**

- Task-based router exists.
- `record_outcome()` is called from agent loop.
- Provider health and fallback pieces exist.

**What is incomplete:**

UX-B1 Mode Router Contract is not implemented:

- no `low/medium/high/extra_high` mode profile module
- no `/api/modes`
- no session/project default mode persistence
- settings currently normalize provider/model back to one default OpenRouter model

**Fix:**

Implement UX-B1 lean backend before claiming product-level mode switching.

**Acceptance:**

- `GET /api/modes` returns four profiles.
- Session can set `mode_id`.
- Trace/context summary records selected mode.
- Selected mode changes actual router decision unless explicit advanced override exists.

---

## Phase R6 — Model Behavior Normalizer v2

### AUD-R6-01 — Calibration Claims Need Fresh Evidence Before Release

**Status:** WATCH
**Severity:** P2
**Files:**

- `tests/calibration/`
- `tests/benchmarks/model_normalizer/`
- `src/services/model_normalizer/`

**What to check:**

Roadmap says calibration suite and normalizer are done. Before a release, run the calibration/eval suite and attach current results, because provider/model behavior changes over time.

**Fix:**

- Add a dated calibration report artifact.
- Record model IDs and provider versions/settings.

**Acceptance:**

- Release checklist includes current calibration run, not old green tests only.

---

## Phase R7 — Trace, Replay & Debug Runtime

### AUD-R7-01 — Context Disclosure Should Reuse Trace/Ledger Instead Of Rebuilding Truth

**Status:** OPEN
**Severity:** P1
**Files:**

- `src/geneva/agent_trace.py`
- `src/services/compact/context_ledger.py`
- missing: `src/geneva/context_disclosure.py`

**What is wrong:**

Trace and ledger exist, but UX-B6 needs a user-facing summary. If disclosure is implemented separately from trace/ledger/context assembly, it can drift.

**Fix:**

- Make context disclosure a projection of context assembly + trace/ledger, not a separate guess.

**Acceptance:**

- A turn's context summary and its trace context blocks agree on block labels/counts.

---

## Phase R8 — Eval & Benchmark Harness

### AUD-R8-01 — Benchmark Harness Exists, But Trust-Gate Benchmarks Need To Be Mandatory

**Status:** OPEN
**Severity:** P1
**Files:**

- `tests/benchmarks/`
- `tests/test_audit_runtime_regressions.py`

**What is wrong:**

Benchmarks exist, but the trust-gate scenarios are not yet treated as mandatory release gates.

**Fix:**

Add a small required benchmark set:

- name recall across new session
- ghost turn leaves no persistence
- conflicting identity update
- context disclosure shows DNA/memory use
- read-file prompt injection stays untrusted

**Acceptance:**

- One command runs the trust-gate eval and fails the release if score regresses.

---

## Phase R9 — Artifact Store

### AUD-R9-01 — No P0 Runtime Gap Found In This Pass

**Status:** VERIFIED LIGHTLY
**Severity:** none found
**Files:**

- `src/geneva/artifact_store.py`
- `tests/test_artifact_store.py`

**Note:**

Artifact store appears present and covered by tests, including ghost behavior. This audit did not deep-review product artifact UX-B3, which is a separate deferred product contract.

---

## Phase R10 — Intent Router + Project/Skill Autopilot

### AUD-R10-01 — Skill Autopilot Is Mode-Set, Not Full Auto-Create

**Status:** OPEN
**Severity:** P1
**Files:**

- `src/geneva/session.py`
- `src/geneva/skill_engine.py`
- `src/geneva/skill_control_plane.py`

**What is working:**

When intent is `create_skill`, session enters a skill-builder context.

**What is incomplete:**

Roadmap R10.6 describes:

- collect skill details
- generate `SKILL.md`
- run eval
- activate if passed
- confirm with Bond

Current session routing mainly sets skill-builder mode/context. The full autopilot flow is not automatic end-to-end.

**Fix:**

- Wire `create_skill` intent to a real skill creation workflow with approval gates.
- Use `SkillControlPlane` to create draft, eval, then activate.

**Acceptance:**

- User says "สร้าง skill สำหรับ X" and Geneva creates a draft skill record, asks for missing required fields, runs eval, then activates only after confirmation/pass.

---

### AUD-R10-02 — B.L.A.S.T. Auto-Writer Works For Progress/Todos, But Findings Extraction Is Thin

**Status:** PARTIAL
**Severity:** P2
**Files:**

- `src/geneva/blast_writer.py`
- `src/geneva/session.py`
- `src/geneva/project_store.py`

**What is working:**

- Project creation initializes B.L.A.S.T. files.
- Todos append to `task-plan.md`.
- Project activity appends progress and simple decision-like inputs.

**What is incomplete:**

Roadmap describes extracting decisions/findings/progress after significant turns. Current implementation mostly logs user input and simple decision keyword matches. It does not deeply extract findings from assistant output.

**Fix:**

- Add post-turn classifier/extractor for:
  - findings
  - decisions
  - progress
  - open questions
- Keep writes permission-gated and undoable.

**Acceptance:**

- A research turn appends a real finding to `findings.md`.
- A decision turn appends to `decisions.md`.
- A normal chat turn does not spam B.L.A.S.T. files.

---

## Advanced Capabilities — E2+, G6+, E+, G4+

### AUD-ADV-01 — Google Connector Is Not Fully Usable Without OAuth

**Status:** DEFERRED / PARTIAL
**Severity:** P2
**Files:**

- `src/services/mcp/connectors/google.py`
- `src/services/mcp/connectors/notion.py`
- `src/services/mcp/connectors/github.py`

**What is wrong:**

G4+ says connector runtime is complete with Google/Notion/GitHub connectors. The Google connector code states OAuth flow is deferred to Layer 1.

**Impact:**

The connector framework may be complete, but "Google connector usable by user" is not complete.

**Fix:**

- Update docs to say framework complete, provider OAuth partial.
- Implement OAuth when Layer 1 connector usage becomes required.

**Acceptance:**

- Connector status API distinguishes `framework_ready`, `credentials_configured`, `oauth_ready`, and `usable`.

---

### AUD-ADV-02 — Documents Runtime Is Still WIP/Deferred

**Status:** DEFERRED
**Severity:** P2
**Files:**

- `src/geneva/document_runtime.py`
- roadmap Phase D9+

**What is wrong:**

Roadmap marks D9+ as WIP/deferred. This is not a bug if documented as deferred, but it must not be presented as a current production capability.

**Fix:**

- Keep D9+ out of "complete" summaries until parse/edit/preview/citation trace acceptance is implemented.

---

## Product Alignment Layer — Backend Contracts

### AUD-UXB6-01 — Context Disclosure Contract Is The Next P0 Trust Gate

**Status:** OPEN
**Severity:** P0
**Files:**

- missing: `src/geneva/context_disclosure.py`
- `src/geneva/session.py`
- `src/geneva/web_api.py`
- `src/services/compact/context_ledger.py`

**Fix:**

Implement UX-B6 lean before KU trial:

- per-turn context summary
- API endpoint
- memory/project/tool/source counts
- ghost privacy proof

**Acceptance:**

- User can inspect why Geneva answered from Soul/DNA/memory/project/tools for a specific turn.

---

### AUD-UXB1-01 — Mode Router Contract Is Not Implemented

**Status:** OPEN
**Severity:** P1
**Files:**

- missing: `src/services/model_router/modes.py`
- `src/services/model_router/router.py`
- `src/geneva/settings_manager.py`
- `src/geneva/web_api.py`

**Fix:**

Implement lean mode profiles after UX-B6:

- `low`
- `medium`
- `high`
- `extra_high`

**Acceptance:**

- Mode selection changes actual model/router behavior.
- Mode is visible in trace/context summary.

---

### AUD-UXB0-01 — Product DTO/Label Layer Is Deferred

**Status:** DEFERRED
**Severity:** P2
**Missing files:**

- `src/geneva/product_contracts.py`
- `src/geneva/product_labels.py`

**Note:**

This is intentionally deferred in Current State. It should stay documented as deferred, not complete.

---

### AUD-UXB2-01 — Project Sources Are Deferred

**Status:** DEFERRED
**Severity:** P2
**Missing files:**

- `src/geneva/project_sources.py`
- `src/geneva/source_parser.py`

**Impact:**

Projects can exist, but product-grade source attachment/indexing is not complete.

---

### AUD-UXB3-01 — Product Artifact Model Is Deferred

**Status:** DEFERRED
**Severity:** P2
**Missing files:**

- `src/geneva/product_artifacts.py`

**Impact:**

Technical artifact store exists, but product-level artifact ownership/version/export model is not complete.

---

### AUD-UXB4-01 — Full Brain Search Is Deferred

**Status:** DEFERRED
**Severity:** P2
**Missing files:**

- `src/geneva/search_service.py`

**Impact:**

Memory/project search pieces exist, but unified full-brain search is not production-complete.

---

### AUD-UXB5-01 — Skill Scope/Invocation Product Contract Is Deferred

**Status:** DEFERRED
**Severity:** P2
**Files:**

- `src/geneva/skill_engine.py`
- `src/geneva/skill_control_plane.py`

**Impact:**

Skill engine exists, but product-level invocation/scope transparency is not complete.

---

### AUD-UXB8-01 — Permission + Activity Center Is Deferred

**Status:** DEFERRED
**Severity:** P2
**Files:**

- `src/geneva/audit_log.py`
- `src/tool_system/registry.py`

**Impact:**

Audit logs exist, but product-grade activity center is not complete.

---

### AUD-UXB9-01 — Deep Research Product Flow Is Deferred

**Status:** DEFERRED
**Severity:** P2
**Files:**

- `src/geneva/research_engine.py`

**Impact:**

Deep Research backend is stronger, but product-level research run lifecycle/status UI contract is not complete.

---

### AUD-UXB10-01 — Library Foundation Is Deferred

**Status:** DEFERRED
**Severity:** P2

**Impact:**

No action until sources/artifacts stabilize.

---

### AUD-UXB11-01 — Owner Manual Onboarding Flow Is Deferred/Partial

**Status:** OPEN
**Severity:** P1
**Files:**

- `src/geneva/onboarding.py`
- `projects/second-brain/Geneva Owner Manual.md`
- local DNA files under `~/.geneva/`

**What is wrong:**

Onboarding can generate DNA files, but it is not yet an owner-manual-grade flow for maintaining Soul/BRAIN/DNA over time.

**Fix:**

- Fix canonical path mismatch first (`AUD-00-01`).
- Add review/diff before updating DNA.
- Add explicit owner confirmation for changes to Soul/BRAIN/DNA.

**Acceptance:**

- Updating "my name / priorities / goals / team" shows a diff and writes to canonical DNA only after confirmation.

---

## Fix Order

Do not fix by roadmap order alone. Fix by trust dependency:

1. `AUD-00-01` — canonical onboarding/DNA root — fixed
2. `AUD-02-01` / `AUD-R1-01` — single context assembly API — still open
3. `AUD-UXB6-01` — Context Disclosure backend — Bond-owned next slice
4. `AUD-03-01` — memory extraction parity across Web/REPL/QueryEngine — fixed
5. `AUD-R2-01` — memory conflict auto-supersede or docs correction — fixed
6. `AUD-R3-01` — task pre-done verification gate — still open
7. `AUD-UXB1-01` — lean mode router profiles — Bond-owned next slice
8. `AUD-R10-01` and `AUD-R10-02` — real skill autopilot and richer B.L.A.S.T. extraction
9. `AUD-08-01` — align roadmap/current state/owner manual with runtime truth
10. Deferred Product Alignment items only after KU trust gate

---

## Definition Of "Layer 0/DNA Completeสุดๆ"

Geneva can be called Layer 0/DNA complete only when all of these are true:

- Soul/BRAIN/DNA physical files exist and are canonical.
- All active runtimes load the same Soul/BRAIN/DNA context.
- New identity facts are extracted and recallable across sessions.
- Ghost mode writes nothing persistent.
- Memory writes are visible, undoable, and source-attributed.
- Context disclosure shows what memory/project/tool/source was used.
- Onboarding updates DNA through review/diff, not silent overwrite or duplicate roots.
- Docs match runtime truth: complete means accepted, partial means partial, deferred means deferred.
