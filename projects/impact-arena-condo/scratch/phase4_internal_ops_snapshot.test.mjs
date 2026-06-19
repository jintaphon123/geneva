import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const workflowData = JSON.parse(fs.readFileSync(new URL('../wf_internal_ops_snapshot.json', import.meta.url), 'utf8'));
const workflow = Array.isArray(workflowData) ? workflowData[0] : workflowData;

const validateNode = workflow.nodes.find((node) => node.name === 'Validate and extract snapshot');
const prepNode = workflow.nodes.find((node) => node.name === 'Prep snapshot context');
const caseNode = workflow.nodes.find((node) => node.name === 'GET open internal ops cases');
const fieldAssistanceNode = workflow.nodes.find((node) => node.name === 'GET open field assistance tasks');
const cleaningTasksNode = workflow.nodes.find((node) => node.name === 'GET open cleaning tasks');
const checklistItemsNode = workflow.nodes.find((node) => node.name === 'GET cleaning checklist items');
const accessPrepNode = workflow.nodes.find((node) => node.name === 'GET booking access preparations');
const buildNode = workflow.nodes.find((node) => node.name === 'Build snapshot reply');
const sendNode = workflow.nodes.find((node) => node.name === 'Send snapshot reply');

assert.ok(validateNode, 'snapshot workflow must validate incoming Internal Ops job');
assert.ok(prepNode, 'snapshot workflow must prepare snapshot context');
assert.ok(caseNode, 'snapshot workflow must fetch open Internal Ops cases for Case Card delivery');
assert.ok(fieldAssistanceNode, 'snapshot workflow must fetch open field assistance tasks');
assert.ok(cleaningTasksNode, 'snapshot workflow must fetch migrated open cleaning_tasks');
assert.ok(checklistItemsNode, 'snapshot workflow must fetch migrated cleaning_task_checklist_items');
assert.ok(accessPrepNode, 'snapshot workflow must fetch booking_access_preparations separately from cleaning');
assert.ok(buildNode, 'snapshot workflow must build snapshot reply');
assert.ok(sendNode, 'snapshot workflow must send through controlled Edge path');

function runValidate(input, env = {}) {
  const sandbox = {
    items: [{ json: input }],
    $env: {
      N8N_WEBHOOK_SECRET: 'test-secret',
      LINE_INTERNAL_OPS_ALLOWED_USER_IDS: 'Uallowed1,Uallowed2',
      ...env,
    },
  };
  vm.createContext(sandbox);
  return vm.runInContext(`(() => {\n${validateNode.parameters.jsCode}\n})()`, sandbox);
}

function runPrep({ validated, adminLookup = [], env = {} }) {
  const sandbox = {
    items: [{ json: { body: adminLookup } }],
    $env: env,
    Intl,
    Date: class extends Date {
      constructor(...args) {
        super(...(args.length ? args : ['2026-06-05T01:30:00.000Z']));
      }
      static now() {
        return new Date('2026-06-05T01:30:00.000Z').valueOf();
      }
    },
    $: (nodeName) => ({
      first: () => {
        if (nodeName === 'Validate and extract snapshot') return { json: validated };
        throw new Error(`Unexpected node lookup: ${nodeName}`);
      },
    }),
  };
  vm.createContext(sandbox);
  return vm.runInContext(`(() => {\n${prepNode.parameters.jsCode}\n})()`, sandbox);
}

