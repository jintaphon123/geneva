import {
  assertEquals,
  assertExists,
} from "https://deno.land/std@0.224.0/assert/mod.ts";
import {
  buildHousekeepingPostbackData,
  createHousekeepingHandler,
} from "./index.ts";

const WEBHOOK_SECRET = "test-webhook-secret-999";
const SOURCE_EVENT_ID = "22222222-2222-4222-8222-222222222277";

type QueryResult = { data: any; error: any };

class MockQueryBuilder {
  private data: any = null;
  private error: any = null;

  constructor(
    private client: MockSupabaseClient,
    private table: string,
  ) {}

  select() {
    return this;
  }

  eq(column: string, value: any) {
    const result = this.client.results[`${this.table}:${column}:${value}`];
    if (result) {
      this.data = result.data;
      this.error = result.error;
    }
    return this;
  }

  maybeSingle(): Promise<QueryResult> {
    return Promise.resolve({ data: this.data, error: this.error });
  }

  insert(payload: any) {
    this.client.writes.push({ table: this.table, method: "insert", payload });
    const result = this.client.results[`${this.table}:insert`] ||
      { data: { id: "hk-new-99", ...payload }, error: null };
    this.data = result.data;
    this.error = result.error;
    const promise = Promise.resolve(result);
    return Object.assign(promise, {
      select: (_cols?: string) => {
        return Object.assign(Promise.resolve(result), {
          single: () => Promise.resolve(result),
          maybeSingle: () => Promise.resolve(result),
        });
      },
      single: () => Promise.resolve(result),
      maybeSingle: () => Promise.resolve(result),
    });
  }

  upsert(payload: any, _options?: any) {
    this.client.writes.push({ table: this.table, method: "upsert", payload });
    const result = this.client.results[`${this.table}:upsert`] ||
      { data: { id: "mock-upsert-id", ...payload }, error: null };
    this.data = result.data;
    this.error = result.error;
    const promise = Promise.resolve(result);
    return Object.assign(promise, {
      select: (_cols?: string) => {
        return Object.assign(Promise.resolve(result), {
          single: () => Promise.resolve(result),
          maybeSingle: () => Promise.resolve(result),
        });
      },
      single: () => Promise.resolve(result),
      maybeSingle: () => Promise.resolve(result),
    });
  }
}

class MockSupabaseClient {
  results: Record<string, QueryResult> = {};
  writes: Array<{ table: string; method: string; payload: any }> = [];
  rpcCalls: Array<{ name: string; args: any }> = [];

  from(table: string) {
    return new MockQueryBuilder(this, table);
  }

  rpc(name: string, args: any): Promise<QueryResult> {
    this.rpcCalls.push({ name, args });
    const result = this.results[`rpc:${name}`] || { data: null, error: null };
    return Promise.resolve(result);
  }
}

function handlerWith(
  db: MockSupabaseClient,
  transition?: any,
  accessTransition?: any,
) {
  return createHousekeepingHandler({
    getEnv: (key) => key === "N8N_WEBHOOK_SECRET" ? WEBHOOK_SECRET : undefined,
    createSupabase: () => db,
    transition,
    accessTransition,
  });
}

function request(body: Record<string, unknown>, secret = WEBHOOK_SECRET) {
  return new Request("http://localhost/functions/v1/housekeeping-handler", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-impact-webhook-secret": secret,
    },
    body: JSON.stringify(body),
  });
}

function activeHousekeeper(db: MockSupabaseClient) {
  db.results["housekeepers:line_user_id:U_active_test_77"] = {
    data: {
      id: "hk-active-77",
      status: "active",
      active: true,
      display_name: "Bond Owner",
    },
    error: null,
  };
}

function focusedTask(db: MockSupabaseClient) {
  db.results["housekeeper_task_focus:housekeeper_id:hk-active-77"] = {
    data: {
      focus_type: "cleaning",
      focused_cleaning_task_id: "task-active-77",
    },
    error: null,
  };
  db.results["cleaning_tasks:id:task-active-77"] = {
    data: {
      id: "task-active-77",
      room_id: "room-active-77",
      status: "waiting_ack",
      assigned_housekeeper_id: "hk-active-77",
    },
    error: null,
  };
  db.results["rooms:id:room-active-77"] = {
    data: { room_code: "C8/13/15" },
    error: null,
  };
}

