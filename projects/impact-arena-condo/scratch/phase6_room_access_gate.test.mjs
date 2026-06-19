import assert from 'node:assert/strict';
import fs from 'node:fs';

const migrationPath = new URL(
  '../runtime/supabase/supabase/migrations/20260619133000_phase6_room_access_readiness.sql',
  import.meta.url,
);
const guestGeneratorPath = new URL('./update_guest_concierge_workflow.mjs', import.meta.url);
const dashboardTypesPath = new URL('../dashboard/src/lib/types.ts', import.meta.url);

export function verdict({
  verified = false,
  clean = false,
  access = false,
  incident = false,
  asset = false,
  assignmentStable = true,
  ownerOverride = false,
  missingWaterPreserved = false,
} = {}) {
  const blockers = [];
  if (!verified) blockers.push('booking_not_verified');
  if (!assignmentStable) blockers.push('room_assignment_changed');
  if (!clean) blockers.push('cleaning_incomplete');
  if (!access) blockers.push('access_prep_incomplete');
  if (incident) blockers.push('active_access_incident');
  if (!asset) blockers.push('approved_access_content_missing');
  if (ownerOverride && missingWaterPreserved) blockers.push('owner_override_blocker_preserved');
  return { ready: blockers.length === 0, blockers };
}

assert.equal(verdict({ verified: true, clean: true, access: false, asset: true }).ready, false);
assert.equal(verdict({ verified: true, clean: false, access: true, asset: true }).ready, false);
assert.equal(verdict({ verified: true, clean: true, access: true, incident: true, asset: true }).ready, false);
assert.equal(verdict({ verified: true, clean: true, access: true, incident: false, asset: true }).ready, true);
assert.equal(verdict({ verified: true, clean: true, access: true, asset: true, ownerOverride: true, missingWaterPreserved: true }).ready, false);
assert.equal(verdict({ verified: true, clean: true, access: true, asset: true, assignmentStable: false }).ready, false);

const sql = fs.readFileSync(migrationPath, 'utf8');
assert.match(sql, /CREATE OR REPLACE FUNCTION public\.get_room_access_readiness/);
for (const key of [
  'booking_verified',
  'room_assignment_stable',
  'cleaning_ready',
  'access_prep_ready',
  'active_access_incident',
  'approved_access_content',
  'blockers',
]) {
  assert.match(sql, new RegExp(key), `readiness RPC must return ${key}`);
}
assert.match(sql, /access_prep_incomplete/);
assert.match(sql, /room_assignment_changed/);
assert.match(sql, /active_access_incident/);
assert.match(sql, /capability_denied/, 'capability-denied events must remain blockers');
assert.match(sql, /booking_id = p_booking_id/, 'cleaning/access prep must be scoped to the current booking');
assert.match(sql, /status = 'done'/, 'only completed Access Prep can unlock access');

const guestGenerator = fs.readFileSync(guestGeneratorPath, 'utf8');
assert.match(guestGenerator, /get_room_access_readiness/);
assert.match(guestGenerator, /readiness_unknown/);
assert.match(guestGenerator, /room_access_readiness/);

const dashboardTypes = fs.readFileSync(dashboardTypesPath, 'utf8');
assert.match(dashboardTypes, /export interface RoomAccessReadiness/);
assert.match(dashboardTypes, /ready:\s*boolean/);
assert.match(dashboardTypes, /blockers:\s*string\[\]/);

console.log('Task 11 room access readiness gate tests passed.');
