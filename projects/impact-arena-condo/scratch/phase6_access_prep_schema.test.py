#!/usr/bin/env python3
import os
import sys
import json
import subprocess

SUPABASE_BIN = os.environ.get("SUPABASE_BIN", "/opt/homebrew/bin/supabase")

def run_db_query(sql):
    cwd = "/Users/jintaphon/Documents/Code/MyBrain/projects/impact-arena-condo/runtime/supabase"
    cmd = [SUPABASE_BIN, "db", "query", "--linked", "-o", "json", sql]
    env = os.environ.copy()
    env["SUPABASE_TELEMETRY_DISABLED"] = "1"
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        print(f"SQL execution error: {result.stderr}", file=sys.stderr)
        return []
    try:
        data = json.loads(result.stdout)
        return data.get("rows", [])
    except Exception as e:
        print(f"JSON parsing error: {e}, Raw: {result.stdout}", file=sys.stderr)
        return []

def run_tests():
    print("Running Phase 6 Access Prep Schema Verification Tests...")
    failed = False

    # 1. Verify tables exist
    print("\n--- 1. PG Catalog Table Verification ---")
    sql_tables = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name IN ('access_prep_tasks', 'access_prep_task_events');
    """
    rows = run_db_query(sql_tables)
    found_tables = {r["table_name"] for r in rows}

    expected_tables = {"access_prep_tasks", "access_prep_task_events"}
    for table in expected_tables:
        if table in found_tables:
            print(f"[PASS] Table '{table}' exists.")
        else:
            print(f"[FAIL] Table '{table}' is MISSING.")
            failed = True

    # 2. Check nullability, types, and columns on access_prep_tasks
    print("\n--- 2. Column Verification ---")
    sql_cols = """
    SELECT column_name, is_nullable, data_type
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'access_prep_tasks';
    """
    cols = run_db_query(sql_cols)
    col_map = {r["column_name"]: r for r in cols}

    required_cols = [
        "id", "task_key", "booking_id", "room_id", "internal_ops_case_id",
        "assigned_housekeeper_id", "owner_admin_user_id", "priority", "status",
        "dispatch_status", "key_custody", "capabilities_required", "scheduled_for",
        "due_at", "ack_due_at", "acknowledged_at", "started_at", "completed_at",
        "blocker_reason", "instructions", "notes", "override_reason",
        "overridden_by", "overridden_at", "created_at", "updated_at"
    ]

    for c in required_cols:
        if c in col_map:
            print(f"[PASS] Column '{c}' exists in access_prep_tasks.")
        else:
            print(f"[FAIL] Column '{c}' is MISSING in access_prep_tasks.")
            failed = True

    # Check access_prep_task_events columns and source_event_id NOT NULL
    sql_cols_events = """
    SELECT column_name, is_nullable, data_type
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'access_prep_task_events';
    """
    cols_events = run_db_query(sql_cols_events)
    col_map_events = {r["column_name"]: r for r in cols_events}

    if "source_event_id" in col_map_events:
        is_nullable = col_map_events["source_event_id"]["is_nullable"]
        if is_nullable == "NO":
            print("[PASS] Column 'access_prep_task_events.source_event_id' is NOT NULL.")
        else:
            print("[FAIL] Column 'access_prep_task_events.source_event_id' is NULLABLE.")
            failed = True
    else:
        print("[FAIL] Column 'access_prep_task_events.source_event_id' is MISSING.")
        failed = True

    # 3. Check CHECK constraints
    print("\n--- 3. CHECK Constraints Verification ---")
    sql_check = """
    SELECT con.conname AS constraint_name, pg_get_constraintdef(con.oid) AS constraint_definition
    FROM pg_constraint con
    JOIN pg_class t ON t.oid = con.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = 'public' AND t.relname = 'access_prep_tasks' AND con.contype = 'c';
    """
    check_rows = run_db_query(sql_check)
    check_defs = {r["constraint_name"]: r["constraint_definition"] for r in check_rows}

    # Check priority check
    priority_check = [name for name, definition in check_defs.items() if "priority" in definition]
    if priority_check:
        print(f"[PASS] priority check constraint exists: {check_defs[priority_check[0]]}")
    else:
        print("[FAIL] priority check constraint is MISSING.")
        failed = True

    # Check status check
    status_check = [name for name, definition in check_defs.items() if "status" in definition and "done" in definition]
    if status_check:
        print(f"[PASS] status check constraint exists: {check_defs[status_check[0]]}")
    else:
        print("[FAIL] status check constraint is MISSING.")
        failed = True

    # Check key_custody check
    key_custody_check = [name for name, definition in check_defs.items() if "key_custody" in definition]
    if key_custody_check:
        print(f"[PASS] key_custody check constraint exists: {check_defs[key_custody_check[0]]}")
    else:
        print("[FAIL] key_custody check constraint is MISSING.")
        failed = True

    # 4. Check Foreign Keys and ON DELETE behaviors
    print("\n--- 4. Foreign Key Delete Behaviors Verification ---")
    sql_fk = """
    SELECT con.conname AS constraint_name, t.relname AS table_name, ref.relname AS referenced_table, con.confdeltype AS delete_behavior
    FROM pg_constraint con
    JOIN pg_class t ON t.oid = con.conrelid
    JOIN pg_class ref ON ref.oid = con.confrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = 'public' AND t.relname IN ('access_prep_tasks', 'access_prep_task_events') AND con.contype = 'f';
    """
    fk_rows = run_db_query(sql_fk)
    behavior_map = {'c': 'CASCADE', 'n': 'SET NULL', 'a': 'NO ACTION', 'r': 'RESTRICT'}

    expected_fks = [
        {"table": "access_prep_tasks", "ref": "bookings", "behavior": "c"}, # ON DELETE CASCADE
        {"table": "access_prep_tasks", "ref": "rooms", "behavior": "n"}, # ON DELETE SET NULL
        {"table": "access_prep_tasks", "ref": "internal_ops_cases", "behavior": "n"}, # ON DELETE SET NULL
        {"table": "access_prep_tasks", "ref": "housekeepers", "behavior": "n"}, # ON DELETE SET NULL
        {"table": "access_prep_tasks", "ref": "admin_users", "behavior": "n"}, # ON DELETE SET NULL
        {"table": "access_prep_task_events", "ref": "access_prep_tasks", "behavior": "c"} # ON DELETE CASCADE
    ]

    for ef in expected_fks:
        match = False
        for r in fk_rows:
            if r["table_name"] == ef["table"] and r["referenced_table"] == ef["ref"]:
                if r["delete_behavior"] == ef["behavior"]:
                    match = True
        if match:
            print(f"[PASS] FK from '{ef['table']}' to '{ef['ref']}' ON DELETE {behavior_map[ef['behavior']]} is verified.")
        else:
            print(f"[FAIL] FK from '{ef['table']}' to '{ef['ref']}' ON DELETE behavior is incorrect or missing.")
            failed = True

    # 5. Check housekeeper_task_focus Column and Constraint Verification
    print("\n--- 5. housekeeper_task_focus Column and Constraint Verification ---")
    sql_focus_cols = """
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'housekeeper_task_focus' AND column_name = 'focused_access_prep_task_id';
    """
    focus_col_rows = run_db_query(sql_focus_cols)
    if focus_col_rows:
        print("[PASS] Column 'focused_access_prep_task_id' exists in housekeeper_task_focus.")
    else:
        print("[FAIL] Column 'focused_access_prep_task_id' is MISSING in housekeeper_task_focus.")
        failed = True

    sql_focus_check = """
    SELECT con.conname AS constraint_name, pg_get_constraintdef(con.oid) AS constraint_definition
    FROM pg_constraint con
    JOIN pg_class t ON t.oid = con.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = 'public' AND t.relname = 'housekeeper_task_focus' AND con.contype = 'c';
    """
    focus_checks = run_db_query(sql_focus_check)
    type_check_ok = False
    focus_check_ok = False
    for r in focus_checks:
        if "focus_type" in r["constraint_definition"] and "access_prep" in r["constraint_definition"]:
            type_check_ok = True
            print(f"[PASS] focus_type check constraint verified: {r['constraint_definition']}")

        if r["constraint_name"] == "housekeeper_task_focus_valid_focus_check":
            definition = r["constraint_definition"]
            if ("focused_access_prep_task_id" in definition and
                "focused_cleaning_task_id" in definition and
                "focused_field_assistance_task_id" in definition and
                "access_prep" in definition):
                focus_check_ok = True
                print(f"[PASS] housekeeper_task_focus valid focus invariant verified: {definition}")
            else:
                print(f"[FAIL] housekeeper_task_focus constraint definition is incomplete: {definition}")
                failed = True

    if not type_check_ok:
        print("[FAIL] housekeeper_task_focus focus_type check constraint does not contain 'access_prep'.")
        failed = True
    if not focus_check_ok:
        print("[FAIL] housekeeper_task_focus_valid_focus_check constraint is MISSING or incomplete.")
        failed = True

    # 6. Verify Unique active task by booking_id and source_event_id uniqueness
    print("\n--- 6. Unique Constraints & Indexes Verification ---")
    sql_indexes = """
    SELECT indexname, indexdef
    FROM pg_indexes
    WHERE schemaname = 'public' AND tablename = 'access_prep_tasks';
    """
    indexes = run_db_query(sql_indexes)
    active_booking_unique_ok = False
    for idx in indexes:
        if "access_prep_tasks_active_booking_unique" in idx["indexname"] or (
            "booking_id" in idx["indexdef"] and "status" in idx["indexdef"] and "done" in idx["indexdef"]
        ):
            active_booking_unique_ok = True
            print(f"[PASS] Unique active task index verified: {idx['indexdef']}")

    if not active_booking_unique_ok:
        print("[FAIL] Unique active task index by booking_id (excluding terminal states) is MISSING.")
        failed = True

    sql_event_indexes = """
    SELECT indexname, indexdef
    FROM pg_indexes
    WHERE schemaname = 'public' AND tablename = 'access_prep_task_events';
    """
    event_indexes = run_db_query(sql_event_indexes)
    event_unique_ok = False
    for idx in event_indexes:
        if idx["indexname"] == "access_prep_task_events_source_event_unique":
            if "WHERE" not in idx["indexdef"]:
                event_unique_ok = True
                print(f"[PASS] Unique source event index verified (no partial filter): {idx['indexdef']}")
            else:
                print(f"[FAIL] Unique source event index is partial (has WHERE clause): {idx['indexdef']}")
                failed = True
    if not event_unique_ok and not failed:
        print("[FAIL] Unique source event index 'access_prep_task_events_source_event_unique' is MISSING.")
        failed = True

    # 7. Check RLS and Grants (no public/anon/authenticated permissions)
    print("\n--- 7. Security Grants & RLS Verification ---")
    sql_rls = """
    SELECT relrowsecurity AS rls_enabled
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relname IN ('access_prep_tasks', 'access_prep_task_events');
    """
    rls_rows = run_db_query(sql_rls)
    if len(rls_rows) == 2 and all(r["rls_enabled"] for r in rls_rows):
        print("[PASS] RLS is enabled on new tables.")
    else:
        print("[FAIL] RLS is NOT enabled on both new tables.")
        failed = True

    sql_grants = """
    SELECT table_name, grantee, privilege_type
    FROM information_schema.role_table_grants
    WHERE table_schema = 'public' AND table_name IN ('access_prep_tasks', 'access_prep_task_events') AND grantee IN ('public', 'anon', 'authenticated');
    """
    grant_rows = run_db_query(sql_grants)
    if len(grant_rows) == 0:
        print("[PASS] Security grants verified: no public/anon/authenticated roles have table access.")
    else:
        print(f"[FAIL] Security grants violation: found active privileges for public/anon/authenticated roles:")
        for r in grant_rows:
            print(f"  - Table '{r['table_name']}' allows '{r['privilege_type']}' to '{r['grantee']}'")
        failed = True

    print("\nSummary:")
    if failed:
        print("RESULT: FAIL")
        sys.exit(1)
    else:
        print("RESULT: PASS")
        sys.exit(0)

if __name__ == "__main__":
    run_tests()
