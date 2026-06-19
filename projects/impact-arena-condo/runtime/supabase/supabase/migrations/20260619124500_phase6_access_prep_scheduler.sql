-- Phase 6 Task 8: T-1 and same-day Access Prep scheduler.

CREATE OR REPLACE FUNCTION public.claim_access_prep_schedule(
  p_now TIMESTAMPTZ,
  p_limit INTEGER DEFAULT 50
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  v_now TIMESTAMPTZ := COALESCE(p_now, now());
  v_bangkok_today DATE := (COALESCE(p_now, now()) AT TIME ZONE 'Asia/Bangkok')::DATE;
  v_bangkok_time TIME := (COALESCE(p_now, now()) AT TIME ZONE 'Asia/Bangkok')::TIME;
  v_limit INTEGER := GREATEST(1, LEAST(100, COALESCE(p_limit, 50)));
  v_actions JSONB := '[]'::JSONB;
  v_row RECORD;
  v_source_event_id UUID;
BEGIN
  PERFORM pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended('phase6_access_prep_scheduler', 0)
  );

  FOR v_row IN
    WITH obsolete AS (
      SELECT
        'cancel_obsolete'::TEXT AS action,
        apt.id AS task_id,
        apt.assigned_housekeeper_id,
        apt.booking_id,
        COALESCE(b.room_id, apt.room_id) AS room_id,
        apt.task_key,
        NULL::JSONB AS task,
        CASE
          WHEN b.id IS NULL THEN 'booking_missing'
          WHEN b.booking_status IN ('canceled', 'no_show') THEN 'booking_' || b.booking_status
          WHEN apt.room_id IS DISTINCT FROM b.room_id THEN 'room_reassigned'
          ELSE 'check_in_date_changed'
        END AS reason,
        'normal'::TEXT AS priority,
        true AS notify_internal,
        true AS notify_owner,
        format(
          'Access Prep task %s was canceled because %s',
          apt.task_key,
          CASE
            WHEN b.id IS NULL THEN 'the linked booking is missing'
            WHEN b.booking_status IN ('canceled', 'no_show') THEN 'the booking is ' || b.booking_status
            WHEN apt.room_id IS DISTINCT FROM b.room_id THEN 'the room assignment changed'
            ELSE 'the check-in date changed'
          END
        ) AS notification_text,
        10 AS rank
      FROM public.access_prep_tasks apt
      LEFT JOIN public.bookings b ON b.id = apt.booking_id
      WHERE apt.status NOT IN ('done', 'canceled', 'delivery_failed')
        AND (
          b.id IS NULL
          OR b.booking_status IN ('canceled', 'no_show')
          OR apt.room_id IS DISTINCT FROM b.room_id
          OR (apt.scheduled_for AT TIME ZONE 'Asia/Bangkok')::DATE
            IS DISTINCT FROM (b.check_in_date - 1)
        )
      ORDER BY apt.created_at, apt.id
      LIMIT v_limit
      FOR UPDATE SKIP LOCKED
    ),
    create_candidates AS (
      SELECT
        CASE
          WHEN b.check_in_date = v_bangkok_today THEN 'same_day_urgent'
          ELSE 'create_t_minus_one'
        END::TEXT AS action,
        NULL::UUID AS task_id,
        NULL::UUID AS assigned_housekeeper_id,
        b.id AS booking_id,
        b.room_id,
        ('access-prep:' || b.id::TEXT) AS task_key,
        jsonb_build_object(
          'task_key', 'access-prep:' || b.id::TEXT,
          'booking_id', b.id,
          'room_id', b.room_id,
          'priority', CASE WHEN b.check_in_date = v_bangkok_today THEN 'urgent' ELSE 'normal' END,
          'key_custody', 'with_owner',
          'capabilities_required', '{"can_place_key":true,"can_open_room":true}'::JSONB,
          'scheduled_for', ((b.check_in_date - 1)::TIMESTAMP + TIME '18:00') AT TIME ZONE 'Asia/Bangkok',
          'due_at', (b.check_in_date::TIMESTAMP + TIME '09:00') AT TIME ZONE 'Asia/Bangkok',
          'ack_due_at', v_now + INTERVAL '30 minutes',
          'instructions', CASE
            WHEN b.check_in_date = v_bangkok_today
              THEN 'Same-day Access Prep: prepare key/access before guest arrival.'
            ELSE 'T-1 Access Prep: prepare key/access for tomorrow check-in.'
          END,
          'source', 'checkin_schedule'
        ) AS task,
        NULL::TEXT AS reason,
        CASE WHEN b.check_in_date = v_bangkok_today THEN 'urgent' ELSE 'normal' END::TEXT AS priority,
        true AS notify_internal,
        CASE WHEN b.check_in_date = v_bangkok_today THEN true ELSE false END AS notify_owner,
        format(
          '%s Access Prep created for booking %s room %s',
          CASE WHEN b.check_in_date = v_bangkok_today THEN 'Same-day urgent' ELSE 'T-1' END,
          b.reservation_number,
          COALESCE(r.room_code, b.room_id::TEXT)
        ) AS notification_text,
        CASE WHEN b.check_in_date = v_bangkok_today THEN 20 ELSE 40 END AS rank
      FROM public.bookings b
      LEFT JOIN public.rooms r ON r.id = b.room_id
      WHERE b.booking_status NOT IN ('canceled', 'no_show')
        AND b.room_id IS NOT NULL
        AND b.check_in_date IN (v_bangkok_today, v_bangkok_today + 1)
        AND NOT EXISTS (
          SELECT 1
          FROM public.access_prep_tasks apt
          WHERE apt.booking_id = b.id
            AND apt.status NOT IN ('done', 'canceled', 'delivery_failed')
        )
      ORDER BY
        CASE WHEN b.check_in_date = v_bangkok_today THEN 0 ELSE 1 END,
        b.check_in_date,
        b.id
      LIMIT v_limit
    ),
    escalation_candidates AS (
      SELECT
        CASE
          WHEN b.check_in_date = v_bangkok_today AND v_bangkok_time >= TIME '09:00'
            THEN 'hard_block_09'
          ELSE 'escalate_22'
        END::TEXT AS action,
        apt.id AS task_id,
        apt.assigned_housekeeper_id,
        apt.booking_id,
        apt.room_id,
        apt.task_key,
        jsonb_build_object(
          'task_key', apt.task_key,
          'booking_id', apt.booking_id,
          'room_id', apt.room_id,
          'priority', 'urgent',
          'scheduled_for', apt.scheduled_for,
          'due_at', apt.due_at,
          'ack_due_at', apt.ack_due_at,
          'instructions', COALESCE(apt.instructions, 'Access Prep escalation before check-in.'),
          'notes', CONCAT_WS(E'\n', apt.notes, 'Scheduler escalation: ' || CASE
            WHEN b.check_in_date = v_bangkok_today AND v_bangkok_time >= TIME '09:00'
              THEN 'hard_block_09'
            ELSE 'escalate_22'
          END),
          'source', 'checkin_schedule'
        ) AS task,
        NULL::TEXT AS reason,
        'urgent'::TEXT AS priority,
        true AS notify_internal,
        true AS notify_owner,
        format(
          '%s for Access Prep task %s before check-in %s',
          CASE
            WHEN b.check_in_date = v_bangkok_today AND v_bangkok_time >= TIME '09:00'
              THEN 'Hard block'
            ELSE '22:00 escalation'
          END,
          apt.task_key,
          b.check_in_date
        ) AS notification_text,
        CASE
          WHEN b.check_in_date = v_bangkok_today AND v_bangkok_time >= TIME '09:00'
            THEN 30
          ELSE 50
        END AS rank
      FROM public.access_prep_tasks apt
      JOIN public.bookings b ON b.id = apt.booking_id
      WHERE b.booking_status NOT IN ('canceled', 'no_show')
        AND apt.status NOT IN ('done', 'canceled', 'delivery_failed')
        AND (
          (
            b.check_in_date = v_bangkok_today + 1
            AND v_bangkok_time >= TIME '22:00'
            AND apt.priority <> 'urgent'
          )
          OR (
            b.check_in_date = v_bangkok_today
            AND v_bangkok_time >= TIME '09:00'
            AND apt.status <> 'done'
          )
        )
      ORDER BY b.check_in_date, apt.due_at NULLS FIRST, apt.id
      LIMIT v_limit
      FOR UPDATE SKIP LOCKED
    ),
    unioned AS (
      SELECT * FROM obsolete
      UNION ALL
      SELECT * FROM create_candidates
      UNION ALL
      SELECT * FROM escalation_candidates
      ORDER BY rank, booking_id, task_id NULLS LAST
      LIMIT v_limit
    )
    SELECT * FROM unioned
  LOOP
    v_source_event_id := gen_random_uuid();

    v_actions := v_actions || jsonb_build_array(jsonb_build_object(
      'action', v_row.action,
      'task_id', v_row.task_id,
      'assigned_housekeeper_id', v_row.assigned_housekeeper_id,
      'booking_id', v_row.booking_id,
      'room_id', v_row.room_id,
      'task_key', v_row.task_key,
      'task', v_row.task,
      'reason', v_row.reason,
      'priority', v_row.priority,
      'notify_internal', v_row.notify_internal,
      'notify_owner', v_row.notify_owner,
      'notification_text', v_row.notification_text,
      'source_event_id', v_source_event_id
    ));
  END LOOP;

  RETURN jsonb_build_object(
    'ok', true,
    'scheduler', 'phase6_access_prep',
    'now', v_now,
    'bangkok_today', v_bangkok_today,
    'actions', v_actions
  );
END;
$$;

REVOKE ALL ON FUNCTION public.claim_access_prep_schedule(TIMESTAMPTZ, INTEGER)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.claim_access_prep_schedule(TIMESTAMPTZ, INTEGER)
TO service_role, postgres;
