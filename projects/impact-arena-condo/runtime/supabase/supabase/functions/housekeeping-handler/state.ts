import { HousekeepingIntent } from "./commands.ts";

export type TransitionResult =
  | {
    ok: true;
    action: string;
    taskId: string;
    previousState: string;
    newState: string;
    replayed?: boolean;
  }
  | { ok: false; error: string; message: string; taskId?: string };

export type CleaningTaskInput = {
  task_key: string;
  room_id: string;
  booking_id?: string | null;
  internal_ops_case_id?: string | null;
  task_type?: "turnover_cleaning" | "room_prep" | "inspection";
  priority?: "urgent" | "high" | "normal";
  assigned_housekeeper_id?: string | null;
  planned_start_at?: string | null;
  due_at?: string | null;
  instructions?: string | null;
  source?: "checkout" | "internal_ops" | "concierge" | "test";
};

export type MergeTaskResult =
  | {
    ok: true;
    taskId: string;
    taskKey: string;
    created: boolean;
    merged: boolean;
    status: string;
  }
  | { ok: false; error: string; message: string };

const TERMINAL_STATUSES = ["completed", "canceled", "delivery_failed"];
const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ACCESS_PREP_ACTIONS = ["mark_key_placed", "mark_room_open"] as const;

function failure(
  error: string,
  message: string,
  taskId?: string,
): TransitionResult {
  return { ok: false, error, message, ...(taskId ? { taskId } : {}) };
}

function intentPayload(intent: HousekeepingIntent): Record<string, unknown> {
  switch (intent.action) {
    case "mark_item_missing":
    case "restore_item":
      return { action: intent.action, item: intent.item };
    case "report_problem":
      return { action: intent.action, problem: intent.problem };
    case "add_note":
      return { action: intent.action, note: intent.note };
    default:
      return { action: intent.action };
  }
}

function replayResult(event: any, action: string): TransitionResult {
  const stored = event?.payload?.result;
  if (stored && typeof stored.ok === "boolean") {
    return stored.ok ? { ...stored, replayed: true } : stored;
  }
  return {
    ok: true,
    action,
    taskId: event.cleaning_task_id,
    previousState: event.previous_state,
    newState: event.new_state,
    replayed: true,
  };
}

async function resolveLegacyAccessCapabilityDenial(
  supabase: any,
  housekeeperId: string,
  action: "mark_key_placed" | "mark_room_open",
): Promise<TransitionResult | null> {
  const requiredCapability = action === "mark_key_placed"
    ? "can_place_key"
    : "can_open_room";
  const { data: focus, error: focusError } = await supabase
    .from("housekeeper_task_focus")
    .select("focused_cleaning_task_id,focus_type")
    .eq("housekeeper_id", housekeeperId)
    .maybeSingle();

  if (focusError) {
    return failure("database_error", "Unable to read Housekeeping focus");
  }
  if (focus?.focus_type !== "cleaning" || !focus.focused_cleaning_task_id) {
    return null;
  }

  const { data: task, error: taskError } = await supabase
    .from("cleaning_tasks")
    .select("id,assigned_housekeeper_id,capabilities")
    .eq("id", focus.focused_cleaning_task_id)
    .maybeSingle();

  if (taskError) {
    return failure(
      "database_error",
      "Unable to validate legacy Access Prep capability",
    );
  }
  if (
    !task ||
    task.assigned_housekeeper_id !== housekeeperId ||
    task.capabilities?.[requiredCapability] !== false
  ) {
    return null;
  }

  return {
    ok: false,
    error: "capability_denied",
    message: "Housekeeper lacks required Access Prep capability",
    required_capability: requiredCapability,
    taskId: task.id,
  } as TransitionResult;
}

async function resolveFocusedTask(
  supabase: any,
  housekeeperId: string,
  intent: HousekeepingIntent,
): Promise<{ taskId?: string; error?: TransitionResult }> {
  const { data: focus, error: focusError } = await supabase
    .from("housekeeper_task_focus")
    .select("focused_cleaning_task_id,focus_type")
    .eq("housekeeper_id", housekeeperId)
    .maybeSingle();

  if (focusError) {
    return {
      error: failure("database_error", "Unable to read Housekeeping focus"),
    };
  }

  if (focus?.focus_type === "cleaning" && focus.focused_cleaning_task_id) {
    const { data: focusedTask, error: focusedError } = await supabase
      .from("cleaning_tasks")
      .select("id,status,assigned_housekeeper_id")
      .eq("id", focus.focused_cleaning_task_id)
      .maybeSingle();

    if (focusedError) {
      return {
        error: failure("database_error", "Unable to validate focused task"),
      };
    }

    if (
      focusedTask &&
      focusedTask.assigned_housekeeper_id === housekeeperId &&
      !TERMINAL_STATUSES.includes(focusedTask.status)
    ) {
      return { taskId: focusedTask.id };
    }
  }

  const { data: openTasks, error: openError } = await supabase
    .from("cleaning_tasks")
    .select("id,status")
    .eq("assigned_housekeeper_id", housekeeperId)
    .not("status", "in", `(${TERMINAL_STATUSES.join(",")})`);

  if (openError) {
    return {
      error: failure("database_error", "Unable to resolve assigned tasks"),
    };
  }
  if (!openTasks || openTasks.length === 0) {
    return {
      error: failure("no_task_assigned", "No open cleaning tasks assigned"),
    };
  }
  if (openTasks.length > 1) {
    return {
      error: failure(
        "ambiguous_target",
        "Ambiguous target: housekeeper has multiple open tasks",
      ),
    };
  }

  const taskId = openTasks[0].id;
  const { error: saveFocusError } = await supabase
    .from("housekeeper_task_focus")
    .upsert({
      housekeeper_id: housekeeperId,
      focused_cleaning_task_id: taskId,
      focused_field_assistance_task_id: null,
      focus_type: "cleaning",
      last_command: intent.action,
      updated_at: new Date().toISOString(),
    });

  if (saveFocusError) {
    return {
      error: failure("database_error", "Unable to save Housekeeping focus"),
    };
  }
  return { taskId };
}

