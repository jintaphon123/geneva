# Phase 6 Housekeeping LINE And Room Readiness Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Housekeeping LINE as a button-first field execution surface with a deterministic combined queue, separate Cleaning and Access Prep tasks, Internal Ops control, and a proven Guest OA room-access gate.

**Architecture:** Extend the verified Phase 4 Slice 3 Housekeeping Core. Keep existing `cleaning_tasks` behavior stable, add a separate `access_prep_tasks` lifecycle, expose both through a service-role-only combined queue RPC, and render native LINE Flex/Quick Reply cards from focused TypeScript modules. Supabase remains operational truth, the Edge Function owns deterministic behavior, n8n orchestrates delivery and schedules, Internal Ops owns overrides, and AI is limited to summarizing free-text `อื่นๆ` reports.

**Tech Stack:** Supabase Postgres/RPC/RLS, Supabase Edge Functions with Deno/TypeScript, n8n workflow generators and public API deployment, LINE Messaging API Flex Messages/Quick Replies/Postbacks, Node.js contract tests, Python standard-library live schema/E2E tests, React/TypeScript dashboard.

---

## Read First

- `docs/superpowers/specs/2026-06-19-phase6-housekeeping-line-room-readiness-execution-design.md`
- `ROADMAP_Codex.md` Section 13
- `local-knowledge-repo/GLOSSARY.md`
- `local-knowledge-repo/admin-playbooks/housekeeping-line.md`
- `local-knowledge-repo/sops/housekeeping-dispatch.md`
- `docs/superpowers/plans/2026-06-10-phase4-slice3-housekeeping-minimum.md`
- `runtime/supabase/supabase/functions/housekeeping-handler/commands.ts`
- `runtime/supabase/supabase/functions/housekeeping-handler/state.ts`
- `runtime/supabase/supabase/functions/housekeeping-handler/index.ts`
- `runtime/supabase/supabase/functions/line-webhook-gateway/line_send.ts`
- `scratch/update_housekeeping_action_workflow.mjs`
- `scratch/update_housekeeping_escalation_monitor_workflow.mjs`
- `log_AI.md`

## Global Non-Negotiables

- Housekeeping users operate through buttons. Hidden commands are transport/test fallbacks, not the visible workflow.
- Cleaning Task and Access Prep Task are separate records and separate lifecycles.
- Direct Admin/Bond priority outranks automatic ordering.
- Supabase is the source of operational truth; n8n does not own task state.
- All task mutations are idempotent by real source event/postback action ID.
- Access Prep requires assignment plus capability.
- Owner override preserves blockers and records actor, reason, and timestamp.
- Every problem report creates durable incident evidence and logical notifications for Internal Ops and owner.
- Guest OA remains blocked unless verified stay, stable room, Cleaning Ready, Access Prep Ready, no active access incident, and approved access content all pass.
- Deploy n8n through export/compare/public API/import/reactivate/export. Never edit n8n SQLite directly.
- Generate migration filenames with `npx supabase migration new`; never invent timestamps manually.
- Run heavy test suites sequentially on the MacBook Air. Do not run the full regression matrix in parallel.
- Append decisions, commands, test results, deploy hashes, and residual gaps to `log_AI.md` after every accepted batch.

## Delivery Gates

| Gate | Tasks | Exit condition |
|---|---|---|
| Slice 1A | 0-4 | Access Prep schema/state and combined queue are green |
| Slice 1B | 5-9 | Button-first LINE cards, scheduler, problems, and delivery are green |
| Slice 1C | 10-11 | Internal control and Guest readiness gate are green |
| Slice 2 | 12-13 | `/ops` and dashboard show truthful linked state |
| Slice 3 | 14-16 | Multi-operator hardening, safe deploy, synthetic + Real LINE DoD pass |

Do not start a later gate until the current gate passes and evidence is recorded.

## File Map

### Create

- `scratch/phase6_housekeeping_baseline.test.py`
- `scratch/phase6_access_prep_schema.test.py`
- `runtime/supabase/supabase/functions/housekeeping-handler/access_prep.ts`
- `runtime/supabase/supabase/functions/housekeeping-handler/access_prep.test.ts`
- `runtime/supabase/supabase/functions/housekeeping-handler/queue.ts`
- `runtime/supabase/supabase/functions/housekeeping-handler/queue.test.ts`
- `runtime/supabase/supabase/functions/housekeeping-handler/cards.ts`
- `runtime/supabase/supabase/functions/housekeeping-handler/cards.test.ts`
- `scratch/phase6_line_flex_send.test.ts`
- `scratch/update_phase6_access_prep_scheduler_workflow.mjs`
- `scratch/phase6_access_prep_scheduler.test.mjs`
- `wf_phase6_access_prep_scheduler.json`
- `runtime/n8n/workflows/wf_phase6_access_prep_scheduler.json`
- `scratch/phase6_housekeeping_problem_menu.test.ts`
- `scratch/phase6_internal_housekeeping_control.test.mjs`
- `scratch/phase6_room_access_gate.test.mjs`
- `scratch/phase6_internal_snapshot.test.mjs`
- `scratch/phase6_multi_operator_queue.test.py`
- `scratch/phase6_full_execution_audit.py`
- `docs/superpowers/checklists/2026-06-19-phase6-real-line-dod-script.md`

### Create Through Supabase CLI

- `runtime/supabase/supabase/migrations/*_phase6_access_prep_task_core.sql`
- `runtime/supabase/supabase/migrations/*_phase6_housekeeping_queue_and_override.sql`
- `runtime/supabase/supabase/migrations/*_phase6_room_access_readiness.sql`

### Modify

- `runtime/supabase/supabase/functions/housekeeping-handler/commands.ts`
- `runtime/supabase/supabase/functions/housekeeping-handler/commands.test.ts`
- `runtime/supabase/supabase/functions/housekeeping-handler/state.ts`
- `runtime/supabase/supabase/functions/housekeeping-handler/state.test.ts`
- `runtime/supabase/supabase/functions/housekeeping-handler/index.ts`
- `runtime/supabase/supabase/functions/housekeeping-handler/index.test.ts`
- `runtime/supabase/supabase/functions/line-webhook-gateway/line_send.ts`
- `runtime/supabase/supabase/functions/line-webhook-gateway/line_send.test.ts`
- `runtime/supabase/supabase/functions/line-webhook-gateway/index.ts`
- `scratch/update_housekeeping_action_workflow.mjs`
- `scratch/phase4_housekeeping_action.test.mjs`
- `wf_housekeeping_action.json`
- `runtime/n8n/workflows/wf_housekeeping_action.json`
- `scratch/update_housekeeping_escalation_monitor_workflow.mjs`
- `scratch/phase4_housekeeping_escalation_monitor.test.mjs`
- `wf_housekeeping_escalation_monitor.json`
- `runtime/n8n/workflows/wf_housekeeping_escalation_monitor.json`
- `scratch/update_internal_ops_agent_harness_workflow.mjs`
- `scratch/gemini_agent_loop.js`
- `scratch/phase4_internal_ops_agent_harness.test.mjs`
- `wf_internal_ops_agent_harness.json`
- `runtime/n8n/workflows/wf_internal_ops_agent_harness.json`
- `scratch/update_internal_ops_snapshot_workflow.mjs`
- `scratch/phase4_internal_ops_snapshot.test.mjs`
- `wf_internal_ops_snapshot.json`
- `runtime/n8n/workflows/wf_internal_ops_snapshot.json`
- `scratch/phase5_bundle.mjs`
- `scratch/update_guest_concierge_workflow.mjs`
- `wf_guest_concierge.json`
- `runtime/n8n/workflows/wf_guest_concierge.json`
- `dashboard/src/lib/types.ts`
- `dashboard/src/hooks/useData.ts`
- `dashboard/src/views/TodayView.tsx`
- `dashboard/src/components/BookingDetailPanel.tsx`
- `local-knowledge-repo/GLOSSARY.md`
- `local-knowledge-repo/admin-playbooks/housekeeping-line.md`
- `local-knowledge-repo/sops/housekeeping-dispatch.md`
- `log_AI.md`

