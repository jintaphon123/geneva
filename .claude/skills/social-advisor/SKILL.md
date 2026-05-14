---
name: social-advisor
argument-hint: "'strategy' for platform/pillar plan / 'post' or 'write' to create content / 'calendar' for monthly plan / 'analyze' for performance audit"
description: >
  Social media strategy, content creation, and growth for Bond's ventures. Covers
  platform selection, content pillars, posting cadence, hook writing, thread engineering,
  Twitter/X growth mechanics, content calendars, community engagement, and performance
  analysis.

  Auto-invoke when Bond asks: social media strategy, write a post, content calendar,
  social media plan, Twitter growth, LinkedIn content, TikTok, Instagram, thread,
  hook writing, grow followers, engagement rate, social audit, which platform,
  community management, viral content, repurpose content for social.
---

# Social Advisor — Bundle Skill Orchestrator

## Sub-Skills

| Sub-Skill | File | Role | Character |
|---|---|---|---|
| Strategist | `references/strategist.md` | Platform selection, content pillars, 90-day growth plan | Growth operator who picks platforms based on audience density, not trends |
| Creator | `references/creator.md` | Write platform-native content: posts, threads, calendars | Native speaker of each platform who knows what gets bookmarked vs ignored |
| Quality Judge | `references/quality-judge.md` | Score 95/100, route loop-backs | Social media director who has seen posts fall flat due to platform-blindness |

## Workflow

```
Phase 1 → Phase 2 → QG → Deliver
   ↑ QG D1 fail    ↑ QG D2/D3/D4 fail
```

## Mode Detection

| Input | Phases to Run |
|---|---|
| "Social strategy / which platforms / plan for Q2 / build presence" | Phase 1 only |
| "Write a post / draft tweet / LinkedIn post / Twitter thread / content for..." | Phase 2 + QG |
| "Content calendar / 30-day plan / monthly schedule" | Phase 2 + QG |
| "Audit my social / what's working / analyze performance" | Phase 2 + QG |
| No argument / general question | Phase 1 → 2 → QG |

## Phase Instructions

### Phase 1 — Strategist
Read `references/strategist.md` fully before executing.
Output: platform selection + 3-5 content pillars + weekly cadence + 90-day growth plan. Hand to Phase 2.

### Phase 2 — Creator
Read `references/creator.md` fully before executing.
Input: Phase 1 strategy OR direct write request with platform specified.
Output: platform-native content ready to post. Hand to QG.

### Phase QG — Quality Judge
Read `references/quality-judge.md` fully before scoring.
Threshold: 95/100. Max 2 loops before forced delivery with warning.

## Global Rules

- Read `context/work.md` before Phase 1. Bond's ventures: Second Brain (LinkedIn + Twitter/X), Impact Arena Condo (Instagram + TikTok).
- Mirror Bond's input language. Content for external posting → match platform's audience language.
