import fs from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';

function bangkokDateParts(date) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Bangkok',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).formatToParts(date);
  const part = (type) => parts.find((item) => item.type === type)?.value;
  return {
    date: `${part('year')}-${part('month')}-${part('day')}`,
    hour: Number(part('hour')),
    minute: Number(part('minute')),
  };
}

function addDays(dateText, days) {
  const date = new Date(`${dateText}T00:00:00+07:00`);
  date.setUTCDate(date.getUTCDate() + days);
  return bangkokDateParts(date).date;
}

function expectedScheduledDate(checkInDate) {
  return addDays(checkInDate, -1);
}

function isTerminalOrExcludedBooking(booking) {
  return ['canceled', 'no_show'].includes(booking.booking_status);
}

export function scheduleFor(booking, nowDate) {
  if (isTerminalOrExcludedBooking(booking)) {
    return { action: 'excluded', create: false, priority: 'normal', notifyInternal: false };
  }

  const localNow = bangkokDateParts(nowDate);
  const today = localNow.date;
  const tomorrow = addDays(today, 1);
  const task = booking.existing_task;
  const expectedDate = expectedScheduledDate(booking.check_in_date);

  if (task) {
    const taskScheduledDate = bangkokDateParts(new Date(task.scheduled_for)).date;
    if (task.room_id !== booking.room_id || taskScheduledDate !== expectedDate) {
      return {
        action: 'cancel_obsolete',
        create: false,
        priority: 'normal',
        notifyInternal: true,
      };
    }
    return { action: 'merge_existing', create: false, priority: 'normal', notifyInternal: false };
  }

  if (booking.check_in_date === today) {
    return sameDayBooking();
  }
  if (booking.check_in_date === tomorrow) {
    return {
      action: 'create_t_minus_one',
      create: true,
      priority: 'normal',
      notifyInternal: true,
    };
  }
  return { action: 'not_due', create: false, priority: 'normal', notifyInternal: false };
}

export function escalationAt(value) {
  const local = bangkokDateParts(new Date(value));
  if (local.hour >= 22) {
    return { action: 'escalate_22', priority: 'urgent', notifyInternal: true, hardBlock: false };
  }
  if (local.hour >= 9) {
    return { action: 'hard_block_09', priority: 'urgent', notifyInternal: true, hardBlock: true };
  }
  return { action: 'none', priority: 'normal', notifyInternal: false, hardBlock: false };
}

export function sameDayBooking() {
  return {
    action: 'same_day_urgent',
    create: true,
    priority: 'urgent',
    notifyInternal: true,
  };
}

