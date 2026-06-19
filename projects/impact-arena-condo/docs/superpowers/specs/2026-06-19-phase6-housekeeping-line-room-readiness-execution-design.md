# Phase 6 Housekeeping LINE And Room Readiness Execution Design

## Status

Approved by Bond on 2026-06-19.

This document defines the canonical Phase 6 product design. It extends the
existing Housekeeping Core that was built during Phase 4 Slice 3; it does not
discard or rebuild verified functionality.

## Source Of Truth

- Phase naming and sequence:
  - `ROADMAP.md`
  - `ROADMAP_Codex.md`
- Current implementation and runtime evidence:
  - `log_AI.md`
  - live Supabase/n8n/LINE evidence
  - current tests and workflow exports
- Canonical domain language:
  - `local-knowledge-repo/GLOSSARY.md`

The Phase 5 closeout phrase `Phase 6 polish/backlog` describes residual audit
gaps. It does not redefine Phase 6.

## Goal

Make Housekeeping LINE the real field-execution surface for room preparation,
while Internal Ops remains the control plane.

Phase 6 must prove that:

- cleaning work can be dispatched, acknowledged, started, blocked, restored,
  and completed through Housekeeping LINE
- Access Prep is a separate booking/stay task with separate ownership and risk
- no-acknowledgement and blockers are visible in Internal Ops
- direct admin instructions take priority over automatic queue planning
- Guest OA cannot send room-entry instructions before all readiness gates pass
- field users operate primarily through buttons, not free-form AI chat

## Existing Baseline

The repository already contains:

- Housekeeping LINE inbound routing
- deterministic command parsing
- Housekeeping Edge Function state handling
- enrollment and capability checks
- cleaning task dispatch
- exception checklist behavior
- acknowledgement and no-acknowledgement monitoring
- 5/10-minute urgent escalation
- Internal Ops incident routing
- Guest room-access suppression gates

Phase 6 should harden and complete this baseline rather than rebuild it.

The main missing or incomplete areas are:

- Access Prep as a first-class task separate from Cleaning Task
- button-first queue and task-card experience
- queue ordering that respects direct admin instructions
- key custody evidence
- full Internal Ops visibility and override behavior
- multi-operator-ready ownership
- complete Real LINE proof across Housekeeping, Internal Ops, and Guest OA

## Locked Product Decisions

### Surface Responsibilities

- Housekeeping LINE is the primary field interface from Slice 1.
- Internal Ops is the control plane.
- Bond/Admin may use Housekeeping LINE as a field operator.
- Internal Ops may inspect, correct, reassign, override, or complete operational
  state with explicit admin evidence.
- Phase 6 Slice 1 covers Cleaning Task and Access Prep Task.
- `field_assistance` remains a separate path and is not expanded in Slice 1.

### Interaction Model

- The experience is deterministic and code-first.
- Users should operate through Rich Menu actions, Flex Message buttons, and
  Quick Reply buttons.
- Users are not expected to type slash commands.
- Bond owns Rich Menu visual setup and publishing.
- The backend owns action contracts, queue rendering, Flex Message cards,
  postback verification, state transitions, and evidence.
- Hidden text commands such as `/queue` may exist as Rich Menu payloads,
  automation hooks, test handles, and emergency fallbacks only.
- AI is used only when language classification or summarization is genuinely
  useful, especially the free-text `อื่นๆ` problem path.
- AI may not directly mutate task state.

## Selected Architecture

### Approach A: Extend Existing Core

Selected.

Reuse the current gateway, Housekeeping workflow, Edge Function, Supabase
tables, incident service, and notification outbox. Add focused Phase 6
contracts around them.

Advantages:

- preserves verified safety behavior
- reduces migration and regression risk
- keeps Supabase as operational truth
- allows incremental Real LINE proof

### Rejected: Full Rebuild

A rebuild could produce cleaner files but would reopen already-solved routing,
security, idempotency, checklist, and escalation problems.

### Deferred: LIFF-First Interface

A LIFF mini-app may become useful later for dense operations, but Phase 6 will
first use native LINE Rich Menu, Flex Messages, Quick Replies, and postbacks.

## Domain Model

