import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import {
  loadHousekeepingQueue,
  orderQueue,
  paginateQueue,
  selectNextEligibleTask,
  todayTasks,
  type QueueTask,
} from "./queue.ts";

const BANGKOK_NOW = new Date("2026-06-19T10:00:00+07:00");

function fixture(overrides: Partial<QueueTask> = {}): QueueTask {
  return {
    id: "task-default",
    taskKind: "cleaning",
    assignedHousekeeperId: "hk-1",
    status: "waiting_ack",
    priority: "normal",
    dueAt: "2026-06-20T05:00:00.000Z",
    checkInDate: "2026-06-21",
    scheduledFor: null,
    adminPriorityRank: 0,
    hasOpenBlocker: false,
    building: "C9",
    floor: 9,
    ...overrides,
  };
}

Deno.test("direct admin work outranks automatic work", () => {
  const ordered = orderQueue([
    fixture({
      id: "auto-checkin",
      checkInDate: "2026-06-19",
      adminPriorityRank: 0,
    }),
    fixture({
      id: "direct",
      checkInDate: "2026-06-21",
      adminPriorityRank: 100,
    }),
  ], BANGKOK_NOW);

  assertEquals(ordered.map((task) => task.id), ["direct", "auto-checkin"]);
});

Deno.test("queue order follows the locked six-level policy", () => {
  const ordered = orderQueue([
    fixture({
      id: "earliest-due",
      dueAt: "2026-06-19T04:00:00.000Z",
      building: "C9",
      floor: 1,
    }),
    fixture({
      id: "same-building",
      dueAt: "2026-06-19T08:00:00.000Z",
      building: "C5",
      floor: 12,
    }),
    fixture({
      id: "open-blocker",
      hasOpenBlocker: true,
      building: "C9",
    }),
    fixture({
      id: "access-near-checkin",
      taskKind: "access_prep",
      checkInDate: "2026-06-20",
      scheduledFor: "2026-06-19T11:00:00.000Z",
    }),
    fixture({
      id: "checkin-today",
      checkInDate: "2026-06-19",
    }),
    fixture({
      id: "admin-direct",
      adminPriorityRank: 100,
    }),
  ], BANGKOK_NOW);

  assertEquals(ordered.map((task) => task.id), [
    "admin-direct",
    "checkin-today",
    "access-near-checkin",
    "open-blocker",
    "same-building",
    "earliest-due",
  ]);
});

Deno.test("one queue contains both task kinds and preserves explicit kind", () => {
  const ordered = orderQueue([
    fixture({ id: "cleaning", taskKind: "cleaning" }),
    fixture({ id: "access", taskKind: "access_prep" }),
  ], BANGKOK_NOW);

  assertEquals(ordered.map((task) => [task.id, task.taskKind]), [
    ["access", "access_prep"],
    ["cleaning", "cleaning"],
  ]);
});

Deno.test("task kind is the stable tie-breaker before task id", () => {
  const ordered = orderQueue([
    fixture({ id: "a-cleaning", taskKind: "cleaning" }),
    fixture({ id: "z-access", taskKind: "access_prep" }),
  ], BANGKOK_NOW);

  assertEquals(ordered.map((task) => task.id), ["z-access", "a-cleaning"]);
});

Deno.test("terminal tasks are excluded from the queue", () => {
  const ordered = orderQueue([
    fixture({ id: "cleaning-open", status: "waiting_ack" }),
    fixture({ id: "cleaning-done", status: "completed" }),
    fixture({ id: "access-open", taskKind: "access_prep", status: "sent" }),
    fixture({ id: "access-done", taskKind: "access_prep", status: "done" }),
    fixture({ id: "canceled", status: "canceled" }),
    fixture({ id: "failed", status: "delivery_failed" }),
  ], BANGKOK_NOW);

  assertEquals(ordered.map((task) => task.id), [
    "access-open",
    "cleaning-open",
  ]);
});

