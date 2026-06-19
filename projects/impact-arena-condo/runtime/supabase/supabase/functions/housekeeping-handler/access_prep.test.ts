import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import {
  createOrMergeAccessPrepTask,
  handleAccessPrepTransition,
  overrideHousekeepingTask,
} from "./access_prep.ts";

const SOURCE_EVENT_ID = "11111111-1111-4111-8111-111111111111";
const TASK_ID = "22222222-2222-4222-8222-222222222222";
const HOUSEKEEPER_ID = "33333333-3333-4333-8333-333333333333";

type QueryResult = { data: any; error: any };

class MockSupabaseClient {
  rpcCalls: Array<{ name: string; args: any }> = [];
  rpcResults: QueryResult[] = [];

  rpc(name: string, args: any): Promise<QueryResult> {
    this.rpcCalls.push({ name, args });
    return Promise.resolve(
      this.rpcResults.shift() ?? { data: null, error: null },
    );
  }
}

function okResult(action: string, previousState: string, newState: string) {
  return {
    ok: true,
    action,
    taskId: TASK_ID,
    previousState,
    newState,
  } as const;
}

Deno.test("access prep delegates task creation and merge to one transactional RPC", async () => {
  const db = new MockSupabaseClient();
  db.rpcResults.push({
    data: {
      ok: true,
      taskId: TASK_ID,
      taskKey: "access-prep:booking-1",
      created: true,
      merged: false,
      status: "new",
    },
    error: null,
  });

  const result = await createOrMergeAccessPrepTask(
    db as any,
    {
      task_key: "access-prep:booking-1",
      booking_id: "44444444-4444-4444-8444-444444444444",
      room_id: "55555555-5555-4555-8555-555555555555",
      scheduled_for: "2026-06-20T18:00:00.000Z",
      assigned_housekeeper_id: HOUSEKEEPER_ID,
      priority: "urgent",
      source: "internal_ops",
    },
    SOURCE_EVENT_ID,
  );

  assertEquals(result.ok, true);
  assertEquals(db.rpcCalls[0].name, "merge_access_prep_task");
  assertEquals(db.rpcCalls[0].args.p_task.task_key, "access-prep:booking-1");
  assertEquals(db.rpcCalls[0].args.p_source_event_id, SOURCE_EVENT_ID);
});

Deno.test("access prep requires a real source event id before calling RPC", async () => {
  const db = new MockSupabaseClient();
  const result = await handleAccessPrepTransition(db as any, {
    taskId: TASK_ID,
    housekeeperId: HOUSEKEEPER_ID,
    action: "mark_key_placed",
    sourceEventId: "not-a-uuid",
  });

  assertEquals(result.ok, false);
  assertEquals((result as any).error, "invalid_source_event_id");
  assertEquals(db.rpcCalls.length, 0);
});

Deno.test("access prep requires assignment and capability", async () => {
  const db = new MockSupabaseClient();
  db.rpcResults.push({
    data: {
      ok: false,
      error: "capability_denied",
      message: "Housekeeper lacks required Access Prep capability",
      required_capability: "can_place_key",
      taskId: TASK_ID,
    },
    error: null,
  });

  const result = await handleAccessPrepTransition(db as any, {
    taskId: TASK_ID,
    housekeeperId: HOUSEKEEPER_ID,
    action: "mark_key_placed",
    sourceEventId: SOURCE_EVENT_ID,
  });

  assertEquals(result, {
    ok: false,
    error: "capability_denied",
    message: "Housekeeper lacks required Access Prep capability",
    required_capability: "can_place_key",
    taskId: TASK_ID,
  });
  assertEquals(db.rpcCalls[0].name, "apply_access_prep_task_action");
});