## Task 0: Freeze And Verify The Existing Housekeeping Baseline

**Files:**

- Create: `scratch/phase6_housekeeping_baseline.test.py`
- Read: `docs/superpowers/plans/2026-06-10-phase4-slice3-housekeeping-minimum.md`
- Modify: `log_AI.md`

- [ ] **Step 1: Write the baseline verifier**

Create a Python standard-library test that runs the existing suites sequentially:

```python
#!/usr/bin/env python3
import subprocess

COMMANDS = [
    ["deno", "test", "--allow-env",
     "runtime/supabase/supabase/functions/housekeeping-handler/commands.test.ts",
     "runtime/supabase/supabase/functions/housekeeping-handler/state.test.ts",
     "runtime/supabase/supabase/functions/housekeeping-handler/index.test.ts"],
    ["node", "scratch/phase4_housekeeping_action.test.mjs"],
    ["node", "scratch/phase4_housekeeping_escalation_monitor.test.mjs"],
    ["node", "scratch/phase4_internal_ops_agent_harness.test.mjs"],
    ["node", "scratch/phase4_internal_ops_snapshot.test.mjs"],
    ["python3", "scratch/phase5_slice8_access_capabilities.test.py"],
]

for command in COMMANDS:
    result = subprocess.run(command, text=True)
    if result.returncode:
        raise SystemExit(result.returncode)

print("PHASE 6 HOUSEKEEPING BASELINE PASSED")
```

- [ ] **Step 2: Run the baseline verifier**

Run:

```bash
python3 scratch/phase6_housekeeping_baseline.test.py
```

Expected:

```text
PHASE 6 HOUSEKEEPING BASELINE PASSED
```

If a pre-existing suite fails, diagnose and record it before Phase 6 edits. Do not weaken the assertion.

- [ ] **Step 3: Record the baseline**

Append the command, pass counts, n8n version, Deno version, and current workflow source hashes to `log_AI.md`.

- [ ] **Step 4: Commit**

```bash
git add scratch/phase6_housekeeping_baseline.test.py log_AI.md
git commit -m "test: freeze phase 6 housekeeping baseline"
```

## Task 1: Add First-Class Access Prep Task Schema

**Files:**

- Create via CLI: `runtime/supabase/supabase/migrations/*_phase6_access_prep_task_core.sql`
- Create: `scratch/phase6_access_prep_schema.test.py`

- [ ] **Step 1: Generate the migration**

```bash
cd runtime/supabase
npx supabase migration new phase6_access_prep_task_core
cd ../..
```

Use the exact generated path printed by Supabase for every later step in this task.

- [ ] **Step 2: Write RED schema tests**

The test must query `pg_catalog` through the linked database and assert:

```python
EXPECTED_TABLES = {
    "access_prep_tasks",
    "access_prep_task_events",
}

EXPECTED_ACCESS_STATUSES = {
    "new", "sent", "acknowledged", "in_progress",
    "blocked", "done", "no_ack", "canceled", "delivery_failed",
}

EXPECTED_KEY_CUSTODY = {
    "with_owner", "with_operator", "placed_in_room", "unknown",
}
```

Also assert:

- unique active task identity by `booking_id`
- `room_id`, `booking_id`, assigned operator, owner admin, priority, due time,
  ack deadline, status, key custody, capabilities snapshot, blocker, notes,
  override fields, and timestamps exist
- task events have unique non-null `source_event_id`
- RLS is enabled
- `anon` and `authenticated` have no grants
- service role can read/write
- operational references use `ON DELETE SET NULL`
- event ownership uses `ON DELETE CASCADE`

- [ ] **Step 3: Run RED**

```bash
set -a
source runtime/.env
set +a
python3 scratch/phase6_access_prep_schema.test.py
```

Expected:

```text
AssertionError: missing table access_prep_tasks
```

- [ ] **Step 4: Implement the schema**

Use this canonical shape in the generated migration:

```sql
CREATE TABLE public.access_prep_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_key TEXT NOT NULL UNIQUE,
  booking_id UUID NOT NULL REFERENCES public.bookings(id) ON DELETE CASCADE,
  room_id UUID REFERENCES public.rooms(id) ON DELETE SET NULL,
  internal_ops_case_id UUID REFERENCES public.internal_ops_cases(id) ON DELETE SET NULL,
  assigned_housekeeper_id UUID REFERENCES public.housekeepers(id) ON DELETE SET NULL,
  owner_admin_user_id UUID REFERENCES public.admin_users(id) ON DELETE SET NULL,
  priority TEXT NOT NULL DEFAULT 'normal'
    CHECK (priority IN ('urgent', 'high', 'normal')),
  status TEXT NOT NULL DEFAULT 'new'
    CHECK (status IN (
      'new','sent','acknowledged','in_progress','blocked','done',
      'no_ack','canceled','delivery_failed'
    )),
  dispatch_status TEXT NOT NULL DEFAULT 'pending'
    CHECK (dispatch_status IN ('pending','sent','failed')),
  key_custody TEXT NOT NULL DEFAULT 'unknown'
    CHECK (key_custody IN ('with_owner','with_operator','placed_in_room','unknown')),
  capabilities_required JSONB NOT NULL DEFAULT
    '{"can_place_key":true,"can_open_room":true}'::JSONB,
  scheduled_for TIMESTAMPTZ NOT NULL,
  due_at TIMESTAMPTZ,
  ack_due_at TIMESTAMPTZ,
  acknowledged_at TIMESTAMPTZ,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  blocker_reason TEXT,
  instructions TEXT,
  notes TEXT,
  override_reason TEXT,
  overridden_by UUID REFERENCES public.admin_users(id) ON DELETE SET NULL,
  overridden_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX access_prep_tasks_active_booking_unique
  ON public.access_prep_tasks(booking_id)
  WHERE status NOT IN ('done','canceled','delivery_failed');

CREATE TABLE public.access_prep_task_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  access_prep_task_id UUID NOT NULL
    REFERENCES public.access_prep_tasks(id) ON DELETE CASCADE,
  housekeeper_id UUID REFERENCES public.housekeepers(id) ON DELETE SET NULL,
  admin_user_id UUID REFERENCES public.admin_users(id) ON DELETE SET NULL,
  event_type TEXT NOT NULL,
  previous_state TEXT,
  new_state TEXT,
  source_event_id UUID,
  payload JSONB NOT NULL DEFAULT '{}'::JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX access_prep_task_events_source_event_unique
  ON public.access_prep_task_events(source_event_id)
  WHERE source_event_id IS NOT NULL;
```

Extend `housekeeper_task_focus`:

```sql
ALTER TABLE public.housekeeper_task_focus
  ADD COLUMN focused_access_prep_task_id UUID
    REFERENCES public.access_prep_tasks(id) ON DELETE SET NULL;

ALTER TABLE public.housekeeper_task_focus
  DROP CONSTRAINT housekeeper_task_focus_type_check;

ALTER TABLE public.housekeeper_task_focus
  ADD CONSTRAINT housekeeper_task_focus_type_check
  CHECK (focus_type IN ('cleaning','access_prep','field_assistance'));
```