export function buildWorkflow() {
  return {
    id: 'impact-phase6-access-prep-scheduler',
    name: 'Impact - Phase 6 Access Prep Scheduler',
    active: true,
    nodes: [
      {
        parameters: {
          rule: {
            interval: [{ field: 'minutes', minutesInterval: 5 }],
          },
        },
        id: 'phase6-access-prep-schedule-trigger',
        name: 'Every 5 minutes',
        type: 'n8n-nodes-base.scheduleTrigger',
        typeVersion: 1.2,
        position: [-600, 0],
      },
      {
        parameters: {
          method: 'POST',
          url: '={{ $env.SUPABASE_URL + "/rest/v1/rpc/claim_access_prep_schedule" }}',
          sendHeaders: true,
          headerParameters: {
            parameters: [
              { name: 'apikey', value: '={{ $env.SUPABASE_SERVICE_ROLE_KEY }}' },
              { name: 'Authorization', value: '={{ "Bearer " + $env.SUPABASE_SERVICE_ROLE_KEY }}' },
              { name: 'Content-Type', value: 'application/json' },
            ],
          },
          sendBody: true,
          specifyBody: 'json',
          jsonBody: '={{ { p_now: $now.toISO(), p_limit: 50 } }}',
          options: {
            response: {
              response: {
                fullResponse: true,
                neverError: true,
              },
            },
          },
        },
        id: 'phase6-access-prep-claim',
        name: 'Claim access prep schedule',
        type: 'n8n-nodes-base.httpRequest',
        typeVersion: 4.2,
        position: [-360, 0],
      },
      {
        parameters: {
          jsCode: `
const response = items[0].json;
const body = response.body ?? response;
const actions = Array.isArray(body?.actions) ? body.actions : [];
return actions.map((action) => ({ json: action }));
`.trim() + '\n',
        },
        id: 'phase6-access-prep-expand',
        name: 'Expand claimed actions',
        type: 'n8n-nodes-base.code',
        typeVersion: 2,
        position: [-120, 0],
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
                id: 'needs-merge',
                leftValue: '={{ ["create_t_minus_one", "same_day_urgent", "escalate_22", "hard_block_09"].includes($json.action) }}',
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
        id: 'phase6-access-prep-if-merge',
        name: 'IF create or merge Access Prep task',
        type: 'n8n-nodes-base.if',
        typeVersion: 2,
        position: [120, -120],
      },
      {
        parameters: {
          method: 'POST',
          url: '={{ $env.SUPABASE_URL + "/rest/v1/rpc/merge_access_prep_task" }}',
          sendHeaders: true,
          headerParameters: {
            parameters: [
              { name: 'apikey', value: '={{ $env.SUPABASE_SERVICE_ROLE_KEY }}' },
              { name: 'Authorization', value: '={{ "Bearer " + $env.SUPABASE_SERVICE_ROLE_KEY }}' },
              { name: 'Content-Type', value: 'application/json' },
            ],
          },
          sendBody: true,
          specifyBody: 'json',
          jsonBody: '={{ { p_task: $json.task, p_source_event_id: $json.source_event_id } }}',
          options: {
            response: {
              response: {
                fullResponse: true,
                neverError: true,
              },
            },
          },
        },
        id: 'phase6-access-prep-merge',
        name: 'Merge access prep task',
        type: 'n8n-nodes-base.httpRequest',
        typeVersion: 4.2,
        position: [360, -220],
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
                id: 'needs-incident',
                leftValue: '={{ ["same_day_urgent", "escalate_22", "hard_block_09", "cancel_obsolete"].includes($json.action) }}',
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
        id: 'phase6-access-prep-if-incident',
        name: 'IF Internal Ops or owner notification needed',
        type: 'n8n-nodes-base.if',
        typeVersion: 2,
        position: [600, 0],
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
                id: 'needs-cancel',
                leftValue: '={{ $json.action === "cancel_obsolete" }}',
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
        id: 'phase6-access-prep-if-cancel',
        name: 'IF cancel obsolete Access Prep task',
        type: 'n8n-nodes-base.if',
        typeVersion: 2,
        position: [360, 40],
      },
      {
        parameters: {
          method: 'POST',
          url: '={{ $env.SUPABASE_URL + "/rest/v1/rpc/apply_access_prep_task_action" }}',
          sendHeaders: true,
          headerParameters: {
            parameters: [
              { name: 'apikey', value: '={{ $env.SUPABASE_SERVICE_ROLE_KEY }}' },
              { name: 'Authorization', value: '={{ "Bearer " + $env.SUPABASE_SERVICE_ROLE_KEY }}' },
              { name: 'Content-Type', value: 'application/json' },
            ],
          },
          sendBody: true,
          specifyBody: 'json',
          jsonBody: '={{ { p_task_id: $json.task_id, p_housekeeper_id: $json.assigned_housekeeper_id ?? null, p_action: "cancel_task", p_source_event_id: $json.source_event_id, p_payload: { reason: $json.reason, scheduler_action: $json.action } } }}',
          options: {
            response: {
              response: {
                fullResponse: true,
                neverError: true,
              },
            },
          },
        },
        id: 'phase6-access-prep-cancel',
        name: 'Cancel obsolete access prep task',
        type: 'n8n-nodes-base.httpRequest',
        typeVersion: 4.2,
        position: [600, 180],
      },
      {
        parameters: {
          method: 'POST',
          url: '={{ $env.SUPABASE_URL + "/rest/v1/rpc/report_operational_incident" }}',
          sendHeaders: true,
          headerParameters: {
            parameters: [
              { name: 'apikey', value: '={{ $env.SUPABASE_SERVICE_ROLE_KEY }}' },
              { name: 'Authorization', value: '={{ "Bearer " + $env.SUPABASE_SERVICE_ROLE_KEY }}' },
              { name: 'Content-Type', value: 'application/json' },
            ],
          },
          sendBody: true,
          specifyBody: 'json',
          jsonBody: '={{ { p_incident: { source_surface: "internal_ops_oa", source_event_id: $json.source_event_id, correlation_id: $json.source_event_id, idempotency_key: "access_prep_scheduler:" + $json.action + ":" + $json.booking_id, booking_id: $json.booking_id, room_id: $json.room_id, issue_family: "access_prep", issue_subtype: $json.action, severity: $json.action === "hard_block_09" ? "critical" : "high", latest_evidence_text: $json.notification_text, requires_internal_ops: true, requires_owner: true, metadata: { owner: true, action: $json.action, task_id: $json.task_id ?? null } } } }}',
          options: {
            response: {
              response: {
                fullResponse: true,
                neverError: true,
              },
            },
          },
        },
        id: 'phase6-access-prep-incident',
        name: 'Report Internal Ops and owner incident',
        type: 'n8n-nodes-base.httpRequest',
        typeVersion: 4.2,
        position: [840, -100],
      },
      {
        parameters: {
          jsCode: `
return items.map((item) => ({
  json: {
    ok: true,
    action: item.json.action,
    booking_id: item.json.booking_id,
    task_id: item.json.task_id ?? null,
    source_event_id: item.json.source_event_id,
    evidence: {
      scheduler: 'phase6_access_prep',
      guest_message_sent: false,
      finalized_at: new Date().toISOString()
    }
  }
}));
`.trim() + '\n',
        },
        id: 'phase6-access-prep-evidence',
        name: 'Finalize access prep schedule evidence',
        type: 'n8n-nodes-base.code',
        typeVersion: 2,
        position: [1080, 80],
      },
    ],
    connections: {
      'Every 5 minutes': {
        main: [[{ node: 'Claim access prep schedule', type: 'main', index: 0 }]],
      },
      'Claim access prep schedule': {
        main: [[{ node: 'Expand claimed actions', type: 'main', index: 0 }]],
      },
      'Expand claimed actions': {
        main: [[{ node: 'IF create or merge Access Prep task', type: 'main', index: 0 }]],
      },
      'IF create or merge Access Prep task': {
        main: [
          [{ node: 'Merge access prep task', type: 'main', index: 0 }],
          [{ node: 'IF cancel obsolete Access Prep task', type: 'main', index: 0 }],
        ],
      },
      'Merge access prep task': {
        main: [[{ node: 'IF Internal Ops or owner notification needed', type: 'main', index: 0 }]],
      },
      'IF cancel obsolete Access Prep task': {
        main: [
          [{ node: 'Cancel obsolete access prep task', type: 'main', index: 0 }],
          [{ node: 'IF Internal Ops or owner notification needed', type: 'main', index: 0 }],
        ],
      },
      'Cancel obsolete access prep task': {
        main: [[{ node: 'IF Internal Ops or owner notification needed', type: 'main', index: 0 }]],
      },
      'IF Internal Ops or owner notification needed': {
        main: [
          [{ node: 'Report Internal Ops and owner incident', type: 'main', index: 0 }],
          [{ node: 'Finalize access prep schedule evidence', type: 'main', index: 0 }],
        ],
      },
      'Report Internal Ops and owner incident': {
        main: [[{ node: 'Finalize access prep schedule evidence', type: 'main', index: 0 }]],
      },
    },
    settings: {
      executionOrder: 'v1',
    },
  };
}

export function writeWorkflow() {
  const workflowJson = JSON.stringify([buildWorkflow()], null, 2) + '\n';
  const outputPath = new URL('../wf_phase6_access_prep_scheduler.json', import.meta.url);
  const runtimeDir = new URL('../runtime/n8n/workflows/', import.meta.url);
  const runtimePath = new URL('wf_phase6_access_prep_scheduler.json', runtimeDir);
  fs.writeFileSync(outputPath, workflowJson);
  fs.mkdirSync(runtimeDir, { recursive: true });
  fs.writeFileSync(runtimePath, workflowJson);
  console.log('Successfully generated wf_phase6_access_prep_scheduler.json and runtime/n8n/workflows/wf_phase6_access_prep_scheduler.json');
}

if (process.argv[1] && import.meta.url === pathToFileURL(fileURLToPath(import.meta.url)).href && fileURLToPath(import.meta.url) === process.argv[1]) {
  writeWorkflow();
}
