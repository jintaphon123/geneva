import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';

const workflowPath = new URL('../wf_internal_ops_agent_harness.json', import.meta.url);

function getGeminiLoopCode() {
  const workflow = JSON.parse(fs.readFileSync(workflowPath, 'utf8'));
  const node = workflow.nodes.find((item) => item.name === 'Gemini Agent Loop');
  assert.ok(node, 'workflow must contain Gemini Agent Loop');
  return node.parameters.jsCode;
}

function httpResponse(body, status = 200) {
  const text = typeof body === 'string' ? body : JSON.stringify(body);
  return {
    ok: status >= 200 && status < 300,
    status,
    async text() { return text; },
    async json() { return typeof body === 'string' ? JSON.parse(body) : body; },
  };
}

function geminiToolCall(toolName, toolArgs) {
  return httpResponse({
    candidates: [{ content: { parts: [{ functionCall: { name: toolName, args: toolArgs } }] } }],
  });
}

function geminiText(text) {
  return httpResponse({ candidates: [{ content: { parts: [{ text }] } }] });
}

async function runGeminiLoopWithTool(toolName, toolArgs, supabaseMock = {}) {
  const calls = [];
  let geminiTurn = 0;
  const fetch = async (url, options = {}) => {
    const href = String(url);
    calls.push({ href, options });
    if (href.includes('generativelanguage.googleapis.com')) {
      geminiTurn += 1;
      return geminiTurn === 1
        ? geminiToolCall(toolName, toolArgs)
        : geminiText('ดำเนินการจากผลลัพธ์ของ tool แล้วค่ะ');
    }
    const entries = Object.entries(supabaseMock).sort((a, b) => b[0].length - a[0].length);
    for (const [pattern, responseBody] of entries) {
      if (href.includes(pattern)) {
        return typeof responseBody === 'function' ? responseBody(url, options) : httpResponse(responseBody);
      }
    }
    return httpResponse([]);
  };

  const context = {
    console: { log: () => {}, warn: () => {}, error: () => {} },
    Buffer,
    URLSearchParams,
    Date,
    Math,
    JSON,
    Intl,
    setTimeout,
    clearTimeout,
    Promise,
    crypto,
    fetch,
    items: [{
      json: {
        admin_user_id: 'admin-001',
        line_user_id: 'Ubond-test',
        line_channel: 'internal_ops_oa',
        message_text: 'ทดสอบ housekeeping control',
        source_event_id: '44444444-4444-4444-8444-444444444444',
        correlation_id: '55555555-5555-4555-8555-555555555555',
        created_at: '2026-06-19T12:00:00.000Z',
      },
    }],
    $env: {
      SUPABASE_URL: 'https://example.supabase.co',
      SUPABASE_SERVICE_ROLE_KEY: 'service-role-test',
      GEMINI_API_KEY: 'gemini-test',
      N8N_WEBHOOK_SECRET: 'secret-test',
    },
    $workflow: { id: 'test-workflow' },
    $execution: { id: 'test-exec' },
  };
  vm.createContext(context);
  const result = await vm.runInContext(`(async () => { ${getGeminiLoopCode()} })()`, context);
  return { result, calls };
}

console.log('Running Task 10 static tool-contract assertions...');
const loopCode = getGeminiLoopCode();
for (const toolName of [
  'create_or_update_access_prep_task',
  'get_housekeeping_queue',
  'get_room_readiness',
  'reassign_housekeeping_task',
  'override_housekeeping_task',
  'cancel_housekeeping_task',
]) {
  assert.ok(loopCode.includes(toolName), `Gemini loop must declare and route ${toolName}`);
}
assert.match(loopCode, /override_reason_required|reason_required/, 'owner override must require a non-empty reason');
assert.match(loopCode, /guest_oa_blocked/, 'tool result must expose Guest OA blocked state');
assert.match(loopCode, /room_access_ready/, 'tool result must expose room access readiness');
assert.doesNotMatch(loopCode, /สำเร็จแล้ว[^]*tool fails/i, 'loop must not hard-code fake success when a tool fails');

console.log('Running Task 10 access prep create tool simulation...');
const commonMock = {
  '/rooms?': [{ id: 'room-001', room_code: 'C5/12/59', building: 'C5' }],
  '/bookings?': [{ id: 'booking-001', room_id: 'room-001', guest_name_snapshot: 'Somchai', check_in_date: '2026-06-20', booking_status: 'confirmed' }],
  '/housekeepers?': [{ id: 'hk-001', line_user_id: 'Uhk-001', display_name: 'Mali', status: 'active', active: true }],
  '/rpc/merge_access_prep_task': { ok: true, taskId: 'access-001', taskKey: 'access-prep:booking-001', created: true, merged: false, status: 'new' },
  '/rpc/get_room_access_readiness': {
    ready: false,
    cleaning_ready: false,
    access_prep_ready: true,
    blockers: ['cleaning_incomplete'],
  },
  '/audit_logs': [{ id: 'audit-001' }],
};
let createRpcBody = null;
const createRun = await runGeminiLoopWithTool('create_or_update_access_prep_task', {
  room_code: 'C5/12/59',
  priority: 'urgent',
  instructions: 'วางกุญแจก่อนลูกค้าเข้า',
}, {
  ...commonMock,
  '/rpc/merge_access_prep_task': (_url, options) => {
    createRpcBody = JSON.parse(options.body);
    return httpResponse(commonMock['/rpc/merge_access_prep_task']);
  },
});
assert.equal(createRpcBody.p_task.priority, 'urgent');
assert.equal(createRpcBody.p_task.source, 'internal_ops');
assert.ok(createRun.calls.some((call) => call.href.includes('/rpc/get_room_access_readiness')));
assert.ok(createRun.calls.some((call) => call.href.includes('/audit_logs')));

console.log('Running Task 10 override reason guard simulation...');
const overrideRun = await runGeminiLoopWithTool('override_housekeeping_task', {
  task_kind: 'cleaning',
  task_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
  reason: '',
}, commonMock);
const toolResponse = overrideRun.calls.find((call) => call.href.includes('generativelanguage.googleapis.com') && call.options?.body?.includes('override_reason_required'));
assert.ok(toolResponse, 'empty override reason must be returned as a tool error to Gemini');

console.log('Task 10 internal housekeeping control tests passed.');
