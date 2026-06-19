import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { createOrMergeCleaningTask, handleStateTransition } from "./state.ts";

const SOURCE_EVENT_ID = "11111111-1111-4111-8111-111111111111";

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
    const key = `${this.table}:${column}:${value}`;
    const result = this.client.results[key];
    if (result) {
      this.data = result.data;
      this.error = result.error;
    }
    return this;
  }

  not() {
    return this;
  }

  gte() {
    return this;
  }

  order() {
    return this;
  }

  limit() {
    return this;
  }

  maybeSingle(): Promise<QueryResult> {
    return Promise.resolve({ data: this.data, error: this.error });
  }

  upsert(payload: any): Promise<QueryResult> {
    this.client.writes.push({ table: this.table, payload });
    const result = this.client.results[`${this.table}:upsert`];
    return Promise.resolve(result || { data: payload, error: null });
  }

  then(resolve: (value: QueryResult) => unknown) {
    const data = Array.isArray(this.data)
      ? this.data
      : (this.data ? [this.data] : []);
    return Promise.resolve({ data, error: this.error }).then(resolve);
  }
}

class MockSupabaseClient {
  results: Record<string, QueryResult> = {};
  writes: Array<{ table: string; payload: any }> = [];
  rpcCalls: Array<{ name: string; args: any }> = [];
  rpcResult: QueryResult = { data: null, error: null };

  from(table: string) {
    return new MockQueryBuilder(this, table);
  }

  rpc(name: string, args: any): Promise<QueryResult> {
    this.rpcCalls.push({ name, args });
    return Promise.resolve(this.rpcResult);
  }
}

function activeHousekeeper(db: MockSupabaseClient) {
  db.results["housekeepers:line_user_id:U123"] = {
    data: { id: "hk-1", status: "active", active: true },
    error: null,
  };
}

function noReplay(db: MockSupabaseClient) {
  db.results[`cleaning_task_events:source_event_id:${SOURCE_EVENT_ID}`] = {
    data: null,
    error: null,
  };
}

function focusedTask(
  db: MockSupabaseClient,
  task: Record<string, unknown> = {
    id: "task-1",
    status: "waiting_ack",
    assigned_housekeeper_id: "hk-1",
  },
) {
  db.results["housekeeper_task_focus:housekeeper_id:hk-1"] = {
    data: {
      focus_type: "cleaning",
      focused_cleaning_task_id: "task-1",
    },
    error: null,
  };
  db.results["cleaning_tasks:id:task-1"] = { data: task, error: null };
}

Deno.test("Task 4 - requires a real webhook source event id", async () => {
  const result = await handleStateTransition(
    new MockSupabaseClient() as any,
    "U123",
    { action: "acknowledge_task" },
  );
  assertEquals(result.ok, false);
  assertEquals((result as any).error, "invalid_source_event_id");
});

Deno.test("Task 4 - rejects missing or inactive housekeeper", async () => {
  const db = new MockSupabaseClient();
  const result = await handleStateTransition(
    db as any,
    "U_unknown",
    { action: "acknowledge_task" },
    SOURCE_EVENT_ID,
  );
  assertEquals(result.ok, false);
  assertEquals((result as any).error, "housekeeper_not_found");
});

Deno.test("Task 4 - replays the stored outcome before resolving current focus", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  db.results[`cleaning_task_events:source_event_id:${SOURCE_EVENT_ID}`] = {
    data: {
      cleaning_task_id: "original-task",
      previous_state: "waiting_ack",
      new_state: "acknowledged",
      payload: {
        result: {
          ok: true,
          action: "acknowledge_task",
          taskId: "original-task",
          previousState: "waiting_ack",
          newState: "acknowledged",
        },
      },
    },
    error: null,
  };

  const result = await handleStateTransition(
    db as any,
    "U123",
    { action: "acknowledge_task" },
    SOURCE_EVENT_ID,
  );

  assertEquals(result.ok, true);
  assertEquals((result as any).taskId, "original-task");
  assertEquals((result as any).replayed, true);
  assertEquals(db.rpcCalls.length, 0);
});

Deno.test("Task 4 - keeps a valid owned nonterminal focus", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  noReplay(db);
  focusedTask(db);
  db.rpcResult = {
    data: {
      ok: true,
      action: "acknowledge_task",
      taskId: "task-1",
      previousState: "waiting_ack",
      newState: "acknowledged",
    },
    error: null,
  };

  const result = await handleStateTransition(
    db as any,
    "U123",
    { action: "acknowledge_task" },
    SOURCE_EVENT_ID,
  );

  assertEquals(result.ok, true);
  assertEquals(db.rpcCalls[0].name, "apply_housekeeping_task_action");
  assertEquals(db.rpcCalls[0].args.p_task_id, "task-1");
});

