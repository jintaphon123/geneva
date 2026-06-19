import fs from 'node:fs';

const workflow = {
  id: 'impact-housekeeping-action',
  name: 'Impact - Housekeeping Action',
  active: true,
  nodes: [
    {
      parameters: {
        httpMethod: 'POST',
        path: 'impact/housekeeping-action',
        options: {},
      },
      id: 'hk-action-webhook',
      name: 'Receive housekeeping action trigger',
      type: 'n8n-nodes-base.webhook',
      typeVersion: 2.1,
      position: [-600, 0],
      webhookId: 'impact-housekeeping-action',
    },
    {
      parameters: {
        jsCode: `
const incoming = items[0].json;
const headers = incoming.headers ?? {};
const body = incoming.body ?? incoming;
const expectedSecret = $env.N8N_WEBHOOK_SECRET;
const receivedSecret = headers['x-impact-webhook-secret'] ?? headers['X-Impact-Webhook-Secret'];
if (!expectedSecret) {
  throw new Error('missing_webhook_secret');
}
if (receivedSecret !== expectedSecret) {
  throw new Error('invalid_webhook_secret');
}

const lineChannel = body.line_channel ?? '';
if (lineChannel !== 'housekeeping_line') {
  return [];
}

const lineUserId = body.actor?.line_user_id ?? body.line_user_id ?? null;
const text = String(body.message_text ?? body.text ?? '').trim();
if (!lineUserId || !text) {
  return [];
}

return [{
  json: {
    line_channel: 'housekeeping_line',
    event_type: body.event_type ?? 'message',
    message_id: body.message_id ?? null,
    message_type: body.message_type ?? 'text',
    line_user_id: lineUserId,
    text: text,
    display_name: body.actor?.display_name ?? body.display_name ?? null,
    conversation_id: body.conversation_id ?? null,
    correlation_id: body.correlation_id ?? null,
    source_event_id: body.source_event_id ?? null,
    reply_token_ephemeral: body.reply_token_ephemeral ?? null,
  },
}];
`.trim() + '\n',
      },
      id: 'hk-action-validate',
      name: 'Validate housekeeping request',
      type: 'n8n-nodes-base.code',
      typeVersion: 2,
      position: [-400, 0],
    },
    {
      parameters: {
        method: 'POST',
        url: '={{ $env.SUPABASE_URL + \'/functions/v1/housekeeping-handler\' }}',
        sendHeaders: true,
        headerParameters: {
          parameters: [
            { name: 'Content-Type', value: 'application/json' },
            { name: 'x-impact-webhook-secret', value: '={{ $env.N8N_WEBHOOK_SECRET }}' },
          ],
        },
        sendBody: true,
        specifyBody: 'json',
        jsonBody: '={{ $json }}',
        options: {
          response: {
            response: {
              fullResponse: true,
              neverError: true,
            },
          },
        },
      },
      id: 'hk-action-handler',
      name: 'Call housekeeping handler',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 4.2,
      position: [-200, 0],
    },
    {
      parameters: {
        jsCode: `
const response = items[0].json;
const statusCode = response.statusCode ?? 200;
const body = response.body ?? response;

if (statusCode >= 400 || !body || body.ok === false) {
  const text = body.message ?? body.error ?? 'unknown_error';
  return [{
    json: {
      ok: false,
      error: body.error ?? 'handler_error',
      message: text,
      internal_notification: {
        text: \`แจ้งเตือนข้อผิดพลาด: housekeeping-handler คืนสถานะ HTTP \${statusCode}\\nรายละเอียด: \${text}\`
      }
    }
  }];
}

if (body.incident_candidate) {
  return this.helpers.httpRequest({
    method: 'POST',
    url: $env.SUPABASE_URL + '/rest/v1/rpc/report_operational_incident',
    headers: {
      apikey: $env.SUPABASE_SERVICE_ROLE_KEY,
      Authorization: 'Bearer ' + $env.SUPABASE_SERVICE_ROLE_KEY,
      'Content-Type': 'application/json'
    },
    body: { p_incident: body.incident_candidate },
    json: true
  }).then(() => {
    return [{
      json: {
        ok: true,
        action: body.action ?? null,
        housekeeping_reply: body.housekeeping_reply ?? null,
        internal_notification: body.internal_notification ?? null,
        guest_draft_request: body.guest_draft_request ?? null,
        incident_candidate: body.incident_candidate ?? null,
        incident_reported: true,
        evidence: body.evidence ?? null
      }
    }];
  }).catch((err) => {
    const errMsg = err.message || String(err);
    return [{
      json: {
        ok: false,
        error: 'incident_rpc_failed',
        message: \`Failed to report operational incident: \${errMsg}\`,
        internal_notification: {
          text: \`แจ้งเตือนข้อผิดพลาด: การเรียก report_operational_incident ล้มเหลว\\nรายละเอียด: \${errMsg}\`
        }
      }
    }];
  });
}

return [{
  json: {
    ok: true,
    action: body.action ?? null,
    housekeeping_reply: body.housekeeping_reply ?? null,
    internal_notification: body.internal_notification ?? null,
    guest_draft_request: body.guest_draft_request ?? null,
    incident_candidate: null,
    incident_reported: false,
    evidence: body.evidence ?? null
  }
}];
`.trim() + '\n',
      },
      id: 'hk-action-process',
      name: 'Process handler response',
      type: 'n8n-nodes-base.code',
      typeVersion: 2,
      position: [0, 0],
    },
    {
      parameters: {
        conditions: {
          options: {
            caseSensitive: true,
            leftValue: '',
            typeValidation: 'loose',
          },
          conditions: [
            {
              id: 'has-reply',
              leftValue: '={{ (() => { const reply = $json.housekeeping_reply ?? {}; return (Array.isArray(reply.messages) && reply.messages.length > 0) || (typeof reply.text === "string" && reply.text.trim() !== ""); })() }}',
              rightValue: true,
              operator: {
                type: 'boolean',
                operation: 'true',
                singleValue: true,
              },
            },
          ],
          combinator: 'and',
        },
        options: {
          response: {
            response: {
              fullResponse: true,
              neverError: true,
            },
          },
        },
      },
      id: 'hk-action-if-reply',
      name: 'IF has housekeeping reply',
      type: 'n8n-nodes-base.if',
      typeVersion: 2,
      position: [200, -100],
    },
    {
      parameters: {
        method: 'POST',
        url: '={{ $env.IMPACT_LINE_SEND_TEXT_URL || ($env.SUPABASE_URL + \'/functions/v1/line-webhook-gateway/line/send-text\') }}',
        sendHeaders: true,
        headerParameters: {
          parameters: [
            { name: 'Content-Type', value: 'application/json' },
            { name: 'x-impact-webhook-secret', value: '={{ $env.N8N_WEBHOOK_SECRET }}' },
          ],
        },
        sendBody: true,
        specifyBody: 'json',
        jsonBody: `={{ (() => {
  const reply = $('Process handler response').first().json.housekeeping_reply ?? {};
  return {
    channel: "housekeeping_line",
    to: $('Validate housekeeping request').first().json.line_user_id,
    messages: reply.messages ?? undefined,
    text: reply.text ?? undefined,
    quickReply: reply.quickReply ?? undefined,
    conversation_id: $('Validate housekeeping request').first().json.conversation_id,
    source_event_id: $('Validate housekeeping request').first().json.source_event_id,
    correlation_id: $('Validate housekeeping request').first().json.correlation_id,
    reply_token_ephemeral: $('Validate housekeeping request').first().json.reply_token_ephemeral
  };
})() }}`,
        options: {
          response: {
            response: {
              fullResponse: true,
              neverError: true,
            },
          },
        },
      },
      id: 'hk-action-send-reply',
      name: 'Send housekeeping LINE reply',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 4.2,
      position: [400, -200],
    },
    {
      parameters: {
        conditions: {
          options: {
            caseSensitive: true,
            leftValue: '',
            typeValidation: 'loose',
          },
          conditions: [
            {
              id: 'has-notify',
              leftValue: '={{ $(\'Process handler response\').first().json.internal_notification !== null && $(\'Process handler response\').first().json.internal_notification !== undefined && $(\'Process handler response\').first().json.internal_notification.text !== null && $(\'Process handler response\').first().json.internal_notification.text !== undefined }}',
              rightValue: true,
              operator: {
                type: 'boolean',
                operation: 'true',
                singleValue: true,
              },
            },
          ],
          combinator: 'and',
        },
        options: {},
      },
      id: 'hk-action-if-notify',
      name: 'IF has internal notification',
      type: 'n8n-nodes-base.if',
      typeVersion: 2,
      position: [600, 100],
    },
    {
      parameters: {
        method: 'POST',
        url: '={{ $env.IMPACT_LINE_SEND_TEXT_URL || ($env.SUPABASE_URL + \'/functions/v1/line-webhook-gateway/line/send-text\') }}',
        sendHeaders: true,
        headerParameters: {
          parameters: [
            { name: 'Content-Type', value: 'application/json' },
            { name: 'x-impact-webhook-secret', value: '={{ $env.N8N_WEBHOOK_SECRET }}' },
          ],
        },
        sendBody: true,
        specifyBody: 'json',
        jsonBody: '={{ ({ channel: "internal_ops_oa", to: $env.LINE_INTERNAL_OPS_DEFAULT_TARGET_ID || ($env.LINE_INTERNAL_OPS_ALLOWED_USER_IDS || \'\').split(\',\')[0].trim(), text: $(\'Process handler response\').first().json.internal_notification.text, conversation_id: $(\'Validate housekeeping request\').first().json.conversation_id, source_event_id: $(\'Validate housekeeping request\').first().json.source_event_id, correlation_id: $(\'Validate housekeeping request\').first().json.correlation_id }) }}',
        options: {
          response: {
            response: {
              fullResponse: true,
              neverError: true,
            },
          },
        },
      },
      id: 'hk-action-send-notify',
      name: 'Send internal ops notification',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 4.2,
      position: [800, 0],
    },
    {
      parameters: {
        conditions: {
          options: {
            caseSensitive: true,
            leftValue: '',
            typeValidation: 'loose',
          },
          conditions: [
            {
              id: 'has-draft',
              leftValue: '={{ $(\'Process handler response\').first().json.guest_draft_request !== null && $(\'Process handler response\').first().json.guest_draft_request !== undefined }}',
              rightValue: true,
              operator: {
                type: 'boolean',
                operation: 'true',
                singleValue: true,
              },
            },
          ],
          combinator: 'and',
        },
        options: {},
      },
      id: 'hk-action-if-draft',
      name: 'IF has guest draft request',
      type: 'n8n-nodes-base.if',
      typeVersion: 2,
      position: [1000, 300],
    },
    {
      parameters: {
        method: 'POST',
        url: '={{ $env.N8N_INTERNAL_OPS_DRAFT_ACTION_URL }}',
        sendHeaders: true,
        headerParameters: {
          parameters: [
            { name: 'Content-Type', value: 'application/json' },
            { name: 'x-impact-webhook-secret', value: '={{ $env.N8N_WEBHOOK_SECRET }}' },
          ],
        },
        sendBody: true,
        specifyBody: 'json',
        jsonBody: '={{ { mode: "create_draft_request", source_event_id: $(\'Validate housekeeping request\').first().json.source_event_id, correlation_id: $(\'Validate housekeeping request\').first().json.correlation_id, draft_request: $json.guest_draft_request } }}',
        options: {
          response: {
            response: {
              fullResponse: true,
              neverError: true,
            },
          },
        },
      },
      id: 'hk-action-create-draft',
      name: 'Create guest draft request',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 4.2,
      position: [1200, 200],
    },
    {
      parameters: {
        jsCode: `
const processNode = $('Process handler response').first().json;

function hasHousekeepingReply(reply) {
  return (Array.isArray(reply?.messages) && reply.messages.length > 0) ||
    (typeof reply?.text === 'string' && reply.text.trim() !== '');
}

const replyRequested = hasHousekeepingReply(processNode.housekeeping_reply);
const notifyRequested = !!processNode.internal_notification;
const draftRequested = !!processNode.guest_draft_request;

const replyResult = replyRequested ? ($('Send housekeeping LINE reply').first()?.json || null) : null;
const notifyResult = notifyRequested ? ($('Send internal ops notification').first()?.json || null) : null;
const draftResult = draftRequested ? ($('Create guest draft request').first()?.json || null) : null;

function unwrap(result) {
  return result?.body ?? result ?? null;
}

function httpSucceeded(result) {
  if (!result) return false;
  const statusCode = Number(result.statusCode ?? result.status ?? 200);
  return statusCode >= 200 && statusCode < 300;
}

function lineDeliverySucceeded(result) {
  const body = unwrap(result);
  return httpSucceeded(result) && body?.ok === true && !!body?.outbound_message_id;
}

function draftCreationSucceeded(result) {
  const body = unwrap(result);
  return httpSucceeded(result) &&
    body?.ok === true &&
    ['draft_created', 'draft_exists'].includes(body?.action) &&
    !!body?.draft_id;
}

const replySent = replyRequested ? lineDeliverySucceeded(replyResult) : false;
const notifySent = notifyRequested ? lineDeliverySucceeded(notifyResult) : false;
const draftCreated = draftRequested ? draftCreationSucceeded(draftResult) : false;
const allRequestedEffectsSucceeded =
  (!replyRequested || replySent) &&
  (!notifyRequested || notifySent) &&
  (!draftRequested || draftCreated);

return [{
  json: {
    ok: processNode.ok === true && allRequestedEffectsSucceeded,
    action: processNode.action,
    housekeeping_reply_sent: replySent,
    internal_notification_sent: notifySent,
    guest_draft_created: draftCreated,
    evidence: processNode.evidence,
    details: {
      reply_result: replyResult,
      notify_result: notifyResult,
      draft_result: draftResult
    }
  }
}];
`.trim() + '\n',
      },
      id: 'hk-action-evidence',
      name: 'Build execution evidence',
      type: 'n8n-nodes-base.code',
      typeVersion: 2,
      position: [1400, 100],
    },
  ],
  connections: {
    'Receive housekeeping action trigger': {
      main: [[{ node: 'Validate housekeeping request', type: 'main', index: 0 }]],
    },
    'Validate housekeeping request': {
      main: [[{ node: 'Call housekeeping handler', type: 'main', index: 0 }]],
    },
    'Call housekeeping handler': {
      main: [[{ node: 'Process handler response', type: 'main', index: 0 }]],
    },
    'Process handler response': {
      main: [[{ node: 'IF has housekeeping reply', type: 'main', index: 0 }]],
    },
    'IF has housekeeping reply': {
      main: [
        [{ node: 'Send housekeeping LINE reply', type: 'main', index: 0 }],
        [{ node: 'IF has internal notification', type: 'main', index: 0 }],
      ],
    },
    'Send housekeeping LINE reply': {
      main: [[{ node: 'IF has internal notification', type: 'main', index: 0 }]],
    },
    'IF has internal notification': {
      main: [
        [{ node: 'Send internal ops notification', type: 'main', index: 0 }],
        [{ node: 'IF has guest draft request', type: 'main', index: 0 }],
      ],
    },
    'Send internal ops notification': {
      main: [[{ node: 'IF has guest draft request', type: 'main', index: 0 }]],
    },
    'IF has guest draft request': {
      main: [
        [{ node: 'Create guest draft request', type: 'main', index: 0 }],
        [{ node: 'Build execution evidence', type: 'main', index: 0 }],
      ],
    },
    'Create guest draft request': {
      main: [[{ node: 'Build execution evidence', type: 'main', index: 0 }]],
    },
  },
  settings: {
    executionOrder: 'v1',
  },
};

const outputPath = new URL('../wf_housekeeping_action.json', import.meta.url);
const runtimeOutputDir = new URL('../runtime/n8n/workflows/', import.meta.url);
const runtimeOutputPath = new URL('wf_housekeeping_action.json', runtimeOutputDir);
const workflowJson = JSON.stringify([workflow], null, 2) + '\n';
fs.writeFileSync(outputPath, workflowJson);
fs.mkdirSync(runtimeOutputDir, { recursive: true });
fs.writeFileSync(runtimeOutputPath, workflowJson);
console.log('Successfully generated wf_housekeeping_action.json and runtime/n8n/workflows/wf_housekeeping_action.json');