function runBuild({
  ctx,
  bookings = [],
  statuses = [],
  openSessions = [],
  openCases = [],
  fieldTasks = [],
  cleaningTasks = [],
  checklistItems = [],
  accessPreps = [],
  housekeepingQueue = [],
  roomAccessReadiness = [],
}) {
  const sandbox = {
    $: (nodeName) => ({
      first: () => {
        if (nodeName === 'Prep snapshot context') return { json: ctx };
        if (nodeName === 'GET bookings window') return { json: { body: bookings } };
        if (nodeName === 'GET room statuses') return { json: { body: statuses } };
        if (nodeName === 'GET open draft sessions') return { json: { body: openSessions } };
        if (nodeName === 'GET open internal ops cases') return { json: { body: openCases } };
        if (nodeName === 'GET open field assistance tasks') return { json: { body: fieldTasks } };
        if (nodeName === 'GET open cleaning tasks') return { json: { body: cleaningTasks } };
        if (nodeName === 'GET cleaning checklist items') return { json: { body: checklistItems } };
        if (nodeName === 'GET booking access preparations') return { json: { body: accessPreps } };
        if (nodeName === 'GET housekeeping queue') return { json: { housekeeping_queue: housekeepingQueue } };
        if (nodeName === 'GET room access readiness') return { json: { room_access_readiness: roomAccessReadiness } };
        throw new Error(`Unexpected node lookup: ${nodeName}`);
      },
    }),
  };
  vm.createContext(sandbox);
  return vm.runInContext(`(() => {\n${buildNode.parameters.jsCode}\n})()`, sandbox);
}

function internalJob(lineUserId) {
  return {
    headers: { 'x-impact-webhook-secret': 'test-secret' },
    body: {
      line_channel: 'internal_ops_oa',
      event_type: 'message',
      message_type: 'text',
      actor: { line_user_id: lineUserId },
      conversation_id: 'conversation-1',
      correlation_id: 'correlation-1',
      source_event_id: 'event-1',
      reply_token_ephemeral: 'reply-token-1',
      trigger_word: '/ops',
      snapshot_scope: 'today',
    },
  };
}

function cleaningTask(overrides = {}) {
  return {
    id: 'cleaning-task-1',
    task_key: 'room-c8:2026-06-05:turnover',
    room_id: 'room-c8',
    booking_id: 'booking-1',
    task_type: 'turnover_cleaning',
    priority: 'urgent',
    status: 'waiting_ack',
    dispatch_status: 'sent',
    checklist_status: 'incomplete',
    assigned_housekeeper_id: 'housekeeper-1',
    due_at: '2026-06-05T06:00:00.000Z',
    ack_due_at: '2026-06-05T06:05:00.000Z',
    dispatched_at: '2026-06-05T05:55:00.000Z',
    started_at: null,
    completed_at: null,
    blocker_reason: null,
    rooms: {
      room_code: 'C8/13/15',
      building: 'C8',
    },
    ...overrides,
  };
}

function checklistItem(overrides = {}) {
  return {
    id: 'checklist-1',
    cleaning_task_id: 'cleaning-task-1',
    item_key: 'water',
    item_label: 'น้ำ',
    status: 'missing',
    issue_note: 'น้ำยังไม่ได้เติม',
    exception_reason: null,
    ...overrides,
  };
}

function accessPrep(overrides = {}) {
  return {
    id: 'access-prep-1',
    booking_id: 'booking-1',
    room_id: 'room-c8',
    key_placed_in_room: true,
    room_left_unlocked_or_open: false,
    status: 'partial',
    note: null,
    updated_at: '2026-06-05T05:50:00.000Z',
    ...overrides,
  };
}

function booking(overrides = {}) {
  return {
    id: 'booking-1',
    platform: 'booking',
    reservation_number: 'R001',
    guest_name_snapshot: 'มาลี ทดสอบเฟสสี่',
    check_in_date: '2026-06-05',
    check_out_date: '2026-06-06',
    nights: 1,
    room_id: 'room-c8',
    listing_tier: 'impact',
    booking_status: 'confirmed',
    created_at: '2026-06-04T10:00:00.000Z',
    rooms: {
      room_code: 'C8/13/15',
      building: 'C8',
      portfolio: 'impact',
      listing_tier: 'impact',
    },
    ...overrides,
  };
}

{
  const out = runValidate(internalJob('Uallowed1'));
  assert.equal(out[0].json.line_user_id, 'Uallowed1');
  assert.equal(out[0].json.reply_token_ephemeral, 'reply-token-1');
  assert.equal(out[0].json.auth_check.line_user_id, 'Uallowed1');
  assert.equal(out[0].json.auth_check.env_allowed, true);
  assert.equal(out[0].json.no_access, undefined);
}

