import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { parseCommand } from "./commands.ts";

Deno.test("Task 3 - parseCommand enroll / เริ่มใช้งาน", () => {
  assertEquals(parseCommand("เริ่มใช้งาน"), { action: "enroll" });
  assertEquals(parseCommand("สมัครสมาชิก"), { action: "enroll" });
  assertEquals(parseCommand("สมัคร"), { action: "enroll" });
});

Deno.test("Task 3 - parseCommand acknowledge_task / รับทราบ", () => {
  assertEquals(parseCommand("รับทราบ"), { action: "acknowledge_task" });
  assertEquals(parseCommand("รับทราบครับ"), { action: "acknowledge_task" });
  assertEquals(parseCommand("รับทราบค่ะ"), { action: "acknowledge_task" });
  assertEquals(parseCommand("รับทราบนะครับ"), { action: "acknowledge_task" });
  assertEquals(parseCommand("รับทราบนะคะ"), { action: "acknowledge_task" });
  assertEquals(parseCommand("โอเค"), { action: "acknowledge_task" });
  assertEquals(parseCommand("ok"), { action: "acknowledge_task" });

  // Bounded match tests
  assertEquals(parseCommand("รับทราบแต่ยังไม่พร้อม"), {
    action: "unknown",
    text: "รับทราบแต่ยังไม่พร้อม",
  });
});

Deno.test("Task 3 - parseCommand start_task / เริ่มทำ", () => {
  assertEquals(parseCommand("เริ่มทำ"), { action: "start_task" });
  assertEquals(parseCommand("เริ่มงาน"), { action: "start_task" });
  assertEquals(parseCommand("เริ่มทำห้อง"), { action: "start_task" });
});

Deno.test("Task 3 - parseCommand mark_item_missing / ไม่มี[ไอเท็ม]", () => {
  assertEquals(parseCommand("ไม่มีน้ำ"), {
    action: "mark_item_missing",
    item: "water",
  });
  assertEquals(parseCommand("ขาดน้ำดื่ม"), {
    action: "mark_item_missing",
    item: "water",
  });
  assertEquals(parseCommand("น้ำหมด"), {
    action: "mark_item_missing",
    item: "water",
  });
  assertEquals(parseCommand("น้ำหมดแล้ว"), {
    action: "mark_item_missing",
    item: "water",
  });

  assertEquals(parseCommand("ไม่มีผ้าปู"), {
    action: "mark_item_missing",
    item: "bedsheet",
  });
  assertEquals(parseCommand("ไม่มีผ้าปูที่นอน"), {
    action: "mark_item_missing",
    item: "bedsheet",
  });

  assertEquals(parseCommand("ไม่มีสบู่"), {
    action: "mark_item_missing",
    item: "soap",
  });
  assertEquals(parseCommand("สบู่หมด"), {
    action: "mark_item_missing",
    item: "soap",
  });
  assertEquals(parseCommand("สบู่หมดแล้ว"), {
    action: "mark_item_missing",
    item: "soap",
  });

  assertEquals(parseCommand("ไม่มีทิชชู"), {
    action: "mark_item_missing",
    item: "tissue",
  });
  assertEquals(parseCommand("ทิชชู่หมด"), {
    action: "mark_item_missing",
    item: "tissue",
  });

  assertEquals(parseCommand("ไม่มีผ้าเช็ดตัว"), {
    action: "mark_item_missing",
    item: "towels",
  });
  assertEquals(parseCommand("ขาดผ้าเช็ดตัว"), {
    action: "mark_item_missing",
    item: "towels",
  });

  // towels synonyms
  assertEquals(parseCommand("ไม่มีผ้าขนหนู"), {
    action: "mark_item_missing",
    item: "towels",
  });
  assertEquals(parseCommand("ผ้าขนหนูหมดแล้ว"), {
    action: "mark_item_missing",
    item: "towels",
  });

  // room_cleaned missing
  assertEquals(parseCommand("ยังไม่ได้ทำความสะอาด"), {
    action: "mark_item_missing",
    item: "room_cleaned",
  });
});

