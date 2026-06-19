export type LineFlexMessage = {
  type: "flex";
  altText: string;
  contents: Record<string, unknown>;
};

export type QueueTaskCard = {
  task_id: string;
  task_kind: "cleaning" | "access_prep";
  room_code?: string | null;
  guest_name?: string | null;
  guest_phone?: string | null;
  reservation_number?: string | null;
  check_in_date?: string | null;
  priority?: "urgent" | "high" | "normal" | string | null;
  status?: string | null;
  due_at?: string | null;
  scheduled_for?: string | null;
  owner_label?: string | null;
  missing_items?: string[] | null;
  linked_task_kind?: "cleaning" | "access_prep" | string | null;
  linked_task_status?: string | null;
  has_open_blocker?: boolean | null;
  claimable?: boolean | null;
  instructions?: string | null;
  blocker_reason?: string | null;
};

export type QueuePage = {
  view: "today" | "all";
  items: QueueTaskCard[];
  next_cursor?: Record<string, unknown> | null;
  previous_cursor?: Record<string, unknown> | null;
};

export type TaskDetail = QueueTaskCard;
export type FocusedTask = Pick<
  QueueTaskCard,
  "task_id" | "task_kind" | "room_code" | "status"
>;

type FlexBox = Record<string, unknown>;

const STATUS_COLORS: Record<string, string> = {
  urgent: "#D92D20",
  high: "#F79009",
  normal: "#12B76A",
  default: "#667085",
};

const TASK_KIND_LABELS: Record<string, string> = {
  cleaning: "ทำความสะอาด",
  access_prep: "Access Prep",
};

const PROBLEM_CATEGORIES = [
  ["water", "ไม่ได้ใส่น้ำ"],
  ["soap", "ไม่ได้ใส่สบู่"],
  ["towels", "ไม่ได้ใส่ผ้าขนหนู"],
  ["damaged_or_lost", "ของเสีย/ของหาย"],
  ["other", "อื่นๆ"],
] as const;

function base64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(
    /=+$/g,
    "",
  );
}