Deno.test("Task 4 - ignores stale foreign focus and auto-focuses the only assigned task", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  noReplay(db);
  focusedTask(db, {
    id: "task-1",
    status: "in_progress",
    assigned_housekeeper_id: "another-housekeeper",
  });
  db.results["cleaning_tasks:assigned_housekeeper_id:hk-1"] = {
    data: [{ id: "task-2", status: "waiting_ack" }],
    error: null,
  };
  db.rpcResult = {
    data: {
      ok: true,
      action: "acknowledge_task",
      taskId: "task-2",
      previousState: "waiting_ack",
      newState: "acknowledged",
    },
    error: null,
  };

  const result = await handleStateTransition(
    db as any,
    "U123",
    { action: "acknowledge_task" },
    SOURCE_EVENT_ID,
  );

  assertEquals(result.ok, true);
  assertEquals(db.rpcCalls[0].args.p_task_id, "task-2");
  assertEquals(db.writes[0].payload.focused_field_assistance_task_id, null);
});

Deno.test("Task 4 - fails closed when multiple tasks are plausible", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  noReplay(db);
  db.results["housekeeper_task_focus:housekeeper_id:hk-1"] = {
    data: null,
    error: null,
  };
  db.results["cleaning_tasks:assigned_housekeeper_id:hk-1"] = {
    data: [
      { id: "task-1", status: "waiting_ack" },
      { id: "task-2", status: "in_progress" },
    ],
    error: null,
  };

  const result = await handleStateTransition(
    db as any,
    "U123",
    { action: "acknowledge_task" },
    SOURCE_EVENT_ID,
  );
  assertEquals(result.ok, false);
  assertEquals((result as any).error, "ambiguous_target");
  assertEquals(db.rpcCalls.length, 0);
});

Deno.test("Task 14 - cleaning completion does not complete access prep", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  noReplay(db);
  focusedTask(db, {
    id: "task-1",
    status: "in_progress",
    assigned_housekeeper_id: "hk-1",
  });
  db.rpcResult = {
    data: {
      ok: true,
      action: "complete_cleaning",
      taskId: "task-1",
      previousState: "in_progress",
      newState: "completed",
    },
    error: null,
  };

  const result = await handleStateTransition(
    db as any,
    "U123",
    { action: "complete_cleaning" },
    SOURCE_EVENT_ID,
  );

  assertEquals(result.ok, true);
  assertEquals(db.rpcCalls[0].name, "apply_housekeeping_task_action");
  assertEquals(db.rpcCalls[0].args.p_action, "complete_cleaning");
});

Deno.test("Task 14 - access prep commands are not resolved through cleaning state", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  noReplay(db);
  db.results["housekeeper_task_focus:housekeeper_id:hk-1"] = {
    data: {
      focus_type: null,
      focused_cleaning_task_id: null,
      focused_access_prep_task_id: null,
    },
    error: null,
  };

  const result = await handleStateTransition(
    db as any,
    "U123",
    { action: "mark_room_open" },
    SOURCE_EVENT_ID,
  );

  assertEquals(result.ok, false);
  assertEquals((result as any).error, "access_prep_required");
  assertEquals(db.rpcCalls.length, 0);
});

Deno.test("Task 14 - legacy cleaning focus preserves access capability denial without mutation", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  noReplay(db);
  focusedTask(db, {
    id: "task-1",
    status: "in_progress",
    assigned_housekeeper_id: "hk-1",
    capabilities: {
      can_place_key: false,
      can_open_room: false,
    },
  });

  const result = await handleStateTransition(
    db as any,
    "U123",
    { action: "mark_key_placed" },
    SOURCE_EVENT_ID,
  );

  assertEquals(result.ok, false);
  assertEquals((result as any).error, "capability_denied");
  assertEquals((result as any).required_capability, "can_place_key");
  assertEquals((result as any).taskId, "task-1");
  assertEquals(db.rpcCalls.length, 0);
});

Deno.test("Task 4 - sends bounded intent data to the transactional RPC", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  noReplay(db);
  focusedTask(db, {
    id: "task-1",
    status: "in_progress",
    assigned_housekeeper_id: "hk-1",
  });
  db.rpcResult = {
    data: {
      ok: true,
      action: "mark_item_missing",
      taskId: "task-1",
      previousState: "in_progress",
      newState: "in_progress",
    },
    error: null,
  };

  await handleStateTransition(
    db as any,
    "U123",
    { action: "mark_item_missing", item: "water" },
    SOURCE_EVENT_ID,
  );

  assertEquals(db.rpcCalls[0].args.p_payload, {
    action: "mark_item_missing",
    item: "water",
  });
});

