export type QueueView = "today" | "all";
export type HousekeepingTaskKind = "cleaning" | "access_prep";

export type QueueTask = {
  id: string;
  taskKind: HousekeepingTaskKind;
  assignedHousekeeperId: string | null;
  status: string;
  priority: "urgent" | "high" | "normal";
  dueAt: string | null;
  checkInDate: string | null;
  scheduledFor: string | null;
  adminPriorityRank: number;
  hasOpenBlocker: boolean;
  building: string | null;
  floor: number | null;
};

export type QueueSortKey = [
  number,
  number,
  number,
  number,
  string,
  number,
  number,
  HousekeepingTaskKind,
  string,
];

export type QueueCursor = {
  direction: "next" | "previous";
  sortKey: QueueSortKey;
};

export type QueuePage = {
  items: QueueTask[];
  nextCursor: QueueCursor | null;
  previousCursor: QueueCursor | null;
};

const TERMINAL_STATUSES = new Set([
  "completed",
  "done",
  "canceled",
  "delivery_failed",
]);

const ELIGIBLE_UNACKNOWLEDGED_STATUSES = new Set([
  "new",
  "pending_dispatch",
  "sent",
  "waiting_ack",
  "no_ack",
]);

function bangkokDate(value: Date): string {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Bangkok",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(value);
  const values = Object.fromEntries(
    parts.filter((part) => part.type !== "literal").map((part) => [
      part.type,
      part.value,
    ]),
  );
  return `${values.year}-${values.month}-${values.day}`;
}

function dateOrdinal(date: string | null): number | null {
  if (!date || !/^\d{4}-\d{2}-\d{2}$/.test(date)) return null;
  const [year, month, day] = date.split("-").map(Number);
  return Math.floor(Date.UTC(year, month - 1, day) / 86_400_000);
}

function isCheckinToday(task: QueueTask, now: Date): boolean {
  return task.checkInDate === bangkokDate(now);
}

function isAccessNearCheckin(task: QueueTask, now: Date): boolean {
  if (task.taskKind !== "access_prep") return false;
  const checkInOrdinal = dateOrdinal(task.checkInDate);
  const todayOrdinal = dateOrdinal(bangkokDate(now));
  if (checkInOrdinal === null || todayOrdinal === null) return false;
  const daysUntilCheckin = checkInOrdinal - todayOrdinal;
  return daysUntilCheckin >= 0 && daysUntilCheckin <= 1;
}

export function queueSortKey(
  task: QueueTask,
  now = new Date(),
): QueueSortKey {
  const dueTimestamp = task.dueAt
    ? Date.parse(task.dueAt)
    : task.scheduledFor
    ? Date.parse(task.scheduledFor)
    : Number.MAX_SAFE_INTEGER;
  return [
    -Math.max(0, task.adminPriorityRank || 0),
    isCheckinToday(task, now) ? 0 : 1,
    isAccessNearCheckin(task, now) ? 0 : 1,
    task.hasOpenBlocker ? 0 : 1,
    (task.building || "\uffff").toUpperCase(),
    task.floor ?? Number.MAX_SAFE_INTEGER,
    Number.isFinite(dueTimestamp) ? dueTimestamp : Number.MAX_SAFE_INTEGER,
    task.taskKind,
    task.id,
  ];
}

function compareSortKeys(left: QueueSortKey, right: QueueSortKey): number {
  for (let index = 0; index < left.length; index += 1) {
    if (left[index] === right[index]) continue;
    return left[index] < right[index] ? -1 : 1;
  }
  return 0;
}

function openTasks(tasks: QueueTask[]): QueueTask[] {
  return tasks.filter((task) => !TERMINAL_STATUSES.has(task.status));
}

export function orderQueue(
  tasks: QueueTask[],
  now = new Date(),
): QueueTask[] {
  return openTasks(tasks).toSorted((left, right) =>
    compareSortKeys(queueSortKey(left, now), queueSortKey(right, now))
  );
}

export function todayTasks(
  tasks: QueueTask[],
  housekeeperId: string,
  now = new Date(),
): QueueTask[] {
  const today = bangkokDate(now);
  return orderQueue(
    tasks.filter((task) =>
      task.assignedHousekeeperId === housekeeperId &&
      task.dueAt !== null &&
      bangkokDate(new Date(task.dueAt)) === today
    ),
    now,
  );
}

export function paginateQueue(
  tasks: QueueTask[],
  cursor: QueueCursor | null,
  limit = 5,
  now = new Date(),
): QueuePage {
  const ordered = orderQueue(tasks, now);
  const pageSize = Math.max(1, Math.min(5, Math.trunc(limit) || 5));
  let candidates = ordered;

  if (cursor?.direction === "next") {
    candidates = ordered.filter((task) =>
      compareSortKeys(queueSortKey(task, now), cursor.sortKey) > 0
    );
  } else if (cursor?.direction === "previous") {
    candidates = ordered.filter((task) =>
      compareSortKeys(queueSortKey(task, now), cursor.sortKey) < 0
    );
  }

  const items = cursor?.direction === "previous"
    ? candidates.slice(-pageSize)
    : candidates.slice(0, pageSize);
  if (items.length === 0) {
    return { items: [], nextCursor: null, previousCursor: null };
  }

  const firstKey = queueSortKey(items[0], now);
  const lastKey = queueSortKey(items.at(-1)!, now);
  const hasPrevious = ordered.some((task) =>
    compareSortKeys(queueSortKey(task, now), firstKey) < 0
  );
  const hasNext = ordered.some((task) =>
    compareSortKeys(queueSortKey(task, now), lastKey) > 0
  );

  return {
    items,
    nextCursor: hasNext ? { direction: "next", sortKey: lastKey } : null,
    previousCursor: hasPrevious
      ? { direction: "previous", sortKey: firstKey }
      : null,
  };
}

export function selectNextEligibleTask(
  tasks: QueueTask[],
  housekeeperId: string,
  now = new Date(),
): QueueTask | null {
  return orderQueue(
    tasks.filter((task) =>
      ELIGIBLE_UNACKNOWLEDGED_STATUSES.has(task.status) &&
      (
        task.assignedHousekeeperId === null ||
        task.assignedHousekeeperId === housekeeperId
      )
    ),
    now,
  )[0] ?? null;
}

export async function loadHousekeepingQueue(
  supabase: any,
  housekeeperId: string,
  view: QueueView,
  cursor: Record<string, unknown> | null,
  limit = 5,
) {
  return await supabase.rpc("get_housekeeping_queue", {
    p_housekeeper_id: housekeeperId,
    p_view: view,
    p_limit: Math.max(1, Math.min(5, Math.trunc(limit) || 5)),
    p_cursor: cursor,
  });
}

export async function claimHousekeepingTask(
  supabase: any,
  taskKind: HousekeepingTaskKind,
  taskId: string,
  housekeeperId: string,
  sourceEventId: string,
) {
  return await supabase.rpc("claim_housekeeping_task", {
    p_task_kind: taskKind,
    p_task_id: taskId,
    p_housekeeper_id: housekeeperId,
    p_source_event_id: sourceEventId,
  });
}