async function signPayload(payload: string, secret: string): Promise<string> {
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

async function signedPostback(
  params: Record<string, string>,
  secret: string,
): Promise<string> {
  const searchParams = new URLSearchParams(params);
  const payload = searchParams.toString();
  searchParams.set("sig", await signPayload(payload, secret));
  return searchParams.toString();
}

function text(value: string, extra: Record<string, unknown> = {}): FlexBox {
  return { type: "text", text: value, wrap: true, ...extra };
}

function statusColor(task: QueueTaskCard): string {
  if (task.has_open_blocker || task.priority === "urgent") {
    return STATUS_COLORS.urgent;
  }
  if (task.priority === "high" || task.status === "no_ack") {
    return STATUS_COLORS.high;
  }
  if (
    task.status === "acknowledged" ||
    task.status === "in_progress" ||
    task.status === "completed" ||
    task.status === "done"
  ) {
    return STATUS_COLORS.normal;
  }
  return STATUS_COLORS.default;
}

function priorityLabel(priority?: string | null): string {
  if (priority === "urgent") return "เร่งด่วน";
  if (priority === "high") return "ด่วน";
  return "ปกติ";
}

function shortGuestName(name?: string | null): string | null {
  const cleaned = name?.trim();
  if (!cleaned) return null;
  return cleaned.split(/\s+/u)[0].slice(0, 24);
}

function taskLabel(kind: string): string {
  return TASK_KIND_LABELS[kind] ?? kind;
}

function dependencyLine(task: QueueTaskCard): string | null {
  if (!task.linked_task_kind || !task.linked_task_status) return null;
  return `${taskLabel(task.linked_task_kind)}: ${task.linked_task_status}`;
}

function statusLine(task: QueueTaskCard): string {
  const canonical = task.task_kind === "cleaning" ? "Cleaning" : "Access Prep";
  return `${canonical}: ${task.status || "unknown"}`;
}

function linkedStatusColor(status?: string | null): string {
  if (
    ["pending_dispatch", "sent", "waiting_ack", "no_ack"].includes(status ?? "")
  ) {
    return STATUS_COLORS.high;
  }
  if (
    ["acknowledged", "in_progress", "done", "completed"].includes(status ?? "")
  ) {
    return STATUS_COLORS.normal;
  }
  return STATUS_COLORS.default;
}

function missingLine(task: QueueTaskCard): string | null {
  if (!task.missing_items || task.missing_items.length === 0) return null;
  return `ขาด: ${task.missing_items.join(", ")}`;
}

function primaryAction(task: QueueTaskCard): string {
  if (
    ["new", "pending_dispatch", "sent", "waiting_ack", "no_ack"].includes(
      task.status ?? "",
    )
  ) {
    return "acknowledge_task";
  }
  if (task.status === "acknowledged") return "start_task";
  return "complete_cleaning";
}

function primaryLabel(task: QueueTaskCard): string {
  const action = primaryAction(task);
  if (action === "acknowledge_task") return "รับทราบ";
  if (action === "start_task") return "เริ่มงาน";
  return task.task_kind === "access_prep" ? "เตรียมพร้อมแล้ว" : "เสร็จงาน";
}

async function taskPostback(
  task: QueueTaskCard | FocusedTask,
  action: string,
  secret: string,
  extra: Record<string, string> = {},
): Promise<string> {
  return await signedPostback({
    action,
    task_id: task.task_id,
    task_kind: task.task_kind,
    ...extra,
  }, secret);
}

async function cursorPostback(
  view: "today" | "all",
  cursor: Record<string, unknown>,
  secret: string,
): Promise<string> {
  const action = view === "today" ? "show_today" : "show_queue";
  return await signedPostback({
    action,
    cursor: JSON.stringify(cursor),
  }, secret);
}

function button(
  label: string,
  data: string,
  style: "primary" | "secondary" = "secondary",
): FlexBox {
  return {
    type: "button",
    style,
    height: "sm",
    action: {
      type: "postback",
      label,
      displayText: label,
      data,
    },
  };
}

async function buildTaskBubble(
  task: QueueTaskCard,
  secret: string,
  paginationButtons: FlexBox[] = [],
): Promise<FlexBox> {
  const guest = shortGuestName(task.guest_name);
  const detailLines = [
    guest ? `แขก: ${guest}` : null,
    task.check_in_date ? `เช็คอิน: ${task.check_in_date}` : null,
    dependencyLine(task),
    missingLine(task),
    task.blocker_reason ? `ติดขัด: ${task.blocker_reason}` : null,
  ].filter((line): line is string => Boolean(line));

  const footer = [
    button(
      primaryLabel(task),
      await taskPostback(task, primaryAction(task), secret),
      "primary",
    ),
    button("รายละเอียด", await taskPostback(task, "view_details", secret)),
    button("แจ้งปัญหา", await taskPostback(task, "show_problem_menu", secret)),
    ...paginationButtons,
  ];

  return {
    type: "bubble",
    size: "mega",
    body: {
      type: "box",
      layout: "vertical",
      spacing: "sm",
      contents: [
        text(task.room_code || "ไม่ระบุห้อง", {
          weight: "bold",
          size: "xl",
          color: "#101828",
        }),
        text(taskLabel(task.task_kind), {
          weight: "bold",
          size: "sm",
          color: statusColor(task),
        }),
        text(priorityLabel(task.priority), {
          size: "xs",
          color: statusColor(task),
        }),
        text(statusLine(task), {
          size: "xs",
          color: "#667085",
        }),
        ...detailLines.map((line) =>
          text(line, {
            size: "xs",
            color: line === dependencyLine(task)
              ? linkedStatusColor(task.linked_task_status)
              : "#344054",
          })
        ),
      ],
    },
    footer: {
      type: "box",
      layout: "vertical",
      spacing: "sm",
      contents: footer,
    },
  };
}

export async function buildQueueFlexMessage(
  input: QueuePage,
  secret: string,
): Promise<LineFlexMessage> {
  const pageItems = input.items.slice(0, 5);
  const bubbles: FlexBox[] = [];
  for (let index = 0; index < pageItems.length; index += 1) {
    const pagination: FlexBox[] = [];
    if (index === pageItems.length - 1) {
      if (input.previous_cursor) {
        pagination.push(
          button(
            "ก่อนหน้า",
            await cursorPostback(input.view, input.previous_cursor, secret),
          ),
        );
      }
      if (input.next_cursor) {
        pagination.push(
          button(
            "ถัดไป",
            await cursorPostback(input.view, input.next_cursor, secret),
          ),
        );
      }
    }
    bubbles.push(await buildTaskBubble(pageItems[index], secret, pagination));
  }

  return {
    type: "flex",
    altText: `คิวงานแม่บ้าน ${pageItems.length} งาน`,
    contents: {
      type: "carousel",
      contents: bubbles,
    },
  };
}

export async function buildTaskDetailFlexMessage(
  input: TaskDetail,
  secret: string,
): Promise<LineFlexMessage> {
  const bodyLines = [
    text(input.room_code || "ไม่ระบุห้อง", {
      weight: "bold",
      size: "xl",
      color: "#101828",
    }),
    text(taskLabel(input.task_kind), {
      weight: "bold",
      color: statusColor(input),
    }),
    text(statusLine(input), {
      size: "sm",
      color: "#667085",
    }),
  ];
  const linked = dependencyLine(input);
  if (linked) {
    bodyLines.push(text(linked, {
      size: "sm",
      color: linkedStatusColor(input.linked_task_status),
    }));
  }
  const guest = shortGuestName(input.guest_name);
  if (guest) {
    bodyLines.push(text(`แขก: ${guest}`, { size: "sm", color: "#344054" }));
  }
  if (input.instructions) {
    bodyLines.push(text(input.instructions, { size: "sm", color: "#344054" }));
  }
  const missing = missingLine(input);
  if (missing) bodyLines.push(text(missing, { size: "sm", color: "#D92D20" }));

  return {
    type: "flex",
    altText: `รายละเอียดงาน ${input.room_code || ""}`.trim(),
    contents: {
      type: "bubble",
      body: {
        type: "box",
        layout: "vertical",
        spacing: "sm",
        contents: bodyLines,
      },
      footer: {
        type: "box",
        layout: "vertical",
        spacing: "sm",
        contents: [
          button(
            primaryLabel(input),
            await taskPostback(input, primaryAction(input), secret),
            "primary",
          ),
          button(
            "แจ้งปัญหา",
            await taskPostback(input, "show_problem_menu", secret),
          ),
        ],
      },
    },
  };
}

export async function buildProblemMenuFlexMessage(
  input: FocusedTask,
  secret: string,
): Promise<LineFlexMessage> {
  const buttons: FlexBox[] = [];
  for (const [category, label] of PROBLEM_CATEGORIES) {
    buttons.push(
      button(
        label,
        await taskPostback(input, "problem_category", secret, { category }),
      ),
    );
  }
  return {
    type: "flex",
    altText: `แจ้งปัญหาห้อง ${input.room_code || ""}`.trim(),
    contents: {
      type: "bubble",
      body: {
        type: "box",
        layout: "vertical",
        spacing: "sm",
        contents: [
          text(input.room_code || "ไม่ระบุห้อง", {
            weight: "bold",
            size: "xl",
            color: "#101828",
          }),
          text("เลือกหมวดปัญหา", { weight: "bold", color: "#D92D20" }),
        ],
      },
      footer: {
        type: "box",
        layout: "vertical",
        spacing: "sm",
        contents: buttons,
      },
    },
  };
}