{
  const out = runValidate(internalJob('Uunknown'));
  assert.equal(out[0].json.reply.channel, 'internal_ops_oa');
  assert.equal(out[0].json.reply.to, 'Uunknown');
  assert.equal(out[0].json.reply.reply_token_ephemeral, 'reply-token-1');
  assert.match(out[0].json.reply.text, /ยังไม่มีสิทธิ์ใช้งาน Internal Ops/);
  assert.equal(out[0].json.no_access, true);
  assert.equal(out[0].json.auth_check.line_user_id, 'Uunknown');
}

{
  const validated = runValidate(internalJob('Uallowed1'))[0].json;
  const deniedAfterLookup = runPrep({ validated, adminLookup: [] })[0].json;
  assert.equal(deniedAfterLookup.no_access, true);
  assert.equal(deniedAfterLookup.reply.to, 'Uallowed1');
  assert.equal(deniedAfterLookup.reply.reply_token_ephemeral, 'reply-token-1');
  assert.match(deniedAfterLookup.reply.text, /ยังไม่มีสิทธิ์ใช้งาน Internal Ops/);
}

{
  const validated = runValidate(internalJob('Uallowed1'))[0].json;
  const prepped = runPrep({
    validated,
    adminLookup: [{
      id: 'admin-1',
      line_user_id: 'Uallowed1',
      display_name: 'Bond',
      role: 'owner',
      active: true,
    }],
  })[0].json;

  const result = runBuild({
    ctx: prepped,
    bookings: [
      booking(),
      booking({
        id: 'booking-tomorrow',
        reservation_number: 'R002',
        guest_name_snapshot: 'พรุ่งนี้ ทดสอบ',
        check_in_date: '2026-06-06',
        check_out_date: '2026-06-07',
        room_id: 'room-c5',
        rooms: {
          room_code: 'C5/12/59',
          building: 'C5',
          portfolio: 'impact',
          listing_tier: 'impact',
        },
      }),
    ],
    statuses: [
      { room_id: 'room-c8', cleaning_status: 'unknown', maintenance_status: 'ok' },
      { room_id: 'room-c5', cleaning_status: 'dirty', maintenance_status: 'ok' },
    ],
  });

  const text = result[0].json.reply.text;
  assert.ok(Array.isArray(result[0].json.bookings));
  assert.ok(Array.isArray(result[0].json.open_cases));
  assert.ok(Array.isArray(result[0].json.field_assistance_tasks));
  assert.ok(Array.isArray(result[0].json.room_statuses));
  assert.ok(Array.isArray(result[0].json.cleaning_tasks));
  assert.ok(Array.isArray(result[0].json.cleaning_checklist_items));
  assert.ok(Array.isArray(result[0].json.access_preparations));
  assert.ok(result[0].json.evidence_contract);
  assert.equal(result[0].json.evidence_contract.room_readiness_separate_from_access_prep, true);
  assert.equal(result[0].json.reply.reply_token_ephemeral, 'reply-token-1');
  assert.match(text, /สรุปวันนี้ 5 มิ.ย./);
  assert.match(text, /ต้องดูแล/);
  assert.match(text, /เช็กอินพรุ่งนี้/);
  assert.match(text, /พรุ่งนี้ ทดสอบ/);
  assert.match(text, /Housekeeping/);
  assert.match(text, /ยังไม่มีสัญญาณ check-in/);
  assert.doesNotMatch(text, /ลูกค้ายังไม่ถึง/);
}