Deno.test("Task 3 - parseCommand restore_item / เติม[ไอเท็ม]แล้ว", () => {
  assertEquals(parseCommand("เติมน้ำแล้ว"), {
    action: "restore_item",
    item: "water",
  });
  assertEquals(parseCommand("ได้น้ำแล้ว"), {
    action: "restore_item",
    item: "water",
  });
  assertEquals(parseCommand("น้ำมีแล้ว"), {
    action: "restore_item",
    item: "water",
  });
  assertEquals(parseCommand("เติมสบู่แล้ว"), {
    action: "restore_item",
    item: "soap",
  });
  assertEquals(parseCommand("สบู่ครบแล้ว"), {
    action: "restore_item",
    item: "soap",
  });
  assertEquals(parseCommand("เติมผ้าเช็ดตัวแล้ว"), {
    action: "restore_item",
    item: "towels",
  });

  // towels synonyms
  assertEquals(parseCommand("เติมผ้าขนหนูแล้ว"), {
    action: "restore_item",
    item: "towels",
  });
  assertEquals(parseCommand("มีผ้าขนหนูแล้ว"), {
    action: "restore_item",
    item: "towels",
  });

  // Negation of items
  assertEquals(parseCommand("น้ำไม่หมดแล้ว"), {
    action: "unknown",
    text: "น้ำไม่หมดแล้ว",
  });
});

Deno.test("Task 3 - parseCommand mark_key_placed / วางกุญแจแล้ว", () => {
  assertEquals(parseCommand("วางกุญแจแล้ว"), { action: "mark_key_placed" });
  assertEquals(parseCommand("วางกุญแจ"), { action: "mark_key_placed" });
  assertEquals(parseCommand("วางกุญแจไว้ในห้องแล้ว"), {
    action: "mark_key_placed",
  });
  assertEquals(parseCommand("ใส่กุญแจไว้ในห้องแล้ว"), { action: "mark_key_placed" });
  assertEquals(parseCommand("กุญแจวางอยู่ในห้องแล้ว"), {
    action: "mark_key_placed",
  });

  // Rejected key commands (should return unknown)
  assertEquals(parseCommand("ยังไม่ได้วางกุญแจไว้ในห้อง"), {
    action: "unknown",
    text: "ยังไม่ได้วางกุญแจไว้ในห้อง",
  });
  assertEquals(parseCommand("ใส่กุญแจไม่ได้"), {
    action: "unknown",
    text: "ใส่กุญแจไม่ได้",
  });
  assertEquals(parseCommand("วางกุญแจผิดห้อง"), {
    action: "unknown",
    text: "วางกุญแจผิดห้อง",
  });
  assertEquals(parseCommand("วางกุญแจไว้หน้าห้อง"), {
    action: "unknown",
    text: "วางกุญแจไว้หน้าห้อง",
  });
  assertEquals(parseCommand("คืนกุญแจแล้ว"), {
    action: "unknown",
    text: "คืนกุญแจแล้ว",
  });
  assertEquals(parseCommand("เก็บกุญแจแล้ว"), {
    action: "unknown",
    text: "เก็บกุญแจแล้ว",
  });
});

Deno.test("Task 3 - parseCommand mark_room_open / เปิดห้องแล้ว", () => {
  assertEquals(parseCommand("เปิดห้องแล้ว"), { action: "mark_room_open" });
  assertEquals(parseCommand("เปิดห้อง"), { action: "mark_room_open" });
  assertEquals(parseCommand("เปิดประตูแล้ว"), { action: "mark_room_open" });
});

Deno.test("Task 3 - parseCommand add_note / หมายเหตุ", () => {
  assertEquals(parseCommand("หมายเหตุ ห้องมีกลิ่นอับ"), {
    action: "add_note",
    note: "ห้องมีกลิ่นอับ",
  });
  assertEquals(parseCommand("หมายเหตุ:ไฟห้องน้ำเสีย"), {
    action: "add_note",
    note: "ไฟห้องน้ำเสีย",
  });
  assertEquals(parseCommand("โน้ต เตียงชำรุด"), {
    action: "add_note",
    note: "เตียงชำรุด",
  });

  // Incomplete note commands
  assertEquals(parseCommand("หมายเหตุ"), { action: "unknown", text: "หมายเหตุ" });
  assertEquals(parseCommand("หมายเหตุ:"), {
    action: "unknown",
    text: "หมายเหตุ:",
  });
  assertEquals(parseCommand("โน้ต"), { action: "unknown", text: "โน้ต" });

  // Notes containing multiple checklist keywords or joining words (must prioritize capture over multi-action detection)
  assertEquals(parseCommand("หมายเหตุ น้ำกับสบู่ไม่พอ"), {
    action: "add_note",
    note: "น้ำกับสบู่ไม่พอ",
  });
  assertEquals(parseCommand("หมายเหตุ ผ้าปูและผ้าขนหนูเปียก"), {
    action: "add_note",
    note: "ผ้าปูและผ้าขนหนูเปียก",
  });
});

