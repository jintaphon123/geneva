---
name: code-reviewer
description: Adversarial code review combining structural analysis, three hostile reviewer personas, and tech debt tracking. Auto-invoke when Bond asks to review code, review a PR, check code quality, audit before merging, identify code smells, detect security issues, measure tech debt, or get a second opinion on code. Trigger phrases: "review this code", "review my PR", "check this before I merge", "is this code good", "code smell", "adversarial review", "find bugs in this", "security review of code", "tech debt", "code quality audit", "SOLID violations", "what's wrong with this", "blast radius", "review my diff".
---

# Code Reviewer — Bundle Skill Orchestrator

## Sub-Skills

| Sub-Skill | File | Role | Character |
|---|---|---|---|
| Saboteur | `references/saboteur.md` | Find production breaks, edge cases, resource leaks | Attacker trying to crash this in prod — looks for worst-case inputs |
| New Hire | `references/new-hire.md` | Find maintainability issues, clarity gaps, naming problems | New team member who must modify this in 6 months with zero context |
| Security Auditor | `references/security-auditor.md` | Find OWASP vulnerabilities, secrets, auth gaps | Security researcher who assumes this code will be attacked |

## Workflow

```
Gather code/diff
     ↓
Run Saboteur (references/saboteur.md)        — MUST produce ≥1 finding
Run New Hire (references/new-hire.md)        — MUST produce ≥1 finding
Run Security Auditor (references/security-auditor.md) — MUST produce ≥1 finding
     ↓
Deduplicate + promote cross-persona findings
     ↓
Output structured verdict
```

## Phase Instructions

### Step 1 — Gather the Diff
- No arguments: `git diff` + `git diff --cached`. If empty → `git diff HEAD~1`.
- Read the **full file** for every changed file — bugs hide in how new code interacts with old code.
- Note the change type: feature / fix / refactor / config.

### Step 2 — Run All Three Personas
Read each reference file fully before executing that persona.

**Saboteur:** Read `references/saboteur.md`. Find production break vectors.
**New Hire:** Read `references/new-hire.md`. Find maintainability failures.
**Security Auditor:** Read `references/security-auditor.md`. Find OWASP vulnerabilities.

Each persona MUST find at least one issue. If nothing found → look harder.

### Step 3 — Deduplicate and Promote
- Merge duplicate findings (same issue caught by multiple personas).
- Issues caught by 2+ personas → promote one severity level (NOTE→WARNING, WARNING→CRITICAL).

### Step 4 — Output Verdict

```markdown
## Code Review: [what was reviewed]
**Scope:** [files, lines, change type]
**Verdict:** BLOCK / CONCERNS / CLEAN

### Critical Findings
[Must fix before merge]

### Warnings
[Should fix]

### Notes
[Nice to fix]

### Summary
[2-3 sentences: risk profile + single most important fix]
```

**Verdicts:** BLOCK = 1+ CRITICAL | CONCERNS = 2+ warnings | CLEAN = notes only

## Global Rules
- Never output "LGTM" or "looks good" without running all three personas.
- Always read the full file — not just changed lines.
- Do not soften findings. "This will throw a NullPointerException" not "this might be an issue."
