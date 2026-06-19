import fs from 'node:fs';

const workflowPath = new URL('../wf_internal_ops_snapshot.json', import.meta.url);
const workflow = JSON.parse(fs.readFileSync(workflowPath, 'utf8'));

function node(name) {
  const found = workflow.nodes.find((item) => item.name === name);
  if (!found) throw new Error(`missing node: ${name}`);
  return found;
}

function code(value) {
  return value.trim() + '\n';
}

node('Validate and extract snapshot').parameters.jsCode = code(`
const incoming = items[0].json;
const headers = incoming.headers ?? {};
const body = incoming.body ?? incoming;
const expectedSecret = $env.N8N_WEBHOOK_SECRET;
const receivedSecret = headers['x-impact-webhook-secret'] ?? headers['X-Impact-Webhook-Secret'];
if (expectedSecret && receivedSecret !== expectedSecret) throw new Error('invalid_webhook_secret');

const lineChannel = body.line_channel ?? '';
if (lineChannel !== 'internal_ops_oa') throw new Error('wrong_channel: ' + lineChannel);

const lineUserId = body.actor?.line_user_id ?? body.line_user_id ?? null;
if (!lineUserId) throw new Error('missing_line_user_id');

const allowedFromEnv = String($env.LINE_INTERNAL_OPS_ALLOWED_USER_IDS ?? '')
  .split(',')
  .map((value) => value.trim())
  .filter(Boolean);

const base = {
  line_user_id: lineUserId,
  conversation_id: body.conversation_id ?? null,
  correlation_id: body.correlation_id ?? null,
  source_event_id: body.source_event_id ?? null,
  reply_token_ephemeral: body.reply_token_ephemeral ?? null,
  line_channel: lineChannel,
  trigger_word: body.trigger_word ?? '',
  intent_hint: body.intent_hint ?? null,
  snapshot_view: body.snapshot_view ?? 'full',
  snapshot_scope: body.snapshot_scope ?? 'today',
  auth_check: {
    line_user_id: lineUserId,
    env_allowlist_configured: allowedFromEnv.length > 0,
    env_allowed: allowedFromEnv.length === 0 || allowedFromEnv.includes(lineUserId),
  },
};

if (allowedFromEnv.length > 0 && !allowedFromEnv.includes(lineUserId)) {
  return [{
    json: {
      ...base,
      no_access: true,
      reply: {
        channel: 'internal_ops_oa',
        to: lineUserId,
        text: 'ขออภัยค่ะ บัญชี LINE นี้ยังไม่มีสิทธิ์ใช้งาน Internal Ops ค่ะ\\nถ้าควรมีสิทธิ์ใช้งาน รบกวนให้เจ้าของระบบเพิ่มบัญชีนี้ก่อนนะคะ',
        conversation_id: body.conversation_id ?? null,
        source_event_id: body.source_event_id ?? null,
        correlation_id: body.correlation_id ?? null,
        reply_token_ephemeral: body.reply_token_ephemeral ?? null,
      },
    },
  }];
}

return [{ json: base }];
`);

const authNode = workflow.nodes.find((item) => item.name === 'Upsert admin user' || item.name === 'GET authorized admin user');
if (!authNode) throw new Error('missing node: Upsert admin user / GET authorized admin user');
authNode.name = 'GET authorized admin user';
authNode.parameters = {
  method: 'GET',
  url: "={{ $env.SUPABASE_URL + '/rest/v1/admin_users?select=id,line_user_id,display_name,role,active&line_user_id=eq.' + $json.line_user_id + '&active=eq.true&limit=1' }}",
  sendHeaders: true,
  headerParameters: {
    parameters: [
      { name: 'apikey', value: '={{ $env.SUPABASE_SERVICE_ROLE_KEY }}' },
      { name: 'Authorization', value: '=Bearer {{ $env.SUPABASE_SERVICE_ROLE_KEY }}' },
    ],
  },
  options: {
    response: {
      response: {
        fullResponse: true,
        neverError: true,
      },
    },
  },
};

node('Prep snapshot context').parameters.jsCode = code(`
const ctx = $('Validate and extract snapshot').first().json;

if (ctx.no_access) {
  return [{ json: ctx }];
}

const adminResp = items[0].json;
const adminBody = adminResp.body ?? adminResp;
const adminArr = Array.isArray(adminBody) ? adminBody : [adminBody].filter(Boolean);
const admin = adminArr.find((item) => item?.line_user_id === ctx.line_user_id && item?.active !== false);

if (!admin?.id) {
  return [{
    json: {
      ...ctx,
      no_access: true,
      auth_check: {
        ...(ctx.auth_check ?? {}),
        supabase_authorized: false,
      },
      reply: {
        channel: 'internal_ops_oa',
        to: ctx.line_user_id,
        text: 'ขออภัยค่ะ บัญชี LINE นี้ยังไม่มีสิทธิ์ใช้งาน Internal Ops ค่ะ\\nตอนนี้ระบบจะไม่แสดงข้อมูลปฏิบัติการให้บัญชีที่ยังไม่ได้รับอนุญาตนะคะ',
        conversation_id: ctx.conversation_id,
        source_event_id: ctx.source_event_id,
        correlation_id: ctx.correlation_id,
        reply_token_ephemeral: ctx.reply_token_ephemeral,
      },
    },
  }];
}

const dateFormatter = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Asia/Bangkok',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
});
const today = dateFormatter.format(new Date());
const tomorrowDate = new Date(today + 'T00:00:00+07:00');
tomorrowDate.setDate(tomorrowDate.getDate() + 1);
const tomorrow = dateFormatter.format(tomorrowDate);

return [{
  json: {
    ...ctx,
    admin_user_id: admin.id,
    admin_display_name: admin.display_name ?? null,
    admin_role: admin.role ?? null,
    auth_check: {
      ...(ctx.auth_check ?? {}),
      supabase_authorized: true,
    },
    today,
    tomorrow,
  },
}];
`);