Deno.test("Task 3 - parseCommand report_problem / ติดปัญหา", () => {
  assertEquals(parseCommand("ติดปัญหา: ท่อตัน"), {
    action: "report_problem",
    problem: "ท่อตัน",
  });
  assertEquals(parseCommand("ติดปัญหา แอร์ไม่เย็น"), {
    action: "report_problem",
    problem: "แอร์ไม่เย็น",
  });
  assertEquals(parseCommand("มีปัญหา น้ำไม่ไหล"), {
    action: "report_problem",
    problem: "น้ำไม่ไหล",
  });

  // Incomplete problem commands
  assertEquals(parseCommand("ติดปัญหา"), { action: "unknown", text: "ติดปัญหา" });
  assertEquals(parseCommand("มีปัญหา"), { action: "unknown", text: "มีปัญหา" });

  // Problems containing multiple checklist keywords or joining words (must prioritize capture over multi-action detection)
  assertEquals(parseCommand("ติดปัญหา น้ำไม่ไหลและสบู่หมด"), {
    action: "report_problem",
    problem: "น้ำไม่ไหลและสบู่หมด",
  });
});

Deno.test("Task 3 - parseCommand complete_cleaning / เสร็จแล้ว", () => {
  assertEquals(parseCommand("เสร็จแล้ว"), { action: "complete_cleaning" });
  assertEquals(parseCommand("เสร็จงาน"), { action: "complete_cleaning" });
  assertEquals(parseCommand("ทำความสะอาดเสร็จแล้ว"), {
    action: "complete_cleaning",
  });
});

Deno.test("Task 3 - parseCommand next_task / งานต่อไป", () => {
  assertEquals(parseCommand("งานต่อไป"), { action: "next_task" });
  assertEquals(parseCommand("ของานต่อไป"), { action: "next_task" });
  assertEquals(parseCommand("รับงานต่อไป"), { action: "next_task" });
});

Deno.test("Task 3 - parseCommand view_details / ดูรายละเอียด", () => {
  assertEquals(parseCommand("ดูรายละเอียด"), { action: "view_details" });
  assertEquals(parseCommand("รายละเอียด"), { action: "view_details" });
  assertEquals(parseCommand("รายละเอียดงาน"), { action: "view_details" });
});

Deno.test("Task 3 - parseCommand unknown", () => {
  assertEquals(parseCommand("สวัสดี"), { action: "unknown", text: "สวัสดี" });
  assertEquals(parseCommand("ทำอะไรดี"), { action: "unknown", text: "ทำอะไรดี" });
});