export async function handleStateTransition(
  supabase: any,
  lineUserId: string,
  intent: HousekeepingIntent,
  sourceEventId?: string | null,
  overrideTaskId?: string | null,
): Promise<TransitionResult> {
  if (!sourceEventId || !UUID_RE.test(sourceEventId)) {
    return failure(
      "invalid_source_event_id",
      "A real webhook source event id is required",
    );
  }

  const { data: housekeeper, error: housekeeperError } = await supabase
    .from("housekeepers")
    .select("id,status,active")
    .eq("line_user_id", lineUserId)
    .maybeSingle();

  if (housekeeperError) {
    return failure("database_error", "Unable to read housekeeper profile");
  }
  if (
    !housekeeper ||
    housekeeper.status !== "active" ||
    housekeeper.active === false
  ) {
    return failure(
      "housekeeper_not_found",
      "Active housekeeper profile not found",
    );
  }

  if (ACCESS_PREP_ACTIONS.includes(intent.action as (typeof ACCESS_PREP_ACTIONS)[number])) {
    const denial = await resolveLegacyAccessCapabilityDenial(
      supabase,
      housekeeper.id,
      intent.action as "mark_key_placed" | "mark_room_open",
    );
    if (denial) return denial;
    return failure(
      "access_prep_required",
      "Access Prep commands must use the Access Prep state service",
    );
  }

  const { data: existingEvent, error: replayError } = await supabase
    .from("cleaning_task_events")
    .select("cleaning_task_id,previous_state,new_state,payload")
    .eq("source_event_id", sourceEventId)
    .maybeSingle();

  if (replayError) {
    return failure("database_error", "Unable to verify event idempotency");
  }
  if (existingEvent) {
    return replayResult(existingEvent, intent.action);
  }

  let resolvedTaskId: string;
  if (overrideTaskId && UUID_RE.test(overrideTaskId)) {
    const { data: task, error: taskError } = await supabase
      .from("cleaning_tasks")
      .select("id,assigned_housekeeper_id,status")
      .eq("id", overrideTaskId)
      .maybeSingle();

    if (taskError) {
      return failure("database_error", "Unable to validate overridden task");
    }
    if (!task) {
      return failure("task_not_found", "Cleaning task not found");
    }
    if (task.assigned_housekeeper_id !== housekeeper.id) {
      return failure("unauthorized", "Housekeeper is not assigned to this task");
    }
    resolvedTaskId = task.id;

    const { error: saveFocusError } = await supabase
      .from("housekeeper_task_focus")
      .upsert({
        housekeeper_id: housekeeper.id,
        focused_cleaning_task_id: resolvedTaskId,
        focused_field_assistance_task_id: null,
        focus_type: "cleaning",
        last_command: intent.action,
        updated_at: new Date().toISOString(),
      });
    if (saveFocusError) {
      return failure("database_error", "Unable to update housekeeper focus");
    }
  } else {
    const resolved = await resolveFocusedTask(
      supabase,
      housekeeper.id,
      intent,
    );
    if (resolved.error) return resolved.error;
    resolvedTaskId = resolved.taskId!;
  }

  const { data, error } = await supabase.rpc(
    "apply_housekeeping_task_action",
    {
      p_task_id: resolvedTaskId,
      p_housekeeper_id: housekeeper.id,
      p_action: intent.action,
      p_source_event_id: sourceEventId,
      p_payload: intentPayload(intent),
    },
  );

  if (error) {
    return failure(
      "database_error",
      "Housekeeping action could not be committed",
      resolvedTaskId,
    );
  }
  if (!data || typeof data.ok !== "boolean") {
    return failure(
      "invalid_state_result",
      "State service returned an invalid result",
      resolvedTaskId,
    );
  }
  return data as TransitionResult;
}

export async function createOrMergeCleaningTask(
  supabase: any,
  task: CleaningTaskInput,
  sourceEventId?: string | null,
): Promise<MergeTaskResult> {
  if (!sourceEventId || !UUID_RE.test(sourceEventId)) {
    return {
      ok: false,
      error: "invalid_source_event_id",
      message: "A real source event id is required",
    };
  }
  if (!task.task_key.trim() || !UUID_RE.test(task.room_id)) {
    return {
      ok: false,
      error: "invalid_task_input",
      message: "A task key and valid room id are required",
    };
  }

  const { data, error } = await supabase.rpc(
    "merge_housekeeping_cleaning_task",
    {
      p_task: task,
      p_source_event_id: sourceEventId,
    },
  );

  if (error) {
    return {
      ok: false,
      error: "database_error",
      message: "Cleaning task could not be created or merged",
    };
  }
  if (!data || data.ok !== true) {
    return {
      ok: false,
      error: "invalid_state_result",
      message: "Task merge service returned an invalid result",
    };
  }
  return data as MergeTaskResult;
}