node('Build snapshot reply').parameters.jsCode = code(`
const ctx = $('Prep snapshot context').first().json;
const bookingBody = $('GET bookings window').first().json.body ?? [];
const statusBody = $('GET room statuses').first().json.body ?? [];
const draftSessionBody = $('GET open draft sessions').first().json.body ?? [];
const caseBody = $('GET open internal ops cases').first().json.body ?? [];
const fieldAssistanceBody = $('GET open field assistance tasks').first().json.body ?? [];
const cleaningTaskBody = $('GET open cleaning tasks').first().json.body ?? [];
const checklistBody = $('GET cleaning checklist items').first().json.body ?? [];
const accessPrepBody = $('GET booking access preparations').first().json.body ?? [];
const housekeepingQueueBody = $('GET housekeeping queue').first().json.housekeeping_queue ?? [];
const roomAccessReadinessBody = $('GET room access readiness').first().json.room_access_readiness ?? [];

const rawBookings = Array.isArray(bookingBody) ? bookingBody : [];
const statuses = Array.isArray(statusBody) ? statusBody : [];
const openSessions = Array.isArray(draftSessionBody) ? draftSessionBody : [];
const openCases = Array.isArray(caseBody) ? caseBody : [];
const fieldAssistanceTasks = Array.isArray(fieldAssistanceBody) ? fieldAssistanceBody : [];
const cleaningTasks = Array.isArray(cleaningTaskBody) ? cleaningTaskBody : [];
const checklistItems = Array.isArray(checklistBody) ? checklistBody : [];
const accessPreparations = Array.isArray(accessPrepBody) ? accessPrepBody : [];
const housekeepingQueue = Array.isArray(housekeepingQueueBody) ? housekeepingQueueBody : [];
const roomAccessReadiness = Array.isArray(roomAccessReadinessBody) ? roomAccessReadinessBody : [];

const statusByRoomId = new Map(statuses.map((s) => [s.room_id, s]));
const checklistByTaskId = new Map();
for (const item of checklistItems) {
  if (!item.cleaning_task_id) continue;
  const arr = checklistByTaskId.get(item.cleaning_task_id) ?? [];
  arr.push(item);
  checklistByTaskId.set(item.cleaning_task_id, arr);
}
const accessPrepByBookingId = new Map(accessPreparations.filter((p) => p.booking_id).map((p) => [p.booking_id, p]));
const bookingById = new Map();
const today = ctx.today;
const tomorrow = ctx.tomorrow;
const platformNames = { booking: 'Booking', agoda: 'Agoda', airbnb: 'Airbnb', direct: 'Direct', line: 'LINE', other: 'Other' };

function bookingKey(booking) {
  if (booking.platform && booking.reservation_number) return booking.platform + '|' + booking.reservation_number;
  return 'id|' + (booking.id || Math.random().toString(36));
}

function isNewer(next, current) {
  const nextTime = next.created_at ? Date.parse(next.created_at) : NaN;
  const currentTime = current.created_at ? Date.parse(current.created_at) : NaN;
  if (Number.isFinite(nextTime) && Number.isFinite(currentTime)) return nextTime > currentTime;
  if (Number.isFinite(nextTime) && !Number.isFinite(currentTime)) return false;
  return false;
}

function dedupeBookings(list) {
  const groups = new Map();
  for (const booking of list) {
    const key = bookingKey(booking);
    const group = groups.get(key);
    if (!group) {
      groups.set(key, { booking, count: 1 });
      continue;
    }
    group.count += 1;
    if (isNewer(booking, group.booking)) group.booking = booking;
  }
  return {
    bookings: [...groups.values()].map((group) => group.booking),
    duplicateGroups: [...groups.values()]
      .filter((group) => group.count > 1)
      .map((group) => ({ booking: group.booking, count: group.count })),
  };
}

const deduped = dedupeBookings(rawBookings);
const bookings = deduped.bookings;
const duplicateGroups = deduped.duplicateGroups;
for (const booking of bookings) {
  if (booking.id) bookingById.set(booking.id, booking);
}

function relatedRoom(booking) {
  return Array.isArray(booking.rooms) ? booking.rooms[0] : booking.rooms;
}

function portfolioOf(booking) {
  const room = relatedRoom(booking);
  if (room?.portfolio === 'mom' || booking.listing_tier === 'flex_popularcondo') return 'mom';
  return 'impact';
}

function roomCodeOf(booking) {
  const room = relatedRoom(booking);
  return room?.room_code || 'ห้องยังไม่ระบุ';
}

function roomStatusOf(booking) {
  return booking.room_id ? statusByRoomId.get(booking.room_id) : null;
}

function missingFor(booking) {
  const missing = [];
  if (!booking.room_id) missing.push('ยังไม่มีห้อง');
  if (booking.check_in_date === today && booking.booking_status === 'confirmed') missing.push('ยังไม่มีสัญญาณ check-in');
  if (booking.check_out_date === today && booking.booking_status !== 'checked_out') missing.push('ยังไม่มีสัญญาณ check-out');
  return missing;
}

function row(booking) {
  const missing = missingFor(booking);
  const suffix = missing.length ? ' | ขาด: ' + missing.join(', ') : '';
  return '- ' + [
    booking.guest_name_snapshot || '-',
    roomCodeOf(booking),
    platformNames[booking.platform] || booking.platform || '-',
    (booking.nights ?? '-') + ' คืน',
    booking.booking_status || '-',
  ].join(' | ') + suffix;
}

function section(title, list) {
  return [title, ...(list.length ? list.map(row) : ['- ไม่มี'])].join('\\n');
}

function titleDate(isoDate) {
  const [, month, day] = isoDate.split('-').map(Number);
  const monthNames = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
  return day + ' ' + monthNames[month - 1];
}

function nextActionFor(item) {
  if (item === 'ยังไม่มีห้อง') return 'เลือกห้องก่อนส่ง room access';
  if (item.includes('check-in')) return 'ถ้าส่ง room access แล้ว ให้ร่างข้อความถามได้ แต่ระบบยังไม่ auto-send';
  if (item.includes('check-out')) return 'ถ้าลูกค้าออกแล้ว ให้บันทึกสัญญาณ check-out หรือร่างข้อความถามได้';
  return 'ตรวจข้อมูลนี้ก่อนดำเนินการต่อ';
}

function duplicateWarningRows() {
  if (!duplicateGroups.length) return [];
  return [
    'พบใบจองซ้ำในระบบ',
    ...duplicateGroups.map(({ booking, count }) => {
      const platform = platformNames[booking.platform] || booking.platform || '-';
      const reservation = booking.reservation_number || booking.id || '-';
      return '- ' + platform + ' ' + reservation + ': พบ ' + count + ' records, แสดงรายการล่าสุดเท่านั้น';
    }),
  ];
}

function needsAttentionRows(scopeBookings) {
  const rows = [];
  for (const booking of scopeBookings) {
    const room = roomCodeOf(booking);
    const guest = booking.guest_name_snapshot || '-';
    for (const item of missingFor(booking)) {
      rows.push('- ' + guest + ' | ' + room + ': ' + item + '\\n  แนะนำ: ' + nextActionFor(item));
    }
    const rs = roomStatusOf(booking);
    const nearCheckIn = booking.check_in_date === today || booking.check_in_date === tomorrow;
    if (nearCheckIn && (!rs || ['unknown', 'dirty'].includes(rs.cleaning_status))) {
      const label = !rs || rs.cleaning_status === 'unknown' ? 'ยังไม่บันทึก' : 'ยังไม่สะอาด';
      rows.push('- ' + room + ': สถานะทำความสะอาด' + label + '\\n  แนะนำ: เช็กห้องและ Access Prep ก่อนส่งข้อมูลเข้าพัก');
    }
    if (rs && ['needs_attention', 'blocked'].includes(rs.maintenance_status)) {
      rows.push('- ' + room + ': maintenance_status = ' + rs.maintenance_status + '\\n  แนะนำ: ตรวจห้องก่อนให้ลูกค้าเข้าพัก');
    }
  }
  if (openSessions.length > 0) {
    rows.push('- มีชุดรูปใบจองที่ยังค้างอยู่\\n  แนะนำ: ถ้าไม่ใช้แล้วให้ปิดชุดรูป หรือส่งให้ครบแล้วพิมพ์ "ครบแล้ว"');
  }
  return rows.length ? rows : ['- ไม่มี'];
}

function safe(value, fallback = '-') {
  if (value === null || value === undefined) return fallback;
  const text = String(value).trim();
  return text || fallback;
}

function channelLabel(value) {
  const labels = {
    guest_oa: 'Guest OA',
    internal_ops_oa: 'Internal Ops',
    housekeeping_oa: 'Housekeeping',
    booking: 'Booking',
    agoda: 'Agoda',
    airbnb: 'Airbnb',
  };
  return labels[value] || safe(value);
}

function priorityRank(value) {
  const ranks = { urgent: 0, high: 1, normal: 2, medium: 2, low: 3 };
  return ranks[String(value || '').toLowerCase()] ?? 4;
}

function caseUpdatedAt(item) {
  const time = Date.parse(item.updated_at || item.created_at || '');
  return Number.isFinite(time) ? time : 0;
}

function caseCardRows() {
  if (!openCases.length) return ['- ไม่มี open case card'];
  return openCases
    .slice()
    .sort((a, b) => priorityRank(a.priority) - priorityRank(b.priority) || caseUpdatedAt(b) - caseUpdatedAt(a))
    .slice(0, 5)
    .flatMap((item) => {
      const code = safe(item.case_code, 'CASE');
      const channel = channelLabel(item.channel_target);
      const platform = item.platform_snapshot ? '/' + safe(item.platform_snapshot) : '';
      const dates = safe(item.check_in_date_snapshot) + ' -> ' + safe(item.check_out_date_snapshot);
      const issue = item.visible_card_summary || item.issue_summary || item.latest_guest_message_excerpt || 'รอ admin ตรวจรายละเอียด';
      return [
        '- ' + code + ' | ' + safe(item.priority, 'normal') + ' | ' + safe(item.status, 'new'),
        '  ลูกค้า: ' + safe(item.guest_display_snapshot) + ' | ห้อง: ' + safe(item.room_code_snapshot) + ' | ' + channel + platform,
        '  วันที่: ' + dates,
        '  Issue: ' + safe(issue),
        '  Latest: ' + safe(item.latest_guest_message_excerpt),
        '  แนะนำ: ' + safe(item.ai_suggestion || item.admin_action_needed, 'ตรวจเคสนี้ก่อนดำเนินการต่อ'),
        '  Actions: ห้องพร้อมแล้ว / ยังไม่พร้อม / ส่งให้แม่บ้าน / รับเคสเอง / ดูรายละเอียด',
      ];
    });
}

function renderFieldAssistanceTasks(tasks) {
  if (!tasks.length) return [];
  const lines = ['Field Assistance ด่วน'];
  const sorted = tasks
    .slice()
    .sort((a, b) => priorityRank(a.priority) - priorityRank(b.priority) || caseUpdatedAt(b) - caseUpdatedAt(a))
    .slice(0, 5);
  for (const task of sorted) {
    const ackText = task.ack_status === 'waiting'
      ? 'รอ Housekeeping รับทราบ'
      : task.ack_status === 'no_ack'
        ? 'ยังไม่มีคนรับทราบ'
        : task.ack_status === 'acknowledged'
          ? 'มีคนรับทราบแล้ว'
          : 'ไม่ต้องรอ ack';
    const dispatchText = task.dispatch_status === 'sent'
      ? 'ส่ง Housekeeping แล้ว'
      : task.dispatch_status === 'unconfigured'
        ? 'ยังไม่มีปลายทาง Housekeeping'
        : task.dispatch_status === 'failed'
          ? 'ส่ง Housekeeping ไม่สำเร็จ'
          : 'รอส่ง Housekeeping';
    const caseCode = task.internal_ops_cases?.case_code ? ' | ' + task.internal_ops_cases.case_code : '';
    lines.push('- ' + safe(task.location_label || task.building) + caseCode + ' | ประเภท: field_assistance | ' + dispatchText + ' | ' + ackText);
  }
  return lines;
}

function roomOfTask(task) {
  const room = Array.isArray(task.rooms) ? task.rooms[0] : task.rooms;
  if (room?.room_code) return room.room_code;
  const booking = task.booking_id ? bookingById.get(task.booking_id) : null;
  return booking ? roomCodeOf(booking) : 'ห้องยังไม่ระบุ';
}

function guestOfTask(task) {
  const booking = task.booking_id ? bookingById.get(task.booking_id) : null;
  return booking?.guest_name_snapshot || '-';
}

function cleaningStatusLabel(value) {
  const labels = {
    pending_dispatch: 'รอส่งงาน',
    waiting_ack: 'ยังไม่รับทราบ',
    acknowledged: 'รับทราบแล้ว',
    in_progress: 'กำลังทำ',
    blocked: 'ติดปัญหา',
    completed: 'เสร็จแล้ว',
    delivery_failed: 'ส่งงานไม่สำเร็จ',
    no_ack: 'ยังไม่มีคนรับทราบ',
    canceled: 'ยกเลิก',
  };
  return labels[value] || 'อยู่ระหว่างดำเนินการ';
}

function checklistLabel(item) {
  const labels = {
    room_cleaned: 'ทำความสะอาด',
    bedsheet: 'ผ้าปูที่นอน',
    towels: 'ผ้าขนหนู',
    water: 'น้ำ',
    tissue: 'ทิชชู่',
    soap: 'สบู่',
  };
  return item.item_label || labels[item.item_key] || 'รายการเช็กลิสต์';
}

function missingItemsForTask(task) {
  return (checklistByTaskId.get(task.id) ?? [])
    .filter((item) => item.status === 'missing')
    .map(checklistLabel);
}

function checklistProgressForTask(task) {
  const items = checklistByTaskId.get(task.id) ?? [];
  if (!items.length) return 'เช็กลิสต์ยังไม่มีข้อมูล';
  const present = items.filter((item) => item.status === 'present').length;
  return 'เช็กลิสต์ ' + present + '/' + items.length;
}

function accessPrepForTask(task) {
  if (task.booking_id && accessPrepByBookingId.has(task.booking_id)) return accessPrepByBookingId.get(task.booking_id);
  return null;
}

function accessPrepLabel(prep) {
  if (!prep) return 'Access Prep: ยังไม่มีข้อมูล';
  const key = prep.key_placed_in_room ? 'วางกุญแจแล้ว' : 'ยังไม่วางกุญแจ';
  const open = prep.room_left_unlocked_or_open ? 'เปิดห้องแล้ว' : 'ยังไม่เปิดห้อง';
  return 'Access Prep: ' + key + ' · ' + open;
}

function housekeepingRows() {
  if (!cleaningTasks.length) {
    return ['- ยังไม่มีงานแม่บ้านที่เปิดอยู่จากระบบ cleaning_tasks ตอนนี้'];
  }
  return cleaningTasks
    .slice()
    .sort((a, b) => priorityRank(a.priority) - priorityRank(b.priority) || caseUpdatedAt(b) - caseUpdatedAt(a))
    .slice(0, 8)
    .flatMap((task) => {
      const missing = missingItemsForTask(task);
      const lines = [
        '- ' + roomOfTask(task) + ' | ' + guestOfTask(task) + ' | ' + cleaningStatusLabel(task.status) + ' | ' + checklistProgressForTask(task),
        '  ' + accessPrepLabel(accessPrepForTask(task)),
      ];
      if (missing.length) lines.push('  ขาด: ' + missing.join(', '));
      if (task.blocker_reason) lines.push('  ติดปัญหา: ' + safe(task.blocker_reason));
      return lines;
    });
}

function housekeepingStatusLabel(status) {
  const labels = {
    pending_dispatch: 'รอส่งงาน',
    waiting_ack: 'ยังไม่รับงาน',
    sent: 'รอรับทราบ',
    acknowledged: 'รับทราบแล้ว',
    in_progress: 'กำลังทำ',
    blocked: 'ติดปัญหา',
    no_ack: 'ไม่ตอบรับ',
    completed: 'Cleaning Ready',
    done: 'Access Prep Ready',
    delivery_failed: 'ส่งงานไม่สำเร็จ',
    canceled: 'ยกเลิก',
    new: 'รอส่งงาน',
  };
  return labels[status] || 'ไม่ทราบสถานะ';
}

function housekeepingTruthRows() {
  const queueItems = housekeepingQueue.flatMap((entry) =>
    Array.isArray(entry?.items) ? entry.items : []
  );
  if (!queueItems.length) return housekeepingRows();
  return queueItems.slice(0, 12).flatMap((task) => {
    const kind = task.task_kind === 'access_prep' ? 'Access Prep' : 'Cleaning';
    const owner = safe(task.owner_label, 'ยังไม่ระบุผู้รับผิดชอบ');
    const lines = [
      '- ' + kind + ' | ' + safe(task.room_code, 'ไม่ระบุห้อง') + ' | ' +
        housekeepingStatusLabel(task.status) + ' | ผู้รับผิดชอบ: ' + owner,
    ];
    if (Array.isArray(task.missing_items) && task.missing_items.length) {
      lines.push('  ขาด: ' + task.missing_items.join(', '));
    }
    if (task.key_custody) lines.push('  กุญแจ: ' + safe(task.key_custody));
    if (task.blocker_reason) lines.push('  ติดปัญหา: ' + safe(task.blocker_reason));
    if (task.linked_task_status) {
      lines.push('  งานที่เชื่อมกัน: ' + housekeepingStatusLabel(task.linked_task_status));
    }
    return lines;
  });
}

function roomReadinessRows() {
  if (!roomAccessReadiness.length) return ['- ยังไม่มีผล get_room_access_readiness'];
  return roomAccessReadiness.slice(0, 12).map((readiness) => {
    const booking = bookingById.get(readiness.booking_id);
    const room = booking ? roomCodeOf(booking) : 'ไม่ระบุห้อง';
    const blockers = Array.isArray(readiness.blockers) && readiness.blockers.length
      ? readiness.blockers.join(', ')
      : 'ไม่มี';
    return '- ' + room +
      ' | Cleaning: ' + (readiness.cleaning_ready ? 'พร้อม' : 'ยังไม่พร้อม') +
      ' | Access Prep: ' + (readiness.access_prep_ready ? 'พร้อม' : 'ยังไม่พร้อม') +
      ' | Guest OA: ' + (readiness.ready ? 'ส่งข้อมูลเข้าห้องได้' : 'ยังบล็อก') +
      ' | เหตุผล: ' + blockers;
  });
}

function block(label, scope) {
  const scopeBookings = bookings.filter((b) => portfolioOf(b) === scope);
  const checkIn = scopeBookings.filter((b) => b.check_in_date === today);
  const staying = scopeBookings.filter((b) => b.check_in_date < today && b.check_out_date > today);
  const checkOut = scopeBookings.filter((b) => b.check_out_date === today);
  const tomorrowCheckIn = scopeBookings.filter((b) => b.check_in_date === tomorrow);
  return [
    label,
    section('เช็กอินวันนี้', checkIn),
    '',
    section('พักอยู่วันนี้', staying),
    '',
    section('เช็กเอาต์วันนี้', checkOut),
    '',
    section('เช็กอินพรุ่งนี้', tomorrowCheckIn),
  ].join('\\n');
}

const duplicateWarnings = duplicateWarningRows();
function buildFullReply() {
  return [
  'สรุปวันนี้ ' + titleDate(today),
  '',
  'ต้องดูแล',
  ...needsAttentionRows(bookings),
  '',
  ...renderFieldAssistanceTasks(fieldAssistanceTasks),
  ...(fieldAssistanceTasks.length ? [''] : []),
  'Case Cards',
  ...caseCardRows(),
  '',
  block('Impact Arena Condo', 'impact'),
  '',
  block('Popular Condo / Mom Portfolio', 'mom'),
  '',
  'Housekeeping',
  ...housekeepingTruthRows(),
  '',
  'Room Access Readiness',
  ...roomReadinessRows(),
  ...(duplicateWarnings.length ? ['', ...duplicateWarnings] : []),
  '',
  'อ้างอิงเฉพาะ booking ที่บันทึกในระบบตอนนี้ค่ะ',
  ].join('\\n');
}

function buildHousekeepingReply() {
  const fieldLines = renderFieldAssistanceTasks(fieldAssistanceTasks);
  return [
    'สถานะแม่บ้านตอนนี้ ' + titleDate(today),
    '',
    'งานแม่บ้านที่เปิดอยู่',
    ...housekeepingTruthRows(),
    '',
    'ความพร้อมเข้าห้อง',
    ...roomReadinessRows(),
    '',
    ...(fieldLines.length ? fieldLines : ['Field Assistance ด่วน', '- ไม่มี']),
  ].join('\\n');
}

function buildCheckInOutReply() {
  const impactBookings = bookings.filter((b) => portfolioOf(b) === 'impact');
  const momBookings = bookings.filter((b) => portfolioOf(b) === 'mom');
  const signalRows = [];
  for (const booking of bookings) {
    const missing = missingFor(booking).filter((item) => item.includes('check-in') || item.includes('check-out'));
    for (const item of missing) {
      signalRows.push('- ' + safe(booking.guest_name_snapshot) + ' | ' + roomCodeOf(booking) + ': ' + item + '\\n  แนะนำ: ' + nextActionFor(item));
    }
  }
  return [
    'เช็กอิน/เช็กเอาต์วันนี้ ' + titleDate(today),
    '',
    block('Impact Arena Condo', 'impact'),
    '',
    block('Popular Condo / Mom Portfolio', 'mom'),
    '',
    'ต้องดูแลจากสัญญาณ check-in/check-out',
    ...(signalRows.length ? signalRows : ['- ไม่มีสัญญาณ check-in/check-out ที่ค้างจากข้อมูลตอนนี้']),
    '',
    'อ้างอิงเฉพาะ booking ที่บันทึกในระบบตอนนี้ค่ะ',
  ].join('\\n');
}

const snapshotView = ctx.snapshot_view === 'housekeeping' || ctx.snapshot_view === 'check_in_out'
  ? ctx.snapshot_view
  : 'full';
const replyText = snapshotView === 'housekeeping'
  ? buildHousekeepingReply()
  : snapshotView === 'check_in_out'
    ? buildCheckInOutReply()
    : buildFullReply();

return [{
  json: {
    ...ctx,
    bookings,
    open_cases: openCases,
    field_assistance_tasks: fieldAssistanceTasks,
    cleaning_tasks: cleaningTasks,
    cleaning_checklist_items: checklistItems,
    access_preparations: accessPreparations,
    housekeeping_queue: housekeepingQueue,
    room_access_readiness: roomAccessReadiness,
    room_statuses: statuses,
    open_draft_sessions: openSessions,
    evidence_contract: {
      version: 'phase4-daily-ops-v1',
      room_readiness_separate_from_access_prep: true,
      sources: ['bookings', 'room_statuses', 'internal_ops_cases', 'field_assistance_tasks', 'cleaning_tasks', 'cleaning_task_checklist_items', 'booking_access_preparations', 'get_housekeeping_queue', 'get_room_access_readiness'],
    },
    reply: {
      channel: 'internal_ops_oa',
      to: ctx.line_user_id,
      text: replyText,
      conversation_id: ctx.conversation_id,
      source_event_id: ctx.source_event_id,
      correlation_id: ctx.correlation_id,
      reply_token_ephemeral: ctx.reply_token_ephemeral,
    },
  },
}];
`);

