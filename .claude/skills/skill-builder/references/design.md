# Skill Design Guide

Complete workflow for designing and building a Claude Code skill from scratch.

---

## Discovery Interview

Run the interview before writing any files. Ask one round at a time — move to the next round only after the user answers. Skip rounds that the user already answered upfront.

### Round 1: Goal & Name

*A clear goal prevents scope creep. The name becomes the `/slash-command`.*

- What does this skill do? What problem does it solve or workflow does it automate?
- What should we call it? (Suggest a name based on their answer — lowercase, hyphens, max 64 chars)

### Round 2: Trigger

*The `description` field is how Claude decides whether to load your skill. Bad trigger words mean Claude never uses it. Too broad means Claude fires it when you don't want it.*

- What would someone say to trigger this? (Get 2-3 natural language phrases)
- Should it be user-only (`/slash-command`), Claude-auto-invocable, or both?
- Does it accept arguments? If so, what? (e.g., a topic, a URL, a file path)

### Round 3: Step-by-Step Process

*Claude follows instructions literally. Vague steps produce vague results. Specific steps produce consistent output every time.*

- Walk through exactly what should happen from trigger to output. What's step 1? Step 2? Keep going.
- For each step: does Claude do it directly, or delegate to a subagent/script?
- Does this need to be conversational (back-and-forth with the user) or is it a fire-and-forget task?

### Round 4: Inputs, Outputs & Dependencies

*Skills that don't specify where to find inputs or where to put outputs produce inconsistent results.*

- What inputs does the skill need? (Files, API responses, user arguments, live data)
- What does it produce? (Files, text output, structured data) Where do outputs go?
- Does it need external APIs, scripts, or tools? Which ones?
- Does it need reference files, style guides, templates, or examples?

### Round 5: Guardrails & Edge Cases

*Skills without guardrails can produce unexpected behavior — wrong outputs, unnecessary API costs, or unintended actions.*

- What could go wrong? What are the common failure modes?
- What should this skill NOT do? Any hard boundaries?
- Are there cost concerns? (API calls, AI image generation, etc.)
- Any ordering or dependency constraints? (e.g., "must check X before doing Y")

---

## Bundle Skill Gate

*Assess after Round 5, before Confirmation. This gate is MANDATORY — never skip it.*

| Criteria | Score 1 if... |
|----------|---------------|
| Multiple distinct thinking modes | The skill requires research, then analysis, then critique, then synthesis — different mindsets per phase |
| Quality gate would help | There's a clear "good enough" standard for output that could be checked before delivery |
| Independent perspectives add value | Having one phase blind to another's output would improve quality |
| Pipeline handoff is natural | Each phase produces an artifact that clearly becomes the next phase's input |
| Persona specialization helps | Different character traits per phase (curious vs. skeptical vs. decisive) would genuinely improve output |

**Score < 2:** Build as a standard skill. Skip to Round 6.

**Score ≥ 2:** MUST build as Bundle Skill. No exceptions. All phases MUST live in separate `references/` files — never inline in SKILL.md.

> Tell the user: "This skill scores [N]/5 on the Bundle Skill Gate — it must be built as a Bundle Skill with separate sub-skill files per phase. I'll ask a few more questions to design it properly."

Then run Rounds B1–B3:

### Round B1: Sub-Skills Design

*Each sub-skill needs a Role (what it does), Purpose (why it exists), and Character/Persona (what personality produces the best output for that phase).*

- How many distinct phases does this skill have? List them.
- For each phase:
  - **Role:** What specific task does this phase perform?
  - **Purpose:** Why does it exist — what would break without it?
  - **Character:** What human expert would be best at this? (e.g., "detective journalist — never satisfied with surface data", "opposing lawyer — finds flaws in every argument", "COO briefing CEO — clear, decisive, no padding")
- Does any phase need to be "blind" to a previous phase's output?

### Round B2: Quality Gate Design

*The quality gate is the skill's immune system. Without a defined threshold and scoring rubric, output quality is inconsistent.*

