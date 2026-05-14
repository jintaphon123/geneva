---
name: consult
description: >
  Bond's strategic consulting engine. A 6-phase bundle skill that transforms any
  business or strategy question into a rigorous, evidence-backed consultation.

  Runs: real-time web research → NotebookLM domain wisdom (with fresh context injected)
  → independent Claude analysis → devil's advocate fight → 95% quality gate with
  loop-back → final synthesis.

  Auto-invoke when Bond asks: strategy decisions, "should I...?", "how do I...?",
  pricing, offer design, team/HR decisions, business model design, scaling,
  competitive situations, project direction, monetization.
---

# Consult — Bundle Skill Orchestrator

## Overview

This skill runs 6 sub-skills in sequence. Each sub-skill has a specific role,
purpose, and character. The Orchestrator (this file) sequences them and routes
loop-backs from the Quality Judge.

If Bond's question is vague → ask ONE clarifying question before starting Phase 1.
Otherwise, run all phases automatically without waiting for user input between phases.

## Context Auto-Load

Before Phase 1, silently read these files (skip if already loaded this session):
- `context/me.md` — who Bond is, constraints, working style
- `context/work.md` — active ventures and status
- `context/current-priorities.md` — live priorities and deadlines

Do NOT ask Bond to re-explain his situation. Use context files directly.

## Complexity Assessment

Run at start, before Phase 1:

| Question type | Mode | Phases |
|---|---|---|
| Simple / tactical (quick facts, minor decisions, < 1 min to answer) | **Lightweight** | Phase 1 → Phase 3 → Phase 6 only |
| Strategic / significant (resource allocation, positioning, architecture, major pivots) | **Full** | All 6 phases |

**Lightweight mode:** Skip NB Bridge (Phase 2), Devil's Advocate (Phase 4), Quality Judge (Phase 5).
Run Phase 1 (Scout) → Phase 3 (Analyst, no blind restriction) → Phase 6 (Synthesis, shorter format).
Note at top of output: `[Lightweight mode — simple question]`

Default to Full mode when in doubt. If unsure: lean Full for anything with ≥ 3 months of impact.

---

## Sub-Skills

| Sub-Skill | File | Role | Character |
|---|---|---|---|
| Context Scout | `references/context-scout.md` | WebSearch for real-time ground truth | Detective journalist — never satisfied with surface data |
| NotebookLM Bridge | `references/notebooklm-bridge.md` | Select notebook + inject fresh context + query | Precise librarian — knows which notebook holds what |
| Independent Analyst | `references/independent-analyst.md` | Claude's own analysis built from data + first principles | First-principles thinker — trusts data over authority |
| Devil's Advocate | `references/devil-advocate.md` | Attack both NB and Claude analyses, find flaws | Relentless opposing counsel — no free passes |
| Quality Judge | `references/quality-judge.md` | Score output 0–100%, loop back if < 95% | McKinsey senior partner — if it's not ready, it goes back |
| Synthesis Master | `references/synthesis-master.md` | Compile final output for Bond | COO briefing the CEO — clear, decisive, no padding |

---

## Workflow

```
Bond: /consult "[question]"
         │
         ▼
[Phase 1] Context Scout
         Read: references/context-scout.md
         Output: 3–5 verified data points with sources
         │
         ▼
[Phase 2] NotebookLM Bridge
         Read: references/notebooklm-bridge.md
         Output: NB response (with fresh context embedded in query)
         │
         ▼
[Phase 3] Independent Analyst   ← builds from Phase 1 data, stress-tests Phase 2 in Phase 4
         Read: references/independent-analyst.md
         Output: Independent analysis + self-critique
         │
         ▼
[Phase 4] Devil's Advocate      ← NOW reads Phase 2 + Phase 3 together
         Read: references/devil-advocate.md
         Output: Fight report — consensus / disagreements / ≥2 flaws identified
         │
         ▼
[Phase 5] Quality Judge
         Read: references/quality-judge.md
         Score: 0–100% across 4 dimensions
         │
         ├── ≥ 95% ──────────────────────────────────────────▶ Phase 6
         │
         └── < 95% → identify weakest dimension
                    → loop back to responsible phase (max 2 loops)
                    → if still < 95% after 2 loops: proceed with ⚠️ WARNING
         │
         ▼
[Phase 6] Synthesis Master
         Read: references/synthesis-master.md
         Output: Final consultation report → Bond
```

---

## Phase Instructions

### Phase 1 — Context Scout
Read `references/context-scout.md` fully before executing.
Run immediately. If Bond's question lacks enough context, ask ONE question first.

### Phase 2 — NotebookLM Bridge
Read `references/notebooklm-bridge.md` fully before executing.
Run immediately after Phase 1.

### Phase 3 — Independent Analyst
Read `references/independent-analyst.md` fully before executing.
Build analysis from Phase 1 data and first principles. Your job is genuine independent
reasoning — anchor to data, not to NB's answer. Phase 4 will stress-test both perspectives.

### Phase 4 — Devil's Advocate
Read `references/devil-advocate.md` fully before executing.
NOW open Phase 2 output. Fight Phase 2 vs Phase 3.
Run immediately after Phase 3.

### Phase 5 — Quality Judge
Read `references/quality-judge.md` fully before executing.
Evaluate all phases. Score. Decide: proceed or loop.
Run immediately after Phase 4.

### Phase 6 — Synthesis Master
Read `references/synthesis-master.md` fully before executing.
Only runs after Quality Judge approves (≥ 95%) or after 2 loops.

---

## Global Rules

- Bond's constraint filter applies to every recommendation:
  - **Zero capital**: Flag any action that requires upfront investment Bond doesn't have
  - **Solo founder**: Flag any action requiring a team Bond doesn't have yet
  - **KU student timeline**: Flag anything taking > 3 months
  - **Thailand context**: Verify US/global frameworks apply to Thai market
- Language:
  - Internal phases (Phase 1–5): English — for framework precision and NB compatibility
  - Final output to Bond (Phase 6): **match Bond's input language**
  - Exception: if the output artifact is for external/international use
    (pitch decks, investor slides, formal documents) → English, state this explicitly
- Never declare output "perfect", "solid", or "done" — Quality Judge decides
- Maximum 3 recommendations in final output — force ranking
