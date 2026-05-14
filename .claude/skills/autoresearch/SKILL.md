---
name: autoresearch
description: >
  Karpathy-style autonomous self-improvement loop for any target file.
  Optimizes one file by a measurable metric through repeated edit → eval →
  keep/revert cycles. Five modes: setup (new session), run (single iteration),
  loop (autonomous ScheduleWakeup loop), resume (restore session), status (dashboard).
  Use when: "optimize this file", "improvement loop", "autoresearch",
  "make this faster/smaller/better", "autonomous experiment", "run overnight".
argument-hint: "setup <file> <eval_cmd> <metric> <direction> | run [id] | loop <id> [stop] | resume [id] | status [id]"
allowed-tools: Read, Write, Edit, Bash, Agent
---

# Autoresearch — Autonomous Self-Improvement Loop

One file. One metric. One change per iteration. Keep what improves, revert what doesn't.

State lives in `.autoresearch/<session-id>.json` in the project root. Each `run` iteration spawns an isolated subagent — the improvement loop never accumulates in the main context window.

## Mode Detection

Parse the first word of `$ARGUMENTS` to determine mode:

| First word | Mode |
|-----------|------|
| `setup` | Create a new session |
| `run` | Single improvement iteration |
| `loop` | Autonomous loop via ScheduleWakeup |
| `resume` | Restore and inspect a session |
| `status` | Dashboard |
| (no args) | `status` |
| (anything else) | Ask: "Which mode? setup / run / loop / resume / status" |

---

## State Schema

All session state lives in one file: `.autoresearch/<session-id>.json`

```json
{
  "session_id": "search-20260501-143022",
  "target_file": "src/api/search.py",
  "eval_cmd": "pytest bench.py --tb=no -q",
  "metric": "p50_ms",
  "metric_direction": "lower",
  "quality_gate": 95,
  "max_loops": 2,
  "baseline_score": 320.0,
  "best_score": 320.0,
  "loop_active": false,
  "loop_count": 0,
  "consecutive_crashes": 0,
  "created_at": "2026-05-01T14:30:22Z",
  "last_run_at": null,
  "runs": []
}
```

Each entry in `runs`:
```json
{"run_id": 1, "score": 285.0, "delta": -35.0, "summary": "added response caching", "status": "keep"}
```

`status`: `keep` | `discard` | `crash`

Session ID format: `{target_file_stem}-{YYYYMMdd-HHmmss}` (e.g., `search-20260501-143022`).

---

## Mode 1 — setup

**Args:** `setup <target_file> <eval_cmd> <metric> <direction> [quality_gate]`

1. **Validate args.** All four required: `target_file`, `eval_cmd`, `metric`, `direction`. `direction` must be `higher` or `lower`. `quality_gate` defaults to 95 if omitted; prompt for it explicitly when metric is a raw numeric target (ms, bytes) rather than a 0-100 score.

2. **Verify target file:**
   ```bash
   ls -la <target_file>
   ```
   Stop if not found.

3. **Verify git repo** (required for revert safety):
   ```bash
   git rev-parse --git-dir
   ```
   Stop if not a git repo. Tell user: `git init && git add . && git commit -m "initial"` first.

4. **Establish baseline:**
   ```bash
   mkdir -p .autoresearch
   <eval_cmd>
   ```
   Parse `<metric>: <value>` from stdout. Stop if metric not found — tell user to verify the eval command works manually first.

5. **Generate session ID:** `{target_file_stem}-{YYYYMMdd-HHmmss}` using current timestamp.

6. **Write `.autoresearch/<session-id>.json`** with all fields. Set `baseline_score` and `best_score` to the parsed eval result.

7. **Confirm:**
   ```
   Session created: <session-id>
     Target:       <target_file>
     Metric:       <metric> (<direction> is better)
     Quality gate: <quality_gate>
     Baseline:     <score>

   Next:
     Single run  — /autoresearch run <session-id>
     Auto loop   — /autoresearch loop <session-id>
   ```

---

## Mode 2 — run

**Args:** `run [session-id]`

If no session-id: `ls .autoresearch/*.json 2>/dev/null`. Auto-select if exactly one exists. If multiple, list them and ask user to pick.

1. **Load JSON:**
   ```bash
   cat .autoresearch/<session-id>.json
   ```

2. **Check quality gate.** If already reached, stop:
   ```
   Quality gate already reached: <metric> = <best_score>. No further runs needed.
   ```

