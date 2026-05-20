---
name: compact
description: Condense long context into an actionable state handoff without losing current task intent
when_to_use: Use when context is long, token pressure is high, or the user asks to compact/compress/summarize the session.
---

Compact the active work into a continuation-safe handoff.

Keep:
- Current user goal and latest instruction.
- Decisions already made and why.
- Exact file paths, APIs, commands, tests, and visual checks.
- Errors encountered and fixes applied.
- Remaining risks, blocked folders, and immediate next action.
- Context ledger facts: token pressure, compact trigger, preserved fresh tail, what was trimmed, and why.

Remove:
- Duplicate exploration.
- Raw tool output unless needed to reproduce a bug.
- Old branches of reasoning that no longer affect the next action.

Output sections:
1. Current Goal
2. Decisions Locked
3. Files/Systems Touched
4. Current State
5. Fresh Tail
6. Context Ledger
7. Risks
8. Do Not Touch

Target 800-1,500 words. Under severe context pressure, compress to 300-600 words while preserving exact paths and next action.