function ifNode(id, name, leftValue, position) {
  return {
    parameters: {
      conditions: {
        options: {
          caseSensitive: true,
          leftValue: '',
          typeValidation: 'loose',
        },
        conditions: [{
          id,
          leftValue,
          rightValue: true,
          operator: {
            type: 'boolean',
            operation: 'true',
            singleValue: true,
          },
        }],
        combinator: 'and',
      },
      options: {},
    },
    id,
    name,
    type: 'n8n-nodes-base.if',
    typeVersion: 2,
    position,
  };
}

function ensureNode(newNode) {
  const index = workflow.nodes.findIndex((item) => item.name === newNode.name);
  if (index >= 0) workflow.nodes[index] = newNode;
  else workflow.nodes.push(newNode);
}

ensureNode(ifNode(
  'p4-s0-if-validate-no-access',
  'IF no access from env',
  '={{ $json.no_access === true }}',
  [-620, 0],
));
ensureNode(ifNode(
  'p4-s0-if-admin-no-access',
  'IF no access after admin lookup',
  '={{ $json.no_access === true }}',
  [240, 0],
));
ensureNode({
  id: 'p4-s1-get-open-internal-ops-cases',
  name: 'GET open internal ops cases',
  type: 'n8n-nodes-base.httpRequest',
  typeVersion: 4.2,
  position: [1120, 180],
  parameters: {
    method: 'GET',
    url: "={{ $env.SUPABASE_URL + '/rest/v1/internal_ops_cases?select=id,case_code,case_type,priority,status,guest_display_snapshot,room_code_snapshot,check_in_date_snapshot,check_out_date_snapshot,channel_target,platform_snapshot,latest_guest_message_excerpt,issue_summary,ai_suggestion,admin_action_needed,visible_card_summary,created_at,updated_at&status=not.in.(resolved,closed)&order=updated_at.desc&limit=10' }}",
    sendHeaders: true,
    headerParameters: {
      parameters: [
        { name: 'apikey', value: '={{ $env.SUPABASE_SERVICE_ROLE_KEY }}' },
        { name: 'Authorization', value: '=Bearer {{ $env.SUPABASE_SERVICE_ROLE_KEY }}' },
      ],
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
});
ensureNode({
  id: 'p4-s22-get-open-field-assistance-tasks',
  name: 'GET open field assistance tasks',
  type: 'n8n-nodes-base.httpRequest',
  typeVersion: 4.2,
  position: [1340, 180],
  parameters: {
    method: 'GET',
    url: "={{ $env.SUPABASE_URL + '/rest/v1/field_assistance_tasks?select=id,building,location_label,priority,status,dispatch_status,ack_status,source_text,created_at,internal_ops_cases(case_code)&status=not.in.(resolved,closed)&order=created_at.desc&limit=10' }}",
    sendHeaders: true,
    headerParameters: {
      parameters: [
        { name: 'apikey', value: '={{ $env.SUPABASE_SERVICE_ROLE_KEY }}' },
        { name: 'Authorization', value: '=Bearer {{ $env.SUPABASE_SERVICE_ROLE_KEY }}' },
      ],
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
});
ensureNode({
  id: 'p4-s3-get-open-cleaning-tasks',
  name: 'GET open cleaning tasks',
  type: 'n8n-nodes-base.httpRequest',
  typeVersion: 4.2,
  position: [1560, 180],
  parameters: {
    method: 'GET',
    url: "={{ $env.SUPABASE_URL + '/rest/v1/cleaning_tasks?select=id,task_key,room_id,booking_id,task_type,priority,status,dispatch_status,checklist_status,assigned_housekeeper_id,due_at,ack_due_at,dispatched_at,acknowledged_at,started_at,completed_at,blocker_reason,created_at,updated_at,rooms(room_code,building)&status=not.in.(completed,canceled)&order=created_at.desc&limit=20' }}",
    sendHeaders: true,
    headerParameters: {
      parameters: [
        { name: 'apikey', value: '={{ $env.SUPABASE_SERVICE_ROLE_KEY }}' },
        { name: 'Authorization', value: '=Bearer {{ $env.SUPABASE_SERVICE_ROLE_KEY }}' },
      ],
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
});
ensureNode({
  id: 'p4-s3-get-cleaning-checklist-items',
  name: 'GET cleaning checklist items',
  type: 'n8n-nodes-base.httpRequest',
  typeVersion: 4.2,
  position: [1780, 180],
  parameters: {
    method: 'GET',
    url: "={{ $env.SUPABASE_URL + '/rest/v1/cleaning_task_checklist_items?select=id,cleaning_task_id,room_id,item_key,item_label,required,status,issue_note,exception_reason&order=item_key.asc&limit=200' }}",
    sendHeaders: true,
    headerParameters: {
      parameters: [
        { name: 'apikey', value: '={{ $env.SUPABASE_SERVICE_ROLE_KEY }}' },
        { name: 'Authorization', value: '=Bearer {{ $env.SUPABASE_SERVICE_ROLE_KEY }}' },
      ],
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
});
ensureNode({
  id: 'p4-s3-get-booking-access-preparations',
  name: 'GET booking access preparations',
  type: 'n8n-nodes-base.httpRequest',
  typeVersion: 4.2,
  position: [2000, 180],
  parameters: {
    method: 'GET',
    url: "={{ $env.SUPABASE_URL + '/rest/v1/booking_access_preparations?select=id,booking_id,room_id,key_placed_in_room,room_left_unlocked_or_open,status,note,updated_at&order=updated_at.desc&limit=100' }}",
    sendHeaders: true,
    headerParameters: {
      parameters: [
        { name: 'apikey', value: '={{ $env.SUPABASE_SERVICE_ROLE_KEY }}' },
        { name: 'Authorization', value: '=Bearer {{ $env.SUPABASE_SERVICE_ROLE_KEY }}' },
      ],
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
});
ensureNode({
  id: 'p6-get-housekeeping-queue',
  name: 'GET housekeeping queue',
  type: 'n8n-nodes-base.code',
  typeVersion: 2,
  position: [2220, 180],
  parameters: {
    jsCode: code(`
const n8nContext = this;
async function request(path, body = null) {
  const response = await n8nContext.helpers.httpRequest({
    method: body ? 'POST' : 'GET',
    url: $env.SUPABASE_URL + '/rest/v1' + path,
    headers: {
      apikey: $env.SUPABASE_SERVICE_ROLE_KEY,
      Authorization: 'Bearer ' + $env.SUPABASE_SERVICE_ROLE_KEY,
      'Content-Type': 'application/json',
    },
    ...(body ? { body, json: true } : {}),
    returnFullResponse: true,
  });
  return response.body ?? response;
}

const housekeepers = await request(
  '/housekeepers?select=id,display_name&status=eq.active&active=eq.true&order=approved_at.asc,id.asc&limit=20'
);
const queue = [];
for (const housekeeper of Array.isArray(housekeepers) ? housekeepers : []) {
  const page = await request('/rpc/get_housekeeping_queue', {
    p_housekeeper_id: housekeeper.id,
    p_view: 'all',
    p_limit: 5,
    p_cursor: null,
  });
  queue.push({
    housekeeper_id: housekeeper.id,
    housekeeper_name: housekeeper.display_name ?? 'ไม่ระบุ',
    items: Array.isArray(page?.items) ? page.items : [],
  });
}
return [{ json: { housekeeping_queue: queue } }];
`),
  },
});
ensureNode({
  id: 'p6-get-room-access-readiness',
  name: 'GET room access readiness',
  type: 'n8n-nodes-base.code',
  typeVersion: 2,
  position: [2440, 180],
  parameters: {
    jsCode: code(`
const n8nContext = this;
const bookingResponse = $('GET bookings window').first().json.body ?? [];
const bookings = Array.isArray(bookingResponse) ? bookingResponse : [];
const readiness = [];
for (const booking of bookings) {
  if (!booking?.id) continue;
  try {
    const response = await n8nContext.helpers.httpRequest({
      method: 'POST',
      url: $env.SUPABASE_URL + '/rest/v1/rpc/get_room_access_readiness',
      headers: {
        apikey: $env.SUPABASE_SERVICE_ROLE_KEY,
        Authorization: 'Bearer ' + $env.SUPABASE_SERVICE_ROLE_KEY,
        'Content-Type': 'application/json',
      },
      body: { p_booking_id: booking.id },
      json: true,
      returnFullResponse: true,
    });
    readiness.push(response.body ?? response);
  } catch (_) {
    readiness.push({
      booking_id: booking.id,
      ready: false,
      cleaning_ready: false,
      access_prep_ready: false,
      blockers: ['readiness_unknown'],
    });
  }
}
return [{ json: { room_access_readiness: readiness } }];
`),
  },
});

node('Validate and extract snapshot').position = [-840, 0];
node('GET authorized admin user').position = [-180, 120];
node('Prep snapshot context').position = [20, 120];
node('GET bookings window').position = [460, 180];
node('GET room statuses').position = [680, 180];
node('GET open draft sessions').position = [900, 180];
node('GET open internal ops cases').position = [1120, 180];
node('GET open field assistance tasks').position = [1340, 180];
node('GET open cleaning tasks').position = [1560, 180];
node('GET cleaning checklist items').position = [1780, 180];
node('GET booking access preparations').position = [2000, 180];
node('GET housekeeping queue').position = [2220, 180];
node('GET room access readiness').position = [2440, 180];
node('Build snapshot reply').position = [2660, 180];
node('Send snapshot reply').position = [2880, 0];

workflow.connections = {
  'Receive snapshot trigger': {
    main: [[{ node: 'Validate and extract snapshot', type: 'main', index: 0 }]],
  },
  'Validate and extract snapshot': {
    main: [[{ node: 'IF no access from env', type: 'main', index: 0 }]],
  },
  'IF no access from env': {
    main: [
      [{ node: 'Send snapshot reply', type: 'main', index: 0 }],
      [{ node: 'GET authorized admin user', type: 'main', index: 0 }],
    ],
  },
  'GET authorized admin user': {
    main: [[{ node: 'Prep snapshot context', type: 'main', index: 0 }]],
  },
  'Prep snapshot context': {
    main: [[{ node: 'IF no access after admin lookup', type: 'main', index: 0 }]],
  },
  'IF no access after admin lookup': {
    main: [
      [{ node: 'Send snapshot reply', type: 'main', index: 0 }],
      [{ node: 'GET bookings window', type: 'main', index: 0 }],
    ],
  },
  'GET bookings window': {
    main: [[{ node: 'GET room statuses', type: 'main', index: 0 }]],
  },
  'GET room statuses': {
    main: [[{ node: 'GET open draft sessions', type: 'main', index: 0 }]],
  },
  'GET open draft sessions': {
    main: [[{ node: 'GET open internal ops cases', type: 'main', index: 0 }]],
  },
  'GET open internal ops cases': {
    main: [[{ node: 'GET open field assistance tasks', type: 'main', index: 0 }]],
  },
  'GET open field assistance tasks': {
    main: [[{ node: 'GET open cleaning tasks', type: 'main', index: 0 }]],
  },
  'GET open cleaning tasks': {
    main: [[{ node: 'GET cleaning checklist items', type: 'main', index: 0 }]],
  },
  'GET cleaning checklist items': {
    main: [[{ node: 'GET booking access preparations', type: 'main', index: 0 }]],
  },
  'GET booking access preparations': {
    main: [[{ node: 'GET housekeeping queue', type: 'main', index: 0 }]],
  },
  'GET housekeeping queue': {
    main: [[{ node: 'GET room access readiness', type: 'main', index: 0 }]],
  },
  'GET room access readiness': {
    main: [[{ node: 'Build snapshot reply', type: 'main', index: 0 }]],
  },
  'Build snapshot reply': {
    main: [[{ node: 'Send snapshot reply', type: 'main', index: 0 }]],
  },
};

workflow.versionId = undefined;
workflow.activeVersionId = undefined;
workflow.versionCounter = undefined;

fs.writeFileSync(workflowPath, JSON.stringify(workflow, null, 2) + '\n');
console.log('updated wf_internal_ops_snapshot.json');