{
  const validated = runValidate(internalJob('Uallowed1'))[0].json;
  const prepped = runPrep({
    validated,
    adminLookup: [{
      id: 'admin-1',
      line_user_id: 'Uallowed1',
      display_name: 'Bond',
      role: 'owner',
      active: true,
    }],
  })[0].json;

  const result = runBuild({
    ctx: prepped,
    openCases: [{
      id: '11111111-2222-3333-4444-555555555555',
      case_code: 'RA-004',
      case_type: 'housekeeping',
      priority: 'urgent',
      status: 'waiting_admin',
      guest_display_snapshot: 'มาลี ทดสอบเฟสสาม',
      room_code_snapshot: 'C8/13/15',
      check_in_date_snapshot: '2026-06-05',
      check_out_date_snapshot: '2026-06-06',
      channel_target: 'guest_oa',
      platform_snapshot: 'Booking',
      latest_guest_message_excerpt: 'ขึ้นห้องยังไงครับ',
      issue_summary: 'Room access blocked: Access Prep incomplete',
      ai_suggestion: 'เช็กว่าห้องพร้อม กุญแจวางแล้ว และเปิดห้องไว้แล้วก่อนปล่อย room access',
      admin_action_needed: 'เลือก: ห้องพร้อมแล้ว / ยังไม่พร้อม / ส่งให้แม่บ้าน / รับเคสเอง / ดูรายละเอียด',
      visible_card_summary: null,
      created_at: '2026-06-05T01:00:00.000Z',
      updated_at: '2026-06-05T01:10:00.000Z',
    }],
  });

  const text = result[0].json.reply.text;
  assert.match(text, /Case Cards/);
  assert.match(text, /RA-004/);
  assert.match(text, /urgent/);
  assert.match(text, /waiting_admin/);
  assert.match(text, /มาลี ทดสอบเฟสสาม/);
  assert.match(text, /C8\/13\/15/);
  assert.match(text, /Room access blocked: Access Prep incomplete/);
  assert.match(text, /ขึ้นห้องยังไงครับ/);
  assert.match(text, /เช็กว่าห้องพร้อม/);
  assert.match(text, /ห้องพร้อมแล้ว \/ ยังไม่พร้อม \/ ส่งให้แม่บ้าน \/ รับเคสเอง \/ ดูรายละเอียด/);
  assert.doesNotMatch(text, /11111111-2222-3333-4444-555555555555/);
}

{
  const validated = runValidate({
    ...internalJob('Uallowed1'),
    body: {
      ...internalJob('Uallowed1').body,
      trigger_word: 'ตอนนี้แม่บ้านทำห้องอะไรไปหรือยัง',
      intent_hint: 'natural_ops_snapshot',
      snapshot_view: 'housekeeping',
    },
  })[0].json;
  const prepped = runPrep({
    validated,
    adminLookup: [{
      id: 'admin-1',
      line_user_id: 'Uallowed1',
      display_name: 'Bond',
      role: 'owner',
      active: true,
    }],
  })[0].json;

  const result = runBuild({
    ctx: prepped,
    bookings: [
      booking(),
      booking({
        id: 'booking-tomorrow',
        reservation_number: 'R002',
        guest_name_snapshot: 'พรุ่งนี้ ทดสอบ',
        check_in_date: '2026-06-06',
        check_out_date: '2026-06-07',
        room_id: 'room-c5',
        rooms: {
          room_code: 'C5/12/59',
          building: 'C5',
          portfolio: 'impact',
          listing_tier: 'impact',
        },
      }),
    ],
    statuses: [
      { room_id: 'room-c8', cleaning_status: 'unknown', maintenance_status: 'ok' },
      { room_id: 'room-c5', cleaning_status: 'dirty', maintenance_status: 'ok' },
    ],
    cleaningTasks: [
      cleaningTask(),
      cleaningTask({
        id: 'cleaning-task-2',
        room_id: 'room-c5',
        booking_id: 'booking-tomorrow',
        status: 'in_progress',
        priority: 'normal',
        checklist_status: 'complete',
        rooms: { room_code: 'C5/12/59', building: 'C5' },
      }),
    ],
    checklistItems: [
      checklistItem(),
      checklistItem({ id: 'checklist-2', item_key: 'towels', item_label: 'ผ้าขนหนู', status: 'present' }),
    ],
    accessPreps: [
      accessPrep(),
    ],
  });

  const text = result[0].json.reply.text;
  assert.match(text, /สถานะแม่บ้านตอนนี้/);
  assert.match(text, /งานแม่บ้านที่เปิดอยู่/);
  assert.match(text, /C8\/13\/15/);
  assert.match(text, /C5\/12\/59/);
  assert.match(text, /ยังไม่รับทราบ/);
  assert.match(text, /กำลังทำ/);
  assert.match(text, /ขาด: น้ำ/);
  assert.match(text, /Access Prep: วางกุญแจแล้ว · ยังไม่เปิดห้อง/);
  assert.doesNotMatch(text, /read-only/);
  assert.doesNotMatch(text, /Case Cards/);
  assert.doesNotMatch(text, /Popular Condo \/ Mom Portfolio/);
}

