import { createClient } from "npm:@supabase/supabase-js@2";
import {
  buildProblemMenuFlexMessage,
  buildQueueFlexMessage,
  type QueuePage,
} from "./cards.ts";
import { HousekeepingIntent, parseCommand } from "./commands.ts";
import { claimHousekeepingTask, loadHousekeepingQueue } from "./queue.ts";
import { handleStateTransition, TransitionResult } from "./state.ts";

type HandlerOptions = {
  getEnv?: (key: string) => string | undefined;
  createSupabase?: () => any;
  transition?: typeof handleStateTransition;
};

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-line-signature, x-impact-webhook-secret",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function base64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(
    /=+$/g,
    "",
  );
}

async function signPostbackPayload(
  payload: string,
  secret: string,
): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(payload),
  );
  return base64Url(new Uint8Array(signature));
}

export async function buildHousekeepingPostbackData(
  action: string,
  taskId: string,
  item: string | null,
  secret: string,
): Promise<string> {
  const params = new URLSearchParams({ action, task_id: taskId });
  if (item) params.set("item", item);
  const payload = params.toString();
  params.set("sig", await signPostbackPayload(payload, secret));
  return params.toString();
}

async function hasValidHousekeepingPostbackSignature(
  value: string,
  secret: string,
): Promise<boolean> {
  const params = new URLSearchParams(value);
  const signature = params.get("sig");
  const taskId = params.get("task_id") || params.get("taskid");
  const action = params.get("action");
  if (!signature || !taskId || !action || !UUID_RE.test(taskId)) return false;
  const payloadParams = new URLSearchParams(params);
  payloadParams.delete("sig");
  const expectedSig = await signPostbackPayload(
    payloadParams.toString(),
    secret,
  );
  return expectedSig === signature;
}

