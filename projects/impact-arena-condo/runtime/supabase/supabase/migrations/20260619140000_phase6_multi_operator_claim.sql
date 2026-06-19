-- Phase 6 Task 14: forward-only atomic claim and reassignment focus invalidation.

CREATE OR REPLACE FUNCTION public.claim_housekeeping_task(
  p_task_kind TEXT,
  p_task_id UUID,
  p_housekeeper_id UUID,
  p_source_event_id UUID
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  v_cleaning public.cleaning_tasks%ROWTYPE;
  v_access public.access_prep_tasks%ROWTYPE;
  v_existing_cleaning public.cleaning_task_events%ROWTYPE;
  v_existing_access public.access_prep_task_events%ROWTYPE;
  v_result JSONB;
BEGIN
  IF p_task_kind NOT IN ('cleaning', 'access_prep') THEN
    RAISE EXCEPTION 'unsupported_task_kind' USING ERRCODE = '22023';
  END IF;
  IF p_source_event_id IS NULL THEN
    RAISE EXCEPTION 'source_event_id_required' USING ERRCODE = '22023';
  END IF;

  PERFORM 1
  FROM public.housekeepers
  WHERE id = p_housekeeper_id
    AND status = 'active'
    AND active = true;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'active_housekeeper_required' USING ERRCODE = '42501';
  END IF;

  PERFORM pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('housekeeping_claim:' || p_source_event_id::TEXT, 0)
  );

  IF p_task_kind = 'cleaning' THEN
    SELECT * INTO v_existing_cleaning
    FROM public.cleaning_task_events
    WHERE source_event_id = p_source_event_id;
    IF FOUND THEN
      RETURN COALESCE(
        v_existing_cleaning.payload -> 'result',
        jsonb_build_object(
          'ok', true,
          'action', 'claimed',
          'taskId', v_existing_cleaning.cleaning_task_id,
          'taskKind', 'cleaning',
          'replayed', true
        )
      ) || jsonb_build_object('replayed', true);
    END IF;

    SELECT * INTO v_cleaning
    FROM public.cleaning_tasks
    WHERE id = p_task_id
    FOR UPDATE;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'task_not_found' USING ERRCODE = 'P0002';
    END IF;
    IF v_cleaning.assigned_housekeeper_id IS NOT NULL
      AND v_cleaning.assigned_housekeeper_id <> p_housekeeper_id
    THEN
      RETURN jsonb_build_object(
        'ok', false,
        'error', 'already_claimed',
        'taskId', v_cleaning.id,
        'taskKind', 'cleaning',
        'previousState', v_cleaning.status,
        'newState', v_cleaning.status
      );
    END IF;
    IF v_cleaning.status IN ('completed', 'canceled', 'delivery_failed') THEN
      RETURN jsonb_build_object(
        'ok', false,
        'error', 'terminal_task',
        'taskId', v_cleaning.id,
        'taskKind', 'cleaning',
        'previousState', v_cleaning.status,
        'newState', v_cleaning.status
      );
    END IF;

    UPDATE public.cleaning_tasks
    SET assigned_housekeeper_id = p_housekeeper_id,
        status = CASE WHEN status = 'pending_dispatch' THEN 'waiting_ack' ELSE status END,
        updated_at = now()
    WHERE id = v_cleaning.id;

    v_result := public.apply_housekeeping_task_action(
      v_cleaning.id,
      p_housekeeper_id,
      'acknowledge_task',
      p_source_event_id,
      '{}'::JSONB
    );
  ELSE
    SELECT * INTO v_existing_access
    FROM public.access_prep_task_events
    WHERE source_event_id = p_source_event_id;
    IF FOUND THEN
      RETURN COALESCE(
        v_existing_access.payload -> 'result',
        jsonb_build_object(
          'ok', true,
          'action', 'claimed',
          'taskId', v_existing_access.access_prep_task_id,
          'taskKind', 'access_prep',
          'replayed', true
        )
      ) || jsonb_build_object('replayed', true);
    END IF;

    SELECT * INTO v_access
    FROM public.access_prep_tasks
    WHERE id = p_task_id
    FOR UPDATE;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'task_not_found' USING ERRCODE = 'P0002';
    END IF;
    IF v_access.assigned_housekeeper_id IS NOT NULL
      AND v_access.assigned_housekeeper_id <> p_housekeeper_id
    THEN
      RETURN jsonb_build_object(
        'ok', false,
        'error', 'already_claimed',
        'taskId', v_access.id,
        'taskKind', 'access_prep',
        'previousState', v_access.status,
        'newState', v_access.status
      );
    END IF;
    IF v_access.status IN ('done', 'canceled', 'delivery_failed') THEN
      RETURN jsonb_build_object(
        'ok', false,
        'error', 'terminal_task',
        'taskId', v_access.id,
        'taskKind', 'access_prep',
        'previousState', v_access.status,
        'newState', v_access.status
      );
    END IF;

    UPDATE public.access_prep_tasks
    SET assigned_housekeeper_id = p_housekeeper_id,
        status = CASE WHEN status = 'new' THEN 'sent' ELSE status END,
        updated_at = now()
    WHERE id = v_access.id;

    v_result := public.apply_access_prep_task_action(
      v_access.id,
      p_housekeeper_id,
      'acknowledge_task',
      p_source_event_id,
      '{}'::JSONB
    );
  END IF;

  IF COALESCE((v_result ->> 'ok')::BOOLEAN, false) THEN
    INSERT INTO public.housekeeper_task_focus (
      housekeeper_id,
      focused_cleaning_task_id,
      focused_field_assistance_task_id,
      focused_access_prep_task_id,
      focus_type,
      last_command,
      updated_at
    )
    VALUES (
      p_housekeeper_id,
      CASE WHEN p_task_kind = 'cleaning' THEN p_task_id ELSE NULL END,
      NULL,
      CASE WHEN p_task_kind = 'access_prep' THEN p_task_id ELSE NULL END,
      p_task_kind,
      'claim_housekeeping_task',
      now()
    )
    ON CONFLICT (housekeeper_id) DO UPDATE SET
      focused_cleaning_task_id = EXCLUDED.focused_cleaning_task_id,
      focused_field_assistance_task_id = NULL,
      focused_access_prep_task_id = EXCLUDED.focused_access_prep_task_id,
      focus_type = EXCLUDED.focus_type,
      last_command = 'claim_housekeeping_task',
      updated_at = now();
  END IF;

  RETURN v_result || jsonb_build_object(
    'action', 'claimed',
    'taskKind', p_task_kind
  );