Deno.test("Task 5 HTTP - rejects requests with missing or invalid secret", async () => {
  const handler = handlerWith(new MockSupabaseClient());
  const res1 = await handler(
    new Request(
      "http://localhost/functions/v1/housekeeping-handler",
      {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          line_user_id: "U123",
          text: "เริ่มใช้งาน",
          source_event_id: SOURCE_EVENT_ID,
        }),
      },
    ),
  );
  assertEquals(res1.status, 401);

  const res2 = await handler(request({
    line_user_id: "U123",
    text: "เริ่มใช้งาน",
    source_event_id: SOURCE_EVENT_ID,
  }, "wrong-secret"));
  assertEquals(res2.status, 401);
});

Deno.test("Task 5 HTTP - requires source_event_id", async () => {
  const handler = handlerWith(new MockSupabaseClient());
  const res = await handler(request({
    line_user_id: "U123",
    text: "เริ่มใช้งาน",
  }));
  assertEquals(res.status, 400);
  assertEquals((await res.json()).error, "bad_request");
});

Deno.test("Task 5 HTTP - pending enrollment masks LINE identity and creates inactive profile", async () => {
  const db = new MockSupabaseClient();
  db.results["housekeepers:line_user_id:U_enroll_test_99"] = {
    data: null,
    error: null,
  };
  const handler = handlerWith(db);

  const res = await handler(request({
    line_user_id: "U_enroll_test_99",
    text: "เริ่มใช้งาน",
    source_event_id: "00000000-0000-4000-8000-000000000099",
    display_name: "Bond Owner",
  }));

  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, true);
  assertEquals(body.action, "enroll");
  assertEquals(body.internal_notification.text.includes("U_enro...t_99"), true);
  assertEquals(
    body.internal_notification.text.includes("U_enroll_test_99"),
    false,
  );
  assertEquals(db.writes[0].payload.status, "pending");
  assertEquals(db.writes[0].payload.active, false);
});

Deno.test("Task 5 HTTP - enrollment insert failure returns database_error", async () => {
  const db = new MockSupabaseClient();
  db.results["housekeepers:line_user_id:U_enroll_test_99"] = {
    data: null,
    error: null,
  };
  db.results["housekeepers:insert"] = {
    data: null,
    error: { message: "insert failed" },
  };
  const handler = handlerWith(db);

  const res = await handler(request({
    line_user_id: "U_enroll_test_99",
    text: "เริ่มใช้งาน",
    source_event_id: "00000000-0000-4000-8000-000000000099",
  }));
  assertEquals(res.status, 500);
  assertEquals((await res.json()).error, "database_error");
});

Deno.test("Task 5 HTTP - rejects unregistered housekeeper trying normal command", async () => {
  const db = new MockSupabaseClient();
  db.results["housekeepers:line_user_id:U_unknown_operator"] = {
    data: null,
    error: null,
  };
  const handler = handlerWith(db);

  const res = await handler(request({
    line_user_id: "U_unknown_operator",
    text: "รับทราบ",
    source_event_id: "00000000-0000-4000-8000-000000000077",
  }));

  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, false);
  assertEquals(body.error, "housekeeper_not_found");
});

Deno.test("Task 5 HTTP - active housekeeper transition returns structured response", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  focusedTask(db);
  let transitionCalls = 0;
  const transition = () => {
    transitionCalls += 1;
    return Promise.resolve({
      ok: true as const,
      action: "acknowledge_task",
      taskId: "task-active-77",
      previousState: "waiting_ack",
      newState: "acknowledged",
    });
  };
  const handler = handlerWith(db, transition as any);

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "รับทราบ",
    source_event_id: SOURCE_EVENT_ID,
    display_name: "Active Housekeeper",
  }));

  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, true);
  assertEquals(body.action, "acknowledge_task");
  assertEquals(body.housekeeping_reply.text.includes("รับทราบงาน"), true);
  assertEquals(body.internal_notification.text.includes("รับทราบงาน"), true);
  assertEquals(body.guest_draft_request, null);
  assertEquals(transitionCalls, 1);
});

