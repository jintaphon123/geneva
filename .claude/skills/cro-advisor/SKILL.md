---
name: cro-advisor
argument-hint: "'audit' for conversion leak diagnosis / 'ab-test' for test design / 'copy' or 'rewrite' for copy improvements / 'onboarding' for activation flow"
description: >
  Conversion rate optimization for Bond's ventures. Three-phase bundle: audit →
  recommendations → copy rewrite. Covers page CRO, form optimization, signup flow,
  onboarding activation, popup/modal design, paywall upgrade flows, A/B test design,
  and behavioral psychology for conversion.

  Auto-invoke when Bond asks: improve conversion, optimize landing page, increase
  signups, form optimization, form completion, CRO, conversion rate optimization,
  why isn't this converting, signup flow friction, onboarding drop-off, A/B test,
  optimize pricing page, popup conversion, paywall, upgrade flow, page not working,
  reduce bounce rate.
---

# CRO Advisor — Bundle Skill Orchestrator

## Sub-Skills

| Sub-Skill | File | Role | Character |
|---|---|---|---|
| Auditor | `references/auditor.md` | 10-point conversion audit, find where visitors drop | Forensic analyst — nothing is a "maybe," only evidence |
| Recommender | `references/recommender.md` | Prioritized fix list, A/B test hypotheses | Product manager — impact × effort, no vague advice |
| Copywriter | `references/copywriter.md` | Rewrite copy with conversion psychology | Direct-response copywriter who speaks customer language |
| Quality Judge | `references/quality-judge.md` | Score 95/100, route loop-backs | CRO lead who has seen every type of conversion failure |

## Workflow

```
Phase 1 → Phase 2 → Phase 3 → QG → Deliver
   ↑ QG D1 fail    ↑ QG D2 fail  ↑ QG D3/D4 fail
```

## Mode Detection

| Input | Phases to Run |
|---|---|
| "Audit this page/form/flow", "why isn't this converting" | Phase 1 only |
| "A/B test ideas", "what to test", "test hypotheses" | Phase 2 only |
| "Rewrite copy", "fix headlines", "better CTAs" | Phase 3 + QG |
| "Optimize signup / onboarding / paywall" | Phase 1 → 2 → 3 → QG |
| No argument / "help me convert better" | Phase 1 → 2 → 3 → QG |

## Phase Instructions

### Phase 1 — Auditor
Read `references/auditor.md` fully before executing.
Output: executive summary + finding table (Issue / Impact / Evidence / Fix / Priority). Hand to Phase 2.

### Phase 2 — Recommender
Read `references/recommender.md` fully before executing.
Input: Phase 1 audit findings.
Output: prioritized fix list + A/B test hypotheses. Hand to Phase 3 or deliver if no copy needed.

### Phase 3 — Copywriter
Read `references/copywriter.md` fully before executing.
Input: Phase 2 recommendations OR direct rewrite request.
Output: rewritten copy sections. Hand to QG.

### Phase QG — Quality Judge
Read `references/quality-judge.md` fully before scoring.
Threshold: 95/100. Max 2 improvement loops before forced delivery with warning.

## Global Rules

- Read `context/work.md` before Phase 1. Apply to correct venture.
- Mirror Bond's input language. Copy for external pages → match target audience language.
- NotebookLM: Alex Hormozi General (`cea608bb`) for offer framing and conversion psychology.
