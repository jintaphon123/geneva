-- Preserve linked Cleaning/Access Prep truth after one side becomes terminal.
-- Active tasks remain preferred; otherwise the latest terminal task is shown.

DO $$
DECLARE
  v_definition TEXT;
BEGIN
  SELECT pg_get_functiondef(p.oid)
  INTO v_definition
  FROM pg_proc p
  JOIN pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname = 'public'
    AND p.proname = 'get_housekeeping_queue'
    AND pg_get_function_identity_arguments(p.oid)
      = 'p_housekeeper_id uuid, p_view text, p_limit integer, p_cursor jsonb';

  IF v_definition IS NULL THEN
    RAISE EXCEPTION 'get_housekeeping_queue_not_found';
  END IF;

  v_definition := replace(
    v_definition,
    E'WHERE apt.booking_id = ct.booking_id\n        AND apt.status NOT IN (''done'', ''canceled'', ''delivery_failed'')\n      ORDER BY apt.due_at NULLS LAST, apt.scheduled_for, apt.id',
    E'WHERE apt.booking_id = ct.booking_id\n      ORDER BY\n        CASE\n          WHEN apt.status IN (''done'', ''canceled'', ''delivery_failed'') THEN 1\n          ELSE 0\n        END,\n        apt.due_at NULLS LAST,\n        apt.scheduled_for DESC,\n        apt.created_at DESC,\n        apt.id'
  );
  v_definition := replace(
    v_definition,
    E'WHERE ct.booking_id = apt.booking_id\n        AND ct.status NOT IN (''completed'', ''canceled'', ''delivery_failed'')\n      ORDER BY ct.due_at NULLS LAST, ct.created_at, ct.id',
    E'WHERE ct.booking_id = apt.booking_id\n      ORDER BY\n        CASE\n          WHEN ct.status IN (''completed'', ''canceled'', ''delivery_failed'') THEN 1\n          ELSE 0\n        END,\n        ct.due_at NULLS LAST,\n        ct.created_at DESC,\n        ct.id'
  );

  IF v_definition LIKE
      '%ORDER BY apt.due_at NULLS LAST, apt.scheduled_for, apt.id%'
    OR v_definition LIKE
      '%ORDER BY ct.due_at NULLS LAST, ct.created_at, ct.id%'
  THEN
    RAISE EXCEPTION 'get_housekeeping_queue_linked_status_patch_incomplete';
  END IF;

  EXECUTE v_definition;
END;
$$;

REVOKE ALL ON FUNCTION public.get_housekeeping_queue(UUID, TEXT, INTEGER, JSONB)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.get_housekeeping_queue(
  UUID, TEXT, INTEGER, JSONB
)
TO service_role, postgres;