- What does "high quality" look like for this skill's final output? Be specific.
- What should the quality threshold be? (Recommended: 95%)
- What are the 3–4 scoring dimensions (0–25 each = 0–100 total)? Example:
  - D1: Factual grounding (claims backed by evidence)
  - D2: Framework depth (frameworks applied to the specific situation, not generically)
  - D3: Critique rigor (genuine flaws found, not token criticism)
  - D4: Actionability (user can act on this without significant extra work)
- What happens when a dimension scores low? Which phase gets the loop-back?
- Maximum loops before forcing output with a warning? (Recommended: 2)

### Round B3: Pipeline Confirmation

*Misunderstanding the handoff between phases is the most common Bundle Skill failure mode.*

- For each phase: what does it receive as input, and what exactly does it output?
- Are there conditional branches? (e.g., "if Phase 2 fails, skip to Phase 4")
- What is the final output format that reaches the user?

After Rounds B1–B3, add this to the Confirmation Summary:

```
## Bundle Skill Design
Sub-skills ([N] total):
1. [Phase name] — [Role] | Character: [persona]
2. [Phase name] — [Role] | Character: [persona]
...

Quality Gate:
- Threshold: [X]%
- Dimensions: D1 [name], D2 [name], D3 [name], D4 [name]
- Loop-back routing: [which dimension → which phase]
- Max loops: [N]

File structure:
.claude/skills/[name]/
├── SKILL.md          (Orchestrator)
└── references/
    ├── [phase-1].md
    ├── [phase-2].md
    └── [quality-judge].md
```

---

## Round 6: Confirmation

After all rounds, summarize your understanding back to the user:

```
## Skill Summary: [name]

**Goal:** [one sentence]
**Trigger:** `/name` + [natural language phrases]
**Arguments:** [what it accepts, or "none"]

**Process:**
1. [step]
2. [step]
...

**Inputs:** [what it reads/needs]
**Outputs:** [what it produces + where]
**Dependencies:** [APIs, scripts, agents, reference files]
**Guardrails:** [what can go wrong, what to avoid]
```

Ask: "Does this capture it? Anything to add or change?" Only proceed to building once the user confirms.

**Skipping rounds:** If the user provides enough context upfront, skip rounds that are already answered. Don't re-ask what you already know.

---

## Build Phase — Standard Skill

### Step 1: Choose the skill type

- **Task skills** (most common) — step-by-step instructions for a specific action. Examples: generate a report, summarize a PR, deploy code.
- **Reference skills** — knowledge Claude applies to current work without performing an action. Examples: coding conventions, API patterns, style guides.
- **Bundle Skills** — use when Bundle Skill Gate scored ≥ 2. See Build Phase — Bundle Skill below.

### Step 2: Configure frontmatter

Only set fields you actually need:

- `name` — matches directory name. Lowercase, hyphens, max 64 chars.
- `description` — "Use when someone asks to [action], [action], or [action]." Include natural keywords from trigger phrases.
- `disable-model-invocation: true` — set if skill has side effects (file generation, API calls, costs money).
- `argument-hint` — set if skill accepts arguments. Shows in `/` menu autocomplete.
- `context: fork` + `agent` — set if self-contained, doesn't need conversation history.
- `model` — set only if a specific model capability is needed.
- `allowed-tools` — set if skill should have restricted tool access.

Full field reference → `references/frontmatter.md`

### Step 3: Write the skill content

Structure task skills as:
1. **Context** — files to read, APIs to call, reference material to load
2. **Step-by-step workflow** — numbered steps; each tells Claude exactly what to do
3. **Output format** — what the result looks like; include templates, file paths, structured formats
4. **Notes** — edge cases, constraints, what to delegate, what NOT to do

Content rules:
- Keep SKILL.md under 500 lines. Move detailed reference material to supporting files.
- Use `$ARGUMENTS` / `$N` for dynamic input from arguments.
- Use `` !`command` `` for dynamic context injection (preprocessing).
- Be specific about agent delegation — include the exact prompt text.
- Specify all file paths (inputs, outputs, scripts, references).

### Step 4: Add supporting files (if needed)

Add alongside SKILL.md in the same directory. Reference them explicitly from SKILL.md — supporting files do NOT load automatically.

### Step 5: Document in CLAUDE.md (recommended)

Add a brief entry: skill name, trigger phrases, what it does, output location.

### Step 6: Test

