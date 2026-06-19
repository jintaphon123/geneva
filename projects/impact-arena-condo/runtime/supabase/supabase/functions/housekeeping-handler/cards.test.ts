import {
  assert,
  assertEquals,
  assertMatch,
} from "https://deno.land/std@0.208.0/assert/mod.ts";
import {
  buildProblemMenuFlexMessage,
  buildQueueFlexMessage,
  buildTaskDetailFlexMessage,
  type LineFlexMessage,
} from "./cards.ts";

const SECRET = "phase6-card-secret";
const CLEANING_ID = "11111111-1111-4111-8111-111111111111";
const ACCESS_ID = "22222222-2222-4222-8222-222222222222";

function collectText(value: unknown): string[] {
  if (!value || typeof value !== "object") return [];
  if (Array.isArray(value)) return value.flatMap(collectText);
  const record = value as Record<string, unknown>;
  const own = typeof record.text === "string" ? [record.text] : [];
  return own.concat(
    Object.entries(record)
      .filter(([key]) => key !== "data")
      .flatMap(([, child]) => collectText(child)),
  );
}

function collectActions(value: unknown): Record<string, unknown>[] {
  if (!value || typeof value !== "object") return [];
  if (Array.isArray(value)) return value.flatMap(collectActions);
  const record = value as Record<string, unknown>;
  const own = record.type === "postback" ? [record] : [];
  return own.concat(Object.values(record).flatMap(collectActions));
}

function carouselBubbles(message: LineFlexMessage): any[] {
  const contents = message.contents as { contents: any[] };
  return contents.contents;
}

function queueInput() {
  return {
    view: "today" as const,
    items: [
      {
        task_id: CLEANING_ID,
        task_kind: "cleaning" as const,
        room_code: "C8/13/15",
        guest_name: "Somchai Verylong Private Guest Name",
        guest_phone: "+66812345678",
        reservation_number: "RSV-SECRET-999999",
        check_in_date: "2026-06-20",
        priority: "urgent" as const,
        status: "waiting_ack",
        due_at: "2026-06-19T11:00:00.000Z",
        owner_label: "Admin Bow",
        missing_items: ["water"],
        linked_task_kind: "access_prep" as const,
        linked_task_status: "pending_dispatch",
        has_open_blocker: true,
        claimable: true,
      },
      {
        task_id: ACCESS_ID,
        task_kind: "access_prep" as const,
        room_code: "C8/13/15",
        guest_name: "Somchai Verylong Private Guest Name",
        check_in_date: "2026-06-20",
        priority: "normal" as const,
        status: "acknowledged",
        scheduled_for: "2026-06-19T18:00:00.000Z",
        linked_task_kind: "cleaning" as const,
        linked_task_status: "waiting_ack",
        has_open_blocker: false,
        claimable: false,
      },
    ],
    next_cursor: { direction: "next", sortKey: "cursor-next" },
    previous_cursor: { direction: "previous", sortKey: "cursor-prev" },
  };
}