Deno.test("Task 6 HTTP - /today returns native queue Flex message without state mutation", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  db.results["rpc:get_housekeeping_queue"] = {
    data: {
      items: [{
        task_id: "11111111-1111-4111-8111-111111111111",
        task_kind: "cleaning",
        room_code: "C8/13/15",
        guest_name: "Somchai Verylong Private Guest Name",
        priority: "urgent",
        status: "waiting_ack",
        linked_task_kind: "access_prep",
        linked_task_status: "pending_dispatch",
        has_open_blocker: true,
        claimable: true,
      }],
      next_cursor: null,
      previous_cursor: null,
    },
    error: null,
  };
  const handler = handlerWith(
    db,
    (() => {
      throw new Error("/today must not call state transition");
    }) as any,
  );

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "/today",
    source_event_id: SOURCE_EVENT_ID,
  }));

  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, true);
  assertEquals(body.action, "show_today");
  assertEquals(body.housekeeping_reply.text, undefined);
  assertEquals(body.housekeeping_reply.messages[0].type, "flex");
  assertEquals(body.housekeeping_reply.messages[0].altText, "คิวงานแม่บ้าน 1 งาน");
  assertEquals(body.internal_notification, null);
  assertEquals(body.evidence, {
    source_event_id: SOURCE_EVENT_ID,
    view: "today",
    count: 1,
  });
  assertEquals(db.rpcCalls, [{
    name: "get_housekeeping_queue",
    args: {
      p_housekeeper_id: "hk-active-77",
      p_view: "today",
      p_limit: 5,
      p_cursor: null,
    },
  }]);
});

Deno.test("Task 6 HTTP - queue navigation decodes signed cursor payload for RPC", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  db.results["rpc:get_housekeeping_queue"] = {
    data: { items: [], next_cursor: null, previous_cursor: null },
    error: null,
  };
  const handler = handlerWith(
    db,
    (() => {
      throw new Error("show_queue must not mutate state");
    }) as any,
  );
  const cursor = encodeURIComponent(JSON.stringify({
    direction: "next",
    sortKey: "cursor-next",
  }));

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: `action=show_queue&cursor=${cursor}&sig=test`,
    source_event_id: SOURCE_EVENT_ID,
  }));

  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, true);
  assertEquals(body.action, "show_queue");
  assertEquals(body.housekeeping_reply.messages[0].altText, "คิวงานแม่บ้าน 0 งาน");
  assertEquals(db.rpcCalls[0].args, {
    p_housekeeper_id: "hk-active-77",
    p_view: "all",
    p_limit: 5,
    p_cursor: { direction: "next", sortKey: "cursor-next" },
  });
});

Deno.test("Task 5 HTTP - system transition failure is not wrapped as success", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  const handler = handlerWith(
    db,
    (() =>
      Promise.resolve({
        ok: false,
        error: "database_error",
        message: "rpc failed",
        taskId: "task-active-77",
      })) as any,
  );

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "รับทราบ",
    source_event_id: SOURCE_EVENT_ID,
  }));
  assertEquals(res.status, 500);
  const body = await res.json();
  assertEquals(body.ok, false);
  assertEquals(body.error, "database_error");
  assertEquals(
    body.internal_notification.text.includes("database_error"),
    true,
  );
});

Deno.test("Task 5 HTTP - task lookup failure after transition is not wrapped as success", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  db.results["cleaning_tasks:id:task-active-77"] = {
    data: null,
    error: { message: "task lookup failed" },
  };
  const handler = handlerWith(
    db,
    (() =>
      Promise.resolve({
        ok: true,
        action: "acknowledge_task",
        taskId: "task-active-77",
        previousState: "waiting_ack",
        newState: "acknowledged",
      })) as any,
  );

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "รับทราบ",
    source_event_id: SOURCE_EVENT_ID,
  }));
  assertEquals(res.status, 500);
  const body = await res.json();
  assertEquals(body.ok, false);
  assertEquals(body.error, "database_error");
  assertEquals(body.housekeeping_reply.text.includes("อ่านรายละเอียดงาน"), true);
});

