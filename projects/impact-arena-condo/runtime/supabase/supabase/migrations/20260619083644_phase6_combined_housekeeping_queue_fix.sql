-- Repair the already-applied Task 3 function without duplicating its full body.
-- Fresh installs already receive the corrected definition from the prior
-- migration, so these replacements become no-ops there.

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
    'page_bounds.item_count',
    '(SELECT item_count FROM page_bounds)'
  );
  v_definition := replace(
    v_definition,
    'page_bounds.last_sort_key',
    '(SELECT last_sort_key FROM page_bounds)'
  );
  v_definition := replace(
    v_definition,
    'page_bounds.first_sort_key',
    '(SELECT first_sort_key FROM page_bounds)'
  );
  v_definition := replace(
    v_definition,
    E'FROM page_rows\n  CROSS JOIN page_bounds;',
    'FROM page_rows;'
  );

  IF v_definition LIKE '%page_bounds.item_count%'
    OR v_definition LIKE '%page_bounds.last_sort_key%'
    OR v_definition LIKE '%page_bounds.first_sort_key%'
    OR v_definition LIKE '%CROSS JOIN page_bounds;%'
  THEN
    RAISE EXCEPTION 'get_housekeeping_queue_patch_incomplete';
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