Add RLS, grants, indexes for assigned open tasks, due work, and ack deadlines.

- [ ] **Step 5: Apply and verify**

```bash
cd runtime/supabase
SUPABASE_TELEMETRY_DISABLED=1 npx supabase db push --linked
cd ../..
python3 scratch/phase6_access_prep_schema.test.py
SUPABASE_TELEMETRY_DISABLED=1 npx supabase db advisors --linked --level warn
```

Expected:

- schema test passes
- no new Phase 6 advisor warnings

- [ ] **Step 6: Commit**

```bash
git add runtime/supabase/supabase/migrations scratch/phase6_access_prep_schema.test.py
git commit -m "feat: add phase 6 access prep task schema"
```

## Task 2: Add Transactional Access Prep State Service

**Files:**

- Create: `runtime/supabase/supabase/functions/housekeeping-handler/access_prep.ts`
- Create: `runtime/supabase/supabase/functions/housekeeping-handler/access_prep.test.ts`
- Create via CLI: `runtime/supabase/supabase/migrations/*_phase6_housekeeping_queue_and_override.sql`
- Modify: `runtime/supabase/supabase/functions/housekeeping-handler/state.ts`
- Modify: `runtime/supabase/supabase/functions/housekeeping-handler/state.test.ts`

- [ ] **Step 1: Generate the RPC migration**

```bash
cd runtime/supabase
npx supabase migration new phase6_housekeeping_queue_and_override
cd ../..
```

- [ ] **Step 2: Write RED tests for Access Prep transitions**

Cover:

```typescript
Deno.test("access prep requires assignment and capability", async () => {
  const result = await handleAccessPrepTransition(db, {
    taskId: "task-access-1",
    housekeeperId: "hk-1",
    action: "mark_key_placed",
    sourceEventId: "11111111-1111-4111-8111-111111111111",
  });
  assertEquals(result, {
    ok: false,
    error: "capability_denied",
    required_capability: "can_place_key",
    taskId: "task-access-1",
  });
});

Deno.test("cleaning completion does not complete access prep", async () => {
  const result = await completeCleaningFixture();
  assertEquals(result.cleaningStatus, "completed");
  assertEquals(result.accessPrepStatus, "new");
});

Deno.test("access prep completes only after key and room-open evidence", async () => {
  await markKeyPlaced();
  assertEquals(await currentAccessStatus(), "in_progress");
  await markRoomOpen();
  assertEquals(await currentAccessStatus(), "done");
});
```

Also test:

- `new -> sent -> acknowledged -> in_progress -> done`
- `sent -> no_ack -> acknowledged`
- blocked/restart behavior
- key custody transitions
- duplicate source event replay
- task cancellation
- owner override with preserved blocker
- assignment mismatch
- missing `can_open_room`

- [ ] **Step 3: Run RED**

```bash
deno test --allow-env \
  runtime/supabase/supabase/functions/housekeeping-handler/access_prep.test.ts
```

Expected:

```text
ReferenceError: handleAccessPrepTransition is not defined
```

- [ ] **Step 4: Implement RPC contracts**

Add service-role-only functions:

```sql
public.merge_access_prep_task(p_task JSONB, p_source_event_id UUID)
public.apply_access_prep_task_action(
  p_task_id UUID,
  p_housekeeper_id UUID,
  p_action TEXT,
  p_source_event_id UUID,
  p_payload JSONB DEFAULT '{}'::JSONB
)
public.override_housekeeping_task(
  p_task_kind TEXT,
  p_task_id UUID,
  p_admin_user_id UUID,
  p_reason TEXT,
  p_source_event_id UUID
)
```

All three must:

- be `SECURITY DEFINER SET search_path = public, pg_temp`
- revoke execution from `public`, `anon`, and `authenticated`
- grant execute only to `service_role` and `postgres`
- lock the task row before mutation
- write the event in the same transaction
- replay duplicate source events

- [ ] **Step 5: Implement the TypeScript adapter**

Export:

```typescript
export type HousekeepingTaskKind = "cleaning" | "access_prep";

export async function handleAccessPrepTransition(
  supabase: any,
  input: {
    taskId: string;
    housekeeperId: string;
    action: string;
    sourceEventId: string;
    payload?: Record<string, unknown>;
  },
): Promise<TransitionResult> {
  const { data, error } = await supabase.rpc("apply_access_prep_task_action", {
    p_task_id: input.taskId,
    p_housekeeper_id: input.housekeeperId,
    p_action: input.action,
    p_source_event_id: input.sourceEventId,
    p_payload: input.payload ?? {},
  });
  if (error) {
    return { ok: false, error: "database_error", message: "Access Prep action could not be committed", taskId: input.taskId };
  }
  return data as TransitionResult;
}
```

Do not add Access Prep mutations back into `apply_housekeeping_task_action`.
Remove the old fallback that finds a recently completed Cleaning Task for key/open actions.

- [ ] **Step 6: Run GREEN tests**

```bash
deno test --allow-env \
  runtime/supabase/supabase/functions/housekeeping-handler/access_prep.test.ts \
  runtime/supabase/supabase/functions/housekeeping-handler/state.test.ts
```

Expected: all pass.

- [ ] **Step 7: Apply migration and verify security**

```bash
cd runtime/supabase
SUPABASE_TELEMETRY_DISABLED=1 npx supabase db push --linked
SUPABASE_TELEMETRY_DISABLED=1 npx supabase db advisors --linked --level warn
cd ../..
```

- [ ] **Step 8: Commit**

```bash
git add runtime/supabase/supabase/migrations \
  runtime/supabase/supabase/functions/housekeeping-handler/access_prep.ts \
  runtime/supabase/supabase/functions/housekeeping-handler/access_prep.test.ts \
  runtime/supabase/supabase/functions/housekeeping-handler/state.ts \
  runtime/supabase/supabase/functions/housekeeping-handler/state.test.ts
git commit -m "feat: add transactional access prep lifecycle"
```

## Task 3: Add Combined Queue Read Model And Priority Rules

**Files:**

- Create: `runtime/supabase/supabase/functions/housekeeping-handler/queue.ts`
- Create: `runtime/supabase/supabase/functions/housekeeping-handler/queue.test.ts`
- Modify generated migration from Task 2

- [ ] **Step 1: Write RED queue tests**

Use fixtures with both task kinds:

```typescript
Deno.test("direct admin work outranks automatic work", () => {
  const ordered = orderQueue([
    fixture({ id: "auto-checkin", adminPriorityRank: 0, checkinToday: true }),
    fixture({ id: "direct", adminPriorityRank: 100, checkinToday: false }),
  ]);
  assertEquals(ordered.map((task) => task.id), ["direct", "auto-checkin"]);
});

Deno.test("queue order follows the locked six-level policy", () => {
  const ordered = orderQueue(phase6PriorityFixtures());
  assertEquals(ordered.map((task) => task.id), [
    "admin-direct",
    "checkin-today",
    "access-near-checkin",
    "open-blocker",
    "same-building",
    "earliest-due",
  ]);
});

Deno.test("today view filters current operator and Bangkok due date", () => {
  assertEquals(todayTasks(fixtures, "hk-1", bangkokNow).map((x) => x.id), [
    "cleaning-today", "access-today",
  ]);
});
```

