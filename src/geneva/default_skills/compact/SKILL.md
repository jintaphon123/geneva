---
name: compact
description: Condense long session context while preserving current task state, decisions, files, and next actions
---

# Compact Skill

Use this skill when:
- The conversation is long, repetitive, or approaching the model context window.
- The user says compact, compress context, summarize session, reduce tokens, or continue without losing state.
- The assistant needs to hand off the session to another AI or future turn.

## Operating Principle

Compact is not a casual summary. It is a state-preservation operation. The output must keep the agent able to continue the work without rereading the whole transcript.

## Required Output

Produce a concise handoff with these sections:

1. **Current Goal** — the exact user objective being pursued.
2. **Decisions Locked** — decisions already made, with rationale.
3. **Files/Systems Touched** — paths, modules, APIs, UI surfaces, tests, and why they matter.
4. **Current State** — what is already implemented, verified, or still failing.
5. **Fresh Tail** — the most recent user intent and immediate next step.
6. **Context Ledger** — what was kept raw, what was summarized, what was trimmed, token pressure, and the reason for each decision.
7. **Risks** — likely bugs, missing tests, stale assumptions, or context that must not be lost.
8. **Do Not Touch** — files/folders owned by other parallel agents.

## Compression Rules

- Keep exact file paths and API names.
- Keep test commands and their pass/fail status.
- Keep user preferences and privacy constraints.
- Keep memory/project scope decisions.
- Keep token budget pressure, compact trigger, preserved fresh-tail count, and any context ledger id if available.
- Remove duplicate narration, old exploration branches, and raw tool output unless it is needed to reproduce a bug.
- Do not claim something was verified unless a test, build, or visual check actually ran.

## Token Budget

Aim for 800-1,500 words for a normal session. If the context is under severe pressure, compress to 300-600 words and keep only: goal, decisions, touched files, current state, next action, blocked folders.
