from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "runtime/supabase/supabase/migrations/20260619083246_phase6_combined_housekeeping_queue.sql"
QUEUE = ROOT / "runtime/supabase/supabase/functions/housekeeping-handler/queue.ts"
HANDLER = ROOT / "runtime/supabase/supabase/functions/housekeeping-handler/index.ts"


def require(text: str, needle: str, failure: str) -> None:
    if needle not in text:
        raise AssertionError(failure)


def main() -> None:
    migration = MIGRATION.read_text()
    queue = QUEUE.read_text()
    handler = HANDLER.read_text()

    require(migration, "CREATE OR REPLACE FUNCTION public.claim_housekeeping_task(", "claim RPC missing")
    require(migration, "FOR UPDATE", "claim RPC must lock the task row")
    require(migration, "'already_claimed'", "claim RPC must return already_claimed")
    require(migration, "assigned_housekeeper_id IS NOT NULL", "claim must detect an existing assignee")
    require(migration, "housekeeper_task_focus", "claim must update operator focus atomically")
    require(migration, "focused_cleaning_task_id = NULL", "reassignment must invalidate old cleaning focus")
    require(migration, "focused_access_prep_task_id = NULL", "reassignment must invalidate old access focus")
    require(migration, "admin_priority_rank", "admin priority must remain the first queue rank")
    require(migration, "sort_key", "pagination must use a stable keyset cursor")

    require(queue, "export async function claimHousekeepingTask(", "queue claim client missing")
    require(queue, 'supabase.rpc("claim_housekeeping_task"', "queue claim client must use RPC")
    require(handler, "claimHousekeepingTask(", "LINE handler must invoke atomic claim")
    require(handler, 'intent.action === "acknowledge_task"', "claim must be connected to the accept button")

    print("phase6 multi-operator queue contract passed")


if __name__ == "__main__":
    main()