Also test:

- one queue contains both task kinds
- task kind remains explicit
- terminal tasks are excluded
- five items per page
- next/previous cursor is stable
- `รับงาน` chooses highest-priority eligible unacknowledged task
- tasks assigned to another operator are not claimable

- [ ] **Step 2: Run RED**

```bash
deno test \
  runtime/supabase/supabase/functions/housekeeping-handler/queue.test.ts
```

- [ ] **Step 3: Add combined queue RPC**

Add:

```sql
public.get_housekeeping_queue(
  p_housekeeper_id UUID,
  p_view TEXT,
  p_limit INTEGER DEFAULT 5,
  p_cursor JSONB DEFAULT NULL
)
```

Return a stable JSON shape:

```json
{
  "task_kind": "cleaning",
  "task_id": "uuid",
  "room_id": "uuid",
  "room_code": "C5/12/59",
  "booking_id": "uuid",
  "guest_name": "จินตนา",
  "check_in_date": "2026-06-20",
  "priority": "urgent",
  "status": "sent",
  "due_at": "2026-06-20T05:00:00Z",
  "owner_label": "Bond",
  "missing_items": ["water"],
  "linked_task_kind": "access_prep",
  "linked_task_status": "new",
  "admin_priority_rank": 100,
  "queue_rank": [100,1,1,0,"C5",12,"2026-06-20T05:00:00Z","uuid"]
}
```

Use deterministic SQL ranking. Do not use Gemini.

- [ ] **Step 4: Implement focused queue helpers**

Export:

```typescript
export type QueueView = "today" | "all";

export async function loadHousekeepingQueue(
  supabase: any,
  housekeeperId: string,
  view: QueueView,
  cursor: Record<string, unknown> | null,
  limit = 5,
) {
  return await supabase.rpc("get_housekeeping_queue", {
    p_housekeeper_id: housekeeperId,
    p_view: view,
    p_limit: limit,
    p_cursor: cursor,
  });
}
```

- [ ] **Step 5: Run GREEN**

```bash
deno test \
  runtime/supabase/supabase/functions/housekeeping-handler/queue.test.ts
```

- [ ] **Step 6: Commit**

```bash
git add runtime/supabase/supabase/migrations \
  runtime/supabase/supabase/functions/housekeeping-handler/queue.ts \
  runtime/supabase/supabase/functions/housekeeping-handler/queue.test.ts
git commit -m "feat: add deterministic housekeeping queue"
```

## Task 4: Add Button Navigation And Focus Intents

**Files:**

- Modify: `runtime/supabase/supabase/functions/housekeeping-handler/commands.ts`
- Modify: `runtime/supabase/supabase/functions/housekeeping-handler/commands.test.ts`

- [ ] **Step 1: Write RED parser tests**

Add typed intents:

```typescript
| { action: "show_today"; cursor?: string | null }
| { action: "show_queue"; cursor?: string | null }
| { action: "accept_next_task" }
| { action: "show_problem_menu" }
| { action: "show_task_details" }
| { action: "select_task"; task_kind: "cleaning" | "access_prep"; task_id: string }
| { action: "problem_category"; category: "water" | "soap" | "towels" | "damaged_or_lost" | "other" }
```

Tests:

```typescript
assertEquals(parseCommand("/today"), { action: "show_today" });
assertEquals(parseCommand("/queue"), { action: "show_queue" });
assertEquals(parseCommand("/accept"), { action: "accept_next_task" });
assertEquals(parseCommand("/problem"), { action: "show_problem_menu" });
assertEquals(parseCommand("/detail"), { action: "show_task_details" });
```

Postback query strings must parse the same actions. User-visible Thai fallback remains supported.

- [ ] **Step 2: Run RED**

```bash
deno test \
  runtime/supabase/supabase/functions/housekeeping-handler/commands.test.ts
```

- [ ] **Step 3: Implement minimal parsing**

Match exact hidden commands before general Thai parsing:

```typescript
const NAV_COMMANDS: Record<string, HousekeepingIntent> = {
  "/today": { action: "show_today" },
  "/queue": { action: "show_queue" },
  "/accept": { action: "accept_next_task" },
  "/problem": { action: "show_problem_menu" },
  "/detail": { action: "show_task_details" },
};
```

Do not expose the commands in normal Housekeeping reply copy.

- [ ] **Step 4: Run GREEN**

```bash
deno test \
  runtime/supabase/supabase/functions/housekeeping-handler/commands.test.ts
```

- [ ] **Step 5: Commit**

```bash
git add runtime/supabase/supabase/functions/housekeeping-handler/commands.ts \
  runtime/supabase/supabase/functions/housekeeping-handler/commands.test.ts
git commit -m "feat: add housekeeping button action intents"
```

## Task 5: Add Native LINE Flex Message Transport

**Files:**

- Modify: `runtime/supabase/supabase/functions/line-webhook-gateway/line_send.ts`
- Modify: `runtime/supabase/supabase/functions/line-webhook-gateway/line_send.test.ts`
- Modify: `runtime/supabase/supabase/functions/line-webhook-gateway/index.ts`
- Create: `scratch/phase6_line_flex_send.test.ts`

- [ ] **Step 1: Write RED transport tests**

Add a raw-message input:

```typescript
type LineSendInput = {
  to: string;
  messages?: Record<string, unknown>[];
  text?: string;
  texts?: string[];
  images?: LineImage[];
  quickReply?: unknown;
};
```

Tests must prove:

```typescript
const flex = {
  type: "flex",
  altText: "คิวงานแม่บ้าน 5 งาน",
  contents: { type: "carousel", contents: [] },
};
assertEquals(buildLinePushPayload({ to: "U1", messages: [flex] }), {
  to: "U1",
  messages: [flex],
});
```

Also reject:

- more than five LINE messages
- Flex without `altText`
- unsupported message type
- mixing `messages` with legacy `texts/images`
- raw `to` or reply token missing

- [ ] **Step 2: Run RED**

```bash
deno test \
  runtime/supabase/supabase/functions/line-webhook-gateway/line_send.test.ts \
  scratch/phase6_line_flex_send.test.ts
```

- [ ] **Step 3: Implement bounded raw message support**

Use:

```typescript
const ALLOWED_LINE_MESSAGE_TYPES = new Set([
  "text", "image", "flex",
]);

function validateRawMessages(messages: unknown[]): Record<string, unknown>[] {
  if (messages.length < 1 || messages.length > 5) {
    throw new Error("line_message_payload_exceeds_limit");
  }
  return messages.map((message) => {
    if (!message || typeof message !== "object") {
      throw new Error("invalid_line_message");
    }
    const type = (message as any).type;
    if (!ALLOWED_LINE_MESSAGE_TYPES.has(type)) {
      throw new Error("unsupported_line_message_type");
    }
    if (type === "flex" && typeof (message as any).altText !== "string") {
      throw new Error("missing_flex_alt_text");
    }
    return message as Record<string, unknown>;
  });
}
```

Persist the exact bounded raw payload in `outbound_messages.payload`.

- [ ] **Step 4: Run GREEN**

```bash
deno test \
  runtime/supabase/supabase/functions/line-webhook-gateway/line_send.test.ts \
  scratch/phase6_line_flex_send.test.ts
```

- [ ] **Step 5: Commit**

```bash
git add runtime/supabase/supabase/functions/line-webhook-gateway \
  scratch/phase6_line_flex_send.test.ts
git commit -m "feat: support bounded LINE flex messages"
```

## Task 6: Build Queue And Task Flex Cards

