---
name: paid-growth-advisor
context: fork
argument-hint: "'plan' for campaign strategy / 'ads' for ad creative / 'optimize' for performance analysis"
description: >
  Paid advertising strategy, creative production, and performance optimization.
  Three-phase bundle: strategy → creative → optimize. Covers Google Ads, Meta Ads,
  LinkedIn Ads, TikTok Ads — campaign architecture, targeting, ad copy, budget
  allocation, ROAS optimization, and weekly performance reporting.

  Auto-invoke when Bond asks: paid ads, run ads, Google ads, Facebook ads, Meta ads,
  LinkedIn ads, TikTok ads, ad creative, ad copy, campaign strategy, ad budget,
  ROAS, CPA, cost per click, paid acquisition, paid marketing, performance marketing,
  campaign optimization, ad performance, which ads to run.
---

# Paid Growth Advisor — Bundle Skill Orchestrator

## Sub-Skills

| Sub-Skill | File | Role | Character |
|---|---|---|---|
| Strategist | `references/strategist.md` | Platform selection, campaign architecture, targeting | Media buyer who treats every dollar as an investment with expected return |
| Creative | `references/creative.md` | Ad copy, headlines, creative briefs | Performance copywriter who writes for the scroll, not the award |
| Optimizer | `references/optimizer.md` | Weekly performance review, diagnosis, budget decisions | Analyst who reads data like a crash report — what broke and why |
| Quality Judge | `references/quality-judge.md` | Score 95/100, route loop-backs | CMO who has burned money on untracked campaigns |

## Workflow

```
Phase 1 → Phase 2 → Phase 3 → QG → Deliver
   ↑ QG D1 fail    ↑ QG D2 fail  ↑ QG D3/D4 fail
```

## Mode Detection

| Input | Phases to Run |
|---|---|
| "Campaign plan / ad strategy / which platform" | Phase 1 only |
| "Ad copy / write ads / creative / headlines" | Phase 2 + QG |
| "Optimize campaign / analyze performance / ROAS" | Phase 3 + QG |
| No argument | Phase 1 → 2 → 3 → QG |

## Phase Instructions

### Phase 1 — Strategist
Read `references/strategist.md` fully before executing.
Output: platform selection + campaign structure + targeting brief + budget split. Hand to Phase 2.

### Phase 2 — Creative
Read `references/creative.md` fully before executing.
Input: Phase 1 strategy OR direct creative request.
Output: 5 headlines + 3 descriptions per ad set + creative brief. Hand to Phase 3 or QG.

### Phase 3 — Optimizer
Read `references/optimizer.md` fully before executing.
Input: performance data Bond provides OR post-launch campaign.
Output: weekly report + diagnosis + specific next actions. Hand to QG.

### Phase QG — Quality Judge
Read `references/quality-judge.md` fully before scoring.
Threshold: 95/100. Max 2 loops before forced delivery with warning.

## Global Rules

- Read `context/work.md` before Phase 1. Bond's current context: zero budget — building knowledge for future launch.
- Mirror Bond's input language. Ad copy → match target market language.
- Context fork: ad creative output can be verbose — isolate from conversation history.