1. **Natural language** — say something matching the description. Does it load?
   - If not, revise `description` to include the keywords you used. Try 2-3 phrasings.
2. **Direct invocation** — run `/skill-name` with test arguments.
3. **Edge cases** — missing arguments, unusual input, empty input.
4. **Character budget** — if many skills exist, run `/context` to confirm descriptions load.

### Complete Example

```yaml
---
name: meeting-notes
description: Use when someone asks to summarize meeting notes, recap a meeting, or format meeting minutes.
argument-hint: [topic or date]
---

## What This Skill Does
Takes raw meeting notes and produces a structured summary with action items.

## Steps
1. Ask the user to paste their raw meeting notes (or provide a file path).
2. Extract: Attendees, Key decisions, Action items (with deadlines), Open questions.
3. Format using the template below.
4. If $ARGUMENTS is provided, use it as the meeting title. Otherwise, infer from content.

## Output Template
# Meeting: [title]
**Date:** [date or "Not specified"]
**Attendees:** [comma-separated list]

## Key Decisions
- [decision]

## Action Items
- [ ] [person]: [task] (due: [date or "TBD"])

## Open Questions
- [question]

## Notes
- Keep summaries concise. Don't add commentary.
- If notes are too vague to extract action items, flag it instead of making them up.
```

---

## Build Phase — Bundle Skill

### File Structure

```
.claude/skills/[name]/
├── SKILL.md                    ← Orchestrator
└── references/
    ├── [phase-1-name].md
    ├── [phase-2-name].md
    └── [quality-judge].md
```

### Writing the Orchestrator (SKILL.md)

The Orchestrator does NOT contain logic for any phase. It:
1. Lists all sub-skills in a table (name, file, role, character)
2. Shows the workflow diagram (phase sequence + loop-back paths)
3. Gives brief phase instructions (which file to read, critical rules)
4. States global rules applying to all phases

Keep Orchestrator under 100 lines — all depth lives in reference files.

Template:

```markdown
---
name: [skill-name]
description: >
  [1-2 sentence description with trigger keywords]
---

# [Skill Name] — Bundle Skill Orchestrator

## Sub-Skills
| Sub-Skill | File | Role | Character |
|---|---|---|---|
| [Name] | `references/[file].md` | [what it does] | [persona description] |

## Workflow
[ASCII diagram showing phase sequence + loop-back paths]

## Phase Instructions
### Phase 1 — [Name]
Read: `references/[file].md` fully before executing.
[Any critical rule for this phase]

## Global Rules
[Rules that apply across all phases]
```

### Writing Each Sub-Skill Reference File

Each file must define:
1. **Role** — What specific task this phase performs
2. **Purpose** — Why it exists (what breaks without it)
3. **Character/Persona** — The specific human expert this phase embodies (be specific, not generic)
4. **Instructions** — Step-by-step with input/output format
5. **Rules** — Hard constraints, what this phase must never do

Template:

```markdown
# [Phase Name] — Sub-Skill Reference

## Role
[One sentence: what this phase does]

## Purpose
[One sentence: why it exists]

## Character: [Persona Name]
[2-3 sentences. Name the trait that matters most and why it improves output quality.]

---

## Instructions (Phase [N])
**Input:** [what this phase receives]
**Output:** [what this phase produces]

### Step 1 — [name]
[instructions]

### Output Format
[template]

---

## Rules
- [hard constraint]
```

### Writing the Quality Judge

Always the second-to-last phase. It:
1. Defines a scoring rubric: 4 dimensions (0–25 each = 0–100 total)
2. Sets the threshold (typically 95%)
3. Routes loop-backs: lowest-scoring dimension → phase to redo
4. After max loops: forces output with ⚠️ WARNING

Each dimension maps to a phase:
- D1 fails → loop to research phase
- D2 fails → loop to analysis phase
- D3 fails → loop to devil's advocate phase
- D4 fails → loop to synthesis phase

### Quality Gate Threshold Guide

| Threshold | Use when |
|-----------|----------|
| 95% | High-stakes outputs Bond will act on (consulting, research, business decisions) |
| 90% | Medium-stakes: summaries, explanations, content drafts |
| 85% | Lower-stakes, speed matters more than perfection |

Default: **95%** unless Bond specifies otherwise.