Deno.test("access prep lifecycle supports sent, ack, progress, and done", async () => {
  const db = new MockSupabaseClient();
  db.rpcResults.push(
    { data: okResult("dispatch_task", "new", "sent"), error: null },
    { data: okResult("mark_no_ack", "sent", "no_ack"), error: null },
    { data: okResult("acknowledge_task", "no_ack", "acknowledged"), error: null },
    { data: okResult("start_task", "acknowledged", "in_progress"), error: null },
    { data: okResult("mark_key_placed", "in_progress", "in_progress"), error: null },
    { data: okResult("mark_room_open", "in_progress", "done"), error: null },
  );

  assertEquals(
    await handleAccessPrepTransition(db as any, {
      taskId: TASK_ID,
      housekeeperId: HOUSEKEEPER_ID,
      action: "dispatch_task",
      sourceEventId: "11111111-1111-4111-8111-111111111112",
    }),
    okResult("dispatch_task", "new", "sent"),
  );
  assertEquals(
    await handleAccessPrepTransition(db as any, {
      taskId: TASK_ID,
      housekeeperId: HOUSEKEEPER_ID,
      action: "mark_no_ack",
      sourceEventId: "11111111-1111-4111-8111-111111111113",
    }),
    okResult("mark_no_ack", "sent", "no_ack"),
  );
  assertEquals(
    await handleAccessPrepTransition(db as any, {
      taskId: TASK_ID,
      housekeeperId: HOUSEKEEPER_ID,
      action: "acknowledge_task",
      sourceEventId: "11111111-1111-4111-8111-111111111114",
    }),
    okResult("acknowledge_task", "no_ack", "acknowledged"),
  );
  assertEquals(
    await handleAccessPrepTransition(db as any, {
      taskId: TASK_ID,
      housekeeperId: HOUSEKEEPER_ID,
      action: "start_task",
      sourceEventId: "11111111-1111-4111-8111-111111111115",
    }),
    okResult("start_task", "acknowledged", "in_progress"),
  );
  assertEquals(
    await handleAccessPrepTransition(db as any, {
      taskId: TASK_ID,
      housekeeperId: HOUSEKEEPER_ID,
      action: "mark_key_placed",
      sourceEventId: "11111111-1111-4111-8111-111111111116",
    }),
    okResult("mark_key_placed", "in_progress", "in_progress"),
  );
  assertEquals(
    await handleAccessPrepTransition(db as any, {
      taskId: TASK_ID,
      housekeeperId: HOUSEKEEPER_ID,
      action: "mark_room_open",
      sourceEventId: "11111111-1111-4111-8111-111111111123",
    }),
    okResult("mark_room_open", "in_progress", "done"),
  );
});

Deno.test("access prep can recover from no-ack into acknowledged", async () => {
  const db = new MockSupabaseClient();
  db.rpcResults.push({
    data: okResult("acknowledge_task", "no_ack", "acknowledged"),
    error: null,
  });

  const result = await handleAccessPrepTransition(db as any, {
    taskId: TASK_ID,
    housekeeperId: HOUSEKEEPER_ID,
    action: "acknowledge_task",
    sourceEventId: SOURCE_EVENT_ID,
  });

  assertEquals(result, okResult("acknowledge_task", "no_ack", "acknowledged"));
});

Deno.test("access prep reports blocked task and allows restart after blocker cleared", async () => {
  const db = new MockSupabaseClient();
  db.rpcResults.push(
    {
      data: {
        ok: false,
        error: "task_blocked",
        message: "Task is blocked: missing key",
        taskId: TASK_ID,
      },
      error: null,
    },
    { data: okResult("start_task", "blocked", "in_progress"), error: null },
  );

  const blocked = await handleAccessPrepTransition(db as any, {
    taskId: TASK_ID,
    housekeeperId: HOUSEKEEPER_ID,
    action: "mark_room_open",
    sourceEventId: "11111111-1111-4111-8111-111111111117",
  });
  const restarted = await handleAccessPrepTransition(db as any, {
    taskId: TASK_ID,
    housekeeperId: HOUSEKEEPER_ID,
    action: "start_task",
    sourceEventId: "11111111-1111-4111-8111-111111111118",
  });

  assertEquals((blocked as any).error, "task_blocked");
  assertEquals(restarted, okResult("start_task", "blocked", "in_progress"));
});

