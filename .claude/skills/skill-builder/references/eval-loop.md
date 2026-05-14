# Eval Loop Guide

Workflow for running test cases, grading results, and iterating on a skill until it's production-ready.

This section is one continuous sequence — don't stop partway through.

---

## Setup: Test Cases

Before running evals, save test cases to `evals/evals.json` alongside the skill directory. Write 2-3 realistic prompts — the kind of thing a real user would actually say. Share them with the user and confirm before running.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

Don't write assertions yet — just the prompts. Assertions come in Step 2 while runs are in progress.

See `references/schemas.md` for the full schema including the `assertions` field.

---

## Step 1: Spawn All Runs in the Same Turn

For each test case, spawn two subagents in the same turn — one with the skill, one without. Launch everything at once so runs finish around the same time.

Put results in `<skill-name>-workspace/` as a sibling to the skill directory. Organize by iteration (`iteration-1/`, `iteration-2/`, etc.), and within that, each test case gets a named directory (use a descriptive name based on what it's testing — not just `eval-0`).

**With-skill run prompt:**
```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files if any, or "none">
- Save outputs to: <workspace>/iteration-<N>/<eval-name>/with_skill/outputs/
- Outputs to save: <what the user cares about>
```

**Baseline run** (same prompt, no skill):
```
Execute this task:
- Task: <eval prompt>
- Input files: <eval files if any, or "none">
- Save outputs to: <workspace>/iteration-<N>/<eval-name>/without_skill/outputs/
- Outputs to save: <what the user cares about>
```

**For improving an existing skill** (not creating from scratch), use the old version as baseline instead of no-skill. Snapshot it first:
```bash
cp -r <skill-path> <workspace>/skill-snapshot/
```

Write an `eval_metadata.json` for each test case (assertions empty for now):

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": []
}
```

---

## Step 2: Draft Assertions While Runs Are in Progress

Don't wait for runs to finish. Use the time to draft quantitative assertions for each test case and explain them to the user.

Good assertions are objectively verifiable and have descriptive names — someone glancing at results should immediately understand what each one checks. Subjective skills (writing style, design quality) are better evaluated qualitatively; don't force assertions onto things that need human judgment.

Update `eval_metadata.json` files and `evals/evals.json` with assertions once drafted.

---

## Step 3: Capture Timing Data

When each subagent task completes, you receive a notification containing `total_tokens` and `duration_ms`. Save this data immediately to `timing.json` in the run directory — this is the only opportunity to capture it:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

Process each notification as it arrives rather than batching them.

---

## Step 4: Grade, Aggregate, and Launch the Viewer

Once all runs are done:

**1. Grade each run** — spawn a grader subagent using `agents/grader.md`. It evaluates each assertion against the outputs and saves results to `grading.json` in each run directory.

`grading.json` expectations array must use: `text`, `passed`, `evidence` (not `name`/`met`/`details`).

For assertions that can be checked programmatically, write and run a script — faster, more reliable, reusable.

**2. Aggregate into benchmark** — run from the skill-builder directory:

```bash
python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
```

This produces `benchmark.json` and `benchmark.md` with pass_rate, time, and tokens for each configuration, with mean ± stddev and delta.

Put each with_skill version before its baseline counterpart.

**3. Do an analyst pass** — read the benchmark data and surface patterns the aggregate stats might hide. Read `agents/analyzer.md` (the "Analyzing Benchmark Results" section) for what to look for:
- Assertions that always pass regardless of skill (non-discriminating)
- High-variance evals (possibly flaky)
- Time/token tradeoffs

**4. Launch the viewer:**

```bash
nohup python <skill-builder-path>/eval-viewer/generate_review.py \
  <workspace>/iteration-N \
  --skill-name "my-skill" \
  --benchmark <workspace>/iteration-N/benchmark.json \
  > /dev/null 2>&1 &
VIEWER_PID=$!
```

For iteration 2+, also pass `--previous-workspace <workspace>/iteration-<N-1>`.

**Headless/no-display environments:** Use `--static <output_path>` to write a standalone HTML file instead of starting a server. Feedback downloads as `feedback.json` when the user clicks "Submit All Reviews."

**IMPORTANT:** Generate the eval viewer BEFORE evaluating inputs yourself. Get results in front of the user ASAP — human review comes before your own analysis.

Tell the user: "I've opened the results in your browser. There are two tabs — 'Outputs' lets you click through each test case and leave feedback, 'Benchmark' shows the quantitative comparison. When you're done, come back here and let me know."

---

## Step 5: Read the Feedback

When the user tells you they're done, read `feedback.json`:

```json
{
  "reviews": [
    {"run_id": "eval-0-with_skill", "feedback": "the chart is missing axis labels", "timestamp": "..."},
    {"run_id": "eval-1-with_skill", "feedback": "", "timestamp": "..."},
    {"run_id": "eval-2-with_skill", "feedback": "perfect, love this", "timestamp": "..."}
  ],
  "status": "complete"
}
```

Empty feedback means the user thought it was fine. Focus improvements on test cases where the user had specific complaints.

Kill the viewer server when done:

```bash
kill $VIEWER_PID 2>/dev/null
```

---

## Improving the Skill

After reading feedback, improve the skill before re-running. How to think about it:

1. **Generalize from the feedback.** You're iterating on a few examples but the skill will run millions of times. Don't make fiddly overfitty changes. If there's a stubborn issue, try different metaphors or patterns — it's cheap to try.

2. **Keep the prompt lean.** Remove things that aren't pulling their weight. Read the transcripts (not just the final outputs) — if the skill wastes time on unproductive steps, cut the instructions causing them.

3. **Explain the why.** Behind every instruction, understand *why* it matters and transmit that understanding into the skill. If you find yourself writing ALWAYS or NEVER in all caps, that's a yellow flag — reframe and explain the reasoning instead.

4. **Look for repeated work across test cases.** If all 3 test cases resulted in the subagent writing a similar helper script, that's a signal the skill should bundle that script. Write it once in `scripts/`, and tell the skill to use it.

---

## Iteration Loop

After improving the skill:

1. Apply improvements to the skill
2. Rerun all test cases into `iteration-<N+1>/` — include baseline runs
3. Launch the viewer with `--previous-workspace` pointing at the previous iteration
4. Wait for the user to review
5. Read new feedback, improve again, repeat

Keep going until:
- The user says they're happy
- Feedback is all empty (everything looks good)
- You're not making meaningful progress

---

## Advanced: Blind Comparison

For rigorous comparison between two versions (e.g., "is the new version actually better?"), read `agents/comparator.md` and `agents/analyzer.md`. The idea: give two outputs to an independent agent without telling it which is which, let it judge quality, then analyze why the winner won.

This is optional and most skills don't need it. The human review loop is usually sufficient.