END;
$$;

REVOKE ALL ON FUNCTION public.claim_housekeeping_task(TEXT, UUID, UUID, UUID)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.claim_housekeeping_task(TEXT, UUID, UUID, UUID)
TO service_role, postgres;

CREATE OR REPLACE FUNCTION public.invalidate_reassigned_housekeeping_focus()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
BEGIN
  IF OLD.assigned_housekeeper_id IS NOT NULL
    AND OLD.assigned_housekeeper_id IS DISTINCT FROM NEW.assigned_housekeeper_id
  THEN
    UPDATE public.housekeeper_task_focus
    SET focused_cleaning_task_id = NULL,
        focused_field_assistance_task_id = NULL,
        focused_access_prep_task_id = NULL,
        focus_type = NULL,
        last_command = 'assignment_changed',
        updated_at = now()
    WHERE housekeeper_id = OLD.assigned_housekeeper_id
      AND (
        (TG_TABLE_NAME = 'cleaning_tasks' AND focused_cleaning_task_id = OLD.id)
        OR
        (TG_TABLE_NAME = 'access_prep_tasks' AND focused_access_prep_task_id = OLD.id)
      );
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS cleaning_task_assignment_focus_invalidation
ON public.cleaning_tasks;
CREATE TRIGGER cleaning_task_assignment_focus_invalidation
AFTER UPDATE OF assigned_housekeeper_id ON public.cleaning_tasks
FOR EACH ROW
EXECUTE FUNCTION public.invalidate_reassigned_housekeeping_focus();

DROP TRIGGER IF EXISTS access_prep_assignment_focus_invalidation
ON public.access_prep_tasks;
CREATE TRIGGER access_prep_assignment_focus_invalidation
AFTER UPDATE OF assigned_housekeeper_id ON public.access_prep_tasks
FOR EACH ROW
EXECUTE FUNCTION public.invalidate_reassigned_housekeeping_focus();