Deno.test("Task 3 - parseCommand adversarial / questions / negations", () => {
  assertEquals(parseCommand("มีปัญหาไหม"), {
    action: "unknown",
    text: "มีปัญหาไหม",
  });
  assertEquals(parseCommand("ไม่มีปัญหา"), { action: "unknown", text: "ไม่มีปัญหา" });
  assertEquals(parseCommand("ไม่มีปัญหา น้ำครบแล้ว"), {
    action: "unknown",
    text: "ไม่มีปัญหา น้ำครบแล้ว",
  });
  assertEquals(parseCommand("ยังไม่ได้เปิดห้อง"), {
    action: "unknown",
    text: "ยังไม่ได้เปิดห้อง",
  });
  assertEquals(parseCommand("เปิดห้องไม่ได้"), {
    action: "unknown",
    text: "เปิดห้องไม่ได้",
  });
  assertEquals(parseCommand("ไม่ต้องเปิดประตู"), {
    action: "unknown",
    text: "ไม่ต้องเปิดประตู",
  });
  assertEquals(parseCommand("อย่าเปิดห้อง"), {
    action: "unknown",
    text: "อย่าเปิดห้อง",
  });
  assertEquals(parseCommand("ยังไม่ได้เริ่มทำ"), {
    action: "unknown",
    text: "ยังไม่ได้เริ่มทำ",
  });
  assertEquals(parseCommand("ไม่ได้เริ่มงาน"), {
    action: "unknown",
    text: "ไม่ได้เริ่มงาน",
  });
  assertEquals(parseCommand("ไม่เอางานต่อไป"), {
    action: "unknown",
    text: "ไม่เอางานต่อไป",
  });
  assertEquals(parseCommand("ดูรายละเอียดไม่ได้"), {
    action: "unknown",
    text: "ดูรายละเอียดไม่ได้",
  });
  assertEquals(parseCommand("ยังไม่เสร็จแล้ว"), {
    action: "unknown",
    text: "ยังไม่เสร็จแล้ว",
  });
  assertEquals(parseCommand("น้ำยาหมด"), { action: "unknown", text: "น้ำยาหมด" });
  assertEquals(parseCommand("ผ้าปูโต๊ะหมด"), {
    action: "unknown",
    text: "ผ้าปูโต๊ะหมด",
  });
});

Deno.test("Task 3 - parseCommand multiple actions or checklist items", () => {
  assertEquals(parseCommand("ไม่มีน้ำและไม่มีสบู่"), {
    action: "unknown",
    text: "ไม่มีน้ำและไม่มีสบู่",
  });
  assertEquals(parseCommand("เติมน้ำและสบู่แล้ว"), {
    action: "unknown",
    text: "เติมน้ำและสบู่แล้ว",
  });
  assertEquals(parseCommand("วางกุญแจและเปิดห้องแล้ว"), {
    action: "unknown",
    text: "วางกุญแจและเปิดห้องแล้ว",
  });

  // Multiple actions/checklist combinations from red-team
  assertEquals(parseCommand("เติมน้ำแล้ว เปิดห้องแล้ว"), {
    action: "unknown",
    text: "เติมน้ำแล้ว เปิดห้องแล้ว",
  });
  assertEquals(parseCommand("ไม่มีน้ำ เปิดห้องแล้ว"), {
    action: "unknown",
    text: "ไม่มีน้ำ เปิดห้องแล้ว",
  });
  assertEquals(parseCommand("เติมน้ำแล้ว เสร็จแล้ว"), {
    action: "unknown",
    text: "เติมน้ำแล้ว เสร็จแล้ว",
  });
});

Deno.test("Task 10 - parseCommand postback query parameters", () => {
  const taskId = "11111111-2222-3333-4444-555555555555";
  assertEquals(parseCommand(`action=acknowledge_task&task_id=${taskId}`), {
    action: "acknowledge_task",
  });
  assertEquals(parseCommand(`action=start_task&task_id=${taskId}`), {
    action: "start_task",
  });
  assertEquals(parseCommand(`action=complete_cleaning&task_id=${taskId}`), {
    action: "complete_cleaning",
  });
  assertEquals(parseCommand(`action=mark_key_placed&task_id=${taskId}`), {
    action: "mark_key_placed",
  });
  assertEquals(parseCommand(`action=mark_room_open&task_id=${taskId}`), {
    action: "mark_room_open",
  });
  assertEquals(parseCommand(`action=enroll&task_id=${taskId}`), {
    action: "enroll",
  });
  assertEquals(parseCommand(`action=next_task&task_id=${taskId}`), {
    action: "next_task",
  });
  assertEquals(parseCommand(`action=view_details&task_id=${taskId}`), {
    action: "view_details",
  });
  assertEquals(
    parseCommand(`action=mark_item_missing&item=water&task_id=${taskId}`),
    {
      action: "mark_item_missing",
      item: "water",
    },
  );
  assertEquals(
    parseCommand(`action=restore_item&item=towels&task_id=${taskId}`),
    {
      action: "restore_item",
      item: "towels",
    },
  );
});

