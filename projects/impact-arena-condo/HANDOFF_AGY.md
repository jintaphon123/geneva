# HANDOFF — impact-arena-condo

> [!IMPORTANT]
> **From:** Codex  →  **To:** Antigravity
> **Date:** 2026-06-19 14:12 ICT
> **Session Goal:** Execute and prove Phase 6 Task 2 only, then return the evidence and diff to Codex for review before starting Task 3.

## 🗜️ Compact Summary

We are building the Impact Arena Condo LINE operations stack for Guest OA, Housekeeping LINE, and Internal Ops. Phase 6 turns Housekeeping LINE into the real field-execution interface for dispatch, acknowledgement, no-ack escalation, checklists, problem reporting, and access preparation, while Internal Ops remains the control plane. The larger goal is safe room readiness: a guest must never receive room-entry instructions until the booking, room, cleaning, access preparation, incidents, and approved content all pass deterministic gates.

Phase 6 Task 0 and Task 1 are accepted. Task 0 froze the verified baseline in `scratch/phase6_housekeeping_baseline.test.py`. Task 1 added first-class `access_prep_tasks` and `access_prep_task_events`, then required a hardening pass after Codex found that the old `housekeeper_task_focus_valid_focus_check` still blocked `focus_type = 'access_prep'`. The accepted schema now has a valid access-prep focus invariant, `access_prep_task_events.source_event_id` is `NOT NULL`, its source event unique index is non-partial, RLS is enabled, and only `postgres`/`service_role` have table grants.

The selected architecture extends the existing Phase 4 Housekeeping Core instead of rebuilding it. Supabase remains operational truth, n8n orchestrates delivery and schedules, Edge Functions own deterministic behavior, and LINE buttons/Flex/postbacks are the primary field interaction. Cleaning Task and Access Prep Task must remain separate records and lifecycles. Direct Admin/Bond instructions outrank automatic queue ordering. AI may summarize free-text `อื่นๆ` reports but may not mutate task state. Migration filenames must be generated with Supabase CLI, and workflow deployments later in the plan must use export/compare/public API/import/reactivate/export, never direct n8n SQLite edits.

The immediate work is Task 2 of the approved implementation plan: add a transactional Access Prep state service. This batch creates the `access_prep.ts` TypeScript adapter and tests, adds service-role-only RPCs for merging access prep tasks, applying access prep actions, and owner/admin override, and removes the old fallback that treats key/open actions as recently-completed cleaning-task behavior. This is the first state-mutation batch, so it must prove assignment, capability, source-event replay, blocker/restart, cancellation, key custody transitions, and owner override before committing. Stop before Task 3 even if green.

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
> - Use real source event or postback action IDs for idempotency in all task mutations.
> - Task 2 requires explicit Codex review after completion; Task 3 is not authorized yet.

## ✅ Current Status

**Completed this session:**
- Phase 6 Task 0 — accepted after Codex reran the baseline.
- Phase 6 Task 1 — accepted after Antigravity hardening commit `9a1aab3` and Codex evidence commit `9c73b53`.
- Codex verified Task 1 with schema test, diff checks, py_compile, Supabase advisors, and full Phase 6 baseline.

**Files changed:**
- `projects/impact-arena-condo/runtime/supabase/supabase/migrations/20260619065346_phase6_access_prep_task_core.sql` — Task 1 core Access Prep schema.
- `projects/impact-arena-condo/runtime/supabase/supabase/migrations/20260619070456_phase6_access_prep_task_focus_and_event_hardening.sql` — Task 1 focus/idempotency hardening.
- `projects/impact-arena-condo/scratch/phase6_access_prep_schema.test.py` — Task 1 schema verifier.
- `projects/impact-arena-condo/log_AI.md` — Task 1 acceptance evidence.
- `projects/impact-arena-condo/HANDOFF_AGY.md` — this Task 2 worker brief.

**What is NOT done yet:**
- Task 2 transactional Access Prep lifecycle — not started.
- Task 3 combined queue read model — not authorized yet.
- Flex cards, scheduler, problem menu, Internal control, dashboard, and real LINE DoD — later tasks only.

## 🔑 Decisions Made (Do Not Override Without Reason)

| Decision | Rationale |
|----------|-----------|
| Task 1 is accepted only after hardening | The first Task 1 pass had a false-green test and an unusable access-prep focus invariant. |
| Start Task 2 only | Task 2 is the first mutation service and must be reviewable before queue work begins. |
| Access Prep mutations must use separate RPCs | Cleaning completion must not imply key placement or room-open readiness. |
| Source event IDs are non-null for Access Prep events | Task 1 locked idempotency through unique non-null event source IDs. |
| RPCs must be service-role-only SECURITY DEFINER with fixed search_path | Supabase advisors and security review require privileged functions to be intentionally scoped and non-public. |
| Stop before Task 3 | Codex must review lifecycle state, replay behavior, grants, advisors, and regressions before queue work begins. |

## 📁 Read These First (In This Order)

1. `projects/impact-arena-condo/HANDOFF_AGY.md` — current worker contract, authorized scope, and stop condition.
2. `projects/impact-arena-condo/docs/superpowers/plans/2026-06-19-phase6-housekeeping-line-room-readiness-execution.md` — implement Task 2 exactly.
3. `projects/impact-arena-condo/docs/superpowers/specs/2026-06-19-phase6-housekeeping-line-room-readiness-execution-design.md` — approved architecture and behavior.
4. `projects/impact-arena-condo/runtime/supabase/supabase/migrations/20260619065346_phase6_access_prep_task_core.sql` — Task 1 base schema.
5. `projects/impact-arena-condo/runtime/supabase/supabase/migrations/20260619070456_phase6_access_prep_task_focus_and_event_hardening.sql` — accepted focus/idempotency invariant.
6. `projects/impact-arena-condo/runtime/supabase/supabase/functions/housekeeping-handler/state.ts` — current cleaning-task state handling and fallback to remove.
7. `projects/impact-arena-condo/runtime/supabase/supabase/functions/housekeeping-handler/state.test.ts` — current state tests to protect.
8. `projects/impact-arena-condo/runtime/supabase/supabase/functions/housekeeping-handler/index.ts` — request routing context.
9. `projects/impact-arena-condo/scratch/phase6_access_prep_schema.test.py` — schema acceptance expectations.
10. `projects/impact-arena-condo/log_AI.md` — append Task 2 command evidence, advisor summary, and residual gaps.

## 🧠 Active Thinking & Next Action

> [!NOTE]
> **Mid-thought:**
> Task 2 must keep Cleaning and Access Prep separate at the mutation layer. The highest-risk regression is accidentally preserving the old “recently completed cleaning task” fallback for key/open actions, which would let Access Prep readiness drift back into cleaning-task state. The second risk is idempotency: duplicate source events must replay the stored outcome without mutating state twice.

> [!TIP]
> **Next action (do this first):**
> Execute Task 2 only: generate the Supabase RPC migration via CLI, write RED Deno tests for `handleAccessPrepTransition`, prove RED, implement the service-role-only RPCs and TypeScript adapter, update state fallback/tests, push linked DB, run GREEN tests and advisors, append evidence to `log_AI.md`, commit Task 2 files, then stop and report exact diff/output/commit hash to Codex.

**Open questions:**
- If existing cleaning state code still routes key/open actions through completed-cleaning fallback, remove that behavior only as required by Task 2 and prove it with tests.
- If RPC replay needs a stable event payload contract, use `access_prep_task_events.payload` and do not invent n8n-owned state.
- If Supabase advisors show the known Phase 4/5 warnings only, record them as pre-existing; do not fix old debt in this task.

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