Deno.test("Task 5 HTTP - view_details is read-only and does not call state mutation", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  focusedTask(db);
  let transitionCalls = 0;
  const handler = handlerWith(
    db,
    (() => {
      transitionCalls += 1;
      throw new Error("view_details must not mutate state");
    }) as any,
  );

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "ดูรายละเอียด",
    source_event_id: SOURCE_EVENT_ID,
  }));
  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, true);
  assertEquals(body.action, "view_details");
  assertEquals(body.housekeeping_reply.text.includes("C8/13/15"), true);
  assertEquals(transitionCalls, 0);
});

Deno.test("Task 5 HTTP - view_details reports task lookup failures as system errors", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  db.results["housekeeper_task_focus:housekeeper_id:hk-active-77"] = {
    data: {
      focus_type: "cleaning",
      focused_cleaning_task_id: "task-active-77",
    },
    error: null,
  };
  db.results["cleaning_tasks:id:task-active-77"] = {
    data: null,
    error: { message: "task lookup failed" },
  };
  let transitionCalls = 0;
  const handler = handlerWith(
    db,
    (() => {
      transitionCalls += 1;
      throw new Error("view_details must not mutate state");
    }) as any,
  );

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "ดูรายละเอียด",
    source_event_id: SOURCE_EVENT_ID,
  }));
  assertEquals(res.status, 500);
  const body = await res.json();
  assertEquals(body.ok, false);
  assertEquals(body.error, "database_error");
  assertEquals(transitionCalls, 0);
});

Deno.test("Task 10 HTTP - view_details renders checklist, access prep, and quick replies", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  focusedTask(db);

  db.results["cleaning_task_checklist_items:cleaning_task_id:task-active-77"] =
    {
      data: [
        { item_key: "water", item_label: "น้ำ", status: "present" },
        { item_key: "towels", item_label: "ผ้าขนหนู", status: "missing" },
      ],
      error: null,
    };
  db.results["bookings:id:booking-active-77"] = {
    data: {
      check_in_date: "2026-06-11",
    },
    error: null,
  };
  db.results["internal_ops_cases:id:case-active-77"] = {
    data: {
      case_code: "IOC-77",
      issue_summary: "เตรียมห้องก่อนแขกมาถึง",
    },
    error: null,
  };
  db.results["booking_access_preparations:booking_id:booking-active-77"] = {
    data: {
      key_placed_in_room: true,
      room_left_unlocked_or_open: false,
      status: "partial",
    },
    error: null,
  };

  db.results["cleaning_tasks:id:task-active-77"] = {
    data: {
      id: "task-active-77",
      room_id: "room-active-77",
      booking_id: "booking-active-77",
      internal_ops_case_id: "case-active-77",
      assigned_housekeeper_id: "hk-active-77",
      status: "in_progress",
      priority: "high",
      instructions: "กรุณาเติมทิชชู่ด้วย",
    },
    error: null,
  };

  const handler = handlerWith(
    db,
    (() => {
      throw new Error("not called");
    }) as any,
  );

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "ดูรายละเอียด",
    source_event_id: SOURCE_EVENT_ID,
  }));

  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, true);

  const replyText = body.housekeeping_reply.text;
  assertEquals(replyText.includes("[ใบสั่งงานห้อง C8/13/15]"), true);
  assertEquals(replyText.includes("ความสำคัญ: ด่วน"), true);
  assertEquals(replyText.includes("คำแนะนำ/โน้ต: กรุณาเติมทิชชู่ด้วย"), true);
  assertEquals(replyText.includes("กุญแจ: วางแล้ว, ประตู: ยังไม่เปิด"), true);
  assertEquals(replyText.includes("IOC-77 - เตรียมห้องก่อนแขกมาถึง"), true);
  assertEquals(replyText.includes("[✓] น้ำ"), true);
  assertEquals(replyText.includes("[ขาด] ผ้าขนหนู"), true);

  const qr = body.housekeeping_reply.quickReply;
  assertEquals(Array.isArray(qr?.items), true);
  const labels = qr.items.map((it: any) => it.action.label);
  assertEquals(labels.includes("เสร็จงาน"), true);
  assertEquals(labels.includes("ไม่มี น้ำ"), true);
  assertEquals(labels.includes("เติม ผ้าขนหนู แล้ว"), true);
  assertEquals(labels.includes("เปิดห้องแล้ว"), true);
  assertEquals(labels.includes("วางกุญแจแล้ว"), false);
  assertEquals(labels.includes("รายละเอียดงาน"), true);
});