function jsonResponse(body: Record<string, unknown>, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

function decodeCursor(cursor?: string | null): Record<string, unknown> | null {
  if (!cursor) return null;
  try {
    const decoded = JSON.parse(cursor);
    return decoded && typeof decoded === "object" && !Array.isArray(decoded)
      ? decoded as Record<string, unknown>
      : null;
  } catch {
    return null;
  }
}

function normalizeQueuePage(
  data: unknown,
  view: "today" | "all",
): QueuePage {
  const record = data && typeof data === "object" && !Array.isArray(data)
    ? data as Record<string, unknown>
    : {};
  return {
    view,
    items: Array.isArray(record.items)
      ? record.items as QueuePage["items"]
      : [],
    next_cursor: record.next_cursor &&
        typeof record.next_cursor === "object" &&
        !Array.isArray(record.next_cursor)
      ? record.next_cursor as Record<string, unknown>
      : null,
    previous_cursor: record.previous_cursor &&
        typeof record.previous_cursor === "object" &&
        !Array.isArray(record.previous_cursor)
      ? record.previous_cursor as Record<string, unknown>
      : null,
  };
}

function createDefaultSupabase(getEnv: (key: string) => string | undefined) {
  const url = getEnv("SUPABASE_URL");
  const key = getEnv("IMPACT_SUPABASE_SECRET_KEY") ||
    getEnv("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) {
    throw new Error("Missing Supabase runtime configuration");
  }
  return createClient(url, key);
}

function maskLineUserId(value: string): string {
  if (value.length <= 10) return `${value.slice(0, 2)}...`;
  return `${value.slice(0, 6)}...${value.slice(-4)}`;
}

function getItemLabel(item: string): string {
  const labels: Record<string, string> = {
    water: "น้ำดื่ม",
    bedsheet: "ผ้าปูที่นอน",
    soap: "สบู่",
    tissue: "กระดาษทิชชู",
    towels: "ผ้าขนหนู",
    room_cleaned: "ความสะอาดห้อง",
  };
  return labels[item] || item;
}

function getProblemCategoryLabel(category: string): string {
  const labels: Record<string, string> = {
    water: "ไม่ได้ใส่น้ำ",
    soap: "ไม่ได้ใส่สบู่",
    towels: "ไม่ได้ใส่ผ้าขนหนู",
    damaged_or_lost: "ของเสีย/ของหาย",
    other: "อื่นๆ",
  };
  return labels[category] ?? category;
}

function getProblemChecklistItem(
  category: string,
): "water" | "soap" | "towels" | null {
  if (category === "water" || category === "soap" || category === "towels") {
    return category;
  }
  return null;
}

function classifyHousekeepingSeverity(
  text: string,
): "low" | "normal" | "high" | "urgent" {
  const lower = text.toLowerCase();
  const urgentPatterns = [
    /ควัน/,
    /ไฟไหม้/,
    /กลิ่นไหม้/,
    /บาดเจ็บ/,
    /รั่ว/,
    /ขโมย/,
    /ทะเลาะ/,
    /smoke/,
    /fire/,
    /burning smell/,
    /injury/,
    /leak/,
    /theft/,
    /conflict/,
  ];
  if (urgentPatterns.some((pat) => pat.test(lower))) {
    return "urgent";
  }
  return "normal";
}

function classifyHousekeepingUnknown(
  text: string,
  isRejectedTransition = false,
): string {
  if (isRejectedTransition) return "transition_failure";
  const lower = text.toLowerCase();
  if (
    lower.includes("ฝน") || lower.includes("สภาพอากาศ") ||
    lower.includes("weather")
  ) return "weather_query";
  if (lower.includes("คืนเงิน") || lower.includes("refund")) {
    return "refund_request";
  }
  if (
    lower.includes("คนนี้") || lower.includes("เขา") || lower.includes("เธอ") ||
    lower.includes("เค้า")
  ) return "ambiguous_pronoun";
  if (
    lower.includes("และ") || lower.includes("แล้วก็") || lower.includes("then") ||
    lower.includes("and")
  ) return "compound_command";
  return "unknown_command";
}

async function buildQuickReplies(
  supabase: any,
  task: any,
  signingSecret: string,
) {
  if (!task || !task.id) return null;
  const taskId = task.id;
  const postback = (action: string, item: string | null = null) =>
    buildHousekeepingPostbackData(action, taskId, item, signingSecret);

  if (task.status === "waiting_ack") {
    return {
      items: [
        {
          type: "action",
          action: {
            type: "postback",
            label: "รับทราบงาน",
            displayText: "รับทราบ",
            data: await postback("acknowledge_task"),
          },
        },
        {
          type: "action",
          action: {
            type: "postback",
            label: "รายละเอียดงาน",
            displayText: "ดูรายละเอียด",
            data: await postback("view_details"),
          },
        },
      ],
    };
  }

  if (task.status === "acknowledged") {
    return {
      items: [
        {
          type: "action",
          action: {
            type: "postback",
            label: "เริ่มทำงาน",
            displayText: "เริ่มทำ",
            data: await postback("start_task"),
          },
        },
        {
          type: "action",
          action: {
            type: "postback",
            label: "รายละเอียดงาน",
            displayText: "ดูรายละเอียด",
            data: await postback("view_details"),
          },
        },
      ],
    };
  }

  if (task.status === "in_progress" || task.status === "blocked") {
    const items = [];

    items.push({
      type: "action",
      action: {
        type: "postback",
        label: "เสร็จงาน",
        displayText: "เสร็จแล้ว",
        data: await postback("complete_cleaning"),
      },
    });

    const { data: checklist, error: checklistError } = await supabase
      .from("cleaning_task_checklist_items")
      .select("item_key,item_label,status")
      .eq("cleaning_task_id", taskId);
    if (checklistError) {
      throw new Error(`checklist_lookup_failed: ${checklistError.message}`);
    }

    if (checklist) {
      for (const clItem of checklist) {
        if (clItem.status === "present") {
          items.push({
            type: "action",
            action: {
              type: "postback",
              label: `ไม่มี ${clItem.item_label}`,
              displayText: `ไม่มี${clItem.item_label}`,
              data: await postback("mark_item_missing", clItem.item_key),
            },
          });
        } else {
          items.push({
            type: "action",
            action: {
              type: "postback",
              label: `เติม ${clItem.item_label} แล้ว`,
              displayText: `เติม${clItem.item_label}แล้ว`,
              data: await postback("restore_item", clItem.item_key),
            },
          });
        }
      }
    }

    if (task.booking_id) {
      const { data: accessPrep, error: accessPrepError } = await supabase
        .from("booking_access_preparations")
        .select("key_placed_in_room,room_left_unlocked_or_open")
        .eq("booking_id", task.booking_id)
        .maybeSingle();
      if (accessPrepError) {
        throw new Error(
          `access_prep_lookup_failed: ${accessPrepError.message}`,
        );
      }

      const prep = accessPrep ?? {
        key_placed_in_room: false,
        room_left_unlocked_or_open: false,
      };
      if (!prep.key_placed_in_room) {
        items.push({
          type: "action",
          action: {
            type: "postback",
            label: "วางกุญแจแล้ว",
            displayText: "วางกุญแจแล้ว",
            data: await postback("mark_key_placed"),
          },
        });
      }
      if (!prep.room_left_unlocked_or_open) {
        items.push({
          type: "action",
          action: {
            type: "postback",
            label: "เปิดห้องแล้ว",
            displayText: "เปิดห้องแล้ว",
            data: await postback("mark_room_open"),
          },
        });
      }
    }

    items.push({
      type: "action",
      action: {
        type: "postback",
        label: "รายละเอียดงาน",
        displayText: "ดูรายละเอียด",
        data: await postback("view_details"),
      },
    });

    return {
      items: items.slice(0, 13),
    };
  }

  if (task.status === "completed") {
    return {
      items: [
        {
          type: "action",
          action: {
            type: "postback",
            label: "ของานต่อไป",
            displayText: "งานต่อไป",
            data: `action=next_task`,
          },
        },
      ],
    };
  }

  return null;
}

async function buildDetailsCardText(
  supabase: any,
  task: any,
  roomCode: string,
): Promise<string> {
  const priorityText = task.priority === "urgent"
    ? "ด่วนที่สุด"
    : task.priority === "high"
    ? "ด่วน"
    : "ปกติ";
  const dueText = task.due_at
    ? new Date(task.due_at).toLocaleString("th-TH", {
      timeZone: "Asia/Bangkok",
    })
    : "-";
  const instructionsText = task.instructions || "-";

  let bookingCheckInText = "-";
  if (task.booking_id) {
    const { data: booking, error: bookingError } = await supabase
      .from("bookings")
      .select("check_in_date")
      .eq("id", task.booking_id)
      .maybeSingle();
    if (bookingError) {
      throw new Error(`booking_lookup_failed: ${bookingError.message}`);
    }
    if (booking) {
      const dateStr = booking.check_in_date
        ? new Date(booking.check_in_date).toLocaleDateString("th-TH")
        : "";
      bookingCheckInText = dateStr || "-";
    }
  }

  let accessPrepText = "ไม่ทราบ";
  if (task.booking_id) {
    const { data: accessPrep, error: accessPrepError } = await supabase
      .from("booking_access_preparations")
      .select("key_placed_in_room,room_left_unlocked_or_open,status")
      .eq("booking_id", task.booking_id)
      .maybeSingle();
    if (accessPrepError) {
      throw new Error(`access_prep_lookup_failed: ${accessPrepError.message}`);
    }
    if (accessPrep) {
      const keyText = accessPrep.key_placed_in_room ? "วางแล้ว" : "ยังไม่วาง";
      const openText = accessPrep.room_left_unlocked_or_open
        ? "เปิดแล้ว"
        : "ยังไม่เปิด";
      accessPrepText =
        `กุญแจ: ${keyText}, ประตู: ${openText} (สถานะ: ${accessPrep.status})`;
    } else {
      accessPrepText = "ยังไม่เริ่มเตรียม";
    }
  }

  let caseText = "-";
  if (task.internal_ops_case_id) {
    const { data: kase, error: caseError } = await supabase
      .from("internal_ops_cases")
      .select("case_code,issue_summary")
      .eq("id", task.internal_ops_case_id)
      .maybeSingle();
    if (caseError) {
      throw new Error(`case_lookup_failed: ${caseError.message}`);
    }
    if (kase) {
      caseText = `${kase.case_code || "-"} - ${kase.issue_summary || "-"}`;
    }
  }

  let checklistStr = "";
  const { data: checklist, error: checklistError } = await supabase
    .from("cleaning_task_checklist_items")
    .select("item_label,status")
    .eq("cleaning_task_id", task.id);
  if (checklistError) {
    throw new Error(`checklist_lookup_failed: ${checklistError.message}`);
  }
  if (checklist && checklist.length > 0) {
    checklistStr = checklist.map((item: any) => {
      const indicator = item.status === "present" ? "[✓]" : "[ขาด]";
      return `  ${indicator} ${item.item_label}`;
    }).join("\n");
  }

  const cardText = [
    `[ใบสั่งงานห้อง ${roomCode}]`,
    `ความสำคัญ: ${priorityText}`,
    `กำหนดเสร็จ: ${dueText}`,
    `เวลาเช็กอินของแขก: ${bookingCheckInText}`,
    `คำแนะนำ/โน้ต: ${instructionsText}`,
    `การเตรียมห้อง (Access Prep): ${accessPrepText}`,
    `เคสอ้างอิง: ${caseText}`,
    `สถานะงาน: ${task.status}`,
  ];

  if (checklistStr) {
    cardText.push(`รายการของในห้อง:\n${checklistStr}`);
  }

  return cardText.join("\n");
}

async function fetchActiveHousekeeper(supabase: any, lineUserId: string) {
  const { data, error } = await supabase
    .from("housekeepers")
    .select("*")
    .eq("line_user_id", lineUserId)
    .maybeSingle();

  if (error) return { error };
  if (!data || data.status !== "active" || data.active === false) {
    return { data: null };
  }
  return { data };
}

async function fetchTaskAndRoom(supabase: any, taskId?: string) {
  if (!taskId) return { task: null, roomCode: "ไม่ระบุ" };
  const { data: task, error: taskError } = await supabase
    .from("cleaning_tasks")
    .select("*")
    .eq("id", taskId)
    .maybeSingle();

  if (taskError) {
    return {
      error: "database_error",
      message: "Unable to read cleaning task",
    };
  }
  if (!task?.room_id) return { task, roomCode: "ไม่ระบุ" };
  const { data: room, error: roomError } = await supabase
    .from("rooms")
    .select("room_code")
    .eq("id", task.room_id)
    .maybeSingle();
  if (roomError) {
    return {
      error: "database_error",
      message: "Unable to read room details",
    };
  }
  return { task, roomCode: room?.room_code || "ไม่ระบุ" };
}

async function fetchFocusedTaskDetails(supabase: any, housekeeperId: string) {
  const { data: focus, error: focusError } = await supabase
    .from("housekeeper_task_focus")
    .select("focused_cleaning_task_id,focus_type")
    .eq("housekeeper_id", housekeeperId)
    .maybeSingle();

  if (focusError) {
    return { error: "database_error", message: "Unable to read task focus" };
  }
  if (focus?.focus_type !== "cleaning" || !focus.focused_cleaning_task_id) {
    return { error: "no_task_assigned", message: "ยังไม่มีงานที่เลือกอยู่ค่ะ" };
  }
  const taskDetails = await fetchTaskAndRoom(
    supabase,
    focus.focused_cleaning_task_id,
  );
  if ("error" in taskDetails) {
    return { error: taskDetails.error, message: taskDetails.message };
  }
  const { task, roomCode } = taskDetails;
  if (!task || task.assigned_housekeeper_id !== housekeeperId) {
    return { error: "no_task_assigned", message: "ยังไม่มีงานที่เลือกอยู่ค่ะ" };
  }
  return { task, roomCode };
}

function buildFailureReply(result: Extract<TransitionResult, { ok: false }>) {
  if (result.error === "missing_checklist_items") {
    return "ไม่สามารถเสร็จงานได้เนื่องจากยังมีไอเท็มที่ขาดแคลนอยู่ค่ะ กรุณาเติมให้ครบก่อนพิมพ์ 'เสร็จแล้ว' นะคะ";
  }
  if (result.error === "task_blocked") {
    return "ไม่สามารถเสร็จงานได้เนื่องจากงานถูกบล็อกอยู่ค่ะ";
  }
  if (result.error === "invalid_transition") {
    return "ขออภัยค่ะ ไม่สามารถดำเนินการคำสั่งนี้ในสถานะปัจจุบันได้ค่ะ";
  }
  if (result.error === "no_booking") {
    return "ไม่สามารถบันทึกสถานะกุญแจหรือเปิดห้องได้เนื่องจากงานนี้ไม่มีการจองพักผูกอยู่ค่ะ";
  }
  return `ขออภัยค่ะ ไม่สามารถทำรายการได้ในขณะนี้: ${result.message}`;
}

function isSystemFailure(result: Extract<TransitionResult, { ok: false }>) {
  return [
    "database_error",
    "invalid_source_event_id",
    "invalid_state_result",
  ].includes(result.error);
}

function buildSuccessTexts(
  intent: HousekeepingIntent,
  roomCode: string,
  task: any,
  operatorName: string,
) {
  let housekeepingText = "บันทึกเรียบร้อยแล้วค่ะ";
  let internalText: string | null = null;

  switch (intent.action) {
    case "acknowledge_task":
      housekeepingText =
        `รับทราบงานห้อง ${roomCode} เรียบร้อยค่ะ ถ้าจะเริ่มงาน พิมพ์ "เริ่มทำ" ได้เลยนะคะ`;
      internalText = `แม่บ้าน ${operatorName} ได้รับทราบงานของห้อง ${roomCode} แล้ว`;
      break;
    case "start_task":
      housekeepingText =
        `เริ่มงานความสะอาดห้อง ${roomCode} แล้วค่ะ หากต้องการบันทึกของขาด พิมพ์ "ไม่มี [ไอเท็ม]" เช่น "ไม่มีน้ำ" นะคะ`;
      internalText = `แม่บ้าน ${operatorName} เริ่มทำความสะอาดห้อง ${roomCode} แล้ว`;
      break;
    case "mark_item_missing": {
      const label = getItemLabel(intent.item);
      housekeepingText =
        `บันทึกสถานะขาด ${label} เรียบร้อยค่ะ เมื่อเติมแล้วพิมพ์ "เติม${label}แล้ว" นะคะ`;
      internalText =
        `แม่บ้าน ${operatorName} รายงานขาด ${label} ที่ห้อง ${roomCode}`;
      break;
    }
    case "restore_item": {
      const label = getItemLabel(intent.item);
      housekeepingText = `บันทึกการเติม ${label} เรียบร้อยค่ะ`;
      internalText =
        `แม่บ้าน ${operatorName} เติม ${label} ที่ห้อง ${roomCode} ครบแล้ว`;
      break;
    }
    case "complete_cleaning":
      housekeepingText = `ทำความสะอาดห้อง ${roomCode} เสร็จสิ้นเรียบร้อยค่ะ`;
      internalText =
        `แม่บ้าน ${operatorName} ทำความสะอาดห้อง ${roomCode} เสร็จเรียบร้อยแล้ว`;
      break;
    case "mark_key_placed":
      housekeepingText = "บันทึกการวางกุญแจในห้องเรียบร้อยค่ะ";
      internalText =
        `แม่บ้าน ${operatorName} วางกุญแจในห้องเรียบร้อยสำหรับห้อง ${roomCode}`;
      break;
    case "mark_room_open":
      housekeepingText = "บันทึกการเปิดห้องเรียบร้อยค่ะ";
      internalText = `แม่บ้าน ${operatorName} เปิดห้องเรียบร้อยสำหรับห้อง ${roomCode}`;
      break;
    case "add_note":
      housekeepingText = "บันทึกหมายเหตุเพิ่มเติมเรียบร้อยค่ะ";
      internalText =
        `แม่บ้าน ${operatorName} บันทึกหมายเหตุที่ห้อง ${roomCode}: ${intent.note}`;
      break;
    case "report_problem":
      housekeepingText = "รับแจ้งปัญหาเรียบร้อยค่ะ เจ้าหน้าที่จะรีบตรวจสอบนะคะ";
      internalText =
        `แจ้งเตือน: แม่บ้าน ${operatorName} รายงานปัญหาที่ห้อง ${roomCode}: ${intent.problem}`;
      break;
    case "view_details":
      housekeepingText = `นี่คือรายละเอียดงานของห้อง ${roomCode} ค่ะ\nสถานะปัจจุบัน: ${
        task ? task.status : "ไม่ทราบ"
      }`;
      break;
  }

  return { housekeepingText, internalText };
}

export function createHousekeepingHandler(options: HandlerOptions = {}) {
  const getEnv = options.getEnv || ((key: string) => Deno.env.get(key));
  const transition = options.transition || handleStateTransition;
  const createSupabaseClient = options.createSupabase ||
    (() => createDefaultSupabase(getEnv));

  return async function handler(req: Request): Promise<Response> {
    if (req.method === "OPTIONS") {
      return new Response("ok", { headers: corsHeaders });
    }
    if (req.method !== "POST") {
      return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
    }

    const expectedSecret = getEnv("N8N_WEBHOOK_SECRET");
    const receivedSecret = req.headers.get("x-impact-webhook-secret");
    if (!expectedSecret || receivedSecret !== expectedSecret) {
      return jsonResponse({ ok: false, error: "unauthorized" }, 401);
    }

    try {
      const {
        line_user_id,
        text,
        source_event_id,
        display_name,
        message_type,
        message_id,
        media,
        ai_summary: _ignoredAiSummary,
      } = await req.json();

      if (!line_user_id || !text || !source_event_id) {
        return jsonResponse({
          ok: false,
          error: "bad_request",
          message: "line_user_id, text, and source_event_id are required",
        }, 400);
      }
      if (!UUID_RE.test(source_event_id)) {
        return jsonResponse({
          ok: false,
          error: "bad_request",
          message: "source_event_id must be a UUID",
        }, 400);
      }

      const supabase = createSupabaseClient();
      const isTaskPostback = text.includes("action=") &&
        (text.includes("task_id=") || text.includes("taskid="));
      if (
        isTaskPostback &&
        !await hasValidHousekeepingPostbackSignature(text, expectedSecret)
      ) {
        return jsonResponse({
          ok: false,
          error: "invalid_postback_signature",
          message:
            "Housekeeping action reference is invalid or has been changed",
        }, 403);
      }
      const intent = parseCommand(text);

      const postbackTaskIdFromText = (() => {
        if (
          text.includes("action=") &&
          (text.includes("task_id=") || text.includes("taskid="))
        ) {
          const searchParams = new URLSearchParams(text);
          const tid = searchParams.get("task_id") || searchParams.get("taskid");
          return tid && UUID_RE.test(tid) ? tid : null;
        }
        return null;
      })();
      const postbackTaskKindFromText = (() => {
        if (!text.includes("action=")) return null;
        const taskKind = new URLSearchParams(text).get("task_kind");
        return taskKind === "cleaning" || taskKind === "access_prep"
          ? taskKind
          : null;
      })();

      if (intent.action === "enroll") {
        const { data: existing, error: lookupError } = await supabase
          .from("housekeepers")
          .select("*")
          .eq("line_user_id", line_user_id)
          .maybeSingle();

        if (lookupError) {
          return jsonResponse({
            ok: false,
            error: "database_error",
            message: "Unable to check Housekeeping enrollment",
          }, 500);
        }

        let housekeeperId = "";
        if (!existing) {
          const { data: inserted, error: insertError } = await supabase
            .from("housekeepers")
            .insert({
              line_user_id,
              display_name: display_name || "Unknown Operator",
              status: "pending",
              role: "housekeeper",
              active: false,
              enrolled_at: new Date().toISOString(),
              created_at: new Date().toISOString(),
            })
            .select("id")
            .single();

          if (insertError) {
            return jsonResponse({
              ok: false,
              error: "database_error",
              message: "Unable to create pending Housekeeping enrollment",
            }, 500);
          }
          housekeeperId = inserted.id;
        } else {
          housekeeperId = existing.id;
        }

        const maskedLineUserId = maskLineUserId(line_user_id);
        return jsonResponse({
          ok: true,
          action: "enroll",
          housekeeping_reply: {
            text: "ระบบได้รับคำขอลงทะเบียนของท่านแล้ว กรุณารอเจ้าหน้าที่อนุมัติการใช้งานค่ะ",
          },
          internal_notification: {
            text: `แจ้งเตือน: มีคำขอสมัครสมาชิกแม่บ้านใหม่\nชื่อ: ${
              display_name || "Unknown"
            }\nLINE User ID: ${maskedLineUserId}\nHousekeeper ID: ${housekeeperId}\nกรุณาอนุมัติโดยพิมพ์: /approve_hk ${housekeeperId} หรือ อนุมัติแม่บ้าน ${housekeeperId}`,
          },
          guest_draft_request: null,
          evidence: {
            line_user_id_masked: maskedLineUserId,
            housekeeper_id: housekeeperId,
            status: existing?.status || "pending",
            source_event_id,
          },
        });
      }

      const housekeeperResult = await fetchActiveHousekeeper(
        supabase,
        line_user_id,
      );
      if (housekeeperResult.error) {
        return jsonResponse({
          ok: false,
          error: "database_error",
          message: "Unable to authorize housekeeper",
        }, 500);
      }
      const housekeeper = housekeeperResult.data;
      if (!housekeeper) {
        return jsonResponse({
          ok: false,
          error: "housekeeper_not_found",
          message: "Active housekeeper profile not found",
        });
      }

      if (intent.action === "show_today" || intent.action === "show_queue") {
        const view = intent.action === "show_today" ? "today" : "all";
        const queueResult = await loadHousekeepingQueue(
          supabase,
          housekeeper.id,
          view,
          decodeCursor(intent.cursor),
          5,
        );
        if (queueResult.error) {
          return jsonResponse({
            ok: false,
            error: "database_error",
            message: "Unable to load Housekeeping queue",
            housekeeping_reply: {
              text:
                "ขออภัยค่ะ ระบบอ่านคิวงานไม่สำเร็จ กรุณาแจ้ง Internal Ops ตรวจสอบค่ะ",
            },
            internal_notification: {
              text:
                `Housekeeping handler error: get_housekeeping_queue (${queueResult.error.message})`,
            },
            guest_draft_request: null,
            evidence: { source_event_id, view, error: "database_error" },
          }, 500);
        }
        const page = normalizeQueuePage(queueResult.data, view);
        return jsonResponse({
          ok: true,
          action: intent.action,
          housekeeping_reply: {
            messages: [await buildQueueFlexMessage(page, expectedSecret)],
          },
          internal_notification: null,
          guest_draft_request: null,
          evidence: {
            source_event_id,
            view,
            count: page.items.length,
          },
        });
      }

      if (intent.action === "show_problem_menu") {
        const taskDetails = await fetchTaskAndRoom(
          supabase,
          postbackTaskIdFromText ?? undefined,
        );
        if ("error" in taskDetails) {
          return jsonResponse({
            ok: false,
            error: taskDetails.error,
            message: taskDetails.message,
            housekeeping_reply: {
              text:
                "ขออภัยค่ะ ระบบอ่านรายละเอียดงานไม่สำเร็จ กรุณาแจ้ง Internal Ops ตรวจสอบค่ะ",
            },
            internal_notification: {
              text:
                `Housekeeping handler error: ${taskDetails.error} (${taskDetails.message})`,
            },
            guest_draft_request: null,
            evidence: { source_event_id, error: taskDetails.error },
          }, 500);
        }
        const { task, roomCode } = taskDetails;
        if (!task || task.assigned_housekeeper_id !== housekeeper.id) {
          return jsonResponse({
            ok: false,
            error: "no_task_assigned",
            message: "Housekeeper is not assigned to this task",
            housekeeping_reply: { text: "ยังไม่มีงานที่เลือกอยู่ค่ะ" },
            internal_notification: null,
            guest_draft_request: null,
            evidence: { source_event_id, task_id: postbackTaskIdFromText },
          });
        }
        return jsonResponse({
          ok: true,
          action: "show_problem_menu",
          housekeeping_reply: {
            messages: [
              await buildProblemMenuFlexMessage({
                task_id: task.id,
                task_kind: "cleaning",
                room_code: roomCode,
                status: task.status,
              }, expectedSecret),
            ],
          },
          internal_notification: null,
          guest_draft_request: null,
          evidence: { source_event_id, task_id: task.id },
        });
      }

      if (
        intent.action === "acknowledge_task" &&
        postbackTaskIdFromText &&
        postbackTaskKindFromText
      ) {
        const claimResult = await claimHousekeepingTask(
          supabase,
          postbackTaskKindFromText,
          postbackTaskIdFromText,
          housekeeper.id,
          source_event_id,
        );
        if (claimResult.error) {
          return jsonResponse({
            ok: false,
            error: "database_error",
            message: "Unable to claim Housekeeping task",
            housekeeping_reply: {
              text: "ขออภัยค่ะ ระบบรับงานไม่สำเร็จ กรุณาลองใหม่อีกครั้ง",
            },
            internal_notification: {
              text: `Housekeeping claim error: ${claimResult.error.message}`,
            },
            guest_draft_request: null,
            evidence: { source_event_id, task_id: postbackTaskIdFromText },
          }, 500);
        }
        const claim = claimResult.data ?? {};
        if (claim.ok === false) {
          return jsonResponse({
            ok: true,
            action: "rejected",
            housekeeping_reply: {
              text: claim.error === "already_claimed"
                ? "งานนี้มีผู้รับไปแล้วค่ะ กรุณากดคิวงานเพื่อดูงานล่าสุด"
                : "ไม่สามารถรับงานนี้ได้ในสถานะปัจจุบันค่ะ",
            },
            internal_notification: null,
            guest_draft_request: null,
            evidence: claim,
          });
        }
        return jsonResponse({
          ok: true,
          action: "acknowledge_task",
          housekeeping_reply: {
            text: "รับงานเรียบร้อยค่ะ กดเริ่มงานเมื่อพร้อมดำเนินการ",
          },
          internal_notification: {
            text: `แม่บ้าน ${housekeeper.display_name || line_user_id} รับงาน ${
              postbackTaskKindFromText === "cleaning"
                ? "Cleaning"
                : "Access Prep"
            } แล้ว`,
          },
          guest_draft_request: null,
          evidence: claim,
        });
      }

      if (intent.action === "problem_category") {
        const taskDetails = await fetchTaskAndRoom(
          supabase,
          postbackTaskIdFromText ?? undefined,
        );
        if ("error" in taskDetails) {
          return jsonResponse({
            ok: false,
            error: taskDetails.error,
            message: taskDetails.message,
            housekeeping_reply: {
              text:
                "ขออภัยค่ะ ระบบอ่านรายละเอียดงานไม่สำเร็จ กรุณาแจ้ง Internal Ops ตรวจสอบค่ะ",
            },
            internal_notification: {
              text:
                `Housekeeping handler error: ${taskDetails.error} (${taskDetails.message})`,
            },
            guest_draft_request: null,
            evidence: { source_event_id, error: taskDetails.error },
          }, 500);
        }
        const { task, roomCode } = taskDetails;
        if (!task || task.assigned_housekeeper_id !== housekeeper.id) {
          return jsonResponse({
            ok: false,
            error: "no_task_assigned",
            message: "Housekeeper is not assigned to this task",
            housekeeping_reply: { text: "ยังไม่มีงานที่เลือกอยู่ค่ะ" },
            internal_notification: null,
            guest_draft_request: null,
            evidence: { source_event_id, task_id: postbackTaskIdFromText },
          });
        }

        const categoryLabel = getProblemCategoryLabel(intent.category);
        const checklistItem = getProblemChecklistItem(intent.category);
        const transitionResult = checklistItem
          ? await transition(
            supabase,
            line_user_id,
            { action: "mark_item_missing", item: checklistItem },
            source_event_id,
            task.id,
          )
          : null;

        if (
          transitionResult && !transitionResult.ok &&
          isSystemFailure(transitionResult)
        ) {
          return jsonResponse({
            ok: false,
            error: transitionResult.error,
            message: transitionResult.message,
            housekeeping_reply: {
              text: "ขออภัยค่ะ ระบบบันทึกงานไม่สำเร็จ กรุณาแจ้ง Internal Ops ตรวจสอบค่ะ",
            },
            internal_notification: {
              text:
                `Housekeeping handler error: ${transitionResult.error} (${transitionResult.message})`,
            },
            guest_draft_request: null,
            evidence: transitionResult,
          }, 500);
        }

        const incidentPayload = {
          source_surface: "housekeeping_line",
          source_event_id,
          correlation_id: source_event_id,
          idempotency_key:
            `housekeeping_line:${source_event_id}:problem_${intent.category}`,
          cleaning_task_id: task.id,
          housekeeper_id: housekeeper.id,
          room_id: task.room_id ?? null,
          booking_id: task.booking_id ?? null,
          issue_family: "housekeeping_problem",
          issue_subtype: checklistItem
            ? `missing_${checklistItem}`
            : intent.category,
          severity: intent.category === "damaged_or_lost" ? "high" : "normal",
          latest_evidence_text: `${
            housekeeper.display_name || line_user_id
          } reported ${categoryLabel} at room ${roomCode}`,
          requires_internal_ops: true,
          requires_owner: true,
          metadata: {
            category: intent.category,
            checklist_item: checklistItem,
            needs_classification: intent.category === "other",
            awaiting_detail: !checklistItem,
            message_type: message_type ?? null,
            message_id: message_id ?? null,
            media: media ?? null,
          },
        };

        const { error: incidentError } = await supabase.rpc(
          "report_operational_incident",
          { p_incident: incidentPayload },
        );
        if (incidentError) {
          return jsonResponse({
            ok: false,
            error: "database_error",
            message: "Unable to report housekeeping problem incident",
            housekeeping_reply: {
              text: "ขออภัยค่ะ ระบบแจ้งปัญหาไม่สำเร็จ กรุณาแจ้ง Internal Ops ตรวจสอบค่ะ",
            },
            internal_notification: {
              text:
                `Housekeeping handler error: report_operational_incident (${incidentError.message})`,
            },
            guest_draft_request: null,
            evidence: { source_event_id, task_id: task.id },
          }, 500);
        }

        const quickReply = await buildQuickReplies(
          supabase,
          task,
          expectedSecret,
        );
        const detailPrompt = checklistItem
          ? `บันทึก ${categoryLabel} ของห้อง ${roomCode} แล้วค่ะ ระบบแจ้ง Internal Ops และเจ้าของแล้ว`
          : `รับแจ้ง ${categoryLabel} ของห้อง ${roomCode} แล้วค่ะ กรุณาส่งรายละเอียดหรือรูปเพิ่มเติมในแชทนี้ได้เลย`;

        return jsonResponse({
          ok: true,
          action: "problem_category",
          housekeeping_reply: {
            text: detailPrompt,
            quickReply,
          },
          internal_notification: {
            text: `แจ้งเตือน: แม่บ้าน ${
              housekeeper.display_name || line_user_id
            } รายงาน ${categoryLabel} ที่ห้อง ${roomCode} (แจ้ง Internal Ops และ owner)`,
          },
          guest_draft_request: null,
          incident_candidate: incidentPayload,
          evidence: transitionResult ?? {
            ok: true,
            action: "problem_category",
            taskId: task.id,
            previousState: task.status,
            newState: task.status,
          },
        });
      }

      if (intent.action === "unknown") {
        const details = await fetchFocusedTaskDetails(supabase, housekeeper.id)
          .catch(() => ({}));
        const focusedTask = (details && "task" in details)
          ? details.task
          : null;

        const incidentCandidate = {
          source_surface: "housekeeping_line",
          source_event_id,
          correlation_id: source_event_id,
          idempotency_key: `housekeeping_line:${source_event_id}:out_of_sop`,
          cleaning_task_id: focusedTask?.id ?? null,
          housekeeper_id: housekeeper.id,
          room_id: focusedTask?.room_id ?? null,
          booking_id: focusedTask?.booking_id ?? null,
          issue_family: "housekeeping_out_of_sop",
          issue_subtype: classifyHousekeepingUnknown(text),
          severity: classifyHousekeepingSeverity(text),
          latest_evidence_text: text,
          requires_internal_ops: true,
          requires_owner: true,
        };

        return jsonResponse({
          ok: true,
          action: "unknown",
          housekeeping_reply: {
            text:
              "รับเรื่องแล้วค่ะ ระบบกำลังแจ้ง Internal Ops และเจ้าของให้ตรวจสอบทันทีค่ะ",
          },
          internal_notification: null,
          guest_draft_request: null,
          incident_candidate: incidentCandidate,
          evidence: { source_event_id, text },
        });
      }

      if (intent.action === "view_details" || intent.action === "next_task") {
        const details = await fetchFocusedTaskDetails(supabase, housekeeper.id);
        if ("error" in details) {
          if (details.error === "database_error") {
            return jsonResponse({
              ok: false,
              error: details.error,
              message: details.message,
              housekeeping_reply: {
                text:
                  "ขออภัยค่ะ ระบบอ่านรายละเอียดงานไม่สำเร็จ กรุณาแจ้ง Internal Ops ตรวจสอบค่ะ",
              },
              internal_notification: {
                text:
                  `Housekeeping handler error: ${details.error} (${details.message})`,
              },
              guest_draft_request: null,
              evidence: { source_event_id, error: details.error },
            }, 500);
          }
          return jsonResponse({
            ok: true,
            action: intent.action,
            housekeeping_reply: { text: details.message },
            internal_notification: null,
            guest_draft_request: null,
            evidence: { source_event_id, error: details.error },
          });
        }
        let replyText = "";
        let qr = null;
        if (intent.action === "next_task") {
          replyText = `งานที่เลือกอยู่ตอนนี้คือห้อง ${details.roomCode} ค่ะ`;
          qr = await buildQuickReplies(supabase, details.task, expectedSecret);
        } else {
          replyText = await buildDetailsCardText(
            supabase,
            details.task,
            details.roomCode,
          );
          qr = await buildQuickReplies(supabase, details.task, expectedSecret);
        }
        return jsonResponse({
          ok: true,
          action: intent.action,
          housekeeping_reply: {
            text: replyText,
            quickReply: qr,
          },
          internal_notification: null,
          guest_draft_request: null,
          evidence: {
            source_event_id,
            task_id: details.task.id,
            status: details.task.status,
          },
        });
      }

      // Extract taskId from command if it is a postback query string
      const postbackTaskId = postbackTaskIdFromText;

      const transitionResult = await transition(
        supabase,
        line_user_id,
        intent,
        source_event_id,
        postbackTaskId,
      );

      if (!transitionResult.ok) {
        if (transitionResult.error === "capability_denied") {
          const details = await fetchFocusedTaskDetails(
            supabase,
            housekeeper.id,
          ).catch(() => ({}));
          const focusedTask = (details && "task" in details)
            ? details.task
            : null;

          const incidentPayload = {
            source_surface: "housekeeping_line",
            source_event_id,
            correlation_id: source_event_id,
            idempotency_key:
              `housekeeping_line:${source_event_id}:unauthorized_access_prep_action`,
            cleaning_task_id: transitionResult.taskId || focusedTask?.id ||
              null,
            housekeeper_id: housekeeper.id,
            room_id: focusedTask?.room_id || null,
            booking_id: focusedTask?.booking_id || null,
            issue_family: "access_prep",
            issue_subtype: "unauthorized_access_prep_action",
            severity: "high",
            latest_evidence_text: `Housekeeper ${
              housekeeper.display_name || line_user_id
            } attempted unauthorized access prep action '${intent.action}'`,
            requires_internal_ops: true,
            requires_owner: true,
            metadata: {
              required_capability:
                (transitionResult as any).required_capability || null,
            },
          };

          const { error: rpcError } = await supabase.rpc(
            "report_operational_incident",
            {
              p_incident: incidentPayload,
            },
          );

          if (rpcError) {
            console.error(
              "Failed to report operational incident via RPC:",
              rpcError,
            );
          }

          return jsonResponse({
            ok: true,
            action: "rejected",
            housekeeping_reply: {
              text: "ขออภัยค่ะ คุณไม่มีสิทธิ์ดำเนินการนี้ ระบบได้แจ้งเตือนความปลอดภัยแล้วค่ะ",
            },
            internal_notification: null,
            guest_draft_request: null,
            incident_candidate: incidentPayload,
            evidence: transitionResult,
          });
        }

        if (isSystemFailure(transitionResult)) {
          return jsonResponse({
            ok: false,
            error: transitionResult.error,
            message: transitionResult.message,
            housekeeping_reply: {
              text: "ขออภัยค่ะ ระบบบันทึกงานไม่สำเร็จ กรุณาแจ้ง Internal Ops ตรวจสอบค่ะ",
            },
            internal_notification: {
              text:
                `Housekeeping handler error: ${transitionResult.error} (${transitionResult.message})`,
            },
            guest_draft_request: null,
            evidence: transitionResult,
          }, 500);
        }

        const details = await fetchFocusedTaskDetails(supabase, housekeeper.id)
          .catch(() => ({}));
        const focusedTask = (details && "task" in details)
          ? details.task
          : null;

        const incidentCandidate = {
          source_surface: "housekeeping_line",
          source_event_id,
          correlation_id: source_event_id,
          idempotency_key: `housekeeping_line:${source_event_id}:out_of_sop`,
          cleaning_task_id: transitionResult.taskId || focusedTask?.id || null,
          housekeeper_id: housekeeper.id,
          room_id: focusedTask?.room_id || null,
          booking_id: focusedTask?.booking_id || null,
          issue_family: "housekeeping_out_of_sop",
          issue_subtype: classifyHousekeepingUnknown(text, true),
          severity: classifyHousekeepingSeverity(text),
          latest_evidence_text: text,
          requires_internal_ops: true,
          requires_owner: true,
        };

        return jsonResponse({
          ok: true,
          action: "rejected",
          housekeeping_reply: {
            text:
              "รับเรื่องแล้วค่ะ ระบบกำลังแจ้ง Internal Ops และเจ้าของให้ตรวจสอบทันทีค่ะ",
          },
          internal_notification: null,
          guest_draft_request: null,
          incident_candidate: incidentCandidate,
          evidence: transitionResult,
        });
      }

      const taskDetails = await fetchTaskAndRoom(
        supabase,
        transitionResult.taskId,
      );
      if ("error" in taskDetails) {
        return jsonResponse({
          ok: false,
          error: taskDetails.error,
          message: taskDetails.message,
          housekeeping_reply: {
            text:
              "ขออภัยค่ะ ระบบอ่านรายละเอียดงานไม่สำเร็จ กรุณาแจ้ง Internal Ops ตรวจสอบค่ะ",
          },
          internal_notification: {
            text:
              `Housekeeping handler error: ${taskDetails.error} (${taskDetails.message})`,
          },
          guest_draft_request: null,
          evidence: {
            source_event_id,
            task_id: transitionResult.taskId,
            error: taskDetails.error,
          },
        }, 500);
      }
      const { task, roomCode } = taskDetails;
      const operatorName = housekeeper.display_name || "Unknown Operator";
      const { housekeepingText, internalText } = buildSuccessTexts(
        intent,
        roomCode,
        task,
        operatorName,
      );

      const qr = await buildQuickReplies(supabase, task, expectedSecret);

      return jsonResponse({
        ok: true,
        action: intent.action,
        housekeeping_reply: {
          text: housekeepingText,
          quickReply: qr,
        },
        internal_notification: internalText ? { text: internalText } : null,
        guest_draft_request: null,
        evidence: transitionResult,
      });
    } catch (err) {
      return jsonResponse({
        ok: false,
        error: "server_error",
        message: err instanceof Error ? err.message : String(err),
      }, 500);
    }
  };
}

const defaultHandler = createHousekeepingHandler();

if (import.meta.main) {
  const port = Number(Deno.env.get("PORT") || 8000);
  Deno.serve({ port }, defaultHandler);
}

export default defaultHandler;
