-- Phase 6 Task 3: deterministic combined Cleaning and Access Prep queue.

ALTER TABLE public.cleaning_tasks
  ADD COLUMN IF NOT EXISTS admin_priority_rank INTEGER NOT NULL DEFAULT 0
    CONSTRAINT cleaning_tasks_admin_priority_rank_check
    CHECK (admin_priority_rank BETWEEN 0 AND 1000);

ALTER TABLE public.access_prep_tasks
  ADD COLUMN IF NOT EXISTS admin_priority_rank INTEGER NOT NULL DEFAULT 0
    CONSTRAINT access_prep_tasks_admin_priority_rank_check
    CHECK (admin_priority_rank BETWEEN 0 AND 1000);

COMMENT ON COLUMN public.cleaning_tasks.admin_priority_rank IS
  'Explicit Admin/Bond queue override. Higher values outrank automatic planning.';
COMMENT ON COLUMN public.access_prep_tasks.admin_priority_rank IS
  'Explicit Admin/Bond queue override. Higher values outrank automatic planning.';

CREATE INDEX IF NOT EXISTS idx_cleaning_tasks_housekeeping_queue
  ON public.cleaning_tasks (
    assigned_housekeeper_id,
    admin_priority_rank DESC,
    due_at,
    id
  )
  WHERE status NOT IN ('completed', 'canceled', 'delivery_failed');

CREATE INDEX IF NOT EXISTS idx_access_prep_tasks_housekeeping_queue
  ON public.access_prep_tasks (
    assigned_housekeeper_id,
    admin_priority_rank DESC,
    due_at,
    scheduled_for,
    id
  )
  WHERE status NOT IN ('done', 'canceled', 'delivery_failed');