**Files:**

- Create: `runtime/supabase/supabase/functions/housekeeping-handler/cards.ts`
- Create: `runtime/supabase/supabase/functions/housekeeping-handler/cards.test.ts`
- Modify: `runtime/supabase/supabase/functions/housekeeping-handler/index.ts`
- Modify: `runtime/supabase/supabase/functions/housekeeping-handler/index.test.ts`

- [ ] **Step 1: Write RED card snapshot tests**

Export:

```typescript
export function buildQueueFlexMessage(input: QueuePage, secret: string): Promise<LineFlexMessage>;
export function buildTaskDetailFlexMessage(input: TaskDetail, secret: string): Promise<LineFlexMessage>;
export function buildProblemMenuFlexMessage(input: FocusedTask, secret: string): Promise<LineFlexMessage>;
```

Assert:

- max five bubbles
- red/yellow/green/grey status palette
- room and task type are first-viewport information
- short guest name only
- no phone/full reservation/database UUID visible
- one dominant action per state
- all mutations are signed postbacks
- pagination buttons use signed cursor payload
- Access Prep and Cleaning dependencies are visible but separate

- [ ] **Step 2: Run RED**

```bash
deno test \
  runtime/supabase/supabase/functions/housekeeping-handler/cards.test.ts
```

- [ ] **Step 3: Implement the renderer**

Use LINE Flex `carousel` with one bubble per task:

```typescript
return {
  type: "flex",
  altText: `คิวงานแม่บ้าน ${page.items.length} งาน`,
  contents: {
    type: "carousel",
    contents: page.items.map((task) => buildTaskBubble(task, secret)),
  },
};
```

Keep renderer pure. It receives already-authorized task data and returns JSON.
Do not query Supabase inside `cards.ts`.

- [ ] **Step 4: Route navigation intents in the handler**

In `index.ts`:

```typescript
if (intent.action === "show_today" || intent.action === "show_queue") {
  const page = await loadHousekeepingQueue(
    supabase,
    housekeeper.id,
    intent.action === "show_today" ? "today" : "all",
    decodeCursor(intent.cursor),
    5,
  );
  return jsonResponse({
    ok: true,
    action: intent.action,
    housekeeping_reply: {
      messages: [await buildQueueFlexMessage(page, expectedSecret)],
    },
    internal_notification: null,
    evidence: { view: page.view, count: page.items.length },
  });
}
```

Move card-building logic out of `index.ts`; retain existing Quick Reply fallback.

- [ ] **Step 5: Run GREEN**

```bash
deno test --allow-env \
  runtime/supabase/supabase/functions/housekeeping-handler/cards.test.ts \
  runtime/supabase/supabase/functions/housekeeping-handler/index.test.ts
```

- [ ] **Step 6: Commit**

```bash
git add runtime/supabase/supabase/functions/housekeeping-handler/cards.ts \
  runtime/supabase/supabase/functions/housekeeping-handler/cards.test.ts \
  runtime/supabase/supabase/functions/housekeeping-handler/index.ts \
  runtime/supabase/supabase/functions/housekeeping-handler/index.test.ts
git commit -m "feat: add housekeeping flex queue cards"
```

## Task 7: Wire Flex Messages Through The Housekeeping Workflow

**Files:**

- Modify: `scratch/update_housekeeping_action_workflow.mjs`
- Modify: `scratch/phase4_housekeeping_action.test.mjs`
- Modify: `wf_housekeeping_action.json`
- Modify: `runtime/n8n/workflows/wf_housekeeping_action.json`

- [ ] **Step 1: Add RED workflow assertions**

Assert the LINE send body forwards:

```javascript
messages: $json.housekeeping_reply?.messages ?? undefined,
text: $json.housekeeping_reply?.text ?? undefined,
quickReply: $json.housekeeping_reply?.quickReply ?? undefined,
```

Also assert:

- no Gemini node
- Internal notification remains separate
- incident candidate still reaches the incident RPC path
- empty Housekeeping reply does not send

- [ ] **Step 2: Run RED**

```bash
node scratch/phase4_housekeeping_action.test.mjs
```

- [ ] **Step 3: Update the generator and regenerate**

```bash
node scratch/update_housekeeping_action_workflow.mjs
node scratch/phase4_housekeeping_action.test.mjs
```

Expected: workflow contract passes.

- [ ] **Step 4: Commit**

```bash
git add scratch/update_housekeeping_action_workflow.mjs \
  scratch/phase4_housekeeping_action.test.mjs \
  wf_housekeeping_action.json \
  runtime/n8n/workflows/wf_housekeeping_action.json
git commit -m "feat: deliver housekeeping flex cards"
```

## Task 8: Add T-1 And Same-Day Access Prep Automation

**Files:**

- Create: `scratch/update_phase6_access_prep_scheduler_workflow.mjs`
- Create: `scratch/phase6_access_prep_scheduler.test.mjs`
- Create: `wf_phase6_access_prep_scheduler.json`
- Create: `runtime/n8n/workflows/wf_phase6_access_prep_scheduler.json`
- Modify generated migration from Task 2

- [ ] **Step 1: Write RED scheduler tests**

Test deterministic decisions:

```javascript
assert.deepEqual(scheduleFor(checkIn("2026-06-20"), now("2026-06-19T18:00:00+07:00")), {
  create: true,
  priority: "normal",
  notifyInternal: true,
});

assert.equal(escalationAt("2026-06-19T22:00:00+07:00").priority, "urgent");
assert.equal(escalationAt("2026-06-20T09:00:00+07:00").hardBlock, true);
assert.equal(sameDayBooking().priority, "urgent");
```

Also test:

- canceled/no-show bookings are excluded
- room reassignment cancels old task and creates new
- check-in date change reschedules task
- duplicate schedule runs merge, not duplicate
- same-day creation notifies Internal Ops

- [ ] **Step 2: Run RED**

```bash
node scratch/phase6_access_prep_scheduler.test.mjs
```

- [ ] **Step 3: Add scheduler RPC**

Add:

```sql
public.claim_access_prep_schedule(
  p_now TIMESTAMPTZ,
  p_limit INTEGER DEFAULT 50
)
```

The RPC must atomically return actions:

- `create_t_minus_one`
- `escalate_22`
- `hard_block_09`
- `cancel_obsolete`
- `same_day_urgent`

Use Asia/Bangkok date boundaries explicitly.

- [ ] **Step 4: Generate workflow**

Workflow:

1. schedule every 5 minutes
2. call `claim_access_prep_schedule`
3. loop through every claimed action
4. merge/cancel/escalate task through RPC
5. report Internal Ops/owner incident for urgent or hard-block action
6. finalize action evidence

Do not send Guest OA.

- [ ] **Step 5: Run GREEN**

```bash
node scratch/update_phase6_access_prep_scheduler_workflow.mjs
node scratch/phase6_access_prep_scheduler.test.mjs
```

- [ ] **Step 6: Commit**

```bash
git add runtime/supabase/supabase/migrations \
  scratch/update_phase6_access_prep_scheduler_workflow.mjs \
  scratch/phase6_access_prep_scheduler.test.mjs \
  wf_phase6_access_prep_scheduler.json \
  runtime/n8n/workflows/wf_phase6_access_prep_scheduler.json
git commit -m "feat: schedule access prep tasks"
```

## Task 9: Add Button Problem Menu, Incidents, And Optional Photo Evidence

**Files:**