3. **Check crash limit.** If `consecutive_crashes >= 5`, stop:
   ```
   5 consecutive crashes. Pausing. Fix the eval command or target file before resuming.
   ```

4. **Spawn iteration subagent** via the Agent tool (`subagent_type: general-purpose`). Substitute all `<placeholders>` from the session JSON before calling:

   ```
   You are running ONE autoresearch iteration. Your ONLY output must be a single JSON
   object — no explanation, no markdown, no other text.

   ## Session
   - Target file: <target_file>
   - Eval command: <eval_cmd>
   - Metric: <metric> (<metric_direction> is better)
   - Best score so far: <best_score>
   - Run number: <len(runs) + 1>

   ## History (last 10 runs)
   <format each as: run_id | score | delta | status | summary>
   (empty if no runs yet)

   ## Strategy by run count
   - Runs 1-5:  low-hanging fruit (caching, early exits, obvious redundancy)
   - Runs 6-15: systematic (vary one parameter at a time)
   - Runs 16-30: structural (algorithm swaps, data structure changes)
   - Runs 30+:  radical (completely different approach)

   ## Your steps
   1. Read the current content of <target_file>
   2. Review history — what worked, what failed, what hasn't been tried
   3. Choose ONE change. One variable only. Do not change multiple things.
   4. Edit <target_file> with that ONE change.
   5. Run the eval: <eval_cmd>
   6. Parse the metric: look for "<metric>: <number>" in stdout
   7. Compare new score to best score (<best_score>). Is it an improvement (<metric_direction>)?
   8. If improvement → keep the change (do nothing to revert).
      If no improvement OR crash → revert: git checkout -- <target_file>

   ## Return format (JSON only, no other text)
   {"score": <float or null>, "delta": <float or null>, "summary": "<one sentence: what changed and why>", "kept": <true|false>, "crashed": <true|false>}

   ## Hard rules
   - ONE change per iteration. Non-negotiable.
   - NEVER modify the eval command or any file it depends on. It is ground truth.
   - No new dependencies.
   - Simplicity wins: equal score with simpler code is a keep.
   - Eval exits non-zero or metric not parseable = crash → revert → return crashed: true, score: null.
   ```

5. **Parse subagent response.** Extract `{score, delta, summary, kept, crashed}`.

6. **Determine status:**
   - `crashed: true` → status = `"crash"`
   - `kept: true` → status = `"keep"`
   - else → status = `"discard"`

7. **Update JSON:**
   - Append to `runs`: `{run_id: <next>, score, delta, summary, status}`
   - If `keep`: set `best_score = score`, reset `consecutive_crashes = 0`
   - If `crash`: `consecutive_crashes += 1`
   - If `discard`: reset `consecutive_crashes = 0`
   - Set `last_run_at` to current ISO timestamp
   - Write JSON back to `.autoresearch/<session-id>.json`

8. **Report:**
   ```
   Run <N>: KEEP | DISCARD | CRASH
     Score:  <score>  (best: <best_score>, delta: <delta>)
     Change: <summary>
   ```

9. **Re-check quality gate.** If now reached, declare success:
   ```
   Quality gate reached after <N> runs. Best <metric>: <best_score>.
   ```

---

## Mode 3 — loop

**Args:** `loop <session-id> [stop]`

### `loop <session-id>` — start or continue

1. Load JSON. Run quality gate and crash limit checks (same as Mode 2, steps 2–3). Stop if either triggered.

2. Check `loop_count >= max_loops`:
   ```
   Max improvement loops reached (2/2).
   Use /autoresearch run <session-id> to continue without the loop limit.
   ```

3. Execute one full iteration (Mode 2, steps 4–9).

4. Re-check quality gate after iteration. If reached: set `loop_active: false`, write JSON, stop — do NOT schedule another wakeup.

5. If not yet at gate: increment `loop_count`, set `loop_active: true`, write JSON.

6. Call `ScheduleWakeup`:
   - `delaySeconds: 270`
   - `reason: "autoresearch loop — <session-id>, run <N> done, best <metric>: <best_score>"`
   - `prompt: "/autoresearch loop <session-id>"`

7. Confirm:
   ```
   Loop scheduled: <session-id>
     Best:       <metric> = <best_score>
     Loop count: <loop_count>/<max_loops>
     Next run:   ~4.5 min

   To stop: /autoresearch loop <session-id> stop
   ```

### `loop <session-id> stop`