CREATE OR REPLACE FUNCTION public.get_housekeeping_queue(
  p_housekeeper_id UUID,
  p_view TEXT,
  p_limit INTEGER DEFAULT 5,
  p_cursor JSONB DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  v_result JSONB;
BEGIN
  IF p_housekeeper_id IS NULL THEN
    RAISE EXCEPTION 'housekeeper_id_required' USING ERRCODE = '22023';
  END IF;
  IF p_view NOT IN ('today', 'all') THEN
    RAISE EXCEPTION 'unsupported_queue_view' USING ERRCODE = '22023';
  END IF;

  WITH
  params AS (
    SELECT
      GREATEST(1, LEAST(5, COALESCE(p_limit, 5))) AS page_limit,
      COALESCE(NULLIF(p_cursor ->> 'direction', ''), 'next') AS cursor_direction,
      NULLIF(p_cursor ->> 'sortKey', '') AS cursor_sort_key,
      (now() AT TIME ZONE 'Asia/Bangkok')::DATE AS bangkok_today
  ),
  cleaning_rows AS (
    SELECT
      'cleaning'::TEXT AS task_kind,
      ct.id AS task_id,
      ct.room_id,
      r.room_code,
      ct.booking_id,
      b.guest_name_snapshot AS guest_name,
      b.check_in_date,
      ct.priority,
      ct.status,
      ct.due_at,
      NULL::TIMESTAMPTZ AS scheduled_for,
      au.display_name AS owner_label,
      COALESCE(mi.missing_items, '[]'::JSONB) AS missing_items,
      CASE WHEN linked_access.id IS NULL THEN NULL ELSE 'access_prep' END::TEXT
        AS linked_task_kind,
      linked_access.status AS linked_task_status,
      GREATEST(
        ct.admin_priority_rank,
        CASE WHEN ct.admin_action_id IS NOT NULL THEN 100 ELSE 0 END
      ) AS admin_priority_rank,
      (
        ct.status = 'blocked'
        OR ct.blocker_reason IS NOT NULL
        OR COALESCE(jsonb_array_length(mi.missing_items), 0) > 0
      ) AS has_open_blocker,
      r.building,
      r.floor,
      ct.assigned_housekeeper_id,
      ct.instructions,
      ct.blocker_reason
    FROM public.cleaning_tasks ct
    LEFT JOIN public.rooms r ON r.id = ct.room_id
    LEFT JOIN public.bookings b ON b.id = ct.booking_id
    LEFT JOIN public.admin_actions aa ON aa.id = ct.admin_action_id
    LEFT JOIN public.admin_users au ON au.id = aa.actor_id
    LEFT JOIN LATERAL (
      SELECT jsonb_agg(item.item_key ORDER BY item.item_key) AS missing_items
      FROM public.cleaning_task_checklist_items item
      WHERE item.cleaning_task_id = ct.id
        AND item.status = 'missing'
    ) mi ON true
    LEFT JOIN LATERAL (
      SELECT apt.id, apt.status
      FROM public.access_prep_tasks apt
      WHERE apt.booking_id = ct.booking_id
      ORDER BY
        CASE
          WHEN apt.status IN ('done', 'canceled', 'delivery_failed') THEN 1
          ELSE 0
        END,
        apt.due_at NULLS LAST,
        apt.scheduled_for DESC,
        apt.created_at DESC,
        apt.id
      LIMIT 1
    ) linked_access ON true
    WHERE ct.status NOT IN ('completed', 'canceled', 'delivery_failed')
      AND (
        ct.assigned_housekeeper_id = p_housekeeper_id
        OR ct.assigned_housekeeper_id IS NULL
      )
  ),
  access_rows AS (
    SELECT
      'access_prep'::TEXT AS task_kind,
      apt.id AS task_id,
      apt.room_id,
      r.room_code,
      apt.booking_id,
      b.guest_name_snapshot AS guest_name,
      b.check_in_date,
      apt.priority,
      apt.status,
      COALESCE(apt.due_at, apt.scheduled_for) AS due_at,
      apt.scheduled_for,
      owner_admin.display_name AS owner_label,
      '[]'::JSONB AS missing_items,
      CASE WHEN linked_cleaning.id IS NULL THEN NULL ELSE 'cleaning' END::TEXT
        AS linked_task_kind,
      linked_cleaning.status AS linked_task_status,
      apt.admin_priority_rank,
      (apt.status = 'blocked' OR apt.blocker_reason IS NOT NULL)
        AS has_open_blocker,
      r.building,
      r.floor,
      apt.assigned_housekeeper_id,
      apt.instructions,
      apt.blocker_reason
    FROM public.access_prep_tasks apt
    LEFT JOIN public.rooms r ON r.id = apt.room_id
    LEFT JOIN public.bookings b ON b.id = apt.booking_id
    LEFT JOIN public.admin_users owner_admin
      ON owner_admin.id = apt.owner_admin_user_id
    LEFT JOIN LATERAL (
      SELECT ct.id, ct.status
      FROM public.cleaning_tasks ct
      WHERE ct.booking_id = apt.booking_id
      ORDER BY
        CASE
          WHEN ct.status IN ('completed', 'canceled', 'delivery_failed') THEN 1
          ELSE 0
        END,
        ct.due_at NULLS LAST,
        ct.created_at DESC,
        ct.id
      LIMIT 1
    ) linked_cleaning ON true
    WHERE apt.status NOT IN ('done', 'canceled', 'delivery_failed')
      AND (
        apt.assigned_housekeeper_id = p_housekeeper_id
        OR apt.assigned_housekeeper_id IS NULL
      )
  ),
  combined AS (
    SELECT * FROM cleaning_rows
    UNION ALL
    SELECT * FROM access_rows
  ),
  view_filtered AS (
    SELECT combined.*
    FROM combined
    CROSS JOIN params
    WHERE p_view = 'all'
      OR (
        combined.assigned_housekeeper_id = p_housekeeper_id
        AND combined.due_at IS NOT NULL
        AND (combined.due_at AT TIME ZONE 'Asia/Bangkok')::DATE
          = params.bangkok_today
      )
  ),
  scored AS (
    SELECT
      view_filtered.*,
      CASE
        WHEN view_filtered.check_in_date = params.bangkok_today THEN 1
        ELSE 0
      END AS checkin_today_rank,
      CASE
        WHEN view_filtered.task_kind = 'access_prep'
          AND view_filtered.check_in_date BETWEEN
            params.bangkok_today AND params.bangkok_today + 1
        THEN 1
        ELSE 0
      END AS access_near_checkin_rank,
      CASE WHEN view_filtered.has_open_blocker THEN 1 ELSE 0 END
        AS blocker_rank
    FROM view_filtered
    CROSS JOIN params
  ),
  ranked AS (
    SELECT
      scored.*,
      jsonb_build_array(
        scored.admin_priority_rank,
        scored.checkin_today_rank,
        scored.access_near_checkin_rank,
        scored.blocker_rank,
        scored.building,
        scored.floor,
        scored.due_at,
        scored.task_id
      ) AS queue_rank,
      CONCAT_WS(
        '|',
        LPAD(
          (
            1000000 - LEAST(999999, GREATEST(0, scored.admin_priority_rank))
          )::TEXT,
          7,
          '0'
        ),
        CASE WHEN scored.checkin_today_rank = 1 THEN '0' ELSE '1' END,
        CASE WHEN scored.access_near_checkin_rank = 1 THEN '0' ELSE '1' END,
        CASE WHEN scored.blocker_rank = 1 THEN '0' ELSE '1' END,
        COALESCE(UPPER(scored.building), 'ZZZZ'),
        LPAD(COALESCE(scored.floor, 9999)::TEXT, 4, '0'),
        LPAD(
          COALESCE(
            FLOOR(EXTRACT(EPOCH FROM scored.due_at) * 1000)::BIGINT,
            9999999999999999
          )::TEXT,
          16,
          '0'
        ),
        scored.task_kind,
        scored.task_id::TEXT
      ) AS sort_key
    FROM scored
  ),
  eligible AS (
    SELECT ranked.*
    FROM ranked
    CROSS JOIN params
    WHERE params.cursor_sort_key IS NULL
      OR (
        params.cursor_direction = 'next'
        AND ranked.sort_key > params.cursor_sort_key
      )
      OR (
        params.cursor_direction = 'previous'
        AND ranked.sort_key < params.cursor_sort_key
      )
  ),
  forward_page AS (
    SELECT eligible.*
    FROM eligible
    CROSS JOIN params
    WHERE params.cursor_direction <> 'previous'
    ORDER BY eligible.sort_key
    LIMIT (SELECT page_limit FROM params)
  ),
  backward_page AS (
    SELECT eligible.*
    FROM eligible
    CROSS JOIN params
    WHERE params.cursor_direction = 'previous'
    ORDER BY eligible.sort_key DESC
    LIMIT (SELECT page_limit FROM params)
  ),
  page_rows AS (
    SELECT * FROM forward_page
    UNION ALL
    SELECT * FROM backward_page
  ),
  page_bounds AS (
    SELECT
      MIN(sort_key) AS first_sort_key,
      MAX(sort_key) AS last_sort_key,
      COUNT(*) AS item_count
    FROM page_rows
  )
  SELECT jsonb_build_object(
    'items',
    COALESCE(
      jsonb_agg(
        jsonb_build_object(
          'task_kind', page_rows.task_kind,
          'task_id', page_rows.task_id,
          'room_id', page_rows.room_id,
          'room_code', page_rows.room_code,
          'booking_id', page_rows.booking_id,
          'guest_name', page_rows.guest_name,
          'check_in_date', page_rows.check_in_date,
          'priority', page_rows.priority,
          'status', page_rows.status,
          'due_at', page_rows.due_at,
          'scheduled_for', page_rows.scheduled_for,
          'owner_label', page_rows.owner_label,
          'missing_items', page_rows.missing_items,
          'linked_task_kind', page_rows.linked_task_kind,
          'linked_task_status', page_rows.linked_task_status,
          'admin_priority_rank', page_rows.admin_priority_rank,
          'has_open_blocker', page_rows.has_open_blocker,
          'building', page_rows.building,
          'floor', page_rows.floor,
          'assigned_housekeeper_id', page_rows.assigned_housekeeper_id,
          'instructions', page_rows.instructions,
          'blocker_reason', page_rows.blocker_reason,
          'claimable',
            page_rows.status IN (
              'new', 'pending_dispatch', 'sent', 'waiting_ack', 'no_ack'
            )
            AND (
              page_rows.assigned_housekeeper_id IS NULL
              OR page_rows.assigned_housekeeper_id = p_housekeeper_id
            ),
          'queue_rank', page_rows.queue_rank
        )
        ORDER BY page_rows.sort_key
      ),
      '[]'::JSONB
    ),
    'next_cursor',
    CASE
      WHEN (SELECT item_count FROM page_bounds) > 0
        AND EXISTS (
          SELECT 1 FROM ranked
          WHERE ranked.sort_key > (SELECT last_sort_key FROM page_bounds)
        )
      THEN jsonb_build_object(
        'direction', 'next',
        'sortKey', (SELECT last_sort_key FROM page_bounds)
      )
      ELSE NULL
    END,
    'previous_cursor',
    CASE
      WHEN (SELECT item_count FROM page_bounds) > 0
        AND EXISTS (
          SELECT 1 FROM ranked
          WHERE ranked.sort_key < (SELECT first_sort_key FROM page_bounds)
        )
      THEN jsonb_build_object(
        'direction', 'previous',
        'sortKey', (SELECT first_sort_key FROM page_bounds)
      )
      ELSE NULL
    END
  )
  INTO v_result
  FROM page_rows;

  RETURN COALESCE(
    v_result,
    jsonb_build_object(
      'items', '[]'::JSONB,
      'next_cursor', NULL,
      'previous_cursor', NULL
    )
  );
END;
$$;

REVOKE ALL ON FUNCTION public.get_housekeeping_queue(UUID, TEXT, INTEGER, JSONB)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.get_housekeeping_queue(
  UUID, TEXT, INTEGER, JSONB
)
TO service_role, postgres;

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
  v_previous_state TEXT;
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

    v_previous_state := v_cleaning.status;
    IF v_cleaning.assigned_housekeeper_id IS NOT NULL
      AND v_cleaning.assigned_housekeeper_id <> p_housekeeper_id
    THEN
      v_result := jsonb_build_object(
        'ok', false,
        'error', 'already_claimed',
        'taskId', v_cleaning.id,
        'taskKind', 'cleaning',
        'previousState', v_cleaning.status,
        'newState', v_cleaning.status
      );
    ELSIF v_cleaning.status IN ('completed', 'canceled', 'delivery_failed') THEN
      v_result := jsonb_build_object(
        'ok', false,
        'error', 'terminal_task',
        'taskId', v_cleaning.id,
        'taskKind', 'cleaning',
        'previousState', v_cleaning.status,
        'newState', v_cleaning.status
      );
    ELSE
      UPDATE public.cleaning_tasks
      SET assigned_housekeeper_id = p_housekeeper_id,
          status = CASE
            WHEN status IN ('pending_dispatch', 'waiting_ack', 'no_ack')
              THEN 'acknowledged'
            ELSE status
          END,
          acknowledged_at = CASE
            WHEN status IN ('pending_dispatch', 'waiting_ack', 'no_ack')
              THEN COALESCE(acknowledged_at, now())
            ELSE acknowledged_at
          END,
          updated_at = now()
      WHERE id = v_cleaning.id
      RETURNING * INTO v_cleaning;

      INSERT INTO public.housekeeper_task_focus (
        housekeeper_id, focused_cleaning_task_id,
        focused_field_assistance_task_id, focused_access_prep_task_id,
        focus_type, last_command, updated_at
      )
      VALUES (
        p_housekeeper_id, v_cleaning.id, NULL, NULL,
        'cleaning', 'claim_housekeeping_task', now()
      )
      ON CONFLICT (housekeeper_id) DO UPDATE SET
        focused_cleaning_task_id = EXCLUDED.focused_cleaning_task_id,
        focused_field_assistance_task_id = NULL,
        focused_access_prep_task_id = NULL,
        focus_type = 'cleaning',
        last_command = 'claim_housekeeping_task',
        updated_at = now();

      v_result := jsonb_build_object(
        'ok', true,
        'action', 'claimed',
        'taskId', v_cleaning.id,
        'taskKind', 'cleaning',
        'previousState', v_previous_state,
        'newState', v_cleaning.status
      );
    END IF;

    INSERT INTO public.cleaning_task_events (
      cleaning_task_id, housekeeper_id, event_type, event_source,
      source_event_id, interaction_mode, llm_used,
      previous_state, new_state, payload
    )
    VALUES (
      v_cleaning.id, p_housekeeper_id,
      CASE WHEN COALESCE((v_result ->> 'ok')::BOOLEAN, false)
        THEN 'task_claimed' ELSE 'claim_rejected' END,
      'housekeeping_line', p_source_event_id, 'button', false,
      v_previous_state, COALESCE(v_result ->> 'newState', v_previous_state),
      jsonb_build_object('result', v_result)
    );
    RETURN v_result;
  END IF;

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

  v_previous_state := v_access.status;
  IF v_access.assigned_housekeeper_id IS NOT NULL
    AND v_access.assigned_housekeeper_id <> p_housekeeper_id
  THEN
    v_result := jsonb_build_object(
      'ok', false,
      'error', 'already_claimed',
      'taskId', v_access.id,
      'taskKind', 'access_prep',
      'previousState', v_access.status,
      'newState', v_access.status
    );
  ELSIF v_access.status IN ('done', 'canceled', 'delivery_failed') THEN
    v_result := jsonb_build_object(
      'ok', false,
      'error', 'terminal_task',
      'taskId', v_access.id,
      'taskKind', 'access_prep',
      'previousState', v_access.status,
      'newState', v_access.status
    );
  ELSE
    UPDATE public.access_prep_tasks
    SET assigned_housekeeper_id = p_housekeeper_id,
        status = CASE
          WHEN status IN ('new', 'sent', 'no_ack') THEN 'acknowledged'
          ELSE status
        END,
        acknowledged_at = CASE
          WHEN status IN ('new', 'sent', 'no_ack')
            THEN COALESCE(acknowledged_at, now())
          ELSE acknowledged_at
        END,
        updated_at = now()
    WHERE id = v_access.id
    RETURNING * INTO v_access;

    INSERT INTO public.housekeeper_task_focus (
      housekeeper_id, focused_cleaning_task_id,
      focused_field_assistance_task_id, focused_access_prep_task_id,
      focus_type, last_command, updated_at
    )
    VALUES (
      p_housekeeper_id, NULL, NULL, v_access.id,
      'access_prep', 'claim_housekeeping_task', now()
    )
    ON CONFLICT (housekeeper_id) DO UPDATE SET
      focused_cleaning_task_id = NULL,
      focused_field_assistance_task_id = NULL,
      focused_access_prep_task_id = EXCLUDED.focused_access_prep_task_id,
      focus_type = 'access_prep',
      last_command = 'claim_housekeeping_task',
      updated_at = now();

    v_result := jsonb_build_object(
      'ok', true,
      'action', 'claimed',
      'taskId', v_access.id,
      'taskKind', 'access_prep',
      'previousState', v_previous_state,
      'newState', v_access.status
    );
  END IF;

  INSERT INTO public.access_prep_task_events (
    access_prep_task_id, housekeeper_id, event_type,
    previous_state, new_state, source_event_id, payload
  )
  VALUES (
    v_access.id, p_housekeeper_id,
    CASE WHEN COALESCE((v_result ->> 'ok')::BOOLEAN, false)
      THEN 'task_claimed' ELSE 'claim_rejected' END,
    v_previous_state, COALESCE(v_result ->> 'newState', v_previous_state),
    p_source_event_id, jsonb_build_object('result', v_result)
  );
  RETURN v_result;
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
    IF TG_TABLE_NAME = 'cleaning_tasks' THEN
      UPDATE public.housekeeper_task_focus
      SET focused_cleaning_task_id = NULL,
          focused_field_assistance_task_id = NULL,
          focused_access_prep_task_id = NULL,
          focus_type = NULL,
          last_command = 'assignment_changed',
          updated_at = now()
      WHERE housekeeper_id = OLD.assigned_housekeeper_id
        AND focused_cleaning_task_id = OLD.id;
    ELSE
      UPDATE public.housekeeper_task_focus
      SET focused_cleaning_task_id = NULL,
          focused_field_assistance_task_id = NULL,
          focused_access_prep_task_id = NULL,
          focus_type = NULL,
          last_command = 'assignment_changed',
          updated_at = now()
      WHERE housekeeper_id = OLD.assigned_housekeeper_id
        AND focused_access_prep_task_id = OLD.id;
    END IF;
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