{
  const validated = runValidate({
    ...internalJob('Uallowed1'),
    body: {
      ...internalJob('Uallowed1').body,
      trigger_word: 'ตอนนี้มีลูกค้า Check out หรือ Check in บ้างมั้ย',
      intent_hint: 'natural_ops_snapshot',
      snapshot_view: 'check_in_out',
    },
  })[0].json;
  const prepped = runPrep({
    validated,
    adminLookup: [{
      id: 'admin-1',
      line_user_id: 'Uallowed1',
      display_name: 'Bond',
      role: 'owner',
      active: true,
    }],
  })[0].json;

  const result = runBuild({
    ctx: prepped,
    bookings: [
      booking(),
      booking({
        id: 'booking-out',
        reservation_number: 'R003',
        guest_name_snapshot: 'เช็กเอาต์ ทดสอบ',
        check_in_date: '2026-06-04',
        check_out_date: '2026-06-05',
        room_id: 'room-c4',
        booking_status: 'confirmed',
        rooms: {
          room_code: 'C4/16/51',
          building: 'C4',
          portfolio: 'impact',
          listing_tier: 'impact',
        },
      }),
    ],
  });

  const text = result[0].json.reply.text;
  assert.match(text, /เช็กอิน\/เช็กเอาต์วันนี้/);
  assert.match(text, /Impact Arena Condo/);
  assert.match(text, /ยังไม่มีสัญญาณ check-in/);
  assert.match(text, /ยังไม่มีสัญญาณ check-out/);
  assert.doesNotMatch(text, /Case Cards/);
  assert.doesNotMatch(text, /Housekeeping \(read-only\)/);
}

{
  const validated = runValidate(internalJob('Uallowed1'))[0].json;
  const prepped = runPrep({
    validated,
    adminLookup: [{
      id: 'admin-1',
      line_user_id: 'Uallowed1',
      display_name: 'Bond',
      role: 'owner',
      active: true,
    }],
  })[0].json;

  const result = runBuild({
    ctx: prepped,
    openCases: [{
      id: 'case-1',
      case_code: 'RA-004',
      priority: 'normal',
      status: 'waiting_admin',
      guest_display_snapshot: 'มาลี',
      room_code_snapshot: 'C8/13/15',
      channel_target: 'guest_oa',
      issue_summary: 'Room access blocked',
      created_at: '2026-06-05T01:00:00.000Z',
      updated_at: '2026-06-05T01:10:00.000Z',
    }],
    fieldTasks: [{
      id: 'field-task-1',
      building: 'C5',
      location_label: 'หน้าตึก C5',
      priority: 'urgent',
      status: 'waiting_ack',
      dispatch_status: 'sent',
      ack_status: 'waiting',
      source_text: 'ลูกค้ารอหน้าตึก C5 ไม่มีใครเปิด รีบให้คนไปรับหน่อย',
      created_at: '2026-06-05T10:00:00.000Z',
      internal_ops_cases: {
        case_code: 'FA-C5-TEST',
      },
    }],
  });

  const text = result[0].json.reply.text;
  assert.match(text, /Field Assistance ด่วน/);
  assert.match(text, /หน้าตึก C5/);
  assert.match(text, /field_assistance/);
  assert.match(text, /รอ Housekeeping รับทราบ/);
  assert.ok(text.indexOf('Field Assistance ด่วน') < text.indexOf('Case Cards'));
}

assert.match(sendNode.parameters.url, /line\/send-(text|message)/);

console.log('phase4 internal ops snapshot tests passed');
