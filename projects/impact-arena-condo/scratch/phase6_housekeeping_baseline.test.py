#!/usr/bin/env python3
import subprocess

COMMANDS = [
    ["deno", "test", "--allow-env",
     "runtime/supabase/supabase/functions/housekeeping-handler/commands.test.ts",
     "runtime/supabase/supabase/functions/housekeeping-handler/state.test.ts",
     "runtime/supabase/supabase/functions/housekeeping-handler/index.test.ts"],
    ["node", "scratch/phase4_housekeeping_action.test.mjs"],
    ["node", "scratch/phase4_housekeeping_escalation_monitor.test.mjs"],
    ["node", "scratch/phase4_internal_ops_agent_harness.test.mjs"],
    ["node", "scratch/phase4_internal_ops_snapshot.test.mjs"],
    ["python3", "scratch/phase5_slice8_access_capabilities.test.py"],
]

for command in COMMANDS:
    print(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, text=True)
    if result.returncode:
        print(f"Command failed with exit code: {result.returncode}")
        raise SystemExit(result.returncode)

print("PHASE 6 HOUSEKEEPING BASELINE PASSED")
