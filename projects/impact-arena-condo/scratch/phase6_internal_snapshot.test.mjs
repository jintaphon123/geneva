import assert from 'node:assert/strict';
import fs from 'node:fs';

const workflowData = JSON.parse(
  fs.readFileSync(new URL('../wf_internal_ops_snapshot.json', import.meta.url), 'utf8'),
);
const workflow = Array.isArray(workflowData) ? workflowData[0] : workflowData;
const text = JSON.stringify(workflow);

for (const name of [
  'GET housekeeping queue',
  'GET room access readiness',
  'Build snapshot reply',
]) {
  assert.ok(workflow.nodes.some((node) => node.name === name), `snapshot workflow must have ${name}`);
}

assert.match(text, /get_housekeeping_queue/);
assert.match(text, /get_room_access_readiness/);
assert.match(text, /Access Prep/);
assert.match(text, /Cleaning/);
assert.match(text, /รอรับงาน|ยังไม่รับงาน|รับทราบ|กำลังทำ|ติดปัญหา/);
assert.match(text, /กุญแจ|ผู้รับผิดชอบ|Guest OA/);
assert.doesNotMatch(text, /task_id[^]*UUID/i, 'snapshot must not expose raw UUID labels');

const buildNode = workflow.nodes.find((node) => node.name === 'Build snapshot reply');
assert.match(buildNode.parameters.jsCode, /housekeeping_queue/);
assert.match(buildNode.parameters.jsCode, /room_access_readiness/);
assert.doesNotMatch(
  buildNode.parameters.jsCode,
  /cleaning_status\s*===\s*['"]clean['"][^]*access_prep.*complete/,
  'snapshot must not reconstruct room readiness independently',
);

console.log('Task 12 internal snapshot tests passed.');
