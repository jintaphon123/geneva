-- Phase 6 Task 11: canonical Room Access Readiness contract.

CREATE OR REPLACE FUNCTION public.get_room_access_readiness(
  p_booking_id UUID
)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  v_booking public.bookings%ROWTYPE;
  v_booking_verified BOOLEAN := false;
  v_room_assignment_stable BOOLEAN := false;
  v_cleaning_ready BOOLEAN := false;
  v_access_prep_ready BOOLEAN := false;
  v_active_access_incident BOOLEAN := false;
  v_approved_access_content BOOLEAN := false;
  v_capability_denied BOOLEAN := false;
  v_blockers JSONB := '[]'::JSONB;
BEGIN
  IF p_booking_id IS NULL THEN
    RAISE EXCEPTION 'booking_id_required' USING ERRCODE = '22023';
  END IF;

  SELECT *
  INTO v_booking
  FROM public.bookings
  WHERE id = p_booking_id;

  IF NOT FOUND THEN
    RETURN jsonb_build_object(
      'ready', false,
      'booking_id', p_booking_id,
      'booking_verified', false,
      'room_assignment_stable', false,
      'cleaning_ready', false,
      'access_prep_ready', false,
      'active_access_incident', false,
      'approved_access_content', false,
      'blockers', jsonb_build_array('booking_not_found')
    );
  END IF;

  SELECT EXISTS (
    SELECT 1
    FROM public.guest_stay_states gss
    WHERE gss.booking_id = p_booking_id
      AND gss.booking_verification_status = 'confirmed'
  )
  INTO v_booking_verified;

  SELECT EXISTS (
    SELECT 1
    FROM public.access_prep_tasks apt
    WHERE apt.booking_id = p_booking_id
      AND apt.room_id IS NOT DISTINCT FROM v_booking.room_id
      AND apt.status NOT IN ('canceled', 'delivery_failed')
  )
  AND NOT EXISTS (
    SELECT 1
    FROM public.access_prep_tasks apt
    WHERE apt.booking_id = p_booking_id
      AND apt.status NOT IN ('canceled', 'delivery_failed')
      AND apt.room_id IS DISTINCT FROM v_booking.room_id
  )
  INTO v_room_assignment_stable;

  SELECT EXISTS (
    SELECT 1
    FROM public.cleaning_tasks ct
    WHERE ct.booking_id = p_booking_id
      AND ct.room_id IS NOT DISTINCT FROM v_booking.room_id
      AND ct.status = 'completed'
      AND NOT EXISTS (
        SELECT 1
        FROM public.cleaning_task_checklist_items item
        WHERE item.cleaning_task_id = ct.id
          AND item.status = 'missing'
      )
  )
  INTO v_cleaning_ready;

  SELECT EXISTS (
    SELECT 1
    FROM public.access_prep_tasks apt
    WHERE apt.booking_id = p_booking_id
      AND apt.room_id IS NOT DISTINCT FROM v_booking.room_id
      AND apt.status = 'done'
      AND apt.blocker_reason IS NULL
      AND apt.key_custody = 'placed_in_room'
  )
  INTO v_access_prep_ready;

  SELECT EXISTS (
    SELECT 1
    FROM public.operational_incidents incident
    WHERE incident.booking_id = p_booking_id
      AND incident.status IN ('open', 'acknowledged', 'in_progress')
      AND incident.issue_family IN (
        'access_prep',
        'room_access_problem',
        'housekeeping_problem',
        'cleaning_delayed_checkin'
      )
  )
  INTO v_active_access_incident;

  SELECT EXISTS (
    SELECT 1
    FROM public.access_prep_task_events event
    JOIN public.access_prep_tasks apt
      ON apt.id = event.access_prep_task_id
    WHERE apt.booking_id = p_booking_id
      AND (
        event.event_type = 'capability_denied'
        OR event.payload -> 'result' ->> 'error' = 'capability_denied'
        OR event.payload ->> 'error' = 'capability_denied'
      )
      AND event.created_at >= COALESCE(apt.updated_at, apt.created_at)
  )
  INTO v_capability_denied;

  SELECT EXISTS (
    SELECT 1
    FROM public.assets asset
    LEFT JOIN public.rooms room ON room.id = v_booking.room_id
    WHERE asset.status = 'approved'
      AND asset.line_sendable = true
      AND (
        asset.room_code_snapshot = room.room_code
        OR asset.building = room.building
      )
      AND (
        asset.asset_type IN ('room_access', 'room_entry', 'check_in', 'key_location')
        OR asset.usage_trigger ILIKE '%access%'
        OR asset.usage_trigger ILIKE '%check%in%'
      )
  )
  INTO v_approved_access_content;

  IF NOT v_booking_verified THEN
    v_blockers := v_blockers || jsonb_build_array('booking_not_verified');
  END IF;
  IF NOT v_room_assignment_stable THEN
    v_blockers := v_blockers || jsonb_build_array('room_assignment_changed');
  END IF;
  IF NOT v_cleaning_ready THEN
    v_blockers := v_blockers || jsonb_build_array('cleaning_incomplete');
  END IF;
  IF NOT v_access_prep_ready THEN
    v_blockers := v_blockers || jsonb_build_array('access_prep_incomplete');
  END IF;
  IF v_active_access_incident THEN
    v_blockers := v_blockers || jsonb_build_array('active_access_incident');
  END IF;
  IF v_capability_denied THEN
    v_blockers := v_blockers || jsonb_build_array('capability_denied');
  END IF;
  IF NOT v_approved_access_content THEN
    v_blockers := v_blockers || jsonb_build_array('approved_access_content_missing');
  END IF;

  RETURN jsonb_build_object(
    'ready', jsonb_array_length(v_blockers) = 0,
    'booking_id', p_booking_id,
    'room_id', v_booking.room_id,
    'booking_verified', v_booking_verified,
    'room_assignment_stable', v_room_assignment_stable,
    'cleaning_ready', v_cleaning_ready,
    'access_prep_ready', v_access_prep_ready,
    'active_access_incident', v_active_access_incident OR v_capability_denied,
    'approved_access_content', v_approved_access_content,
    'blockers', v_blockers
  );
END;
$$;

REVOKE ALL ON FUNCTION public.get_room_access_readiness(UUID)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.get_room_access_readiness(UUID)
TO service_role, postgres;
