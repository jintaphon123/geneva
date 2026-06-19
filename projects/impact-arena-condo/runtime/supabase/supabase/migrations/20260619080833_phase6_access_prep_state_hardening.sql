-- Phase 6 Task 2 hardening:
-- serialize duplicate source events and merge direct updates into the active
-- Access Prep task for the same booking.

ALTER FUNCTION public.merge_access_prep_task(JSONB, UUID)
  RENAME TO phase6_merge_access_prep_task_impl;
ALTER FUNCTION public.apply_access_prep_task_action(UUID, UUID, TEXT, UUID, JSONB)
  RENAME TO phase6_apply_access_prep_task_action_impl;
ALTER FUNCTION public.override_housekeeping_task(TEXT, UUID, UUID, TEXT, UUID)
  RENAME TO phase6_override_housekeeping_task_impl;

REVOKE ALL ON FUNCTION public.phase6_merge_access_prep_task_impl(JSONB, UUID)
FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.phase6_apply_access_prep_task_action_impl(
  UUID, UUID, TEXT, UUID, JSONB
)
FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.phase6_override_housekeeping_task_impl(
  TEXT, UUID, UUID, TEXT, UUID
)
FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION public.phase6_merge_access_prep_task_impl(JSONB, UUID)
TO postgres;
GRANT EXECUTE ON FUNCTION public.phase6_apply_access_prep_task_action_impl(
  UUID, UUID, TEXT, UUID, JSONB
)
TO postgres;
GRANT EXECUTE ON FUNCTION public.phase6_override_housekeeping_task_impl(
  TEXT, UUID, UUID, TEXT, UUID
)
TO postgres;

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
  v_payload JSONB := p_task;
  v_existing_event public.access_prep_task_events%ROWTYPE;
  v_booking_id UUID;
  v_active_task_key TEXT;
BEGIN
  IF p_source_event_id IS NULL THEN
    RAISE EXCEPTION 'source_event_id_required' USING ERRCODE = '22023';
  END IF;

  PERFORM pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('housekeeping_event:' || p_source_event_id::TEXT, 0)
  );

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

  v_booking_id := NULLIF(BTRIM(p_task ->> 'booking_id'), '')::UUID;
  IF v_booking_id IS NOT NULL THEN
    PERFORM pg_catalog.pg_advisory_xact_lock(
      pg_catalog.hashtextextended('access_prep_booking:' || v_booking_id::TEXT, 0)
    );

    SELECT task_key INTO v_active_task_key
    FROM public.access_prep_tasks
    WHERE booking_id = v_booking_id
      AND status NOT IN ('done', 'canceled', 'delivery_failed')
    FOR UPDATE;

    IF FOUND THEN
      v_payload := jsonb_set(
        v_payload,
        '{task_key}',
        to_jsonb(v_active_task_key),
        true
      );
    END IF;
  END IF;

  RETURN public.phase6_merge_access_prep_task_impl(
    v_payload,
    p_source_event_id
  );
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
BEGIN
  IF p_source_event_id IS NULL THEN
    RAISE EXCEPTION 'source_event_id_required' USING ERRCODE = '22023';
  END IF;

  PERFORM pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('housekeeping_event:' || p_source_event_id::TEXT, 0)
  );

  RETURN public.phase6_apply_access_prep_task_action_impl(
    p_task_id,
    p_housekeeper_id,
    p_action,
    p_source_event_id,
    p_payload
  );
END;
$$;

REVOKE ALL ON FUNCTION public.apply_access_prep_task_action(
  UUID, UUID, TEXT, UUID, JSONB
)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.apply_access_prep_task_action(
  UUID, UUID, TEXT, UUID, JSONB
)
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
BEGIN
  IF p_source_event_id IS NULL THEN
    RAISE EXCEPTION 'source_event_id_required' USING ERRCODE = '22023';
  END IF;

  PERFORM pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('housekeeping_event:' || p_source_event_id::TEXT, 0)
  );

  RETURN public.phase6_override_housekeeping_task_impl(
    p_task_kind,
    p_task_id,
    p_admin_user_id,
    p_reason,
    p_source_event_id
  );
END;
$$;

REVOKE ALL ON FUNCTION public.override_housekeeping_task(
  TEXT, UUID, UUID, TEXT, UUID
)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.override_housekeeping_task(
  TEXT, UUID, UUID, TEXT, UUID
)
TO service_role, postgres;