- Create: `scratch/phase6_housekeeping_problem_menu.test.ts`
- Modify: `runtime/supabase/supabase/functions/housekeeping-handler/commands.ts`
- Modify: `runtime/supabase/supabase/functions/housekeeping-handler/index.ts`
- Modify: `runtime/supabase/supabase/functions/housekeeping-handler/index.test.ts`
- Modify: `scratch/update_housekeeping_action_workflow.mjs`

- [ ] **Step 1: Write RED tests**

Prove:

- water/soap/towels update structured checklist and block normal completion
- damaged/lost item stores description and optional LINE media reference
- `อื่นๆ` produces `needs_classification=true`
- every category calls `report_operational_incident`
- incident requires `internal_ops` and `owner`
- AI summary cannot mutate task state

Example:

```typescript
assertEquals(parseCommand("action=problem_category&category=water&task_id=...&sig=..."), {
  action: "problem_category",
  category: "water",
});
```

- [ ] **Step 2: Run RED**

```bash
deno test --allow-env \
  scratch/phase6_housekeeping_problem_menu.test.ts \
  runtime/supabase/supabase/functions/housekeeping-handler/index.test.ts
```

- [ ] **Step 3: Implement problem categories**

Canonical mapping:

```typescript
const PROBLEM_CATEGORY_TO_ITEM = {
  water: "water",
  soap: "soap",
  towels: "towels",
} as const;
```

For `damaged_or_lost` and `other`, prompt for one follow-up text/photo if detail is absent. Persist inbound media metadata; do not run image understanding.

- [ ] **Step 4: Run GREEN**

```bash
deno test --allow-env \
  scratch/phase6_housekeeping_problem_menu.test.ts \
  runtime/supabase/supabase/functions/housekeeping-handler/index.test.ts
```

- [ ] **Step 5: Commit**

```bash
git add scratch/phase6_housekeeping_problem_menu.test.ts \
  runtime/supabase/supabase/functions/housekeeping-handler \
  scratch/update_housekeeping_action_workflow.mjs
git commit -m "feat: add housekeeping problem menu"
```

## Task 10: Add Internal Ops Task Control And Owner Override

**Files:**

- Create: `scratch/phase6_internal_housekeeping_control.test.mjs`
- Modify: `scratch/gemini_agent_loop.js`
- Modify: `scratch/update_internal_ops_agent_harness_workflow.mjs`
- Modify: `scratch/phase4_internal_ops_agent_harness.test.mjs`
- Modify: `wf_internal_ops_agent_harness.json`
- Modify: `runtime/n8n/workflows/wf_internal_ops_agent_harness.json`

- [ ] **Step 1: Write RED tool-contract tests**

Add deterministic tools:

```javascript
create_or_update_access_prep_task
get_housekeeping_queue
get_room_readiness
reassign_housekeeping_task
override_housekeeping_task
cancel_housekeeping_task
```

Test natural Internal messages:

```text
พรุ่งนี้ห้อง C5/12/59 มีลูกค้าเข้า สร้างงานเตรียมกุญแจให้ฉัน
ส่งงานวางกุญแจ C5/12/59 ให้แม่บ้านคนนี้
ห้อง C5/12/59 เสร็จแล้ว ปิดงานแม้ยังขาดน้ำ เหตุผลฉันตรวจเองแล้ว
ย้ายงานทำความสะอาด C5/12/59 ขึ้นอันดับแรก
```

Assertions:

- direct admin priority rank is highest
- override requires a non-empty reason
- blocker evidence remains
- response states whether Cleaning Ready, Access Prep Ready, and Guest OA blocked
- ambiguous room/booking/operator causes clarification and no mutation

- [ ] **Step 2: Run RED**

```bash
node scratch/phase6_internal_housekeeping_control.test.mjs
```

- [ ] **Step 3: Implement deterministic tool wrappers**

Tool results must have:

```json
{
  "ok": true,
  "task_kind": "access_prep",
  "task_id": "uuid",
  "room_code": "C5/12/59",
  "status": "done",
  "cleaning_ready": false,
  "access_prep_ready": true,
  "room_access_ready": false,
  "guest_oa_blocked": true,
  "evidence": ["owner_override", "missing_water_preserved"]
}
```

Gemini may choose a declared tool after deterministic target resolution. Gemini
must not manufacture a success response when the tool fails.

- [ ] **Step 4: Regenerate and run GREEN**

```bash
node scratch/update_internal_ops_agent_harness_workflow.mjs
node scratch/phase6_internal_housekeeping_control.test.mjs
node scratch/phase4_internal_ops_agent_harness.test.mjs
```

- [ ] **Step 5: Commit**

```bash
git add scratch/gemini_agent_loop.js \
  scratch/update_internal_ops_agent_harness_workflow.mjs \
  scratch/phase6_internal_housekeeping_control.test.mjs \
  scratch/phase4_internal_ops_agent_harness.test.mjs \
  wf_internal_ops_agent_harness.json \
  runtime/n8n/workflows/wf_internal_ops_agent_harness.json
git commit -m "feat: add internal housekeeping control tools"
```

## Task 11: Make Room Access Readiness A Single Deterministic Contract

**Files:**

- Create via CLI: `runtime/supabase/supabase/migrations/*_phase6_room_access_readiness.sql`
- Create: `scratch/phase6_room_access_gate.test.mjs`
- Modify: `scratch/phase5_bundle.mjs`
- Modify: `scratch/update_guest_concierge_workflow.mjs`
- Modify: `wf_guest_concierge.json`
- Modify: `runtime/n8n/workflows/wf_guest_concierge.json`
- Modify: `dashboard/src/lib/types.ts`

- [ ] **Step 1: Generate migration**

```bash
cd runtime/supabase
npx supabase migration new phase6_room_access_readiness
cd ../..
```

- [ ] **Step 2: Write RED readiness tests**

Scenarios:

```javascript
assert.equal(verdict({ verified: true, clean: true, access: false }).ready, false);
assert.equal(verdict({ verified: true, clean: false, access: true }).ready, false);
assert.equal(verdict({ verified: true, clean: true, access: true, incident: true }).ready, false);
assert.equal(verdict({ verified: true, clean: true, access: true, incident: false, asset: true }).ready, true);
assert.equal(verdict({ ownerOverride: true, missingWaterPreserved: true }).ready, false);
```

Also prove:

- room assignment changed after Access Prep blocks readiness
- canceled Access Prep task blocks readiness
- stale completed Cleaning Task for an old booking does not unlock a new stay
- capability-denied action does not change readiness

- [ ] **Step 3: Run RED**

```bash
node scratch/phase6_room_access_gate.test.mjs
```

- [ ] **Step 4: Implement RPC**

Add:

```sql
public.get_room_access_readiness(p_booking_id UUID)
```

Return:

```json
{
  "ready": false,
  "booking_verified": true,
  "room_assignment_stable": true,
  "cleaning_ready": true,
  "access_prep_ready": false,
  "active_access_incident": false,
  "approved_access_content": true,
  "blockers": ["access_prep_incomplete"]
}
```

The RPC is the canonical read contract for Guest OA, Internal Ops, and dashboard.

- [ ] **Step 5: Replace duplicated readiness inference**

Guest workflow and dashboard must consume the RPC result. Retain local fallback
only for explicit runtime failure and fail closed:

```typescript
if (!readiness || readiness.ready !== true) {
  return { ready: false, blockers: readiness?.blockers ?? ["readiness_unknown"] };
}
```

- [ ] **Step 6: Regenerate and run GREEN**

