---
name: seo-advisor
argument-hint: "'audit' for technical SEO check / 'ai-search' for AI citation optimization / 'architecture' for site structure"
description: >
  SEO audit, AI search optimization (GEO), and site architecture for Bond's ventures.
  Three-phase bundle: technical audit → AI search optimization → architecture planning.
  Covers Core Web Vitals, on-page issues, schema markup, Perplexity/ChatGPT citation
  optimization, programmatic SEO templates, and crawl architecture.

  Auto-invoke when Bond asks: SEO audit, why am I not ranking, technical SEO,
  on-page SEO, site audit, improve ranking, AI search, optimize for Perplexity,
  ChatGPT citation, AI Overviews, GEO, generative engine optimization, schema markup,
  structured data, site architecture, information architecture, content at scale,
  programmatic SEO, organic search.
---

# SEO Advisor — Bundle Skill Orchestrator

## Sub-Skills

| Sub-Skill | File | Role | Character |
|---|---|---|---|
| SEO Auditor | `references/seo-auditor.md` | Technical + on-page audit, issue prioritization | Detective who treats every ranking problem as a crime scene |
| AI Search Optimizer | `references/ai-search-optimizer.md` | GEO: optimize for Perplexity/ChatGPT citations | AI researcher who knows how LLMs extract and cite content |
| Architecture Planner | `references/architecture-planner.md` | Site structure, topic clusters, programmatic SEO | Information architect who designs crawl paths like an engineer |
| Quality Judge | `references/quality-judge.md` | Score 95/100, route loop-backs | SEO director who has seen audits with no action plans |

## Workflow

```
Phase 1 → Phase 2 → Phase 3 → QG → Deliver
   ↑ QG D1 fail    ↑ QG D2 fail  ↑ QG D3 fail  ↑ QG D4 fail
```

## Mode Detection

| Input | Phases to Run |
|---|---|
| "SEO audit / why not ranking / technical issues / health check" | Phase 1 only |
| "AI search / Perplexity / ChatGPT citation / AI Overviews / GEO" | Phase 2 only |
| "Site architecture / information architecture / programmatic SEO" | Phase 3 only |
| No argument / "do full SEO" | All 3 phases + QG |

## Phase Instructions

### Phase 1 — SEO Auditor
Read `references/seo-auditor.md` fully before executing.
Output: executive summary + finding table (Issue / Impact / Evidence / Fix / Priority). Hand to Phase 2.

### Phase 2 — AI Search Optimizer
Read `references/ai-search-optimizer.md` fully before executing.
Input: Phase 1 findings OR direct GEO request.
Output: bot access check + citation audit + extractability scorecard + rewrite recommendations. Hand to Phase 3.

### Phase 3 — Architecture Planner
Read `references/architecture-planner.md` fully before executing.
Input: Phases 1-2 findings OR direct architecture request.
Output: URL structure + cluster map + internal linking spec. Hand to QG.

### Phase QG — Quality Judge
Read `references/quality-judge.md` fully before scoring.
Threshold: 95/100. Max 2 loops before forced delivery with warning.

## Global Rules

- Read `context/work.md` before Phase 1. Apply to correct venture (Second Brain or Impact Arena Condo).
- Mirror Bond's input language. Technical specs and SEO recommendations → English.
- NotebookLM: NopPongsatorn (`13a59d44`) for deeper SEO/content frameworks.
