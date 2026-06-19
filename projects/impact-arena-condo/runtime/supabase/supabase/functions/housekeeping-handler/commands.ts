type ChecklistItem =
  | "room_cleaned"
  | "bedsheet"
  | "towels"
  | "water"
  | "tissue"
  | "soap";

type ProblemCategory =
  | "water"
  | "soap"
  | "towels"
  | "damaged_or_lost"
  | "other";

export type HousekeepingIntent =
  | { action: "enroll" }
  | { action: "acknowledge_task" }
  | { action: "start_task" }
  | { action: "mark_item_missing"; item: ChecklistItem }
  | { action: "restore_item"; item: ChecklistItem }
  | { action: "mark_key_placed" }
  | { action: "mark_room_open" }
  | { action: "add_note"; note: string }
  | { action: "report_problem"; problem: string }
  | { action: "complete_cleaning" }
  | { action: "next_task" }
  | { action: "view_details" }
  | { action: "show_today"; cursor?: string | null }
  | { action: "show_queue"; cursor?: string | null }
  | { action: "accept_next_task" }
  | { action: "show_problem_menu" }
  | { action: "show_task_details" }
  | {
    action: "select_task";
    task_kind: "cleaning" | "access_prep";
    task_id: string;
  }
  | { action: "problem_category"; category: ProblemCategory }
  | { action: "unknown"; text: string };

const ITEM_KEYWORDS: Record<ChecklistItem, string[]> = {
  water: ["น้ำ", "น้ำดื่ม", "น้ำเปล่า"],
  bedsheet: ["ผ้าปู", "ผ้าปูที่นอน"],
  soap: ["สบู่"],
  tissue: ["ทิชชู", "ทิชชู่", "กระดาษทิชชู"],
  towels: ["ผ้าเช็ดตัว", "ผ้าขนหนู"],
  room_cleaned: ["ทำความสะอาดห้อง", "ทำความสะอาด", "ทำห้อง"],
};

const KEY_PLACED_ALLOWLIST = [
  "วางกุญแจ",
  "วางกุญแจแล้ว",
  "วางกุญแจไว้ในห้องแล้ว",
  "ใส่กุญแจไว้ในห้องแล้ว",
  "กุญแจวางอยู่ในห้องแล้ว",
];

const START_TASK_ALLOWLIST = ["เริ่มทำ", "เริ่มงาน", "ทำห้อง", "เริ่มทำห้อง"];
const ROOM_OPEN_ALLOWLIST = ["เปิดห้อง", "เปิดห้องแล้ว", "เปิดประตู", "เปิดประตูแล้ว"];
const COMPLETE_CLEANING_ALLOWLIST = [
  "เสร็จแล้ว",
  "เสร็จงาน",
  "ทำความสะอาดเสร็จแล้ว",
];
const NEXT_TASK_ALLOWLIST = ["งานต่อไป", "ของานต่อไป", "รับงานต่อไป"];
const VIEW_DETAILS_ALLOWLIST = ["ดูรายละเอียด", "รายละเอียดงาน", "รายละเอียด"];
const CHECKLIST_ITEMS = new Set<ChecklistItem>([
  "room_cleaned",
  "bedsheet",
  "towels",
  "water",
  "tissue",
  "soap",
]);
const PROBLEM_CATEGORIES = new Set<ProblemCategory>([
  "water",
  "soap",
  "towels",
  "damaged_or_lost",
  "other",
]);
const TASK_KINDS = new Set(["cleaning", "access_prep"] as const);
const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const NAV_COMMANDS: Record<string, HousekeepingIntent> = {
  "/today": { action: "show_today" },
  "/queue": { action: "show_queue" },
  "/accept": { action: "accept_next_task" },
  "/problem": { action: "show_problem_menu" },
  "/detail": { action: "show_task_details" },
};

function isChecklistItem(value: string | null): value is ChecklistItem {
  return value !== null && CHECKLIST_ITEMS.has(value as ChecklistItem);
}

function isProblemCategory(value: string | null): value is ProblemCategory {
  return value !== null && PROBLEM_CATEGORIES.has(value as ProblemCategory);
}

function isTaskKind(
  value: string | null,
): value is "cleaning" | "access_prep" {
  return value !== null && TASK_KINDS.has(value as "cleaning" | "access_prep");
}

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function matchesMissing(lower: string, keywords: string[]): boolean {
  return keywords.some((kw) => {
    const escaped = escapeRegex(kw);
    return (
      new RegExp(`^(?:ไม่มี|ขาด)\\s*${escaped}(?:แล้ว)?$`).test(lower) ||
      new RegExp(`^${escaped}\\s*(?:หมด|ขาด)(?:แล้ว)?$`).test(lower) ||
      new RegExp(`^(?:ยังไม่ได้|ไม่ได้)\\s*${escaped}(?:แล้ว)?$`).test(lower)
    );
  });
}

