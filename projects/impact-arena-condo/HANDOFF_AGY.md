# HANDOFF — impact-arena-condo

> [!IMPORTANT]
> **From:** Codex  →  **To:** Antigravity
> **Date:** 2026-06-19 13:50 ICT
> **Session Goal:** Execute and prove Phase 6 Task 1 only, then return the evidence and diff to Codex for review before starting Task 2.

## 🗜️ Compact Summary

We are building the Impact Arena Condo LINE operations stack for Guest OA, Housekeeping LINE, and Internal Ops. Phase 6 turns Housekeeping LINE into the real field-execution interface for dispatch, acknowledgement, no-ack escalation, checklists, problem reporting, and access preparation, while Internal Ops remains the control plane. The larger goal is safe room readiness: a guest must never receive room-entry instructions until the booking, room, cleaning, access preparation, incidents, and approved content all pass deterministic gates.

Phase 6 planning is locked and committed. Task 0 has now passed and was reviewed by Codex: Antigravity created the sequential baseline verifier in `scratch/phase6_housekeeping_baseline.test.py` and committed it as `afbed7e93ce39f8f80c3e0aee66c845b08f09f16`; Codex then corrected evidence in `log_AI.md` and committed `1f945a1` after independently running the baseline. The verified baseline command is `python3 scratch/phase6_housekeeping_baseline.test.py`, ending with `PHASE 6 HOUSEKEEPING BASELINE PASSED`. The current runtime has cleaning-task behavior, Housekeeping command handling, existing access capability denial, Internal Ops harness, and n8n workflow contract tests; it does not yet have first-class `access_prep_tasks`, access-prep events, combined queue RPCs, Flex cards, scheduler, or the final room-access readiness contract.

The selected architecture extends the existing Phase 4 Housekeeping Core instead of rebuilding it. Supabase remains operational truth, n8n orchestrates delivery and schedules, Edge Functions own deterministic behavior, and LINE buttons/Flex/postbacks are the primary field interaction. Cleaning Task and Access Prep Task must remain separate records and lifecycles. Direct Admin/Bond instructions outrank automatic queue ordering. AI may summarize free-text `อื่นๆ` reports but may not mutate task state. Migration filenames must be generated with Supabase CLI, and workflow deployments later in the plan must use export/compare/public API/import/reactivate/export, never direct n8n SQLite edits.

The immediate work is Task 1 of the approved implementation plan: add the first-class Access Prep Task schema. This is a database/schema batch only. You must create the migration through `npx supabase migration new phase6_access_prep_task_core`, write a RED schema test, prove the RED failure before applying the migration, implement the canonical schema and grants, push to the linked Supabase database, verify the schema test passes, run Supabase advisors, append exact evidence to `log_AI.md`, commit only Task 1 files if green, and stop before Task 2. If the linked database or Supabase CLI is unavailable, stop and report the exact failure instead of fabricating a migration or weakening assertions.

## 👤 User Preferences & Dislikes (Do Not Violate)

> [!CAUTION]
> **Dislikes / Pain Points (What the user explicitly disliked, rejected, or complained about in this session):**
> - Do not treat Internal Ops as the primary Phase 6 interface; Housekeeping LINE is primary from day one.
> - Do not make the field workflow mostly AI or require users to type slash commands.
> - Do not merge Cleaning Task and Access Prep Task; cleaning may finish long before a guest arrives and key placement has separate security risk.
> - Do not trust a phase-complete claim without runtime or test evidence.
> - Do not edit n8n SQLite directly or use unsafe workflow deployment shortcuts.
>
> **Preferences / Working Style (What the user preferred, style choices, or specific tools they like):**
> - Antigravity is the implementation worker; Codex plans, reviews, audits, and issues the next task.
> - Work in small reviewable batches and report back before crossing a delivery gate.
> - Housekeeping LINE should be button-first and resemble LINE MAN in clarity, using persistent navigation, list cards, Flex buttons, Quick Replies, and postbacks.
> - Use Thai for coordination with Bond, English for code, tests, commit messages, and formal technical artifacts.
>
> **Minor Nuances / Small Details (Specific habits or minor context details that are easy to forget):**
> - Run heavy test suites sequentially on the MacBook Air.
> - Preserve unrelated dirty worktree changes; do not reset, clean, or revert files you did not change.
> - Use real source event or postback action IDs for idempotency in later tasks.
> - Task 1 requires explicit Codex review after completion; Task 2 is not authorized yet.

## ✅ Current Status

**Completed this session:**
- Phase 6 product design — approved and committed as `725c593`.
- Phase 6 implementation plan — written as 16 gated tasks and committed as `2f6b1ad`.
- Phase 6 terminology — Cleaning Task and Access Prep Task separated in project context, glossary, and Housekeeping playbook.
- Task 0 baseline — Antigravity created and committed verifier as `afbed7e93ce39f8f80c3e0aee66c845b08f09f16`.
- Task 0 Codex review — Codex corrected evidence and committed `1f945a1`; baseline passed independently.