Deno.test("Task 6 cards - queue flex renders bounded private task carousel with signed actions", async () => {
  const message = await buildQueueFlexMessage(queueInput(), SECRET);

  assertEquals(message.type, "flex");
  assertEquals(message.altText, "คิวงานแม่บ้าน 2 งาน");
  assertEquals(message.contents.type, "carousel");
  assert(carouselBubbles(message).length <= 5);

  const firstBubble = carouselBubbles(message)[0];
  const firstTexts = collectText(firstBubble);
  assertEquals(firstTexts[0], "C8/13/15");
  assertEquals(firstTexts[1], "ทำความสะอาด");
  assert(firstTexts.includes("เร่งด่วน"));
  assert(firstTexts.includes("Access Prep: pending_dispatch"));
  assert(firstTexts.includes("ขาด: water"));

  const rendered = firstTexts.join("\n");
  assert(rendered.includes("Somchai"));
  assertEquals(rendered.includes("Verylong Private Guest Name"), false);
  assertEquals(rendered.includes("+66812345678"), false);
  assertEquals(rendered.includes("RSV-SECRET-999999"), false);
  assertEquals(rendered.includes(CLEANING_ID), false);

  const actions = collectActions(message);
  const mutationActions = actions.filter((action) =>
    String(action.data ?? "").includes("task_id=")
  );
  assert(mutationActions.length > 0);
  for (const action of mutationActions) {
    assertMatch(String(action.data), /sig=[A-Za-z0-9_-]+/);
  }

  const cursorActions = actions.filter((action) =>
    String(action.data ?? "").includes("cursor=")
  );
  assertEquals(cursorActions.length, 2);
  for (const action of cursorActions) {
    assertMatch(String(action.data), /^action=show_(?:today|queue)&cursor=/);
    assertMatch(String(action.data), /sig=[A-Za-z0-9_-]+/);
  }

  const dominantButtons = carouselBubbles(message).map((bubble: any) =>
    bubble.footer.contents.filter((item: any) =>
      item.type === "button" && item.style === "primary"
    ).length
  );
  assertEquals(dominantButtons, [1, 1]);

  const colors = JSON.stringify(message);
  assert(colors.includes("#D92D20"));
  assert(colors.includes("#F79009"));
  assert(colors.includes("#12B76A"));
  assert(colors.includes("#667085"));
});

Deno.test("Task 6 cards - task detail separates Cleaning and Access Prep dependencies", async () => {
  const message = await buildTaskDetailFlexMessage({
    task_id: CLEANING_ID,
    task_kind: "cleaning",
    room_code: "C8/13/15",
    guest_name: "Somchai Verylong Private Guest Name",
    priority: "high",
    status: "in_progress",
    check_in_date: "2026-06-20",
    instructions: "เติมน้ำ 4 ขวด",
    missing_items: ["soap", "towels"],
    linked_task_kind: "access_prep",
    linked_task_status: "sent",
  }, SECRET);

  const text = collectText(message).join("\n");
  assert(text.includes("C8/13/15"));
  assert(text.includes("ทำความสะอาด"));
  assert(text.includes("Cleaning: in_progress"));
  assert(text.includes("Access Prep: sent"));
  assert(text.includes("เติมน้ำ 4 ขวด"));
  assertEquals(text.includes(CLEANING_ID), false);
});

Deno.test("Task 6 cards - problem menu uses fixed categories and signed postbacks", async () => {
  const message = await buildProblemMenuFlexMessage({
    task_id: CLEANING_ID,
    task_kind: "cleaning",
    room_code: "C8/13/15",
    status: "in_progress",
  }, SECRET);

  const labels = collectActions(message).map((action) => action.label);
  assertEquals(labels, [
    "ไม่ได้ใส่น้ำ",
    "ไม่ได้ใส่สบู่",
    "ไม่ได้ใส่ผ้าขนหนู",
    "ของเสีย/ของหาย",
    "อื่นๆ",
  ]);
  for (const action of collectActions(message)) {
    assertMatch(String(action.data), /action=problem_category/);
    assertMatch(
      String(action.data),
      /task_id=11111111-1111-4111-8111-111111111111/,
    );
    assertMatch(String(action.data), /sig=[A-Za-z0-9_-]+/);
  }
});

Deno.test("Task 6 cards - queue renderer caps carousel at five bubbles", async () => {
  const page = queueInput();
  page.items = Array.from({ length: 7 }, (_, index) => ({
    ...page.items[0],
    task_id: `${index + 1}1111111-1111-4111-8111-111111111111`,
    room_code: `C8/${index + 1}`,
  }));

  const message = await buildQueueFlexMessage(page, SECRET);

  assertEquals(carouselBubbles(message).length, 5);
});

// Keeps the public contract obvious for Task 7 workflow wiring.
function assertFlexMessageShape(_message: LineFlexMessage) {}
