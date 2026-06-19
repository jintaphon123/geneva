import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { buildProblemMenuFlexMessage } from "../runtime/supabase/supabase/functions/housekeeping-handler/cards.ts";
import { parseCommand } from "../runtime/supabase/supabase/functions/housekeeping-handler/commands.ts";
import { createHousekeepingHandler } from "../runtime/supabase/supabase/functions/housekeeping-handler/index.ts";

const WEBHOOK_SECRET = "test-webhook-secret-999";
const SOURCE_EVENT_ID = "33333333-3333-4333-8333-333333333333";
const TASK_ID = "77777777-7777-4777-8777-777777777777";

type QueryResult = { data: any; error: any };

class MockQueryBuilder {
  data: any = null;
  error: any = null;

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

  then(resolve: (value: QueryResult) => unknown) {
    return Promise.resolve({ data: this.data, error: this.error }).then(
      resolve,
    );
  }
}

class MockSupabaseClient {
  results: Record<string, QueryResult> = {};
  rpcCalls: Array<{ name: string; args: any }> = [];

  from(table: string) {
    return new MockQueryBuilder(this, table);
  }

  rpc(name: string, args: any): Promise<QueryResult> {
    this.rpcCalls.push({ name, args });
    return Promise.resolve(
      this.results[`rpc:${name}`] || { data: { ok: true }, error: null },
    );
  }
}

function activeFixture(db: MockSupabaseClient) {
  db.results["housekeepers:line_user_id:U_problem_test"] = {
    data: {
      id: "hk-problem-1",
      status: "active",
      active: true,
      display_name: "Mali",
    },
    error: null,
  };
  db.results[`cleaning_tasks:id:${TASK_ID}`] = {
    data: {
      id: TASK_ID,
      room_id: "room-problem-1",
      booking_id: "booking-problem-1",
      status: "in_progress",
      assigned_housekeeper_id: "hk-problem-1",
    },
    error: null,
  };
  db.results["rooms:id:room-problem-1"] = {
    data: { room_code: "C5/12/59" },
    error: null,
  };
  db.results[`cleaning_task_checklist_items:cleaning_task_id:${TASK_ID}`] = {
    data: [
      { item_key: "water", item_label: "น้ำ", status: "missing" },
      { item_key: "soap", item_label: "สบู่", status: "present" },
    ],
    error: null,
  };
}

function handlerWith(db: MockSupabaseClient, transition: any) {
  return createHousekeepingHandler({
    getEnv: (key) => key === "N8N_WEBHOOK_SECRET" ? WEBHOOK_SECRET : undefined,
    createSupabase: () => db,
    transition,
  });
}

function request(text: string, extra: Record<string, unknown> = {}) {
  return new Request("http://localhost/functions/v1/housekeeping-handler", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-impact-webhook-secret": WEBHOOK_SECRET,
    },
    body: JSON.stringify({
      line_user_id: "U_problem_test",
      text,
      source_event_id: SOURCE_EVENT_ID,
      display_name: "Mali",
      ...extra,
    }),
  });
}

async function problemPostback(category: string) {
  const message = await buildProblemMenuFlexMessage({
    task_id: TASK_ID,
    task_kind: "cleaning",
    room_code: "C5/12/59",
    status: "in_progress",
  }, WEBHOOK_SECRET);
  const contents: any[] = ((message.contents as any).footer.contents) ?? [];
  const button = contents.find((item) =>
    String(item.action?.data ?? "").includes(`category=${category}`)
  );
  return String(button.action.data);
}

Deno.test("Task 9 - parse problem category postback with task id", async () => {
  const data = await problemPostback("water");
  assertEquals(parseCommand(data), {
    action: "problem_category",
    category: "water",
  });
});

Deno.test("Task 9 - water category marks checklist missing and reports Internal Ops plus owner incident", async () => {
  const db = new MockSupabaseClient();
  activeFixture(db);
  const transitionCalls: any[] = [];
  const handler = handlerWith(
    db,
    (
      _supabase: any,
      _lineUserId: string,
      intent: any,
      sourceEventId: string,
      overrideTaskId: string | null,
    ) => {
      transitionCalls.push({ intent, sourceEventId, overrideTaskId });
      return Promise.resolve({
        ok: true,
        action: "mark_item_missing",
        taskId: TASK_ID,
        previousState: "in_progress",
        newState: "blocked",
      });
    },
  );

  const res = await handler(request(await problemPostback("water")));
  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, true);
  assertEquals(body.action, "problem_category");
  assertEquals(transitionCalls[0].intent, {
    action: "mark_item_missing",
    item: "water",
  });
  assertEquals(transitionCalls[0].overrideTaskId, TASK_ID);
  assertEquals(db.rpcCalls[0].name, "report_operational_incident");
  assertEquals(db.rpcCalls[0].args.p_incident.issue_subtype, "missing_water");
  assertEquals(db.rpcCalls[0].args.p_incident.requires_internal_ops, true);
  assertEquals(db.rpcCalls[0].args.p_incident.requires_owner, true);
  assertEquals(body.internal_notification.text.includes("ไม่ได้ใส่น้ำ"), true);
});

Deno.test("Task 9 - damaged/lost prompts for detail and stores optional media evidence without state mutation", async () => {
  const db = new MockSupabaseClient();
  activeFixture(db);
  let transitionCalls = 0;
  const handler = handlerWith(db, () => {
    transitionCalls += 1;
    throw new Error(
      "damaged_or_lost without detail must not mutate task state",
    );
  });

  const res = await handler(request(await problemPostback("damaged_or_lost"), {
    message_type: "image",
    message_id: "line-image-1",
    media: { line_content_id: "content-123" },
  }));
  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(body.ok, true);
  assertEquals(body.action, "problem_category");
  assertEquals(transitionCalls, 0);
  assertEquals(db.rpcCalls[0].name, "report_operational_incident");
  assertEquals(db.rpcCalls[0].args.p_incident.issue_subtype, "damaged_or_lost");
  assertEquals(
    db.rpcCalls[0].args.p_incident.metadata.media.line_content_id,
    "content-123",
  );
  assertEquals(body.housekeeping_reply.text.includes("ส่งรายละเอียด"), true);
});

Deno.test("Task 9 - other category needs classification and cannot mutate from AI-like summary", async () => {
  const db = new MockSupabaseClient();
  activeFixture(db);
  let transitionCalls = 0;
  const handler = handlerWith(db, () => {
    transitionCalls += 1;
    throw new Error(
      "other category must not mutate task state without classification",
    );
  });

  const res = await handler(request(await problemPostback("other"), {
    ai_summary: "เติมน้ำแล้ว",
  }));
  assertEquals(res.status, 200);
  const body = await res.json();
  assertEquals(transitionCalls, 0);
  assertEquals(db.rpcCalls[0].args.p_incident.issue_subtype, "other");
  assertEquals(
    db.rpcCalls[0].args.p_incident.metadata.needs_classification,
    true,
  );
});