### Cleaning Task

Cleaning Task prepares the room itself.

It owns:

- cleaning progress
- standard-room exception checklist
- cleaning notes
- assigned cleaning operator
- cleaning acknowledgement
- cleaning blockers

Standard checklist:

- room cleaned
- bedsheet
- towels
- water
- tissue
- soap

Checklist items begin present/checked. A field user reports only missing
items. Missing items block normal completion.

### Access Prep Task

Access Prep Task prepares a specific booking/stay for safe guest entry.

It is separate from Cleaning Task because:

- cleaning may happen before a guest is booked
- a cleaned room should normally be locked
- the key should return to the owner/admin after cleaning
- leaving a key in an unlocked room without an arriving guest creates risk
- the person doing Access Prep may differ from the person cleaning

Access Prep Task owns:

- key placement
- room-open/unlocked preparation
- access preparation note
- assigned access operator
- acknowledgement
- capability checks
- key custody

Cleaning completion must not complete Access Prep. Access Prep completion must
not imply cleaning completion.

### Key Custody

Canonical values:

- `with_owner`
- `with_operator`
- `placed_in_room`
- `unknown`

After routine cleaning, the expected state is a locked room with the key
returned to owner/admin unless an explicit Access Prep Task authorizes room
entry preparation.

### Task Lifecycle

Shared launch lifecycle:

- `new`
- `sent`
- `acknowledged`
- `in_progress`
- `blocked`
- `done`
- `no_ack`

Delivery success is not acknowledgement. Silence is not completion.

### Owner Override

Internal Ops/owner may complete a task despite open missing items or blockers.

The override must:

- preserve the missing-item and blocker evidence
- record the admin identity and timestamp
- record an override reason
- display a warning that the task was completed by owner override
- avoid automatically declaring Room Access Ready

## Task Creation

### Cleaning Task Creation

Cleaning Task may be created by:

- checkout automation
- upcoming check-in need
- direct Internal Ops instruction
- room defect follow-up
- urgent operational need

Default owner is a registered Housekeeping operator. Bond/Admin is the
fallback operator through Housekeeping LINE.

### Access Prep Task Creation

Default schedule:

- create at 18:00 Asia/Bangkok on the day before check-in
- notify Internal Ops immediately
- at 22:00, if incomplete, raise priority to urgent
- at 09:00 on check-in day, if incomplete, send hard-block alert

Same-day booking:

- create Access Prep Task immediately
- mark urgent
- notify Internal Ops immediately

Default owner:

- Internal Ops / Bond/Admin

Housekeeping LINE assignment is allowed only when the operator:

- is assigned to the Access Prep Task
- has the required capability, such as `can_place_key` or `can_open_room`

### Booking Changes

Booking cancellation or room reassignment:

- cancel the old task with audit evidence
- create a new task for the new booking/room when required
- do not overwrite the historical task identity

Check-in date change:

- recompute the T-1 schedule
- cancel obsolete reminders/escalations
- preserve the schedule-change event

## Deduplication And Updates

For the same room, booking/stay, task type, and operational cycle:

- update the existing active task
- append notes and instructions
- preserve every admin command as an event
- do not create duplicate cards

Create a new task when:

- task type differs
- booking/stay differs
- room assignment changes
- the previous task is terminal and a new operational cycle begins

## Queue Engine

Housekeeping LINE uses one combined queue for Cleaning Tasks and Access Prep
Tasks. Task type must remain visually distinct.

Priority order:

1. direct Admin/Bond instruction
2. room checking in today
3. Access Prep near check-in
4. open blocker or defect
5. route efficiency by building/floor
6. due time

Direct admin instruction always outranks automatic planning.

Automatic queue planning is a fallback and assistance layer. It must not
silently undo or demote an explicit admin instruction.

### Queue Views

`งานวันนี้`:

- tasks assigned to the current operator
- due today
- includes Cleaning and Access Prep

`คิวงาน`:

- all open tasks visible to the operator
- ordered by canonical queue priority

Display five cards per page with next/previous navigation.

## Button-First LINE Experience

### Rich Menu

Bond manages Rich Menu visual setup.

Launch entries:

- งานวันนี้
- คิวงาน
- รับงาน
- แจ้งปัญหา
- รายละเอียดงาน

Rich Menu actions may send hidden command text or postback actions to the
backend. The user should experience them as real buttons.

### Flex Message Queue Card

Each task card displays:

- room
- task type
- priority
- due/check-in time
- owner
- task status
- missing checklist summary
- linked Cleaning/Access Prep dependency
- Access Prep status
- short note

Primary buttons:

- รับงาน
- เริ่มทำ
- แจ้งปัญหา
- เสร็จแล้ว
- ดูรายละเอียด

Buttons use bounded, signed postbacks. Visible labels must not expose full
database IDs.

### Visual Language

- red: urgent
- yellow: blocked or no-ack
- green: in progress or done
- grey: waiting/new/sent

Cards should follow the LINE MAN reference style:

- strong status hierarchy
- clear room/task title
- compact operational details
- one dominant action per state
- large, readable action buttons
- no backend-heavy text

### Customer Privacy

Housekeeping may see:

- short guest name
- room
- check-in time

Housekeeping should not see:

- phone number
- full reservation number
- unnecessary personal information

## Button Action Contracts

### งานวันนี้

Return the first page of current operator tasks due today.

### คิวงาน

Return the first page of all visible open tasks in priority order.

### รับงาน

Open the highest-priority unacknowledged eligible task and show a confirmation
card. It must not accept the task without confirmation.

### แจ้งปัญหา

Show problem categories:

- ไม่ได้ใส่น้ำ
- ไม่ได้ใส่สบู่
- ไม่ได้ใส่ผ้าขนหนู
- ของเสีย/ของหาย
- อื่นๆ

All problem reports create durable incident evidence and notify:

- Internal Ops
- owner

### รายละเอียดงาน

Show the focused task with:

- complete instructions
- checklist/blockers
- linked task dependency
- notes
- task history summary
- allowed actions for the current operator

## Problem Handling

### Missing Standard Items

The first three problem categories update the structured exception checklist:

- water missing
- soap missing
- towels missing

The task cannot complete normally until the item is restored.

Owner override through Internal Ops can complete the task while preserving the
missing-item evidence and warning.

### Damaged Or Lost Items

Slice 1 supports:

- description
- optional photo evidence
- room/task/booking context
- Internal Ops and owner notification
- durable incident evidence

Full lost-item return lifecycle is deferred to a later slice.

### Other

Free text may be classified and summarized by AI.

Deterministic code remains responsible for:

- creating the incident
- selecting notification targets
- applying allowed state transitions
- deciding whether readiness is blocked

### Photo Evidence

Photo evidence is:

- optional for routine work
- useful for damage, lost item, blocker, or unusual room condition
- not automatically interpreted by AI in Phase 6

## Quantities And Instructions

Standard quantities such as water, soap, and towels come from a room/guest
template. Internal Ops may override quantities per task.

Direct admin instructions are displayed prominently and outrank default
templates.

## Timing And No-Ack

Acknowledgement deadlines:

- urgent or guest waiting: 5 minutes
- check-in today: 15 minutes
- routine: 30 minutes

When the deadline expires:

- mark `no_ack`
- notify Internal Ops
- propose reassignment
- preserve delivery and no-ack evidence
- do not send a guest message solely because of no-ack

Cleaning due time should normally be at least 60 minutes before check-in.

## Room Readiness

### Cleaning Ready

Cleaning is ready only when:

- Cleaning Task is done, or owner override exists
- no unresolved required checklist item remains unless explicitly overridden
- no open cleaning blocker remains unless explicitly overridden

### Access Prep Ready

Access Prep is ready only when:

- key placement requirement is satisfied
- room-open/unlocked requirement is satisfied
- current operator had capability or admin override evidence exists
- key custody is consistent with the prepared state
- no open Access Prep blocker remains

### Room Access Ready

Guest OA may send room-entry instructions only when all are true:

1. booking/stay is verified
2. room assignment is stable
3. Cleaning Ready passes
4. Access Prep Ready passes
5. no active room/access incident blocks entry
6. approved room-entry asset or approved fallback is available