Deno.test("Task 4 - reports database failure instead of claiming success", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  noReplay(db);
  focusedTask(db);
  db.rpcResult = { data: null, error: { message: "database write failed" } };

  const result = await handleStateTransition(
    db as any,
    "U123",
    { action: "acknowledge_task" },
    SOURCE_EVENT_ID,
  );
  assertEquals(result.ok, false);
  assertEquals((result as any).error, "database_error");
});

Deno.test("Task 4 - preserves a replayed rejection", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  db.results[`cleaning_task_events:source_event_id:${SOURCE_EVENT_ID}`] = {
    data: {
      cleaning_task_id: "task-1",
      previous_state: "waiting_ack",
      new_state: "waiting_ack",
      payload: {
        result: {
          ok: false,
          error: "invalid_transition",
          message: "Cannot start task in status waiting_ack",
          taskId: "task-1",
        },
      },
    },
    error: null,
  };

  const result = await handleStateTransition(
    db as any,
    "U123",
    { action: "start_task" },
    SOURCE_EVENT_ID,
  );
  assertEquals(result.ok, false);
  assertEquals((result as any).error, "invalid_transition");
});

Deno.test("Task 4 - delegates task-key creation and merge to one transactional RPC", async () => {
  const db = new MockSupabaseClient();
  db.rpcResult = {
    data: {
      ok: true,
      taskId: "task-1",
      taskKey: "turnover:room-1:booking-1",
      created: false,
      merged: true,
      status: "waiting_ack",
    },
    error: null,
  };

  const result = await createOrMergeCleaningTask(
    db as any,
    {
      task_key: "turnover:room-1:booking-1",
      room_id: "22222222-2222-4222-8222-222222222222",
      priority: "urgent",
      source: "internal_ops",
    },
    SOURCE_EVENT_ID,
  );

  assertEquals(result.ok, true);
  assertEquals((result as any).merged, true);
  assertEquals(db.rpcCalls[0].name, "merge_housekeeping_cleaning_task");
  assertEquals(
    db.rpcCalls[0].args.p_task.task_key,
    "turnover:room-1:booking-1",
  );
});

Deno.test("Task 4 - task merge reports database failures truthfully", async () => {
  const db = new MockSupabaseClient();
  db.rpcResult = { data: null, error: { message: "merge failed" } };
  const result = await createOrMergeCleaningTask(
    db as any,
    {
      task_key: "turnover:room-1:booking-1",
      room_id: "22222222-2222-4222-8222-222222222222",
    },
    SOURCE_EVENT_ID,
  );
  assertEquals(result.ok, false);
  assertEquals((result as any).error, "database_error");
});

Deno.test("Task 10 - handleStateTransition overrides focus using valid overrideTaskId", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  noReplay(db);

  const taskId = "99999999-9999-4999-b999-999999999999";
  db.results[`cleaning_tasks:id:${taskId}`] = {
    data: {
      id: taskId,
      status: "waiting_ack",
      assigned_housekeeper_id: "hk-1",
    },
    error: null,
  };
  db.results[`housekeeper_task_focus:insert`] = {
    data: { id: "focus-id" },
    error: null,
  };
  db.rpcResult = {
    data: {
      ok: true,
      action: "acknowledge_task",
      taskId: taskId,
      previousState: "waiting_ack",
      newState: "acknowledged",
    },
    error: null,
  };

  const result = await handleStateTransition(
    db as any,
    "U123",
    { action: "acknowledge_task" },
    SOURCE_EVENT_ID,
    taskId,
  );

  assertEquals(result.ok, true);
  assertEquals(db.rpcCalls[0].name, "apply_housekeeping_task_action");
  assertEquals(db.rpcCalls[0].args.p_task_id, taskId);
  const focusWrite = db.writes.find((w) => w.table === "housekeeper_task_focus");
  assertEquals(focusWrite?.payload.focused_cleaning_task_id, taskId);
});

Deno.test("Task 10 - handleStateTransition rejects overrideTaskId if housekeeper is unauthorized", async () => {
  const db = new MockSupabaseClient();
  activeHousekeeper(db);
  noReplay(db);

  const taskId = "99999999-9999-4999-b999-999999999999";
  db.results[`cleaning_tasks:id:${taskId}`] = {
    data: {
      id: taskId,
      status: "waiting_ack",
      assigned_housekeeper_id: "another-housekeeper-id",
    },
    error: null,
  };

  const result = await handleStateTransition(
    db as any,
    "U123",
    { action: "acknowledge_task" },
    SOURCE_EVENT_ID,
    taskId,
  );

  assertEquals(result.ok, false);
  assertEquals((result as any).error, "unauthorized");
  assertEquals(db.rpcCalls.length, 0);
});
