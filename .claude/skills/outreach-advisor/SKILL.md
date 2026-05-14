---
name: outreach-advisor
argument-hint: "'sequence' to design email flow / 'cold' for B2B cold outreach / 'welcome' for onboarding emails / 'nurture' for lead nurture"
description: >
  Email outreach strategy and copywriting for Bond's ventures. Two-phase bundle:
  sequence design → copy writing. Covers welcome/onboarding sequences, lead nurture,
  re-engagement, cold B2B outreach, follow-up sequences, breakup emails, and
  subject line optimization.

  Auto-invoke when Bond asks: email sequence, cold email, outreach email, nurture
  sequence, welcome email, onboarding email, follow-up email, re-engagement email,
  B2B email, email automation, drip campaign, write an email, email flow,
  cold outreach, prospect email, sales email.
---

# Outreach Advisor — Bundle Skill Orchestrator

## Sub-Skills

| Sub-Skill | File | Role | Character |
|---|---|---|---|
| Sequence Designer | `references/sequence-designer.md` | Design email flow architecture, timing, exit conditions | Systems thinker who maps user journey stages to email triggers |
| Copywriter | `references/copywriter.md` | Write every email in the sequence | Peer-to-peer writer who sounds human, not marketing |
| Quality Judge | `references/quality-judge.md` | Score 95/100, route loop-backs | Inbox reader who deletes anything that sounds like mass email |

## Workflow

```
Phase 1 → Phase 2 → QG → Deliver
   ↑ QG D1 fail    ↑ QG D2/D3/D4 fail
```

## Mode Detection

| Input | Phases to Run |
|---|---|
| "Design a sequence / plan email flow / what emails should I send" | Phase 1 only |
| "Write the emails / cold email to X / draft welcome sequence" | Phase 2 + QG |
| "Nurture / welcome / re-engagement / onboarding" | Phase 1 → 2 → QG |
| "Cold email / B2B outreach / prospect email" | Phase 2 + QG (cold mode) |

## Phase Instructions

### Phase 1 — Sequence Designer
Read `references/sequence-designer.md` fully before executing.
Output: sequence architecture (trigger / goal / exit conditions / email list with day + purpose + subject direction + CTA). Hand to Phase 2.

### Phase 2 — Copywriter
Read `references/copywriter.md` fully before executing.
Input: Phase 1 architecture OR direct write request.
Output: every email written, ready to send. Hand to QG.

### Phase QG — Quality Judge
Read `references/quality-judge.md` fully before scoring.
Threshold: 95/100. Max 2 loops before forced delivery with warning.

## Global Rules

- Read `context/work.md` before Phase 1 — apply to correct venture.
- Mirror Bond's input language. Emails for Thai recipients → Thai. English-market → English.