**Files changed:**
- `projects/impact-arena-condo/scratch/phase6_housekeeping_baseline.test.py` — sequential baseline verifier from Task 0.
- `projects/impact-arena-condo/log_AI.md` — Task 0 evidence plus Codex review corrections.
- `projects/impact-arena-condo/HANDOFF_AGY.md` — this Task 1 worker brief.

**What is NOT done yet:**
- Task 1 Access Prep schema — not started.
- Task 2 transactional Access Prep state service — not authorized yet.
- Combined queue, cards, scheduler, problem menu, Internal control, dashboard, and real LINE DoD — later tasks only.

## 🔑 Decisions Made (Do Not Override Without Reason)

| Decision | Rationale |
|----------|-----------|
| Task 0 is accepted after Codex correction commit `1f945a1` | Codex reran baseline and fixed evidence drift before allowing schema work. |
| Start Task 1 only | Task 1 is the first database change and must be reviewable before state-service work begins. |
| Generate migration with Supabase CLI | The plan explicitly forbids invented timestamps and requires CLI-generated migration filenames. |
| Prove RED before schema implementation | The plan requires TDD and protects against tests that only validate the final happy path. |
| Keep Access Prep separate from Cleaning | Key custody and guest-entry preparation have different timing, risk, and capabilities from room cleaning. |
| Stop before Task 2 | Codex must review database schema, grants, advisors, and evidence before state mutations are implemented. |

## 📁 Read These First (In This Order)

1. `projects/impact-arena-condo/HANDOFF_AGY.md` — current worker contract, authorized scope, and stop condition.
2. `projects/impact-arena-condo/docs/superpowers/plans/2026-06-19-phase6-housekeeping-line-room-readiness-execution.md` — implement Task 1 exactly, especially lines under "Task 1: Add First-Class Access Prep Task Schema".
3. `projects/impact-arena-condo/docs/superpowers/specs/2026-06-19-phase6-housekeeping-line-room-readiness-execution-design.md` — approved product and architecture decisions.
4. `projects/impact-arena-condo/local-knowledge-repo/GLOSSARY.md` — terminology for Cleaning Task, Access Prep Task, Room Readiness, and LINE surfaces.
5. `projects/impact-arena-condo/local-knowledge-repo/admin-playbooks/housekeeping-line.md` — field behavior and task separation.
6. `projects/impact-arena-condo/runtime/supabase/supabase/migrations/20260610152521_phase4_slice3_housekeeping_core.sql` — existing housekeeping schema pattern, RLS, grants, focus table, and delete behavior.
7. `projects/impact-arena-condo/scratch/phase4_slice3_schema.test.py` — existing Supabase schema-test style to mirror for Task 1.
8. `projects/impact-arena-condo/scratch/phase6_housekeeping_baseline.test.py` — current baseline verifier to rerun if needed.
9. `projects/impact-arena-condo/log_AI.md` — append Task 1 command evidence, RED/GREEN results, advisor output summary, and residual gaps.

## 🧠 Active Thinking & Next Action

> [!NOTE]
> **Mid-thought:**
> Task 1 is the schema foundation for everything after it. The fragile spots are grants/RLS, active booking uniqueness, focus table consistency, and deletion behavior. The schema test should not merely check table existence; it should assert the exact operational constraints that later deterministic state services will depend on. Treat Supabase advisor warnings as a gate: if there are new warnings, document and fix them before committing.

> [!TIP]
> **Next action (do this first):**
> Execute Task 1 only: generate the Supabase migration via CLI, create `scratch/phase6_access_prep_schema.test.py`, run it once to prove the expected RED failure, implement the schema, push to linked Supabase, verify the schema test and advisors, append evidence to `log_AI.md`, commit Task 1 files, then stop and report exact diff/output/commit hash to Codex.

**Open questions:**
- If `npx supabase db push --linked` fails because of local environment or remote state, stop and report exact stderr; do not hand-edit remote DB through another path.
- If existing `housekeeper_task_focus` constraints differ from the plan, inspect the actual migration history and adapt minimally while preserving the intended invariant.
- If Supabase advisors return old warnings unrelated to Task 1, report them separately and identify whether any are new Phase 6 warnings.

<!-- RESUME INSTRUCTIONS
This file is a handoff brief for an incoming AI session.

To resume:
1. Read this file completely.
2. Read every file listed under "📁 Read These First" in order, using the Read tool.
3. Announce your understanding in 3 sections: situation & preferences / what was done / what's next.
4. State the Next Action you will take.
5. Wait for Bond to confirm or redirect before doing anything.

Do not start working before step 5.
-->
