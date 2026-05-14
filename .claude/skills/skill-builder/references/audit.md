# Skill Audit Guide

Comprehensive checklists for auditing any Claude Code skill. Read the skill file first, then work through the relevant checklists. Fix issues before marking the audit complete.

---

## Frontmatter Audit

- [ ] `name` matches the directory name
- [ ] `description` uses natural keywords someone would actually say when they need this skill
- [ ] `description` is specific enough to avoid false triggers but broad enough to catch real requests
- [ ] `disable-model-invocation: true` is set if the skill has side effects (generates files, calls APIs, sends messages, costs money)
- [ ] `argument-hint` is set if the skill accepts arguments via `/name`
- [ ] `allowed-tools` is set if the skill should NOT have access to all tools
- [ ] `context: fork` is used if the skill is self-contained and produces verbose output
- [ ] `model` is set only if a specific model capability is needed
- [ ] No unnecessary fields are set (don't add frontmatter just because you can)

---

## Content Audit

- [ ] Total SKILL.md is under 500 lines (detailed reference moved to supporting files)
- [ ] Clear step-by-step workflow with numbered steps (for task skills)
- [ ] Output format is specified with templates or examples
- [ ] All file paths and locations are documented
- [ ] Agent delegation instructions include the actual prompt text to send
- [ ] Notes section covers edge cases, constraints, and what NOT to do
- [ ] No vague instructions — every step tells Claude exactly what to do
- [ ] String substitutions (`$ARGUMENTS`, `$N`) are used where the skill takes input

---

## Integration Audit

- [ ] Skill is documented in CLAUDE.md (recommended, not required)
- [ ] Supporting files (if any) are referenced from SKILL.md, not orphaned
- [ ] Scripts (if any) have correct file paths and are executable
- [ ] API keys (if any) are stored in environment variables, never hardcoded

---

## Quality Audit

- [ ] A beginner could follow the instructions without prior context
- [ ] Instructions are actionable, not abstract
- [ ] Delegates to subagents when appropriate to keep main context clean
- [ ] Doesn't duplicate information that lives elsewhere (CLAUDE.md, other skills)
- [ ] Output paths follow a predictable convention

---

## Bundle Skill Audit

*Run only for Bundle Skills.*

**Orchestrator (SKILL.md):**
- [ ] Lists all sub-skills with: file path, role, and character/persona
- [ ] Workflow diagram shows: phase sequence, loop-back paths, and exit conditions
- [ ] Phase instructions reference the correct file and state any critical rules
- [ ] Orchestrator stays under 100 lines — depth lives in reference files, not here
- [ ] Global rules section covers constraints that apply across ALL phases

**Each Sub-Skill Reference File:**
- [ ] Defines Role (what), Purpose (why), and Character/Persona (who) explicitly
- [ ] Character is a specific human expert, not a generic AI description
- [ ] Input and output are clearly defined for each phase
- [ ] Output format includes a template
- [ ] Rules section states what this phase must never do

**Quality Judge:**
- [ ] Scoring rubric has 4 dimensions, each 0–25 points (total 0–100)
- [ ] Each dimension maps to a specific phase for loop-back routing
- [ ] Threshold is stated explicitly (default 95%)
- [ ] Max loop limit stated (default 2) with forced-output + warning behavior defined
- [ ] Conservative scoring rule stated: "when unsure, use lower score band"

**Pipeline Integrity:**
- [ ] Blind phases documented — no phase reads ahead before it should
- [ ] Handoffs explicit: each phase knows exactly what it receives and returns
- [ ] Bundle Skill Gate criteria were met (≥ 2 of 5) — not over-engineered for a simple task

---

## Optimization Opportunities

After running the audit, check `references/frontmatter.md` for advanced features that could improve the skill:

- `context: fork` — run in isolated subagent to keep main context clean
- `allowed-tools` — restrict tool access for safer/cheaper execution
- Dynamic context injection (`` !`command` ``) — inject live data before execution
- `hooks` — lifecycle hooks scoped to this skill
- Supporting files — move verbose reference material out of SKILL.md

---

## Recommended Conventions

- Skills live in `.claude/skills/[skill-name]/SKILL.md`
- Output files go in a predictable location (e.g., `output/[skill-name]/`)
- API keys go in environment variables, never hardcoded in skill files
- Document all active skills in your project's CLAUDE.md
- Frontmatter `description` written as: "Use when someone asks to [action], [action], or [action]."

---

## Important Notes

- Always read an existing skill before auditing or optimizing it
- When building a new skill, check if a similar skill already exists that could be extended instead
- For advanced patterns (subagent execution, hooks, permissions), see `references/frontmatter.md`