```bash
node scratch/update_guest_concierge_workflow.mjs
node scratch/phase6_room_access_gate.test.mjs
python3 scratch/phase5_slice4_workflow.test.py
```

Expected:

- Guest entry asset is suppressed before readiness
- Guest entry asset becomes eligible only after full readiness

- [ ] **Step 7: Commit**

```bash
git add runtime/supabase/supabase/migrations \
  scratch/phase6_room_access_gate.test.mjs \
  scratch/phase5_bundle.mjs \
  scratch/update_guest_concierge_workflow.mjs \
  wf_guest_concierge.json \
  runtime/n8n/workflows/wf_guest_concierge.json \
  dashboard/src/lib/types.ts
git commit -m "feat: centralize room access readiness"
```

## Task 12: Add Internal Snapshot Visibility

**Files:**

- Create: `scratch/phase6_internal_snapshot.test.mjs`
- Modify: `scratch/update_internal_ops_snapshot_workflow.mjs`
- Modify: `scratch/phase4_internal_ops_snapshot.test.mjs`
- Modify: `wf_internal_ops_snapshot.json`
- Modify: `runtime/n8n/workflows/wf_internal_ops_snapshot.json`

- [ ] **Step 1: Write RED snapshot tests**

Require `/ops` to show:

- Cleaning Tasks: sent/ack/in-progress/blocked/no-ack
- Access Prep Tasks: scheduled/urgent/hard-block/done
- missing checklist items
- key custody
- task owner
- linked task state
- Guest OA room-access blocked reason

Use human labels; do not expose raw enums or UUIDs.

- [ ] **Step 2: Run RED**

```bash
node scratch/phase6_internal_snapshot.test.mjs
```

- [ ] **Step 3: Implement the snapshot section**

Use `get_housekeeping_queue` and `get_room_access_readiness`; do not reconstruct
readiness independently in JavaScript.

- [ ] **Step 4: Regenerate and run GREEN**

```bash
node scratch/update_internal_ops_snapshot_workflow.mjs
node scratch/phase6_internal_snapshot.test.mjs
node scratch/phase4_internal_ops_snapshot.test.mjs
```

- [ ] **Step 5: Commit**

```bash
git add scratch/update_internal_ops_snapshot_workflow.mjs \
  scratch/phase6_internal_snapshot.test.mjs \
  scratch/phase4_internal_ops_snapshot.test.mjs \
  wf_internal_ops_snapshot.json \
  runtime/n8n/workflows/wf_internal_ops_snapshot.json
git commit -m "feat: show housekeeping truth in ops snapshot"
```

## Task 13: Align Dashboard Read Models

**Files:**

- Modify: `dashboard/src/lib/types.ts`
- Modify: `dashboard/src/hooks/useData.ts`
- Modify: `dashboard/src/views/TodayView.tsx`
- Modify: `dashboard/src/components/BookingDetailPanel.tsx`

- [ ] **Step 1: Add the types**

```typescript
export interface AccessPrepTask {
  id: string;
  booking_id: string;
  room_id: string | null;
  priority: 'urgent' | 'high' | 'normal';
  status: 'new' | 'sent' | 'acknowledged' | 'in_progress' | 'blocked' | 'done' | 'no_ack' | 'canceled' | 'delivery_failed';
  key_custody: 'with_owner' | 'with_operator' | 'placed_in_room' | 'unknown';
  due_at: string | null;
  blocker_reason: string | null;
}
```

Add labels for all actual existing cleaning statuses:

```typescript
pending_dispatch, waiting_ack, acknowledged, in_progress, blocked,
completed, delivery_failed, no_ack, canceled
```

- [ ] **Step 2: Load Access Prep Tasks**

Add tolerant query and Realtime subscription:

```typescript
supabase
  .from("access_prep_tasks")
  .select("id,booking_id,room_id,priority,status,key_custody,due_at,blocker_reason,assigned_housekeeper_id,owner_admin_user_id")
  .not("status", "in", '("done","canceled")');
```

- [ ] **Step 3: Update Today and Booking Detail**

Show Cleaning and Access Prep as separate rows/cards with linked readiness.
Owner override must show a visible warning.

- [ ] **Step 4: Build**

```bash
cd dashboard
npm run build
```

Expected: TypeScript/Vite build succeeds.

- [ ] **Step 5: Commit**

```bash
git add dashboard/src
git commit -m "feat: show phase 6 readiness in dashboard"
```

## Task 14: Harden Multi-Operator Assignment And Queue Concurrency

**Files:**

- Create: `scratch/phase6_multi_operator_queue.test.py`
- Modify generated migration from Task 2
- Modify: `runtime/supabase/supabase/functions/housekeeping-handler/queue.ts`
- Modify: `runtime/supabase/supabase/functions/housekeeping-handler/queue.test.ts`

- [ ] **Step 1: Write RED concurrency tests**

Test:

- two operators cannot accept the same unassigned task
- assigned operator sees the task; other operator does not
- direct admin reassignment invalidates old focus
- queue pagination remains stable during unrelated task insert
- building/floor efficiency applies only after admin/check-in/access/blocker ranks
- operator capacity does not demote explicit admin priority

- [ ] **Step 2: Run RED**

```bash
set -a
source runtime/.env
set +a
python3 scratch/phase6_multi_operator_queue.test.py
```

- [ ] **Step 3: Add atomic claim RPC**

```sql
public.claim_housekeeping_task(
  p_task_kind TEXT,
  p_task_id UUID,
  p_housekeeper_id UUID,
  p_source_event_id UUID
)
```

Use conditional update/row lock and return `already_claimed` without mutation.

- [ ] **Step 4: Run GREEN**

```bash
python3 scratch/phase6_multi_operator_queue.test.py
deno test runtime/supabase/supabase/functions/housekeeping-handler/queue.test.ts
```

- [ ] **Step 5: Commit**

```bash
git add runtime/supabase/supabase/migrations \
  runtime/supabase/supabase/functions/housekeeping-handler/queue.ts \
  runtime/supabase/supabase/functions/housekeeping-handler/queue.test.ts \
  scratch/phase6_multi_operator_queue.test.py
git commit -m "feat: harden multi-operator housekeeping claims"
```

## Task 15: Full Regression, Safe Deploy, And Synthetic Acceptance

**Files:**

- Create: `scratch/phase6_full_execution_audit.py`
- Modify: `log_AI.md`

- [ ] **Step 1: Write the synthetic audit**

The audit creates isolated fixtures and exercises:

- direct Admin priority task
- button queue view
- accept/start
- missing water
- incident + dual logical notifications
- blocked completion
- restore and complete
- Access Prep remains separate
- unauthorized Access Prep rejection
- authorized Access Prep completion
- same-day urgent creation
- no-ack thresholds
- owner override with preserved blocker
- Guest OA blocked/unblocked
- duplicate postback replay

Final assertion:

```python
FAILURE_KEYS = [
    "queue_priority_wrong",
    "duplicate_task_created",
    "missing_dual_notification",
    "completion_not_blocked",
    "access_prep_coupled_to_cleaning",
    "capability_gate_failed",
    "owner_override_lost_evidence",
    "guest_gate_opened_early",
    "postback_not_idempotent",
]
```

- [ ] **Step 2: Run all Phase 6 tests sequentially**