function matchesRestore(lower: string, keywords: string[]): boolean {
  return keywords.some((kw) => {
    const escaped = escapeRegex(kw);
    return (
      new RegExp(`^เติม\\s*${escaped}\\s*แล้ว$`).test(lower) ||
      new RegExp(`^ได้\\s*${escaped}\\s*แล้ว$`).test(lower) ||
      new RegExp(`^มี\\s*${escaped}\\s*แล้ว$`).test(lower) ||
      new RegExp(`^${escaped}\\s*(?:มีแล้ว|ครบแล้ว|ครบ|แล้ว)$`).test(lower)
    );
  });
}

export function parseCommand(text: string): HousekeepingIntent {
  const trimmed = text.trim();
  const lower = trimmed.toLowerCase();

  const navCommand = NAV_COMMANDS[lower];
  if (navCommand) {
    return navCommand;
  }

  // Thai double negation check (e.g. "ไม่ได้ไม่มี", "ไม่ได้ขาด", "ไม่ได้หมด", "ไม่ใช่ไม่มี")
  if (
    lower.includes("ไม่ได้ไม่มี") ||
    lower.includes("ไม่ได้ขาด") ||
    lower.includes("ไม่ได้หมด") ||
    lower.includes("ไม่ใช่ไม่มี") ||
    lower.includes("ไม่ใช่ขาด") ||
    lower.includes("ไม่ใช่หมด")
  ) {
    return { action: "unknown", text: trimmed };
  }

  // 0. Postback query string parsing
  if (lower.includes("action=")) {
    const searchParams = new URLSearchParams(trimmed);
    const action = searchParams.get("action")?.toLowerCase() ?? null;
    const item = searchParams.get("item")?.toLowerCase() ?? null;
    const taskId = searchParams.get("task_id") ?? searchParams.get("taskid");
    const cursor = searchParams.get("cursor");

    if (action === "show_today") {
      return cursor
        ? { action: "show_today", cursor }
        : { action: "show_today" };
    }
    if (action === "show_queue") {
      return cursor
        ? { action: "show_queue", cursor }
        : { action: "show_queue" };
    }
    if (action === "accept_next_task") {
      return { action: "accept_next_task" };
    }
    if (action === "show_problem_menu") {
      return { action: "show_problem_menu" };
    }
    if (action === "show_task_details") {
      return { action: "show_task_details" };
    }
    if (action === "select_task") {
      const taskKind = searchParams.get("task_kind")?.toLowerCase() ?? null;
      if (isTaskKind(taskKind) && taskId && UUID_RE.test(taskId)) {
        return {
          action: "select_task",
          task_kind: taskKind,
          task_id: taskId,
        };
      }
    }
    if (action === "problem_category") {
      const category = searchParams.get("category")?.toLowerCase() ?? null;
      if (isProblemCategory(category)) {
        return { action: "problem_category", category };
      }
    }
    if (action === "mark_item_missing" && taskId && isChecklistItem(item)) {
      return {
        action: "mark_item_missing",
        item,
      };
    }
    if (action === "restore_item" && taskId && isChecklistItem(item)) {
      return {
        action: "restore_item",
        item,
      };
    }
    if (action === "acknowledge_task" && taskId) {
      return { action: "acknowledge_task" };
    }
    if (action === "start_task" && taskId) {
      return { action: "start_task" };
    }
    if (action === "complete_cleaning" && taskId) {
      return { action: "complete_cleaning" };
    }
    if (action === "mark_key_placed" && taskId) {
      return { action: "mark_key_placed" };
    }
    if (action === "mark_room_open" && taskId) {
      return { action: "mark_room_open" };
    }
    if (action === "enroll") {
      return { action: "enroll" };
    }
    if (action === "next_task" && taskId) {
      return { action: "next_task" };
    }
    if (action === "view_details" && taskId) {
      return { action: "view_details" };
    }
  }

  // 1. Explicit Text Captures (checked first to prioritize notes/problems over multi-action/multi-item checks)
  if (
    lower.startsWith("หมายเหตุ") ||
    lower.startsWith("โน้ต") ||
    lower.startsWith("note")
  ) {
    let note = trimmed;
    const prefixes = [
      "หมายเหตุ:",
      "หมายเหตุ ",
      "หมายเหตุ",
      "โน้ต:",
      "โน้ต ",
      "โน้ต",
      "note:",
      "note ",
      "note",
    ];
    for (const prefix of prefixes) {
      if (note.toLowerCase().startsWith(prefix)) {
        note = note.slice(prefix.length).trim();
        break;
      }
    }
    if (!note) {
      return { action: "unknown", text: trimmed };
    }
    return { action: "add_note", note };
  }

  if (
    lower.startsWith("ติดปัญหา") ||
    lower.startsWith("มีปัญหา") ||
    lower.startsWith("แจ้งปัญหา")
  ) {
    // Check for question particles
    const QUESTION_PARTICLE_RE = /(ไหม|มั้ย|หรือไม่|หรือเปล่า|ป่าว)(?![่้๊๋])/u;
    if (
      QUESTION_PARTICLE_RE.test(lower) ||
      lower.includes("ไม่มีปัญหา")
    ) {
      return { action: "unknown", text: trimmed };
    }
    let problem = trimmed;
    const prefixes = [
      "ติดปัญหา:",
      "ติดปัญหา ",
      "ติดปัญหา",
      "มีปัญหา:",
      "มีปัญหา ",
      "มีปัญหา",
      "แจ้งปัญหา:",
      "แจ้งปัญหา ",
      "แจ้งปัญหา",
    ];
    for (const prefix of prefixes) {
      if (problem.toLowerCase().startsWith(prefix)) {
        problem = problem.slice(prefix.length).trim();
        break;
      }
    }
    if (!problem) {
      return { action: "unknown", text: trimmed };
    }
    return { action: "report_problem", problem };
  }

  // 2. Reject questions/negations generally
  const QUESTION_PARTICLE_RE = /(ไหม|มั้ย|หรือไม่|หรือเปล่า|ป่าว)(?![่้๊๋])/u;
  if (
    QUESTION_PARTICLE_RE.test(lower) ||
    lower.includes("ไม่มีปัญหา")
  ) {
    return { action: "unknown", text: trimmed };
  }

  // 3. Multi-action / Multi-item ambiguity detection signals
  const hasKeySignal = lower.includes("กุญแจ");
  const hasOpenSignal = lower.includes("เปิดห้อง") || lower.includes("เปิดประตู");
  const hasCompleteSignal = lower.includes("เสร็จแล้ว") ||
    lower.includes("เสร็จงาน") || lower.includes("ทำความสะอาดเสร็จแล้ว");
  const hasAckSignal = /รับทราบ|ทราบ|โอเค|ok/i.test(lower);
  const hasStartSignal = lower.includes("เริ่มทำ") || lower.includes("เริ่มงาน") ||
    lower === "ทำห้อง" || lower === "เริ่มทำห้อง";
  const hasNextSignal = lower.includes("งานต่อไป") ||
    lower.includes("ของานต่อไป") || lower.includes("รับงานต่อไป");
  const hasViewSignal = lower.includes("ดูรายละเอียด") ||
    lower.includes("รายละเอียดงาน") || lower.includes("รายละเอียด");

  let actionTypesCount = 0;
  if (hasKeySignal) actionTypesCount++;
  if (hasOpenSignal) actionTypesCount++;
  if (hasCompleteSignal) actionTypesCount++;
  if (hasAckSignal) actionTypesCount++;
  if (hasStartSignal) actionTypesCount++;
  if (hasNextSignal) actionTypesCount++;
  if (hasViewSignal) actionTypesCount++;

  const itemsMentioned = new Set<string>();
  for (const [item, keywords] of Object.entries(ITEM_KEYWORDS)) {
    const typedItem = item as ChecklistItem;
    if (matchesMissing(lower, keywords) || matchesRestore(lower, keywords)) {
      itemsMentioned.add(typedItem);
    }
  }

  if (actionTypesCount + itemsMentioned.size > 1) {
    return { action: "unknown", text: trimmed };
  }

  // 4. Candidate Actions Collection (when only one type is present)
  const candidates: HousekeepingIntent[] = [];

  // A. enroll
  if (lower === "เริ่มใช้งาน" || lower === "สมัครสมาชิก" || lower === "สมัคร") {
    candidates.push({ action: "enroll" });
  }

  // B. acknowledge_task
  const ackRegex = /^(รับทราบ|ทราบ|โอเค|ok)(ครับ|ค่ะ|นะ|นะครับ|นะคะ)?$/i;
  if (ackRegex.test(lower)) {
    candidates.push({ action: "acknowledge_task" });
  }

  // C. start_task
  if (START_TASK_ALLOWLIST.includes(lower)) {
    candidates.push({ action: "start_task" });
  }

  // D. mark_key_placed
  if (KEY_PLACED_ALLOWLIST.includes(lower)) {
    candidates.push({ action: "mark_key_placed" });
  }

  // E. mark_room_open
  if (ROOM_OPEN_ALLOWLIST.includes(lower)) {
    candidates.push({ action: "mark_room_open" });
  }

  // F. complete_cleaning
  if (COMPLETE_CLEANING_ALLOWLIST.includes(lower)) {
    candidates.push({ action: "complete_cleaning" });
  }

  // G. next_task
  if (NEXT_TASK_ALLOWLIST.includes(lower)) {
    candidates.push({ action: "next_task" });
  }

  // H. view_details
  if (VIEW_DETAILS_ALLOWLIST.includes(lower)) {
    candidates.push({ action: "view_details" });
  }

  // I. Checklist items missing/restore
  for (const [item, keywords] of Object.entries(ITEM_KEYWORDS)) {
    const typedItem = item as ChecklistItem;
    if (matchesMissing(lower, keywords)) {
      candidates.push({ action: "mark_item_missing", item: typedItem });
    } else if (matchesRestore(lower, keywords)) {
      candidates.push({ action: "restore_item", item: typedItem });
    }
  }

  // Return action only if exactly one candidate is matched
  if (candidates.length === 1) {
    return candidates[0];
  }

  return { action: "unknown", text: trimmed };
}