Deno.test("access prep duplicate source event returns replayed result", async () => {
  const db = new MockSupabaseClient();
  db.rpcResults.push({
    data: {
      ...okResult("mark_key_placed", "in_progress", "in_progress"),
      replayed: true,
    },
    error: null,
  });

  const result = await handleAccessPrepTransition(db as any, {
    taskId: TASK_ID,
    housekeeperId: HOUSEKEEPER_ID,
    action: "mark_key_placed",
    sourceEventId: SOURCE_EVENT_ID,
  });

  assertEquals((result as any).replayed, true);
});

Deno.test("access prep supports cancellation and owner override outcomes", async () => {
  const db = new MockSupabaseClient();
  db.rpcResults.push(
    { data: okResult("cancel_task", "sent", "canceled"), error: null },
    {
      data: {
        ok: true,
        action: "owner_override",
        taskId: TASK_ID,
        previousState: "blocked",
        newState: "done",
        blockerPreserved: "owner will place key",
      },
      error: null,
    },
  );

  const canceled = await handleAccessPrepTransition(db as any, {
    taskId: TASK_ID,
    housekeeperId: HOUSEKEEPER_ID,
    action: "cancel_task",
    sourceEventId: "11111111-1111-4111-8111-111111111119",
  });
  const override = await overrideHousekeepingTask(db as any, {
    taskKind: "access_prep",
    taskId: TASK_ID,
    adminUserId: "66666666-6666-4666-8666-666666666666",
    reason: "owner will place key",
    sourceEventId: "11111111-1111-4111-8111-111111111120",
  });

  assertEquals(canceled, okResult("cancel_task", "sent", "canceled"));
  assertEquals((override as any).blockerPreserved, "owner will place key");
  assertEquals(db.rpcCalls[1].name, "override_housekeeping_task");
  assertEquals(db.rpcCalls[1].args.p_task_kind, "access_prep");
});

Deno.test("access prep reports assignment mismatch and missing open-room capability", async () => {
  const db = new MockSupabaseClient();
  db.rpcResults.push(
    {
      data: {
        ok: false,
        error: "unauthorized",
        message: "Housekeeper is not assigned to this Access Prep task",
        taskId: TASK_ID,
      },
      error: null,
    },
    {
      data: {
        ok: false,
        error: "capability_denied",
        message: "Housekeeper lacks required Access Prep capability",
        required_capability: "can_open_room",
        taskId: TASK_ID,
      },
      error: null,
    },
  );

  const unauthorized = await handleAccessPrepTransition(db as any, {
    taskId: TASK_ID,
    housekeeperId: HOUSEKEEPER_ID,
    action: "acknowledge_task",
    sourceEventId: "11111111-1111-4111-8111-111111111121",
  });
  const missingOpenCapability = await handleAccessPrepTransition(db as any, {
    taskId: TASK_ID,
    housekeeperId: HOUSEKEEPER_ID,
    action: "mark_room_open",
    sourceEventId: "11111111-1111-4111-8111-111111111122",
  });

  assertEquals((unauthorized as any).error, "unauthorized");
  assertEquals((missingOpenCapability as any).required_capability, "can_open_room");
});

Deno.test("access prep adapter reports database failures truthfully", async () => {
  const db = new MockSupabaseClient();
  db.rpcResults.push({ data: null, error: { message: "write failed" } });

  const result = await handleAccessPrepTransition(db as any, {
    taskId: TASK_ID,
    housekeeperId: HOUSEKEEPER_ID,
    action: "mark_key_placed",
    sourceEventId: SOURCE_EVENT_ID,
  });

  assertEquals(result.ok, false);
  assertEquals((result as any).error, "database_error");
  assertEquals((result as any).taskId, TASK_ID);
});
