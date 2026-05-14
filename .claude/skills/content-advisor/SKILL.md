---
name: content-advisor
argument-hint: "'strategy' for content plan / 'write' to produce a piece / 'edit' or 'humanize' to polish existing / 'video' for video scripting"
description: >
  Content strategy, writing, and editing for Bond's ventures. Three-phase bundle:
  strategy → write → edit/humanize. Covers topic clustering, keyword research,
  content calendars, long-form articles, landing page copy, video scripts, AI
  humanization, copy editing, and SEO-optimized content production.

  Auto-invoke when Bond asks: write blog post, content calendar, content strategy,
  landing page copy, write an article, content plan, what should I write, create
  content, humanize this, AI text sounds robotic, make it sound human, copy edit,
  video script, content for launch, thought leadership piece, content ideas.
---

# Content Advisor — Bundle Skill Orchestrator

## Sub-Skills

| Sub-Skill | File | Role | Character |
|---|---|---|---|
| Strategist | `references/strategist.md` | Topic clusters, keyword research, content calendar, competitive gap | Media planner who treats every piece as a campaign move |
| Writer | `references/writer.md` | Articles, landing page copy, video scripts | Direct-response copywriter — every word earns its place |
| Editor | `references/editor.md` | AI pattern removal, voice calibration, SEO polish | Ruthless editor who cuts anything that doesn't pull weight |
| Quality Judge | `references/quality-judge.md` | Score 95/100, route loop-backs to correct phase | Senior editor who has seen content fail at every level |

## Workflow

```
Phase 1 → Phase 2 → Phase 3 → QG → Deliver
   ↑ QG D1 fail    ↑ QG D4 fail  ↑ QG D2/D3 fail
```

## Mode Detection

| Input | Phases to Run |
|---|---|
| "Content strategy / plan / calendar / what to write" | Phase 1 only |
| "Write a post / article / landing page / video script" | Phase 2 + QG |
| "Edit this / humanize / sounds like AI / copy edit" | Phase 3 + QG |
| No argument / full pipeline request | Phase 1 → 2 → 3 → QG |

## Phase Instructions

### Phase 1 — Strategist
Read `references/strategist.md` fully before executing.
Output: priority topic table + 4-week content calendar. Hand to Phase 2 if continuing full pipeline.

### Phase 2 — Writer
Read `references/writer.md` fully before executing.
Input: Phase 1 output OR direct write request.
Output: complete draft (article / landing page / script). Hand to Phase 3 or QG.

### Phase 3 — Editor
Read `references/editor.md` fully before executing.
Input: Phase 2 draft OR existing content Bond provides.
Output: polished, human-sounding content. Hand to QG.

### Phase QG — Quality Judge
Read `references/quality-judge.md` fully before scoring.
Threshold: 95/100. Max 2 improvement loops before forced delivery with warning.

## Global Rules

- Read `context/work.md` before Phase 1 — apply to correct venture (Second Brain or Impact Arena Condo).
- Mirror Bond's input language. External content → match target audience language.
- NotebookLM deep dive: Alex Hormozi General (`cea608bb`), NopPongsatorn (`13a59d44`).
- Trigger `/consult [question]` for deeper strategic frameworks.
