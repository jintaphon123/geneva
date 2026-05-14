---
name: wrapup
description: End-of-session wrap-up for Bond's MyBrain. Saves memories, writes session summary, updates decisions log, and pushes summary to Bond AI Brain NotebookLM notebook. Trigger on /wrapup, "wrap up", "end session", "สรุป session", "จบ session".
---

# WrapUp Skill — Bond's MyBrain

Runs at the end of every session. Handles all session-end tasks in one shot.

Bond AI Brain notebook ID: `664fde45-bda9-4072-85ec-27ed2cbd15f5`

---

## Step 1: Review the Session

Look back through the full conversation and identify:
- **Decisions made** — what was decided and why
- **Work completed** — what was built, configured, or shipped
- **Key learnings** — anything non-obvious or surprising
- **Open threads** — anything unfinished to pick up next time
- **New info about Bond** — preferences, context, constraints revealed

---

## Step 2: Update Memory Files

Check `/Users/jintaphon/.claude/projects/-Users-jintaphon-Documents-Code-MyBrain/memory/MEMORY.md`.

Save or update memories as needed:
- `feedback` — corrections or confirmed approaches from this session
- `project` — ongoing work, goals, deadlines that future sessions need
- `user` — new info about Bond's role, preferences, or working style
- `reference` — external tools or systems referenced

Rules:
- Don't duplicate existing memories — update them
- Convert relative dates to absolute (e.g., "Thursday" → "2026-05-01")
- Include **Why:** and **How to apply:** for feedback and project entries
- Don't save things derivable from code or git history

---

## Step 3: Write Session Summary

Save to `templates/session-summary.md` (overwrite, not append — this is a rolling single-file summary):

```markdown
# Session Summary — YYYY-MM-DD

## What We Did
- Bullet points of key work

## Decisions Made
- Decision + rationale

## Key Learnings
- Non-obvious insights

## Open Threads
- Anything to pick up next time

## Tools & Systems Touched
- List of tools, files, services involved
```

---

## Step 4: Update decisions/log.md

For every significant decision made this session, append a new row to `decisions/log.md`:

Format:
```
| YYYY-MM-DD | [decision] | [rationale] | [status: decided/pending/reversed] |
```

Do NOT batch at end — log as decisions happen during the session.

---

## Step 5: Check scratch/

```bash
find /Users/jintaphon/Documents/Code/MyBrain/scratch -mindepth 1 -not -name '.gitignore' 2>/dev/null
```

If non-empty, ask Bond: "งานนี้เสร็จแล้วรึยัง? ถ้าใช่ให้บอกฉัน แล้วฉันจะลบ scratch/ ให้"
If Bond says yes: `rm -f /Users/jintaphon/Documents/Code/MyBrain/scratch/*`

---

## Step 6: Push to Bond AI Brain (NotebookLM)

Do NOT push the session summary from Step 3. Instead, write a **separate, richer
knowledge document** specifically for NotebookLM — optimized for future semantic
retrieval, not for Bond to skim.

### What to include in the NB document

The NB document must answer these questions in full prose + bullets, not just headers:

**1. Context — Why this session happened**
- What problem or question Bond brought to this session
- What was the starting point / what Bond already knew
- What was at stake or time-sensitive

**2. Decisions — Full reasoning, not just outcomes**
- Every significant decision: what was decided, what alternatives were considered,
  why this option was chosen, what risks were accepted, what conditions apply
- Include the reasoning chain, not just the conclusion

**3. Key Insights — Non-obvious learnings**
- Anything that contradicted prior assumptions
- Market data, competitor findings, framework applications — with sources and numbers
- What Bond now knows that he didn't know before

**4. Strategic State — Where things stand**
- Current status of every active project touched this session
- What's been validated vs what's still an assumption
- What the next critical action is for each project and why

**5. Open Questions — Unresolved threads**
- Each open thread with enough context so future sessions can pick it up cold
- Why it matters, what needs to happen to resolve it, what's blocking it

**6. Bond's Thinking — Preferences and patterns revealed**
- Any new preferences, constraints, or working style signals Bond showed
- Corrections Bond made to prior assumptions or plans

### Format

```
# Bond AI Brain — Session Log [YYYY-MM-DD]

## Session Context
[2–4 sentences: what prompted this session, what Bond was trying to figure out]

## Full Decision Log

### [Decision Title]
**Decision:** [what was decided]
**Alternatives considered:** [what else was on the table]
**Why this choice:** [full reasoning]
**Conditions / risks accepted:** [what could invalidate this]

[repeat for each decision]

## Key Insights & Data

### [Topic]
[Full explanation — include numbers, sources, frameworks applied, implications]

[repeat for each insight]

## Strategic State as of [date]

### [Project Name]
- Status: [current state]
- What's validated: [...]
- What's still assumed: [...]
- Next critical action: [exact action + why it's the right next step]

## Open Threads

### [Thread Title]
- **What it is:** [full description]
- **Why it matters:** [stakes]
- **What needs to happen:** [specific next step]
- **What's blocking it:** [if anything]

## Bond's Preferences & Patterns
- [Observed preference or pattern + evidence from this session]
```

### Push command

```bash
export PATH="$HOME/bin:$PATH"

FILENAME="/tmp/nb-session-$(date +%Y-%m-%d).md"

cat > "$FILENAME" << 'NBEOF'
[NB document content]
NBEOF

notebooklm source add "$FILENAME" \
  --notebook 664fde45-bda9-4072-85ec-27ed2cbd15f5

rm -f "$FILENAME"
```

If notebooklm auth fails → skip this step, warn Bond, proceed.
If same-day session already pushed → append counter: `nb-session-YYYY-MM-DD-2.md`

---

## Step 7: Confirm

Tell Bond:
- How many memories were saved/updated
- Whether session summary was pushed to AI Brain (or skipped if auth failed)
- Open threads to pick up next time

Keep it tight — no need to read back the full summary.

---

## Error Handling

| Error | Action |
|--|--|
| notebooklm not on PATH | `export PATH="$HOME/bin:$PATH"` then retry |
| Auth expired | Warn Bond, skip Step 6, complete other steps |
| AI Brain notebook deleted | `notebooklm create "Bond AI Brain" --json` → update this skill with new ID |
| Nothing meaningful to save | Say so, don't force empty entries |