1. Load JSON. Set `loop_active: false`, `loop_count: 0`. Write JSON.
2. **Important:** ScheduleWakeup fires cannot be cancelled mid-flight. If a scheduled wakeup fires after `stop`, the loop mode re-checks `loop_count` (now 0), runs one more iteration, then re-schedules. To fully stop after a `stop` command, respond "stop" when the next wakeup fires.
3. Confirm:
   ```
   Loop stopped: <session-id>
     Runs completed: <len(runs)>
     Best score:     <best_score>
   ```

---

## Mode 4 — resume

**Args:** `resume [session-id]`

If no ID: `ls .autoresearch/*.json 2>/dev/null`, show a one-line summary per session, ask user to pick.

1. Load JSON.

2. Display current state:
   ```
   Session: <session-id>
     Target:       <target_file>
     Metric:       <metric> (<metric_direction>)
     Baseline:     <baseline_score>
     Best:         <best_score> (<pct change>% from baseline)
     Quality gate: <quality_gate> — <REACHED | not reached>
     Runs:         <total> total — <kept> kept / <discarded> discarded / <crashed> crashed
     Last run:     <last_run_at | "never">

   Recent runs (last 5):
   run | score | delta | status | summary
   ----|-------|-------|--------|--------
   ...

   Patterns observed:
   <Analyze kept vs discarded. State 1-3 plain-English patterns.
    e.g.: "Caching strategies: 3 kept. Structural rewrites: consistently discarded.">
   ```

3. Offer:
   ```
   Continue with:
     Single run  — /autoresearch run <session-id>
     Auto loop   — /autoresearch loop <session-id>
   ```

---

## Mode 5 — status

**Args:** `status [session-id]`

### Single session (`status <session-id>`)

Full detail view — all JSON fields + complete run history table:

```
Session: <session-id>
  Target:       <target_file>
  Eval:         <eval_cmd>
  Metric:       <metric> (<metric_direction>)
  Baseline:     <baseline_score>
  Best:         <best_score> (<pct>% from baseline)
  Quality gate: <quality_gate> — REACHED | not reached
  Loop:         active (<loop_count>/<max_loops>) | stopped
  Runs:         <total> — <kept> kept / <discarded> discarded / <crashed> crashed
  Last run:     <last_run_at>

run | score  | delta  | status  | summary
----|--------|--------|---------|--------
  1 | 285.0  | -35.0  | keep    | added response caching
  2 | 290.0  |  +5.0  | discard | removed null checks (regression)
...
```

### Dashboard (no ID)

```bash
ls .autoresearch/*.json 2>/dev/null
```

For each file, load and display one row:

```
SESSION-ID                  TARGET                BEST     RUNS  LOOP      LAST RUN
search-20260501-143022      src/api/search.py     285ms    12    active    2026-05-01
bundle-20260430-091500      src/index.ts          412KB    8     stopped   2026-04-30
```

If no `.autoresearch/*.json` files exist:
```
No autoresearch sessions found.
Start one: /autoresearch setup <file> <eval_cmd> <metric> <direction>
```

---

## Quality Gate Logic

| Direction | Success condition |
|-----------|------------------|
| `higher` | `best_score >= quality_gate` |
| `lower` | `best_score <= quality_gate` |

Default `quality_gate: 95` works naturally for LLM-judge metrics (0-100 scale). For raw numeric metrics (ms, bytes), the user sets their own target number at setup time — prompt for it if the 5th arg is not provided and the metric doesn't look like a 0-100 score.

---

## Hard Rules

- **One change per iteration.** The subagent changes exactly one thing. Multiple variable changes in one run invalidate the signal.
- **Never modify the eval command or its supporting files.** It is fixed ground truth. Hard stop if detected.
- **No new dependencies.** Only what's already in the project.
- **Simplicity wins.** Equal score with simpler code is a keep. Removing code that achieves the same result is always preferred.
- **5 consecutive crashes → stop.** Alert user. Do not continue burning cycles on a broken setup.
- **Context isolation.** Every `run` iteration spawns a subagent via the Agent tool. The improvement loop never accumulates in the main context window.
- **Token economy.** Eval output is compressed to `{score, delta, summary}` before storage. Never store raw eval stdout in the JSON.
- **Git is the safety net.** Revert is always `git checkout -- <target_file>`. The session JSON tracks outcomes; git tracks file state.
- **Max 2 improvement loops.** `loop` mode runs at most `max_loops` (default: 2) ScheduleWakeup cycles. After that, user must manually invoke `run` or acknowledge the limit.
