---
name: research-brief
description: >
  Bond's deep research engine. A 4-phase bundle skill that produces a structured,
  confidence-mapped research brief on any topic.

  Unlike /consult (which gives action recommendations), /research-brief gives Bond
  a comprehensive landscape view: what is known, what is uncertain, what is missing,
  and what to investigate next.

  Auto-invoke when Bond asks: "what is X?", "research Y", "give me a brief on Z",
  "what's the landscape for...", "understand X before deciding", "what's happening
  with...", competitive landscape, market sizing, technology research, academic
  subject research, or any "understand first" question.
---

# Research Brief — Bundle Skill Orchestrator

## Overview

4 sub-skills run in sequence to produce a structured research brief with a
Confidence Map showing what is strongly known vs. speculative.

Unlike /consult, this skill does NOT fight for a recommendation. It builds
understanding. The output is a brief Bond can use to form his own judgment or
feed into a future /consult session.

Run all phases automatically without waiting for user input between phases.
If Bond's topic is ambiguous, ask ONE clarifying question before Phase 1.

## Context Auto-Load

Before Phase 1, silently read these files (skip if already loaded this session):
- `context/me.md` — who Bond is, constraints, working style
- `context/work.md` — active ventures and status
- `context/current-priorities.md` — live priorities and deadlines

Use this context to frame research angles relevant to Bond's situation.

---

## Sub-Skills

| Sub-Skill | File | Role | Character |
|---|---|---|---|
| Research Scout | `references/research-scout.md` | Multi-angle web research on the topic | Investigative journalist — goes 3 levels deep, not just headlines |
| Academic Mode | `references/academic-mode.md` | IMRAD extraction, citation formatting, comparative paper synthesis | Activate when input is a peer-reviewed paper, thesis, or academic preprint |
| Domain Connector | `references/domain-connector.md` | Find relevant NotebookLM knowledge to ground the research | Specialist advisor — bridges current findings with accumulated wisdom |
| Synthesis Journalist | `references/synthesis-journalist.md` | Compile research + domain knowledge into the brief | Science communicator — makes complex clear without losing depth |
| Quality Editor | `references/quality-editor.md` | Check brief completeness and confidence accuracy. ≥ 95% to pass | Senior editor — every claim needs to earn its confidence level |

---

## Workflow

```
Bond: /research-brief "[topic]"
         │
         ▼
[Phase 1] Research Scout
         Read: references/research-scout.md
         Output: 2–3 search angles + 6–10 verified findings
         │
         ▼
[Phase 2] Domain Connector
         Read: references/domain-connector.md
         Output: Relevant NB knowledge + gaps NB can't fill
         │
         ▼
[Phase 3] Synthesis Journalist
         Read: references/synthesis-journalist.md
         Output: Draft research brief with Confidence Map
         │
         ▼
[Phase 4] Quality Editor
         Read: references/quality-editor.md
         Score: 0–100% — checks completeness and confidence accuracy
         │
         ├── ≥ 95% ─────────────────────────────────▶ Deliver to Bond
         │
         └── < 95% → loop back to weakest phase (max 2 loops)
                    → if still < 95% after 2 loops: deliver with ⚠️ WARNING
```

---

## Phase Instructions

### Phase 1 — Research Scout
Read `references/research-scout.md` fully before executing.
Run immediately. Perform 2–3 searches covering different angles of the topic.

### Phase 2 — Domain Connector
Read `references/domain-connector.md` fully before executing.
Run immediately after Phase 1.
If no relevant notebook exists for this topic: skip NB query, note clearly,
proceed — Research Scout data alone is sufficient for the brief.

### Phase 3 — Synthesis Journalist
Read `references/synthesis-journalist.md` fully before executing.
Compile Phase 1 + Phase 2 outputs into the draft brief.

### Phase 4 — Quality Editor
Read `references/quality-editor.md` fully before executing.
Evaluate the draft brief. Score. Loop back or approve.

---

## Global Rules

- This skill produces understanding, not recommendations — avoid framing as
  "you should do X" (that's /consult's job)
- Every claim in the brief must be labeled with a confidence level
- "Known unknowns" section is mandatory — if Bond doesn't know what he doesn't
  know, the brief has failed
- Language: match Bond's input language. Exception: if the brief is for an
  international document, pitch deck, or formal submission → English, state this explicitly
- At the end of every brief, include a one-line escalation signal:
  - If the brief reveals a clear decision Bond needs to make → "Ready for /consult: [exact question to ask]"
  - If more research is needed first → "Next: research [specific angle] before deciding"
  - If brief is complete and no decision needed → omit the escalation line