```bash
python3 scratch/phase6_housekeeping_baseline.test.py
python3 scratch/phase6_access_prep_schema.test.py
deno test --allow-env runtime/supabase/supabase/functions/housekeeping-handler
deno test runtime/supabase/supabase/functions/line-webhook-gateway/line_send.test.ts
node scratch/phase4_housekeeping_action.test.mjs
node scratch/phase4_housekeeping_escalation_monitor.test.mjs
node scratch/phase6_access_prep_scheduler.test.mjs
node scratch/phase6_internal_housekeeping_control.test.mjs
node scratch/phase6_room_access_gate.test.mjs
node scratch/phase6_internal_snapshot.test.mjs
python3 scratch/phase6_multi_operator_queue.test.py
python3 scratch/phase6_full_execution_audit.py assert
```

Expected: every command passes and final output is:

```text
ALL PHASE 6 SYNTHETIC ACCEPTANCE CRITERIA PASSED
```

- [ ] **Step 3: Export live workflows before deploy**

Export and hash:

- Gateway
- Housekeeping Action
- Housekeeping Escalation Monitor
- Phase 6 Access Prep Scheduler
- Internal Ops Agent Harness
- Internal Ops Snapshot
- Guest Concierge

Save under:

```text
scratch/live-exports/2026-06-19-phase6-predeploy/
```

- [ ] **Step 4: Deploy Supabase**

```bash
cd runtime/supabase
SUPABASE_TELEMETRY_DISABLED=1 npx supabase db push --linked
npx supabase functions deploy housekeeping-handler --no-verify-jwt
npx supabase functions deploy line-webhook-gateway --no-verify-jwt
cd ../..
```

- [ ] **Step 5: Deploy only changed n8n workflows**

Require `N8N_API_KEY` in the process environment; do not read or print a raw key
from Markdown, logs, or source. Deploy each changed workflow explicitly:

```bash
N8N_API_KEY="$N8N_API_KEY" node scratch/deploy_n8n_workflow_via_api.mjs \
  --file wf_housekeeping_action.json \
  --id impact-housekeeping-action \
  --reactivate

N8N_API_KEY="$N8N_API_KEY" node scratch/deploy_n8n_workflow_via_api.mjs \
  --file wf_housekeeping_escalation_monitor.json \
  --id impact-housekeeping-escalation-monitor \
  --reactivate

N8N_API_KEY="$N8N_API_KEY" node scratch/deploy_n8n_workflow_via_api.mjs \
  --file wf_phase6_access_prep_scheduler.json \
  --id impact-phase6-access-prep-scheduler \
  --reactivate

N8N_API_KEY="$N8N_API_KEY" node scratch/deploy_n8n_workflow_via_api.mjs \
  --file wf_internal_ops_agent_harness.json \
  --id impact-internal-ops-agent-harness \
  --reactivate

N8N_API_KEY="$N8N_API_KEY" node scratch/deploy_n8n_workflow_via_api.mjs \
  --file wf_internal_ops_snapshot.json \
  --id impact-internal-ops-snapshot \
  --reactivate
```

Deploy Guest Concierge only when Task 11 produced a source diff:

```bash
N8N_API_KEY="$N8N_API_KEY" node scratch/deploy_n8n_workflow_via_api.mjs \
  --file wf_guest_concierge.json \
  --id impact-guest-concierge \
  --reactivate
```

For every invocation, preserve the helper output showing workflow ID, active
state, and node count. Do not restart or republish unrelated workflows.

- [ ] **Step 6: Export after deploy and compare**

Save under:

```text
scratch/live-exports/2026-06-19-phase6-postdeploy/
```

Assert:

- changed workflow hashes equal source
- unrelated workflow hashes equal predeploy
- Guest Concierge changes only if Task 11 required them

- [ ] **Step 7: Run controlled live backend smoke**

Run the synthetic audit against live n8n/Edge/Supabase without real LINE
recipients. Clean all fixture rows.

- [ ] **Step 8: Record evidence and commit**

Append commands, hashes, test outputs, migration names, and residual risks to
`log_AI.md`.

```bash
git add scratch/phase6_full_execution_audit.py log_AI.md
git commit -m "test: accept phase 6 synthetic execution"
```

## Task 16: Real LINE Definition Of Done And Phase Close

**Files:**

- Create: `docs/superpowers/checklists/2026-06-19-phase6-real-line-dod-script.md`
- Modify: `log_AI.md`
- Modify: `HANDOFF.md`

- [ ] **Step 1: Write the Real LINE script**

The checklist must use button labels, not slash commands:

1. Bond taps `งานวันนี้`
2. Bond taps `คิวงาน`
3. verify five cards and page navigation
4. tap `รับงาน`
5. confirm task
6. tap `เริ่มทำ`
7. tap `แจ้งปัญหา`
8. tap `ไม่ได้ใส่น้ำ`
9. verify Internal Ops and owner notifications
10. tap `เสร็จแล้ว` and verify blocked response
11. restore water
12. complete Cleaning Task
13. verify Access Prep remains open
14. unauthorized operator attempts Access Prep and is rejected
15. authorized operator/Admin completes Access Prep
16. verify Internal Ops shows Cleaning Ready + Access Prep Ready
17. verify Guest OA room-entry remains blocked before step 15
18. verify Guest OA room-entry becomes eligible after step 15
19. replay one postback and verify no duplicate event

- [ ] **Step 2: Prepare isolated fixtures**

Use one controlled guest, booking, room, Internal admin, and Housekeeping
operator. Do not reuse production guest rows without explicit fixture markers.

- [ ] **Step 3: Execute Real LINE DoD**

Capture:

- visible Housekeeping cards
- visible Internal Ops alerts
- Guest OA blocked/unblocked behavior
- event IDs
- task IDs
- incident/outbox IDs
- outbound IDs
- masked LINE identities

- [ ] **Step 4: Inspect database evidence**

Verify:

- Cleaning Task lifecycle and checklist events
- Access Prep Task lifecycle and key custody
- task focus
- no duplicate transitions
- Internal Ops owner override evidence if exercised
- dual logical problem notifications
- Room Access Readiness RPC before/after

- [ ] **Step 5: Close or keep Phase 6 open**

Close only if all completion criteria pass. Safe but awkward wording may move to
polish backlog. Missing evidence, wrong readiness, unauthorized access mutation,
silent no-ack, or false delivery claims keep Phase 6 open.

- [ ] **Step 6: Update documentation**

Update:

- `log_AI.md`
- `HANDOFF.md`
- checklist verdict
- `ROADMAP.md` runtime status section if Phase 6 closes

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/checklists/2026-06-19-phase6-real-line-dod-script.md \
  log_AI.md HANDOFF.md ROADMAP.md
git commit -m "docs: close phase 6 housekeeping execution"
```

## Plan Self-Review Checklist

- [ ] Every design requirement maps to at least one task.
- [ ] Button-first UX is implemented through Rich Menu payload contracts,
  Flex Messages, Quick Replies, and signed postbacks.
- [ ] Users are never required to type slash commands.
- [ ] Cleaning and Access Prep use separate records and state services.
- [ ] Direct Admin priority is first in the queue.
- [ ] T-1, 22:00, 09:00, and same-day Access Prep paths are covered.
- [ ] Assignment plus capability is required for Access Prep.
- [ ] Key custody is persisted.
- [ ] Owner override preserves blockers.
- [ ] All no-ack thresholds are tested.
- [ ] Internal Ops and owner receive problem evidence.
- [ ] Guest OA readiness uses the central RPC.
- [ ] Dashboard does not invent readiness separately.
- [ ] Multi-operator claims are atomic.
- [ ] Deployment avoids direct SQLite writes.
- [ ] Synthetic and Real LINE acceptance are both required.