Deno.test("Task 10 HTTP - supports postbackTaskId parameter in transition request", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  focusedTask(db);

  const targetTaskId = "88888888-8888-4888-8888-888888888888";
  db.results[`cleaning_tasks:id:${targetTaskId}`] = {
    data: {
      id: targetTaskId,
      room_id: "room-active-77",
      status: "waiting_ack",
      assigned_housekeeper_id: "hk-active-77",
    },
    error: null,
  };
  db.results[`housekeeper_task_focus:insert`] = {
    data: { id: "focus-id" },
    error: null,
  };

  let receivedOverrideId: string | null = null;
  const transition = (
    _supabase: any,
    _lineUserId: string,
    _intent: any,
    _sourceEventId: string,
    overrideTaskId?: string | null,
  ) => {
    receivedOverrideId = overrideTaskId ?? null;
    return Promise.resolve({
      ok: true as const,
      action: "acknowledge_task",
      taskId: targetTaskId,
      previousState: "waiting_ack",
      newState: "acknowledged",
    });
  };

  const handler = handlerWith(db, transition as any);

  const postbackData = await buildHousekeepingPostbackData(
    "acknowledge_task",
    targetTaskId,
    null,
    WEBHOOK_SECRET,
  );
  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: postbackData,
    source_event_id: SOURCE_EVENT_ID,
  }));

  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, true);
  assertEquals(receivedOverrideId, targetTaskId);
});

Deno.test("Phase 6 HTTP routes Access Prep postbacks to the Access Prep state service", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  const taskId = "77777777-7777-4777-8777-777777777777";
  db.results[`access_prep_tasks:id:${taskId}`] = {
    data: {
      id: taskId,
      room_id: "room-active-77",
      status: "in_progress",
      assigned_housekeeper_id: "hk-active-77",
    },
    error: null,
  };
  db.results["rooms:id:room-active-77"] = {
    data: { room_code: "C8/13/15" },
    error: null,
  };

  let cleaningCalls = 0;
  let accessInput: any = null;
  const handler = handlerWith(
    db,
    (() => {
      cleaningCalls += 1;
      throw new Error("cleaning transition must not handle Access Prep");
    }) as any,
    ((_db: any, input: any) => {
      accessInput = input;
      return Promise.resolve({
        ok: true,
        action: "mark_key_placed",
        taskId,
        previousState: "in_progress",
        newState: "in_progress",
      });
    }) as any,
  );

  const postbackData = await buildHousekeepingPostbackData(
    "mark_key_placed",
    taskId,
    null,
    WEBHOOK_SECRET,
    "access_prep",
  );
  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: postbackData,
    source_event_id: SOURCE_EVENT_ID,
  }));
  const body = await res.json();

  assertEquals(res.status, 200);
  assertEquals(body.ok, true);
  assertEquals(body.action, "mark_key_placed");
  assertEquals(cleaningCalls, 0);
  assertEquals(accessInput, {
    taskId,
    housekeeperId: "hk-active-77",
    action: "mark_key_placed",
    sourceEventId: SOURCE_EVENT_ID,
    payload: {},
  });
});

Deno.test("Task 10 HTTP - rejects tampered task postback signature", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  focusedTask(db);
  const handler = handlerWith(db);

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text:
      "action=acknowledge_task&task_id=88888888-8888-4888-8888-888888888888&sig=tampered",
    source_event_id: SOURCE_EVENT_ID,
  }));

  assertEquals(res.status, 403);
  const body = await res.json();
  assertEquals(body.error, "invalid_postback_signature");
});