Cleaning Ready alone is not Room Access Ready. Access Prep Ready alone is not
Room Access Ready.

## Internal Ops Control Plane

Internal Ops can:

- create or update Cleaning Tasks
- create or update Access Prep Tasks
- specify room, quantities, instructions, priority, and due time
- assign/reassign owner
- change queue priority
- inspect delivery, acknowledgement, progress, blockers, and linked tasks
- update checklist/memory/state with admin authority
- mark cleaning or Access Prep complete
- perform owner override with reason
- cancel obsolete tasks
- acknowledge no-ack and choose fallback action

Internal Ops must clearly state:

- what was changed
- what evidence remains unresolved
- whether the room is Cleaning Ready
- whether Access Prep is ready
- whether Guest OA remains blocked

## Slices

### Slice 1: Native Housekeeping LINE Execution

- button action contracts
- one combined queue
- Flex Message cards
- Cleaning Task hardening
- separate Access Prep Task
- key custody
- capability and assignment gate
- problem categories and incident notification
- no-ack thresholds
- same-day and T-1 Access Prep automation

### Slice 2: Internal Visibility And Control

- `/ops` and Internal cards show task truth
- owner override
- reassignment
- linked Cleaning/Access Prep status
- dashboard data/type alignment
- access-readiness explanation

### Slice 3: Multi-Operator And Route Hardening

- multiple registered operators
- deterministic assignment and capacity behavior
- building/floor route optimization after admin priority
- queue pagination and concurrency hardening
- full cross-surface synthetic and Real LINE acceptance

## Error Handling

- delivery failure must remain visible and retryable
- duplicate postback must be idempotent
- expired or tampered postback must fail closed
- unauthorized Access Prep action must be rejected and reported
- ambiguous focused task must show a selection card instead of guessing
- database or provider failure must not claim task mutation succeeded
- missing Housekeeping recipient keeps the task actionable in Internal Ops
- Guest OA must remain blocked when readiness cannot be proven

## Testing Strategy

### Deterministic Tests

- queue ordering
- task deduplication
- lifecycle transitions
- checklist blocking/restoration
- Access Prep task creation and scheduling
- capability plus assignment checks
- key custody transitions
- admin override audit
- no-ack thresholds
- booking cancellation/date/room changes
- same-day booking urgency
- postback signature and idempotency
- incident dual-target evidence

### Synthetic Cross-Surface Tests

- Internal Ops creates a direct-priority Cleaning Task
- Housekeeping receives and acknowledges it
- Housekeeping reports missing water
- Internal Ops and owner receive incident evidence
- completion is blocked
- item is restored and cleaning completes
- Access Prep remains separate and blocks Guest OA
- authorized Access Prep completes
- Guest OA room-entry gate then opens

### Real LINE Definition Of Done

Through real Housekeeping LINE:

1. open งานวันนี้ using a button
2. open คิวงาน using a button
3. receive five-card pagination behavior
4. accept one task
5. start work
6. report missing water from a button
7. confirm Internal Ops and owner notification
8. prove completion is blocked
9. restore water
10. complete cleaning
11. prove Access Prep remains separate
12. complete Access Prep with authorized operator/admin
13. prove Internal Ops shows both states
14. prove Guest OA is blocked before readiness and allowed afterward
15. replay a postback and prove no duplicate mutation

## Phase 6 Completion Criteria

Phase 6 is complete only when:

- Housekeeping LINE is operational as the primary field interface
- button-first task flow works without requiring typed commands
- Cleaning Task and Access Prep Task are separate and auditable
- direct admin instructions outrank automatic queue planning
- acknowledgement/no-ack works at all locked thresholds
- checklist and owner override behavior are proven
- key custody and capability gates are enforced
- Internal Ops sees and controls current truth
- Guest OA room-access gate uses both Cleaning and Access Prep evidence
- deterministic regression passes
- synthetic three-surface acceptance passes
- Real LINE DoD passes with database, audit, incident, and outbound evidence

## Explicitly Deferred

- LIFF mini-app
- AI image understanding
- full lost-item return lifecycle
- broad field-assistance expansion
- advanced route scoring beyond deterministic building/floor optimization
- conversational polish unrelated to Housekeeping execution