Deno.test("Task 4 - parseCommand hidden navigation commands", () => {
  assertEquals(parseCommand("/today"), { action: "show_today" });
  assertEquals(parseCommand("/queue"), { action: "show_queue" });
  assertEquals(parseCommand("/accept"), { action: "accept_next_task" });
  assertEquals(parseCommand("/problem"), { action: "show_problem_menu" });
  assertEquals(parseCommand("/detail"), { action: "show_task_details" });

  assertEquals(parseCommand("/today now"), {
    action: "unknown",
    text: "/today now",
  });
  assertEquals(parseCommand("please /queue"), {
    action: "unknown",
    text: "please /queue",
  });
});

Deno.test("Task 4 - parseCommand navigation postbacks without task id", () => {
  assertEquals(parseCommand("action=show_today&cursor=Next%3AABC_123"), {
    action: "show_today",
    cursor: "Next:ABC_123",
  });
  assertEquals(parseCommand("action=show_queue"), { action: "show_queue" });
  assertEquals(parseCommand("action=accept_next_task"), {
    action: "accept_next_task",
  });
  assertEquals(parseCommand("action=show_problem_menu"), {
    action: "show_problem_menu",
  });
  assertEquals(parseCommand("action=show_task_details"), {
    action: "show_task_details",
  });
});

Deno.test("Task 4 - parseCommand task selection postbacks", () => {
  const taskId = "11111111-2222-3333-8444-555555555555";
  assertEquals(
    parseCommand(`action=select_task&task_kind=cleaning&task_id=${taskId}`),
    {
      action: "select_task",
      task_kind: "cleaning",
      task_id: taskId,
    },
  );
  assertEquals(
    parseCommand(`action=select_task&task_kind=access_prep&task_id=${taskId}`),
    {
      action: "select_task",
      task_kind: "access_prep",
      task_id: taskId,
    },
  );

  assertEquals(
    parseCommand(`action=select_task&task_kind=inspection&task_id=${taskId}`),
    {
      action: "unknown",
      text: `action=select_task&task_kind=inspection&task_id=${taskId}`,
    },
  );
  assertEquals(
    parseCommand("action=select_task&task_kind=cleaning&task_id=not-a-uuid"),
    {
      action: "unknown",
      text: "action=select_task&task_kind=cleaning&task_id=not-a-uuid",
    },
  );
});

Deno.test("Task 4 - parseCommand problem category postbacks", () => {
  for (
    const category of [
      "water",
      "soap",
      "towels",
      "damaged_or_lost",
      "other",
    ] as const
  ) {
    assertEquals(
      parseCommand(`action=problem_category&category=${category}`),
      { action: "problem_category", category },
    );
  }

  assertEquals(parseCommand("action=problem_category&category=minibar"), {
    action: "unknown",
    text: "action=problem_category&category=minibar",
  });
});

Deno.test("Task H3 - parseCommand Thai double negations", () => {
  assertEquals(parseCommand("ไม่ได้ไม่มีสบู่"), {
    action: "unknown",
    text: "ไม่ได้ไม่มีสบู่",
  });
  assertEquals(parseCommand("ไม่ได้ขาดน้ำ"), {
    action: "unknown",
    text: "ไม่ได้ขาดน้ำ",
  });
  assertEquals(parseCommand("ไม่ได้หมดทิชชู่"), {
    action: "unknown",
    text: "ไม่ได้หมดทิชชู่",
  });
  assertEquals(parseCommand("ไม่ใช่ไม่มีผ้าเช็ดตัว"), {
    action: "unknown",
    text: "ไม่ใช่ไม่มีผ้าเช็ดตัว",
  });
});

Deno.test("ไหม้ is a safety problem, not a question particle", () => {
  assertEquals(
    parseCommand("ติดปัญหา แอร์ในห้องมีน้ำหยดและมีกลิ่นไหม้"),
    {
      action: "report_problem",
      problem: "แอร์ในห้องมีน้ำหยดและมีกลิ่นไหม้",
    },
  );
});

Deno.test("actual question remains unknown", () => {
  assertEquals(
    parseCommand("มีปัญหาไหม"),
    { action: "unknown", text: "มีปัญหาไหม" },
  );
});
