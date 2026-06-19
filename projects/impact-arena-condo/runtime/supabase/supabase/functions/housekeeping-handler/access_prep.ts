export type HousekeepingTaskKind = "cleaning" | "access_prep";

export type TransitionResult =
  | {
    ok: true;
    action: string;
    taskId: string;
    previousState: string | null;
    newState: string;
    replayed?: boolean;
    [key: string]: unknown;
  }
  | {
    ok: false;
    error: string;
    message: string;
    taskId?: string;
    required_capability?: string;
    [key: string]: unknown;
  };

export type AccessPrepTaskInput = {
  task_key: string;
  booking_id: string;
  room_id?: string | null;
  internal_ops_case_id?: string | null;
  assigned_housekeeper_id?: string | null;
  owner_admin_user_id?: string | null;
  priority?: "urgent" | "high" | "normal";
  key_custody?: "with_owner" | "with_operator" | "placed_in_room" | "unknown";
  capabilities_required?: Record<string, boolean>;
  scheduled_for: string;
  due_at?: string | null;
  ack_due_at?: string | null;
  instructions?: string | null;
  notes?: string | null;
  source?: "checkin_schedule" | "internal_ops" | "owner" | "test";
};

export type MergeAccessPrepTaskResult =
  | {
    ok: true;
    taskId: string;
    taskKey: string;
    created: boolean;
    merged: boolean;
    status: string;
    replayed?: boolean;
  }
  | { ok: false; error: string; message: string; taskId?: string };

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function invalidSourceEventId(taskId?: string): TransitionResult {
  return {
    ok: false,
    error: "invalid_source_event_id",
    message: "A real source event id is required",
    ...(taskId ? { taskId } : {}),
  };
}

function invalidMergeSourceEventId(): MergeAccessPrepTaskResult {
  return {
    ok: false,
    error: "invalid_source_event_id",
    message: "A real source event id is required",
  };
}

export async function handleAccessPrepTransition(
  supabase: any,
  input: {
    taskId: string;
    housekeeperId: string;
    action: string;
    sourceEventId: string;
    payload?: Record<string, unknown>;
  },
): Promise<TransitionResult> {
  if (!input.sourceEventId || !UUID_RE.test(input.sourceEventId)) {
    return invalidSourceEventId(input.taskId);
  }

  const { data, error } = await supabase.rpc("apply_access_prep_task_action", {
    p_task_id: input.taskId,
    p_housekeeper_id: input.housekeeperId,
    p_action: input.action,
    p_source_event_id: input.sourceEventId,
    p_payload: input.payload ?? {},
  });

  if (error) {
    return {
      ok: false,
      error: "database_error",
      message: "Access Prep action could not be committed",
      taskId: input.taskId,
    };
  }
  if (!data || typeof data.ok !== "boolean") {
    return {
      ok: false,
      error: "invalid_state_result",
      message: "Access Prep state service returned an invalid result",
      taskId: input.taskId,
    };
  }
  return data as TransitionResult;
}

export async function createOrMergeAccessPrepTask(
  supabase: any,
  task: AccessPrepTaskInput,
  sourceEventId?: string | null,
): Promise<MergeAccessPrepTaskResult> {
  if (!sourceEventId || !UUID_RE.test(sourceEventId)) {
    return invalidMergeSourceEventId();
  }
  if (
    !task.task_key.trim() ||
    !UUID_RE.test(task.booking_id) ||
    !task.scheduled_for.trim()
  ) {
    return {
      ok: false,
      error: "invalid_task_input",
      message: "A task key, booking id, and scheduled time are required",
    };
  }

  const { data, error } = await supabase.rpc("merge_access_prep_task", {
    p_task: task,
    p_source_event_id: sourceEventId,
  });

  if (error) {
    return {
      ok: false,
      error: "database_error",
      message: "Access Prep task could not be created or merged",
    };
  }
  if (!data || data.ok !== true) {
    return {
      ok: false,
      error: "invalid_state_result",
      message: "Access Prep merge service returned an invalid result",
    };
  }
  return data as MergeAccessPrepTaskResult;
}

export async function overrideHousekeepingTask(
  supabase: any,
  input: {
    taskKind: HousekeepingTaskKind;
    taskId: string;
    adminUserId: string;
    reason: string;
    sourceEventId: string;
  },
): Promise<TransitionResult> {
  if (!input.sourceEventId || !UUID_RE.test(input.sourceEventId)) {
    return invalidSourceEventId(input.taskId);
  }
  if (!input.reason.trim()) {
    return {
      ok: false,
      error: "override_reason_required",
      message: "An override reason is required",
      taskId: input.taskId,
    };
  }

  const { data, error } = await supabase.rpc("override_housekeeping_task", {
    p_task_kind: input.taskKind,
    p_task_id: input.taskId,
    p_admin_user_id: input.adminUserId,
    p_reason: input.reason,
    p_source_event_id: input.sourceEventId,
  });

  if (error) {
    return {
      ok: false,
      error: "database_error",
      message: "Housekeeping override could not be committed",
      taskId: input.taskId,
    };
  }
  if (!data || typeof data.ok !== "boolean") {
    return {
      ok: false,
      error: "invalid_state_result",
      message: "Housekeeping override service returned an invalid result",
      taskId: input.taskId,
    };
  }
  return data as TransitionResult;
}