Deno.test("Task 10 HTTP - fails truthfully when checklist lookup fails", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  focusedTask(db);
  db.results["cleaning_task_checklist_items:cleaning_task_id:task-active-77"] =
    {
      data: null,
      error: { message: "database unavailable" },
    };

  const handler = handlerWith(
    db,
    (() => {
      throw new Error("view_details must not mutate state");
    }) as any,
  );

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "ดูรายละเอียด",
    source_event_id: SOURCE_EVENT_ID,
  }));

  assertEquals(res.status, 500);
  const body = await res.json();
  assertEquals(body.ok, false);
  assertEquals(body.error, "server_error");
});

Deno.test("Task H4 - buildFailureReply returns polite Thai message for no_booking", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  focusedTask(db);
  const handler = handlerWith(
    db,
    (() =>
      Promise.resolve({
        ok: false,
        error: "no_booking",
        message: "No booking is associated with the cleaning task",
        taskId: "task-active-77",
      })) as any,
  );

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "วางกุญแจแล้ว",
    source_event_id: SOURCE_EVENT_ID,
  }));
  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, true);
  assertEquals(body.action, "rejected");
  assertEquals(
    body.housekeeping_reply.text,
    "รับเรื่องแล้วค่ะ ระบบกำลังแจ้ง Internal Ops และเจ้าของให้ตรวจสอบทันทีค่ะ",
  );
  assertEquals(body.incident_candidate.requires_internal_ops, true);
  assertEquals(body.incident_candidate.requires_owner, true);
  assertEquals(body.incident_candidate.issue_family, "housekeeping_out_of_sop");
  assertEquals(body.incident_candidate.issue_subtype, "transition_failure");
});

Deno.test("Task 5 HTTP - weather query unknown command returns incident candidate", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  focusedTask(db);
  const handler = handlerWith(db);

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "พรุ่งนี้ฝนจะตกไหม",
    source_event_id: SOURCE_EVENT_ID,
  }));
  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, true);
  assertEquals(body.action, "unknown");
  assertEquals(
    body.housekeeping_reply.text,
    "รับเรื่องแล้วค่ะ ระบบกำลังแจ้ง Internal Ops และเจ้าของให้ตรวจสอบทันทีค่ะ",
  );
  assertEquals(body.incident_candidate.requires_internal_ops, true);
  assertEquals(body.incident_candidate.requires_owner, true);
  assertEquals(body.incident_candidate.issue_family, "housekeeping_out_of_sop");
  assertEquals(body.incident_candidate.issue_subtype, "weather_query");
  assertEquals(body.incident_candidate.severity, "normal");
});

Deno.test("Task 5 HTTP - refund query unknown command returns incident candidate", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  focusedTask(db);
  const handler = handlerWith(db);

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "ขอคืนเงิน",
    source_event_id: SOURCE_EVENT_ID,
  }));
  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, true);
  assertEquals(body.incident_candidate.issue_subtype, "refund_request");
});

Deno.test("Task 5 HTTP - ambiguous pronoun unknown command returns incident candidate", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  focusedTask(db);
  const handler = handlerWith(db);

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "คนนี้จะเช็คเอาท์",
    source_event_id: SOURCE_EVENT_ID,
  }));
  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, true);
  assertEquals(body.incident_candidate.issue_subtype, "ambiguous_pronoun");
});

Deno.test("Task 5 HTTP - compound command unknown command returns incident candidate", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  focusedTask(db);
  const handler = handlerWith(db);

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "วางกุญแจและเริ่มงาน",
    source_event_id: SOURCE_EVENT_ID,
  }));
  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, true);
  assertEquals(body.incident_candidate.issue_subtype, "compound_command");
});

Deno.test("Task 5 HTTP - urgent severity incident candidate on safety issues", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  focusedTask(db);
  const handler = handlerWith(db);

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "มีกลิ่นไหม้ในห้องพัก",
    source_event_id: SOURCE_EVENT_ID,
  }));
  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, true);
  assertEquals(body.incident_candidate.severity, "urgent");
});

