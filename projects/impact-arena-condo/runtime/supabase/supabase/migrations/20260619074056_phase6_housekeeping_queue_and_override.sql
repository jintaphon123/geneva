-- Phase 6 Task 2: transactional Access Prep lifecycle and admin override.

CREATE OR REPLACE FUNCTION public.merge_access_prep_task(
  p_task JSONB,
  p_source_event_id UUID
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  v_task public.access_prep_tasks%ROWTYPE;
  v_existing_event public.access_prep_task_events%ROWTYPE;
  v_result JSONB;
  v_created BOOLEAN := false;
  v_previous_state TEXT;
BEGIN
  IF p_source_event_id IS NULL THEN
    RAISE EXCEPTION 'source_event_id_required' USING ERRCODE = '22023';
  END IF;
  IF NULLIF(BTRIM(p_task ->> 'task_key'), '') IS NULL THEN
    RAISE EXCEPTION 'task_key_required' USING ERRCODE = '22023';
  END IF;
  IF NULLIF(BTRIM(p_task ->> 'booking_id'), '') IS NULL THEN
    RAISE EXCEPTION 'booking_id_required' USING ERRCODE = '22023';
  END IF;
  IF NULLIF(BTRIM(p_task ->> 'scheduled_for'), '') IS NULL THEN
    RAISE EXCEPTION 'scheduled_for_required' USING ERRCODE = '22023';
  END IF;

  SELECT * INTO v_existing_event
  FROM public.access_prep_task_events
  WHERE source_event_id = p_source_event_id;

  IF FOUND THEN
    RETURN COALESCE(v_existing_event.payload -> 'result', jsonb_build_object(
      'ok', true,
      'taskId', v_existing_event.access_prep_task_id,
      'replayed', true
    )) || jsonb_build_object('replayed', true);
  END IF;

  SELECT * INTO v_task
  FROM public.access_prep_tasks
  WHERE task_key = p_task ->> 'task_key'
  FOR UPDATE;

  IF FOUND THEN
    v_previous_state := v_task.status;
    IF v_task.status IN ('done', 'canceled', 'delivery_failed') THEN
      v_result := jsonb_build_object(
        'ok', false,
        'error', 'task_terminal',
        'message', 'Access Prep task is terminal',
        'taskId', v_task.id,
        'status', v_task.status
      );
    ELSE
      UPDATE public.access_prep_tasks
      SET priority = COALESCE(NULLIF(p_task ->> 'priority', ''), priority),
          room_id = COALESCE((p_task ->> 'room_id')::UUID, room_id),
          internal_ops_case_id = COALESCE(
            (p_task ->> 'internal_ops_case_id')::UUID,
            internal_ops_case_id
          ),
          assigned_housekeeper_id = COALESCE(
            (p_task ->> 'assigned_housekeeper_id')::UUID,
            assigned_housekeeper_id
          ),
          owner_admin_user_id = COALESCE(
            (p_task ->> 'owner_admin_user_id')::UUID,
            owner_admin_user_id
          ),
          key_custody = COALESCE(NULLIF(p_task ->> 'key_custody', ''), key_custody),
          capabilities_required = COALESCE(
            NULLIF(p_task -> 'capabilities_required', 'null'::JSONB),
            capabilities_required
          ),
          scheduled_for = COALESCE((p_task ->> 'scheduled_for')::TIMESTAMPTZ, scheduled_for),
          due_at = COALESCE((p_task ->> 'due_at')::TIMESTAMPTZ, due_at),
          ack_due_at = COALESCE((p_task ->> 'ack_due_at')::TIMESTAMPTZ, ack_due_at),
          instructions = COALESCE(NULLIF(p_task ->> 'instructions', ''), instructions),
          notes = COALESCE(NULLIF(p_task ->> 'notes', ''), notes),
          updated_at = now()
      WHERE id = v_task.id
      RETURNING * INTO v_task;
    END IF;
  ELSE
    INSERT INTO public.access_prep_tasks (
      task_key, booking_id, room_id, internal_ops_case_id,
      assigned_housekeeper_id, owner_admin_user_id, priority,
      key_custody, capabilities_required, scheduled_for, due_at, ack_due_at,
      instructions, notes
    )
    VALUES (
      p_task ->> 'task_key',
      (p_task ->> 'booking_id')::UUID,
      (p_task ->> 'room_id')::UUID,
      (p_task ->> 'internal_ops_case_id')::UUID,
      (p_task ->> 'assigned_housekeeper_id')::UUID,
      (p_task ->> 'owner_admin_user_id')::UUID,
      COALESCE(NULLIF(p_task ->> 'priority', ''), 'normal'),
      COALESCE(NULLIF(p_task ->> 'key_custody', ''), 'unknown'),
      COALESCE(p_task -> 'capabilities_required', '{"can_place_key":true,"can_open_room":true}'::JSONB),
      (p_task ->> 'scheduled_for')::TIMESTAMPTZ,
      (p_task ->> 'due_at')::TIMESTAMPTZ,
      (p_task ->> 'ack_due_at')::TIMESTAMPTZ,
      NULLIF(p_task ->> 'instructions', ''),
      NULLIF(p_task ->> 'notes', '')
    )
    RETURNING * INTO v_task;
    v_created := true;
    v_previous_state := NULL;
  END IF;

  IF v_result IS NULL THEN
    v_result := jsonb_build_object(
      'ok', true,
      'taskId', v_task.id,
      'taskKey', v_task.task_key,
      'created', v_created,
      'merged', NOT v_created,
      'status', v_task.status
    );
  END IF;

  INSERT INTO public.access_prep_task_events (
    access_prep_task_id, housekeeper_id, admin_user_id, event_type,
    previous_state, new_state, source_event_id, payload
  )
  VALUES (
    v_task.id,
    v_task.assigned_housekeeper_id,
    v_task.owner_admin_user_id,
    CASE WHEN v_created THEN 'task_created' ELSE 'task_merged' END,
    v_previous_state,
    v_task.status,
    p_source_event_id,
    jsonb_build_object('task', p_task, 'result', v_result)
  );

  RETURN v_result;
END;
$$;

REVOKE ALL ON FUNCTION public.merge_access_prep_task(JSONB, UUID)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.merge_access_prep_task(JSONB, UUID)
TO service_role, postgres;

CREATE OR REPLACE FUNCTION public.apply_access_prep_task_action(
  p_task_id UUID,
  p_housekeeper_id UUID,
  p_action TEXT,
  p_source_event_id UUID,
  p_payload JSONB DEFAULT '{}'::JSONB
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  v_task public.access_prep_tasks%ROWTYPE;
  v_existing_event public.access_prep_task_events%ROWTYPE;
  v_access public.booking_access_preparations%ROWTYPE;
  v_previous_state TEXT;
  v_new_state TEXT;
  v_result JSONB;
  v_problem TEXT;
  v_note TEXT;
  v_key_ready BOOLEAN;
  v_room_open_ready BOOLEAN;
BEGIN
  IF p_source_event_id IS NULL THEN
    RAISE EXCEPTION 'source_event_id_required' USING ERRCODE = '22023';
  END IF;

  SELECT * INTO v_existing_event
  FROM public.access_prep_task_events
  WHERE source_event_id = p_source_event_id;

  IF FOUND THEN
    RETURN COALESCE(v_existing_event.payload -> 'result', jsonb_build_object(
      'ok', true,
      'action', p_action,
      'taskId', v_existing_event.access_prep_task_id,
      'previousState', v_existing_event.previous_state,
      'newState', v_existing_event.new_state,
      'replayed', true
    )) || jsonb_build_object('replayed', true);
  END IF;

  SELECT * INTO v_task
  FROM public.access_prep_tasks
  WHERE id = p_task_id
  FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'task_not_found' USING ERRCODE = 'P0002';
  END IF;

  v_previous_state := v_task.status;
  v_new_state := v_previous_state;
  v_problem := NULLIF(BTRIM(p_payload ->> 'problem'), '');
  v_note := NULLIF(BTRIM(p_payload ->> 'note'), '');

  IF v_task.assigned_housekeeper_id IS DISTINCT FROM p_housekeeper_id THEN
    v_result := jsonb_build_object(
      'ok', false,
      'error', 'unauthorized',
      'message', 'Housekeeper is not assigned to this Access Prep task',
      'taskId', v_task.id
    );
  ELSIF p_action = 'dispatch_task' THEN
    IF v_previous_state NOT IN ('new', 'delivery_failed') THEN
      v_result := jsonb_build_object('ok', false, 'error', 'invalid_transition',
        'message', 'Cannot dispatch Access Prep task in status ' || v_previous_state,
        'taskId', v_task.id);
    ELSE
      v_new_state := 'sent';
      UPDATE public.access_prep_tasks
      SET status = v_new_state,
          dispatch_status = 'sent',
          ack_due_at = COALESCE(ack_due_at, now() + interval '30 minutes'),
          updated_at = now()
      WHERE id = v_task.id;
    END IF;
  ELSIF p_action = 'mark_no_ack' THEN
    IF v_previous_state <> 'sent' THEN
      v_result := jsonb_build_object('ok', false, 'error', 'invalid_transition',
        'message', 'Cannot mark no-ack in status ' || v_previous_state,
        'taskId', v_task.id);
    ELSE
      v_new_state := 'no_ack';
      UPDATE public.access_prep_tasks
      SET status = v_new_state, updated_at = now()
      WHERE id = v_task.id;
    END IF;
  ELSIF p_action = 'acknowledge_task' THEN
    IF v_previous_state NOT IN ('sent', 'no_ack') THEN
      v_result := jsonb_build_object('ok', false, 'error', 'invalid_transition',
        'message', 'Cannot acknowledge Access Prep task in status ' || v_previous_state,
        'taskId', v_task.id);
    ELSE
      v_new_state := 'acknowledged';
      UPDATE public.access_prep_tasks
      SET status = v_new_state, acknowledged_at = now(), updated_at = now()
      WHERE id = v_task.id;
    END IF;
  ELSIF p_action = 'start_task' THEN
    IF v_previous_state NOT IN ('acknowledged', 'blocked') THEN
      v_result := jsonb_build_object('ok', false, 'error', 'invalid_transition',
        'message', 'Cannot start Access Prep task in status ' || v_previous_state,
        'taskId', v_task.id);
    ELSE
      v_new_state := 'in_progress';
      UPDATE public.access_prep_tasks
      SET status = v_new_state,
          started_at = COALESCE(started_at, now()),
          blocker_reason = NULL,
          updated_at = now()
      WHERE id = v_task.id;
    END IF;
  ELSIF p_action = 'report_problem' THEN
    IF v_previous_state IN ('done', 'canceled', 'delivery_failed') THEN
      v_result := jsonb_build_object('ok', false, 'error', 'terminal_task',
        'message', 'Access Prep task is terminal', 'taskId', v_task.id);
    ELSIF v_problem IS NULL THEN
      v_result := jsonb_build_object('ok', false, 'error', 'problem_required',
        'message', 'Problem detail is required', 'taskId', v_task.id);
    ELSE
      v_new_state := 'blocked';
      UPDATE public.access_prep_tasks
      SET status = v_new_state, blocker_reason = v_problem, updated_at = now()
      WHERE id = v_task.id;
    END IF;
  ELSIF p_action = 'cancel_task' THEN
    IF v_previous_state IN ('done', 'canceled', 'delivery_failed') THEN
      v_result := jsonb_build_object('ok', false, 'error', 'terminal_task',
        'message', 'Access Prep task is terminal', 'taskId', v_task.id);
    ELSE
      v_new_state := 'canceled';
      UPDATE public.access_prep_tasks
      SET status = v_new_state, updated_at = now()
      WHERE id = v_task.id;
    END IF;
  ELSIF p_action = 'add_note' THEN
    IF v_previous_state IN ('done', 'canceled', 'delivery_failed') THEN
      v_result := jsonb_build_object('ok', false, 'error', 'terminal_task',
        'message', 'Access Prep task is terminal', 'taskId', v_task.id);
    ELSE
      UPDATE public.access_prep_tasks
      SET notes = CONCAT_WS(E'\n', NULLIF(notes, ''), v_note),
          updated_at = now()
      WHERE id = v_task.id;
    END IF;
  ELSIF p_action IN ('mark_key_placed', 'mark_room_open') THEN
    IF v_previous_state = 'blocked' THEN
      v_result := jsonb_build_object('ok', false, 'error', 'task_blocked',
        'message', 'Task is blocked: ' || COALESCE(v_task.blocker_reason, 'unknown'),
        'taskId', v_task.id);
    ELSIF v_previous_state IN ('done', 'canceled', 'delivery_failed') THEN
      v_result := jsonb_build_object('ok', false, 'error', 'terminal_task',
        'message', 'Access Prep task is terminal', 'taskId', v_task.id);
    ELSIF v_previous_state <> 'in_progress' THEN
      v_result := jsonb_build_object('ok', false, 'error', 'invalid_transition',
        'message', 'Cannot update Access Prep evidence in status ' || v_previous_state,
        'taskId', v_task.id);
    ELSIF p_action = 'mark_key_placed'
      AND NOT COALESCE((v_task.capabilities_required ->> 'can_place_key')::BOOLEAN, false)
    THEN
      v_result := jsonb_build_object('ok', false, 'error', 'capability_denied',
        'message', 'Housekeeper lacks required Access Prep capability',
        'required_capability', 'can_place_key', 'taskId', v_task.id);
    ELSIF p_action = 'mark_room_open'
      AND NOT COALESCE((v_task.capabilities_required ->> 'can_open_room')::BOOLEAN, false)
    THEN
      v_result := jsonb_build_object('ok', false, 'error', 'capability_denied',
        'message', 'Housekeeper lacks required Access Prep capability',
        'required_capability', 'can_open_room', 'taskId', v_task.id);
    ELSE
      SELECT * INTO v_access
      FROM public.booking_access_preparations
      WHERE booking_id = v_task.booking_id;

      INSERT INTO public.booking_access_preparations (
        booking_id, room_id, key_placed_in_room, key_placed_at, key_placed_by,
        room_left_unlocked_or_open, room_opened_at, room_opened_by, status, updated_at
      )
      VALUES (
        v_task.booking_id,
        v_task.room_id,
        p_action = 'mark_key_placed' OR COALESCE(v_access.key_placed_in_room, false),
        CASE WHEN p_action = 'mark_key_placed' THEN now() ELSE v_access.key_placed_at END,
        CASE WHEN p_action = 'mark_key_placed' THEN p_housekeeper_id ELSE v_access.key_placed_by END,
        p_action = 'mark_room_open' OR COALESCE(v_access.room_left_unlocked_or_open, false),
        CASE WHEN p_action = 'mark_room_open' THEN now() ELSE v_access.room_opened_at END,
        CASE WHEN p_action = 'mark_room_open' THEN p_housekeeper_id ELSE v_access.room_opened_by END,
        CASE
          WHEN (p_action = 'mark_key_placed' OR COALESCE(v_access.key_placed_in_room, false))
           AND (p_action = 'mark_room_open' OR COALESCE(v_access.room_left_unlocked_or_open, false))
          THEN 'complete'
          ELSE 'partial'
        END,
        now()
      )
      ON CONFLICT (booking_id) DO UPDATE SET
        room_id = EXCLUDED.room_id,
        key_placed_in_room = EXCLUDED.key_placed_in_room,
        key_placed_at = EXCLUDED.key_placed_at,
        key_placed_by = EXCLUDED.key_placed_by,
        room_left_unlocked_or_open = EXCLUDED.room_left_unlocked_or_open,
        room_opened_at = EXCLUDED.room_opened_at,
        room_opened_by = EXCLUDED.room_opened_by,
        status = EXCLUDED.status,
        updated_at = EXCLUDED.updated_at
      RETURNING * INTO v_access;

      IF p_action = 'mark_key_placed' THEN
        UPDATE public.access_prep_tasks
        SET key_custody = 'placed_in_room', updated_at = now()
        WHERE id = v_task.id
        RETURNING * INTO v_task;
      END IF;

      v_key_ready := COALESCE(v_access.key_placed_in_room, false);
      v_room_open_ready := COALESCE(v_access.room_left_unlocked_or_open, false);
      IF v_key_ready AND v_room_open_ready THEN
        v_new_state := 'done';
        UPDATE public.access_prep_tasks
        SET status = v_new_state,
            completed_at = COALESCE(completed_at, now()),
            updated_at = now()
        WHERE id = v_task.id;
      END IF;
    END IF;
  ELSE
    v_result := jsonb_build_object('ok', false, 'error', 'unsupported_action',
      'message', 'Action is not handled by the Access Prep state service',
      'taskId', v_task.id);
  END IF;

  IF v_result IS NULL THEN
    v_result := jsonb_build_object(
      'ok', true,
      'action', p_action,
      'taskId', v_task.id,
      'previousState', v_previous_state,
      'newState', v_new_state
    );
  END IF;

  INSERT INTO public.access_prep_task_events (
    access_prep_task_id, housekeeper_id, event_type,
    previous_state, new_state, source_event_id, payload
  )
  VALUES (
    v_task.id,
    p_housekeeper_id,
    CASE WHEN COALESCE((v_result ->> 'ok')::BOOLEAN, false) THEN p_action ELSE 'rejected' END,
    v_previous_state,
    v_new_state,
    p_source_event_id,
    jsonb_build_object('intent', p_payload, 'result', v_result)
  );

  RETURN v_result;
END;
$$;

REVOKE ALL ON FUNCTION public.apply_access_prep_task_action(UUID, UUID, TEXT, UUID, JSONB)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.apply_access_prep_task_action(UUID, UUID, TEXT, UUID, JSONB)
TO service_role, postgres;

CREATE OR REPLACE FUNCTION public.override_housekeeping_task(
  p_task_kind TEXT,
  p_task_id UUID,
  p_admin_user_id UUID,
  p_reason TEXT,
  p_source_event_id UUID
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  v_access_task public.access_prep_tasks%ROWTYPE;
  v_cleaning_task public.cleaning_tasks%ROWTYPE;
  v_existing_access public.access_prep_task_events%ROWTYPE;
  v_existing_cleaning public.cleaning_task_events%ROWTYPE;
  v_reason TEXT;
  v_result JSONB;
  v_previous_state TEXT;
BEGIN
  IF p_source_event_id IS NULL THEN
    RAISE EXCEPTION 'source_event_id_required' USING ERRCODE = '22023';
  END IF;
  IF p_task_kind NOT IN ('cleaning', 'access_prep') THEN
    RAISE EXCEPTION 'unsupported_task_kind' USING ERRCODE = '22023';
  END IF;
  v_reason := NULLIF(BTRIM(p_reason), '');
  IF v_reason IS NULL THEN
    RAISE EXCEPTION 'override_reason_required' USING ERRCODE = '22023';
  END IF;

  PERFORM 1
  FROM public.admin_users
  WHERE id = p_admin_user_id AND active = true;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'active_admin_required' USING ERRCODE = '42501';
  END IF;

  IF p_task_kind = 'access_prep' THEN
    SELECT * INTO v_existing_access
    FROM public.access_prep_task_events
    WHERE source_event_id = p_source_event_id;

    IF FOUND THEN
      RETURN COALESCE(v_existing_access.payload -> 'result', jsonb_build_object(
        'ok', true,
        'action', 'owner_override',
        'taskId', v_existing_access.access_prep_task_id,
        'previousState', v_existing_access.previous_state,
        'newState', v_existing_access.new_state,
        'replayed', true
      )) || jsonb_build_object('replayed', true);
    END IF;

    SELECT * INTO v_access_task
    FROM public.access_prep_tasks
    WHERE id = p_task_id
    FOR UPDATE;

    IF NOT FOUND THEN
      RAISE EXCEPTION 'task_not_found' USING ERRCODE = 'P0002';
    END IF;

    v_previous_state := v_access_task.status;
    UPDATE public.access_prep_tasks
    SET status = 'done',
        completed_at = COALESCE(completed_at, now()),
        override_reason = v_reason,
        overridden_by = p_admin_user_id,
        overridden_at = now(),
        updated_at = now()
    WHERE id = v_access_task.id
    RETURNING * INTO v_access_task;

    v_result := jsonb_build_object(
      'ok', true,
      'action', 'owner_override',
      'taskId', v_access_task.id,
      'previousState', v_previous_state,
      'newState', v_access_task.status,
      'blockerPreserved', COALESCE(v_access_task.blocker_reason, v_reason)
    );

    INSERT INTO public.access_prep_task_events (
      access_prep_task_id, admin_user_id, event_type,
      previous_state, new_state, source_event_id, payload
    )
    VALUES (
      v_access_task.id,
      p_admin_user_id,
      'owner_override',
      v_previous_state,
      v_access_task.status,
      p_source_event_id,
      jsonb_build_object('reason', v_reason, 'result', v_result)
    );

    RETURN v_result;
  END IF;

  SELECT * INTO v_existing_cleaning
  FROM public.cleaning_task_events
  WHERE source_event_id = p_source_event_id;

  IF FOUND THEN
    RETURN COALESCE(v_existing_cleaning.payload -> 'result', jsonb_build_object(
      'ok', true,
      'action', 'admin_override',
      'taskId', v_existing_cleaning.cleaning_task_id,
      'previousState', v_existing_cleaning.previous_state,
      'newState', v_existing_cleaning.new_state,
      'replayed', true
    )) || jsonb_build_object('replayed', true);
  END IF;

  SELECT * INTO v_cleaning_task
  FROM public.cleaning_tasks
  WHERE id = p_task_id
  FOR UPDATE;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'task_not_found' USING ERRCODE = 'P0002';
  END IF;

  v_previous_state := v_cleaning_task.status;
  UPDATE public.cleaning_tasks
  SET status = 'completed',
      completed_at = COALESCE(completed_at, now()),
      notes = CONCAT_WS(E'\n', NULLIF(notes, ''), 'Admin override: ' || v_reason),
      updated_at = now()
  WHERE id = v_cleaning_task.id
  RETURNING * INTO v_cleaning_task;

  v_result := jsonb_build_object(
    'ok', true,
    'action', 'admin_override',
    'taskId', v_cleaning_task.id,
    'previousState', v_previous_state,
    'newState', v_cleaning_task.status,
    'blockerPreserved', COALESCE(v_cleaning_task.blocker_reason, v_reason)
  );

  INSERT INTO public.cleaning_task_events (
    cleaning_task_id, housekeeper_id, event_type, event_source, source_event_id,
    previous_state, new_state, payload
  )
  VALUES (
    v_cleaning_task.id,
    v_cleaning_task.assigned_housekeeper_id,
    'admin_override',
    'internal_ops',
    p_source_event_id,
    v_previous_state,
    v_cleaning_task.status,
    jsonb_build_object('reason', v_reason, 'result', v_result)
  );

  RETURN v_result;
END;
$$;

REVOKE ALL ON FUNCTION public.override_housekeeping_task(TEXT, UUID, UUID, TEXT, UUID)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.override_housekeeping_task(TEXT, UUID, UUID, TEXT, UUID)
TO service_role, postgres;
