import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const workflowPath = new URL('../wf_housekeeping_action.json', import.meta.url);
const workflowData = JSON.parse(fs.readFileSync(workflowPath, 'utf8'));
const workflow = Array.isArray(workflowData) ? workflowData[0] : workflowData;

const validateNode = workflow.nodes.find((node) => node.name === 'Validate housekeeping request');
const processNode = workflow.nodes.find((node) => node.name === 'Process handler response');
const evidenceNode = workflow.nodes.find((node) => node.name === 'Build execution evidence');
const createDraftNode = workflow.nodes.find((node) => node.name === 'Create guest draft request');
const sendNotifyNode = workflow.nodes.find((node) => node.name === 'Send internal ops notification');
const sendReplyNode = workflow.nodes.find((node) => node.name === 'Send housekeeping LINE reply');
const ifReplyNode = workflow.nodes.find((node) => node.name === 'IF has housekeeping reply');
const ifNotifyNode = workflow.nodes.find((node) => node.name === 'IF has internal notification');
const ifDraftNode = workflow.nodes.find((node) => node.name === 'IF has guest draft request');

assert.ok(validateNode, 'workflow must have Validate housekeeping request node');
assert.ok(processNode, 'workflow must have Process handler response node');
assert.ok(evidenceNode, 'workflow must have Build execution evidence node');
assert.ok(createDraftNode, 'workflow must have Create guest draft request node');
assert.ok(sendNotifyNode, 'workflow must have Send internal ops notification node');
assert.ok(sendReplyNode, 'workflow must have Send housekeeping LINE reply node');
assert.ok(ifReplyNode, 'workflow must have IF has housekeeping reply node');
assert.ok(ifNotifyNode, 'workflow must have IF has internal notification node');
assert.ok(ifDraftNode, 'workflow must have IF has guest draft request node');
const workflowText = JSON.stringify(workflow);
assert.match(
  createDraftNode.parameters.url,
  /N8N_INTERNAL_OPS_DRAFT_ACTION_URL/,
  'guest draft requests must go through the Draft Action contract',
);
assert.doesNotMatch(
  createDraftNode.parameters.url,
  /message_drafts/,
  'Housekeeping workflow must not insert message_drafts directly',
);
assert.equal(
  sendNotifyNode.parameters.options?.response?.response?.neverError,
  true,
  'Internal notification delivery must return bounded evidence instead of aborting the workflow',
);
assert.equal(
  sendNotifyNode.parameters.options?.response?.response?.fullResponse,
  true,
  'Internal notification delivery must expose its HTTP status to evidence building',
);
assert.match(
  sendReplyNode.parameters.jsonBody,
  /^\s*=\{\{/,
  'Housekeeping reply payload must be built as a full object expression',
);
assert.doesNotMatch(
  sendReplyNode.parameters.jsonBody,
  /"=\{\{/,
  'Housekeeping reply payload must not quote inline expressions as string literals',
);
assert.match(
  sendReplyNode.parameters.jsonBody,
  /\bmessages\b/,
  'Housekeeping reply payload must forward Flex/raw LINE messages when handler returns housekeeping_reply.messages',
);
assert.match(
  sendReplyNode.parameters.jsonBody,
  /\btext\b/,
  'Housekeeping reply payload must still forward text replies for legacy/simple responses',
);
assert.match(
  sendReplyNode.parameters.jsonBody,
  /\bquickReply\b/,
  'Housekeeping reply payload must preserve quickReply when present with a valid reply',
);
assert.match(
  ifReplyNode.parameters.conditions.conditions[0].leftValue,
  /messages/,
  'Housekeeping reply IF must allow Flex/raw LINE messages, not only text',
);
assert.match(
  ifReplyNode.parameters.conditions.conditions[0].leftValue,
  /trim/,
  'Housekeeping reply IF must require non-empty text when no messages are present',
);
assert.doesNotMatch(
  ifReplyNode.parameters.conditions.conditions[0].leftValue,
  /quickReply[^|&]*!==/,
  'Housekeeping reply IF must not send when quickReply is present without messages or text',
);
assert.match(
  sendNotifyNode.parameters.jsonBody,
  /^\s*=\{\{/,
  'Internal notification payload must be built as a full object expression',
);
assert.match(
  sendNotifyNode.parameters.jsonBody,
  /internal_ops_oa/,
  'Internal notification must remain on the Internal Ops channel',
);
assert.doesNotMatch(
  sendNotifyNode.parameters.jsonBody,
  /housekeeping_line/,
  'Internal notification must stay separate from the Housekeeping LINE reply',
);
assert.doesNotMatch(
  workflowText,
  /Gemini|gemini|AI Agent|ai-agent|@n8n\/n8n-nodes-langchain/,
  'Housekeeping action workflow must remain deterministic and must not introduce Gemini/AI nodes',
);
assert.match(
  processNode.parameters.jsCode,
  /report_operational_incident/,
  'Incident candidates must still reach the report_operational_incident RPC path',
);
assert.match(
  processNode.parameters.jsCode,
  /p_incident:\s*body\.incident_candidate/,
  'Incident RPC payload must preserve the p_incident contract',
);
assert.match(
  ifNotifyNode.parameters.conditions.conditions[0].leftValue,
  /Process handler response/,
  'Internal notification IF must inspect the process node output, not whatever previous branch item happens to be current',
);
assert.match(
  ifDraftNode.parameters.conditions.conditions[0].leftValue,
  /Process handler response/,
  'Guest draft IF must inspect the process node output, not whatever previous branch item happens to be current',
);

function runValidate(input, headers, envSecret = 'test-secret') {
  const sandbox = {
    items: [{ json: { body: input, headers } }],
    $env: { N8N_WEBHOOK_SECRET: envSecret },
    console,
  };
  vm.createContext(sandbox);
  return vm.runInContext(`(() => {\n${validateNode.parameters.jsCode}\n})()`, sandbox);
}

function runProcess(handlerResponse) {
  const sandbox = {
    items: [{ json: handlerResponse }],
    console,
  };
  vm.createContext(sandbox);
  return vm.runInContext(`(() => {\n${processNode.parameters.jsCode}\n})()`, sandbox);
}

function runEvidence(processNodeOutput, ifReplyOutput, ifNotifyOutput, ifDraftOutput, sendReplyOutput, sendNotifyOutput, createDraftOutput) {
  const sandbox = {
    $: (nodeName) => {
      const mappings = {
        'Process handler response': { first() { return { json: processNodeOutput }; } },
        'IF has housekeeping reply': { first() { return { json: ifReplyOutput }; } },
        'IF has internal notification': { first() { return { json: ifNotifyOutput }; } },
        'IF has guest draft request': { first() { return { json: ifDraftOutput }; } },
        'Send housekeeping LINE reply': { first() { return { json: sendReplyOutput }; } },
        'Send internal ops notification': { first() { return { json: sendNotifyOutput }; } },
        'Create guest draft request': { first() { return { json: createDraftOutput }; } },
      };
      if (!(nodeName in mappings)) throw new Error(`Missing mock node: ${nodeName}`);
      return mappings[nodeName];
    },
    console,
  };
  vm.createContext(sandbox);
  return vm.runInContext(`(() => {\n${evidenceNode.parameters.jsCode}\n})()`, sandbox);
}

// --- Test 1: Validate webhook secret verification ---
console.log('Running Test 1: Webhook secret verification...');
assert.throws(() => {
  runValidate({}, { 'x-impact-webhook-secret': 'wrong-secret' }, 'correct-secret');
}, /invalid_webhook_secret/);
assert.throws(() => {
  runValidate({}, {}, '');
}, /missing_webhook_secret/);

// --- Test 2: Reject non-housekeeping channel ---
console.log('Running Test 2: Channel verification...');
const result2 = runValidate({
  line_channel: 'guest_oa',
  actor: { line_user_id: 'U1' },
  text: 'รับทราบ',
}, { 'x-impact-webhook-secret': 'test-secret' }, 'test-secret');
assert.equal(result2.length, 0);

// --- Test 3: Accept valid housekeeping request ---
console.log('Running Test 3: Valid housekeeping request...');
const result3 = runValidate({
  line_channel: 'housekeeping_line',
  actor: { line_user_id: 'Uhk123', display_name: 'Mali' },
  message_text: 'รับทราบ',
  conversation_id: 'conv-99',
  correlation_id: 'corr-99',
  source_event_id: 'event-99',
  reply_token_ephemeral: 'reply-99',
}, { 'x-impact-webhook-secret': 'test-secret' }, 'test-secret');
assert.equal(result3.length, 1);
assert.equal(result3[0].json.line_channel, 'housekeeping_line');
assert.equal(result3[0].json.line_user_id, 'Uhk123');
assert.equal(result3[0].json.text, 'รับทราบ');
assert.equal(result3[0].json.conversation_id, 'conv-99');
assert.equal(result3[0].json.correlation_id, 'corr-99');
assert.equal(result3[0].json.source_event_id, 'event-99');
assert.equal(result3[0].json.reply_token_ephemeral, 'reply-99');

// --- Test 4: Process handler success response ---
console.log('Running Test 4: Success handler response...');
const result4 = runProcess({
  statusCode: 200,
  body: {
    ok: true,
    action: 'acknowledge_task',
    housekeeping_reply: { text: 'รับทราบงานเรียบร้อยค่ะ' },
    internal_notification: { text: 'แม่บ้านได้รับทราบงานแล้ว' },
    guest_draft_request: null,
    evidence: { task_id: 't-1' }
  }
});
assert.equal(result4.length, 1);
assert.equal(result4[0].json.ok, true);
assert.equal(result4[0].json.action, 'acknowledge_task');
assert.equal(result4[0].json.housekeeping_reply.text, 'รับทราบงานเรียบร้อยค่ะ');
assert.equal(result4[0].json.internal_notification.text, 'แม่บ้านได้รับทราบงานแล้ว');

// --- Test 4B: Process handler success with Flex reply messages ---
console.log('Running Test 4B: Success handler response with Flex messages...');
const flexReply = {
  messages: [{
    type: 'flex',
    altText: 'คิวงานแม่บ้าน 1 งาน',
    contents: { type: 'bubble', body: { type: 'box', layout: 'vertical', contents: [] } },
  }],
};
const result4b = runProcess({
  statusCode: 200,
  body: {
    ok: true,
    action: 'show_queue',
    housekeeping_reply: flexReply,
    internal_notification: null,
    guest_draft_request: null,
    evidence: { task_count: 1 },
  },
});
assert.equal(result4b.length, 1);
assert.deepEqual(result4b[0].json.housekeeping_reply, flexReply);

// --- Test 5: Process handler failure response ---
console.log('Running Test 5: Failure handler response (HTTP 500)...');
const result5 = runProcess({
  statusCode: 500,
  body: {
    ok: false,
    error: 'database_error',
    message: 'Lookup failed'
  }
});
assert.equal(result5.length, 1);
assert.equal(result5[0].json.ok, false);
assert.equal(result5[0].json.error, 'database_error');
assert.ok(result5[0].json.internal_notification.text.includes('แจ้งเตือนข้อผิดพลาด: housekeeping-handler คืนสถานะ HTTP 500'));

// --- Test 6: Bounded execution evidence generation ---
console.log('Running Test 6: Bounded execution evidence...');
const processNodeOutput = {
  ok: true,
  action: 'start_task',
  housekeeping_reply: { text: 'เริ่มงานทำความสะอาดแล้วค่ะ' },
  internal_notification: null,
  guest_draft_request: null,
  evidence: { task_id: 't-1' }
};
const ifReplyOutput = { housekeeping_reply: { text: 'เริ่มงานทำความสะอาดแล้วค่ะ' } };
const ifNotifyOutput = { internal_notification: null };
const ifDraftOutput = { guest_draft_request: null };
const sendReplyOutput = { ok: true, outbound_message_id: 'msg-reply-123' };
const sendNotifyOutput = null;
const createDraftOutput = null;

const result6 = runEvidence(
  processNodeOutput,
  ifReplyOutput,
  ifNotifyOutput,
  ifDraftOutput,
  sendReplyOutput,
  sendNotifyOutput,
  createDraftOutput
);
assert.equal(result6.length, 1);
assert.equal(result6[0].json.ok, true);
assert.equal(result6[0].json.action, 'start_task');
assert.equal(result6[0].json.housekeeping_reply_sent, true);
assert.equal(result6[0].json.internal_notification_sent, false);
assert.equal(result6[0].json.guest_draft_created, false);
assert.equal(result6[0].json.details.reply_result.outbound_message_id, 'msg-reply-123');

// --- Test 7: Evidence must not claim delivery when the provider result failed ---
console.log('Running Test 7: Truthful failed delivery evidence...');
const result7 = runEvidence(
  processNodeOutput,
  ifReplyOutput,
  ifNotifyOutput,
  ifDraftOutput,
  { ok: false, error: 'quota_exceeded' },
  null,
  null,
);
assert.equal(result7[0].json.ok, false);
assert.equal(result7[0].json.housekeeping_reply_sent, false);

// --- Test 8: Flex reply evidence counts successful LINE message delivery ---
console.log('Running Test 8: Flex reply delivery evidence...');
const result8 = runEvidence(
  {
    ok: true,
    action: 'show_queue',
    housekeeping_reply: flexReply,
    internal_notification: null,
    guest_draft_request: null,
    evidence: { task_count: 1 },
  },
  { housekeeping_reply: flexReply },
  ifNotifyOutput,
  ifDraftOutput,
  { ok: true, outbound_message_id: 'msg-flex-123' },
  null,
  null,
);
assert.equal(result8[0].json.ok, true);
assert.equal(result8[0].json.housekeeping_reply_sent, true);
assert.equal(result8[0].json.details.reply_result.outbound_message_id, 'msg-flex-123');

// --- Test 9: Empty replies do not request LINE delivery ---
console.log('Running Test 9: Empty housekeeping replies do not request delivery...');
const result9 = runEvidence(
  {
    ok: true,
    action: 'noop',
    housekeeping_reply: {},
    internal_notification: null,
    guest_draft_request: null,
    evidence: { task_id: 't-empty' },
  },
  { housekeeping_reply: {} },
  ifNotifyOutput,
  ifDraftOutput,
  null,
  null,
  null,
);
assert.equal(result9[0].json.ok, true);
assert.equal(result9[0].json.housekeeping_reply_sent, false);
assert.equal(result9[0].json.details.reply_result, null);

console.log('All housekeeping n8n workflow tests passed successfully!');