Deno.test("Phase 6 HTTP - Access Prep acknowledge sets access focus with onConflict housekeeper_id", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  db.results[`housekeeper_task_focus:upsert`] = { data: null, error: null };
  const targetTaskId = "ap-task-42";

  let receivedPayload: any = null;
  const accessTransition = (_client: any, params: any) => {
    return Promise.resolve({
      ok: true,
      action: "acknowledge_task",
      taskId: targetTaskId,
      previousState: "sent",
      newState: "acknowledged",
    });
  };

  const originalUpsert = db.from;
  db.from = (table: string) => {
    const chain = originalUpsert.call(db, table);
    if (table === "housekeeper_task_focus") {
      const origUpsert = (chain as any).upsert;
      (chain as any).upsert = (payload: any, options: any) => {
        receivedPayload = payload;
        assertEquals(options, { onConflict: "housekeeper_id" });
        return origUpsert.call(chain, payload, options);
      };
    }
    return chain;
  };

  const handler = handlerWith(db, undefined, accessTransition as any);

  const postbackData = await buildHousekeepingPostbackData(
    "acknowledge_task",
    targetTaskId,
    "access_prep",
    WEBHOOK_SECRET,
  );

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "not used",
    source_event_id: SOURCE_EVENT_ID,
    postback_data: postbackData,
  }));

  assertEquals(res.status, 200);
  assertExists(receivedPayload);
  assertEquals(receivedPayload.focus_type, "access_prep");
  assertEquals(receivedPayload.focused_access_prep_task_id, targetTaskId);
});

Deno.test("Phase 6 HTTP - Access Prep done clears access focus", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  db.results[`housekeeper_task_focus:upsert`] = { data: null, error: null };
  db.results[`cleaning_tasks:select`] = { data: null, error: null };
  const targetTaskId = "ap-task-42";

  let receivedPayload: any = null;
  const accessTransition = (_client: any, params: any) => {
    return Promise.resolve({
      ok: true,
      action: "mark_room_open",
      taskId: targetTaskId,
      previousState: "in_progress",
      newState: "done",
    });
  };

  const originalUpsert = db.from;
  db.from = (table: string) => {
    const chain = originalUpsert.call(db, table);
    if (table === "housekeeper_task_focus") {
      const origUpsert = (chain as any).upsert;
      (chain as any).upsert = (payload: any, options: any) => {
        receivedPayload = payload;
        assertEquals(options, { onConflict: "housekeeper_id" });
        return origUpsert.call(chain, payload, options);
      };
    }
    return chain;
  };

  const handler = handlerWith(db, undefined, accessTransition as any);

  const postbackData = await buildHousekeepingPostbackData(
    "mark_room_open",
    targetTaskId,
    "access_prep",
    WEBHOOK_SECRET,
  );

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "not used",
    source_event_id: SOURCE_EVENT_ID,
    postback_data: postbackData,
  }));

  assertEquals(res.status, 200);
  assertExists(receivedPayload);
  assertEquals(receivedPayload.focus_type, null);
  assertEquals(receivedPayload.focused_access_prep_task_id, null);
  assertEquals(receivedPayload.focused_cleaning_task_id, null);
});

Deno.test("Phase 6 HTTP - capability denial stores access_prep_task_id and cleaning_task_id=null", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  const targetTaskId = "ap-task-42";

  const accessTransition = (_client: any, params: any) => {
    return Promise.resolve({
      ok: false,
      error: "capability_denied",
      message: "Insufficient capabilities",
      taskId: targetTaskId,
      required_capability: "open_room",
    });
  };

  const handler = handlerWith(db, undefined, accessTransition as any);

  const postbackData = await buildHousekeepingPostbackData(
    "mark_room_open",
    targetTaskId,
    "access_prep",
    WEBHOOK_SECRET,
  );

  const res = await handler(request({
    line_user_id: "U_active_test_77",
    text: "not used",
    source_event_id: SOURCE_EVENT_ID,
    postback_data: postbackData,
  }));

  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, false);
  const incident = body.incident_candidate;
  assertExists(incident);
  assertEquals(incident.issue_family, "housekeeping_out_of_sop");
  assertEquals(incident.issue_subtype, "unauthorized_access_prep_action");
  assertEquals(incident.cleaning_task_id, null);
  assertEquals(incident.metadata.access_prep_task_id, targetTaskId);
});
