import assert from 'node:assert/strict';
import fs from 'node:fs';

import {
  escalationAt,
  sameDayBooking,
  scheduleFor,
} from './update_phase6_access_prep_scheduler_workflow.mjs';

const workflowPath = new URL('../wf_phase6_access_prep_scheduler.json', import.meta.url);
const runtimeWorkflowPath = new URL('../runtime/n8n/workflows/wf_phase6_access_prep_scheduler.json', import.meta.url);
const migrationPath = new URL(
  '../runtime/supabase/supabase/migrations/20260619124500_phase6_access_prep_scheduler.sql',
  import.meta.url,
);

function now(value) {
  return new Date(value);
}

function checkIn(value, overrides = {}) {
  return {
    id: overrides.id ?? 'booking-1',
    booking_status: overrides.booking_status ?? 'confirmed',
    check_in_date: value,
    room_id: overrides.room_id ?? 'room-1',
    existing_task: overrides.existing_task ?? null,
  };
}

console.log('Running Task 8 scheduler decision tests...');
assert.deepEqual(scheduleFor(checkIn('2026-06-20'), now('2026-06-19T18:00:00+07:00')), {
  action: 'create_t_minus_one',
  create: true,
  priority: 'normal',
  notifyInternal: true,
});
assert.equal(escalationAt('2026-06-19T22:00:00+07:00').action, 'escalate_22');
assert.equal(escalationAt('2026-06-19T22:00:00+07:00').priority, 'urgent');
assert.equal(escalationAt('2026-06-20T09:00:00+07:00').action, 'hard_block_09');
assert.equal(escalationAt('2026-06-20T09:00:00+07:00').hardBlock, true);
assert.equal(sameDayBooking().action, 'same_day_urgent');
assert.equal(sameDayBooking().priority, 'urgent');
assert.equal(scheduleFor(checkIn('2026-06-20', { booking_status: 'canceled' }), now('2026-06-19T18:00:00+07:00')).create, false);
assert.equal(scheduleFor(checkIn('2026-06-20', { booking_status: 'no_show' }), now('2026-06-19T18:00:00+07:00')).create, false);
assert.equal(
  scheduleFor(
    checkIn('2026-06-20', { room_id: 'room-2', existing_task: { room_id: 'room-1', scheduled_for: '2026-06-19T18:00:00+07:00' } }),
    now('2026-06-19T18:00:00+07:00'),
  ).action,
  'cancel_obsolete',
);
assert.equal(
  scheduleFor(
    checkIn('2026-06-21', { existing_task: { room_id: 'room-1', scheduled_for: '2026-06-19T18:00:00+07:00' } }),
    now('2026-06-19T18:00:00+07:00'),
  ).action,
  'cancel_obsolete',
);
assert.equal(
  scheduleFor(
    checkIn('2026-06-20', { existing_task: { room_id: 'room-1', scheduled_for: '2026-06-19T18:00:00+07:00' } }),
    now('2026-06-19T18:00:00+07:00'),
  ).action,
  'merge_existing',
);

console.log('Running Task 8 SQL contract tests...');
const migrationSql = fs.readFileSync(migrationPath, 'utf8');
assert.match(migrationSql, /CREATE OR REPLACE FUNCTION public\.claim_access_prep_schedule/);
for (const action of ['create_t_minus_one', 'escalate_22', 'hard_block_09', 'cancel_obsolete', 'same_day_urgent']) {
  assert.match(migrationSql, new RegExp(action), `scheduler RPC must return ${action}`);
}
assert.match(migrationSql, /AT TIME ZONE 'Asia\/Bangkok'/, 'scheduler must use explicit Asia/Bangkok boundaries');
assert.match(migrationSql, /booking_status NOT IN \('canceled', 'no_show'\)/, 'scheduler must exclude canceled and no-show bookings');
assert.match(migrationSql, /task_key.*access-prep/s, 'scheduler task keys must be deterministic for merge/idempotency');
assert.match(migrationSql, /GRANT EXECUTE ON FUNCTION public\.claim_access_prep_schedule/, 'scheduler RPC must be executable by service_role');

console.log('Running Task 8 workflow contract tests...');
const workflowData = JSON.parse(fs.readFileSync(workflowPath, 'utf8'));
const runtimeWorkflowData = JSON.parse(fs.readFileSync(runtimeWorkflowPath, 'utf8'));
assert.deepEqual(runtimeWorkflowData, workflowData, 'runtime workflow must match source workflow');
const workflow = Array.isArray(workflowData) ? workflowData[0] : workflowData;
const workflowText = JSON.stringify(workflow);
assert.equal(workflow.id, 'impact-phase6-access-prep-scheduler');
assert.match(workflowText, /claim_access_prep_schedule/);
assert.match(workflowText, /merge_access_prep_task/);
assert.match(workflowText, /apply_access_prep_task_action/);
assert.match(workflowText, /cancel_task/, 'obsolete tasks must be canceled through the Access Prep state RPC');
assert.match(workflowText, /report_operational_incident/);
assert.match(workflowText, /internal_ops_oa/);
assert.match(workflowText, /owner/, 'urgent and hard-block actions must preserve owner notification intent');
assert.doesNotMatch(workflowText, /guest_oa/, 'Access Prep scheduler must not send Guest OA messages');
assert.doesNotMatch(workflowText, /Gemini|gemini|AI Agent|@n8n\/n8n-nodes-langchain/, 'scheduler must remain deterministic');

console.log('Task 8 access prep scheduler tests passed.');