Deno.test("today view filters current operator and Bangkok due date", () => {
  const tasks = [
    fixture({
      id: "cleaning-today",
      dueAt: "2026-06-19T16:59:00.000Z",
    }),
    fixture({
      id: "access-today",
      taskKind: "access_prep",
      dueAt: "2026-06-18T17:01:00.000Z",
    }),
    fixture({
      id: "other-operator",
      assignedHousekeeperId: "hk-2",
      dueAt: "2026-06-19T04:00:00.000Z",
    }),
    fixture({
      id: "tomorrow-bangkok",
      dueAt: "2026-06-19T17:01:00.000Z",
    }),
  ];

  assertEquals(
    todayTasks(tasks, "hk-1", BANGKOK_NOW).map((task) => task.id),
    ["access-today", "cleaning-today"],
  );
});

Deno.test("pagination uses five items and stable next and previous cursors", () => {
  const tasks = Array.from({ length: 12 }, (_, index) =>
    fixture({
      id: `task-${String(index + 1).padStart(2, "0")}`,
      dueAt: new Date(
        Date.parse("2026-06-19T01:00:00.000Z") + index * 60_000,
      ).toISOString(),
    })
  );

  const first = paginateQueue(tasks, null, 5, BANGKOK_NOW);
  const second = paginateQueue(tasks, first.nextCursor, 5, BANGKOK_NOW);
  const back = paginateQueue(tasks, second.previousCursor, 5, BANGKOK_NOW);

  assertEquals(first.items.map((task) => task.id), [
    "task-01",
    "task-02",
    "task-03",
    "task-04",
    "task-05",
  ]);
  assertEquals(second.items.map((task) => task.id), [
    "task-06",
    "task-07",
    "task-08",
    "task-09",
    "task-10",
  ]);
  assertEquals(back.items.map((task) => task.id), first.items.map((task) => task.id));
  assertEquals(first.previousCursor, null);
  assertEquals(second.nextCursor?.direction, "next");
  assertEquals(second.previousCursor?.direction, "previous");
});

Deno.test("accept next chooses the highest-priority eligible unacknowledged task", () => {
  const chosen = selectNextEligibleTask([
    fixture({
      id: "already-started",
      adminPriorityRank: 100,
      status: "in_progress",
    }),
    fixture({
      id: "auto-checkin",
      checkInDate: "2026-06-19",
      status: "waiting_ack",
    }),
    fixture({
      id: "admin-direct",
      adminPriorityRank: 100,
      status: "sent",
    }),
  ], "hk-1", BANGKOK_NOW);

  assertEquals(chosen?.id, "admin-direct");
});

Deno.test("tasks assigned to another operator are not claimable", () => {
  const chosen = selectNextEligibleTask([
    fixture({
      id: "other-admin-direct",
      assignedHousekeeperId: "hk-2",
      adminPriorityRank: 100,
      status: "sent",
    }),
    fixture({
      id: "own-task",
      assignedHousekeeperId: "hk-1",
      status: "waiting_ack",
    }),
  ], "hk-1", BANGKOK_NOW);

  assertEquals(chosen?.id, "own-task");
});

Deno.test("loadHousekeepingQueue sends bounded RPC arguments", async () => {
  const calls: Array<{ name: string; args: unknown }> = [];
  const db = {
    rpc(name: string, args: unknown) {
      calls.push({ name, args });
      return Promise.resolve({
        data: { items: [], next_cursor: null, previous_cursor: null },
        error: null,
      });
    },
  };

  const result = await loadHousekeepingQueue(
    db as any,
    "hk-1",
    "today",
    { direction: "next", sortKey: ["cursor"] },
    5,
  );

  assertEquals(result.error, null);
  assertEquals(calls, [{
    name: "get_housekeeping_queue",
    args: {
      p_housekeeper_id: "hk-1",
      p_view: "today",
      p_limit: 5,
      p_cursor: { direction: "next", sortKey: ["cursor"] },
    },
  }]);
});
