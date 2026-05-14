---
name: product-strategist
argument-hint: "[mode] — okr / roadmap / stakeholder / quarterly"
description: >
  Product strategy covering OKR cascade design, roadmap planning, stakeholder communications,
  and quarterly planning. Distinct from ceo-advisor (operational product level vs executive level)
  and ops-advisor (product OKRs vs org-level OKR implementation).

  Auto-invoke when Bond asks: OKR cascade, key results, product OKRs, roadmap, product roadmap,
  Now/Next/Later, roadmap narrative, stakeholder update, board update, engineering update,
  customer update, quarterly plan, strategy review, Q1/Q2/Q3/Q4 planning,
  feature announcement, release notes communication.
---

# Product Strategist

Four modes for product strategy and communication.

---

## Mode Detection

| Input | Mode |
|---|---|
| "OKR", "OKR cascade", "key results", "align OKRs" | **OKR Cascade** |
| "roadmap", "product roadmap", "Now/Next/Later", "timeline" | **Roadmap** |
| "stakeholder update", "board update", "engineering update", "customer update" | **Stakeholder Update** |
| "quarterly plan", "strategy review", "Q1/Q2/Q3/Q4 planning" | **Quarterly Plan** |

---

## Mode 1 — OKR Cascade

Cascade company-level OKRs down to product and team level, score alignment.

### OKR Cascade Structure

```
Company OKRs (set by CEO / board)
└── Product OKRs (set by Head of Product)
    ├── Team OKRs — Growth Team
    ├── Team OKRs — Retention Team
    └── Team OKRs — Platform Team
```

### OKR Format

```
Objective: [Qualitative, inspiring, direction-setting — no metrics]
  KR1: [Measurable result — specific number, by when]
  KR2: [Measurable result]
  KR3: [Measurable result, max 3-5 per objective]
```

### Alignment Scoring

| Dimension | Target | Formula |
|---|---|---|
| Vertical alignment | > 90% | % of product KRs that directly support a company KR |
| Horizontal alignment | > 75% | % of team KRs that directly support a product KR |
| Coverage | > 80% | % of company KRs covered by at least one product KR |
| Balance | > 80% | No single team responsible for > 40% of product KRs |

If any score < threshold: identify unlinked KRs and either link them or cut them.

### 5 Strategy Types

| Type | Focus | Typical Objectives |
|---|---|---|
| Growth | Scale user base and acquisition | Active users, new signups, channel expansion |
| Retention | Reduce churn, improve loyalty | Retention rate, NPS, renewal rate |
| Revenue | Increase ARPU, expand accounts | ARR, expansion revenue, upgrade rate |
| Innovation | Differentiate, create new markets | New capabilities shipped, patents, NPS for new feature |
| Operational | Improve efficiency, reduce costs | Time-to-ship, support ticket volume, infra cost |

Full OKR framework and templates → `references/okr-framework.md`

---

## Mode 2 — Roadmap

Build and communicate a product roadmap in the right format for the audience.

### Format Selection Guide

| Situation | Format |
|---|---|
| High uncertainty, startup or early-stage | Now / Next / Later |
| Committed delivery dates, stakeholder contracts | Timeline |
| Outcome-led, theme-based planning | Theme-based |

### Format 1: Now / Next / Later

```
NOW (this quarter — committed)
- Feature A: [2-line description + success metric]
- Feature B

NEXT (next quarter — planned, not committed)
- Feature C
- Feature D

LATER (beyond 6 months — directional only)
- Theme: [area of investment, not specific features]
```

**Use when:** uncertainty is high, priorities are likely to change, you want to avoid false date commitments.

### Format 2: Timeline Roadmap

```
Q1 2026       Q2 2026       Q3 2026       Q4 2026
|─────────────|─────────────|─────────────|
  [Feature A]  [Feature B]   [Feature C]
               [Feature D]
```

Per milestone:
- Feature name + 1-line description
- Key dependencies noted
- Owner team

**Use when:** there are committed delivery dates, contracted milestones, or coordinated marketing launches.

### Format 3: Theme-Based Roadmap

```
Theme 1: [Strategic area — e.g., "Make onboarding 50% faster"]
  Now: [What we're shipping this quarter in this theme]
  Next: [What follows]
  Later: [Direction]

Theme 2: [Strategic area]
  ...
```

**Use when:** you want to communicate strategy without committing to specific features, or when engineering still owns the "how."

### Roadmap Communication Rules

- Audience clarity: use Now/Next/Later for internal, Timeline for contracts, Theme-based for external/customers
- No features on the roadmap without a problem statement behind them
- Mark confidence level on each item: Committed / Planned / Directional
- Re-publish after every quarterly planning cycle

Full formats and communication checklist → `references/roadmap-formats.md`

---

## Mode 3 — Stakeholder Update

Write updates for different audiences — each wants different information.

### Board / Executive Update

Focus: outcome and risk. No feature lists.

```
Subject: [Product] Q[X] Update — [1-line headline]

Highlights:
- [Metric] moved from [X] to [Y] — [because of what]
- [Key decision made / milestone hit]

On Track:
- [OKR / initiative]: [status in 1 line]

At Risk:
- [OKR / initiative]: [what's at risk, what we're doing about it]

Asks:
- [Specific decision or resource needed from this group]
```

### Engineering Update

Focus: scope, dependencies, sequencing.

```
Sprint [N] — [date range]

Shipping:
- [Feature] — [status: in review / merged / deployed]

Blocked:
- [Feature] needs [dependency] from [team] by [date]

Upcoming:
- [What's planned for next sprint]

Technical debt / risk:
- [1-2 items worth flagging]
```

### Customer Update

Focus: value narrative and timing. No internal roadmap language.

```
Subject: What's new in [Product] — [Month Year]

[Lead with what changed and why it matters to them]

New this month:
- [Feature name]: [What it does for them — benefit-first, not feature-first]
- [Feature name]: [Same]

Coming soon:
- [Theme or outcome — not specific feature names unless committed]

[CTA: Try it / Read more / Give feedback]
```

### Feature Announcement Framework

```
1. Problem context: [Why this mattered / what wasn't working]
2. What changed: [What we built — 1 sentence]
3. Why it matters: [Concrete benefit]
4. Who benefits: [Which users / use cases]
5. How to get started: [Specific action]
6. CTA: [Link / button / next step]
```

Full templates → `references/comms-templates.md`

---

## Mode 4 — Quarterly Plan

Structure a quarterly planning cycle.

### Quarterly Planning Sequence

```
Week -3: Collect inputs
  - Review previous quarter OKR results
  - Gather customer research, support themes, competitive intel
  - Collect team capacity estimates

Week -2: Strategy alignment
  - Confirm company OKRs for the quarter (or generate from top-down direction)
  - Identify top 3 strategic bets
  - Alignment meeting with leadership

Week -1: OKR cascade
  - Draft product OKRs
  - Review with team leads — adjust for feasibility
  - Run alignment scoring (vertical + horizontal)

Week 0 (Q start): Finalize and publish
  - Finalize OKRs with final scores
  - Publish roadmap (right format for each audience)
  - Kickoff sprint 1
```

### Strategy Review Checklist (end of quarter)

- [ ] All KRs scored (0–1.0 scale — 0.7 is target, 1.0 may mean too easy)
- [ ] Retrospective: what caused misses? (data → decision → action)
- [ ] Learnings documented before next cycle begins
- [ ] Unfinished items triaged: carry forward, rescope, or cut
- [ ] Roadmap updated for next quarter

### OKR Scoring Scale

| Score | Meaning |
|---|---|
| 1.0 | Achieved 100% — may have been too easy |
| 0.7 | Target — ambitious but achieved |
| 0.5 | Partial — acceptable if context changed |
| 0.3 | Below — investigate root cause |
| 0.0 | Not started — requires explanation |

---

## References

- `references/okr-framework.md` — OKR cascade structure, alignment scoring, 5 strategy types, sample OKRs, anti-patterns
- `references/roadmap-formats.md` — Now/Next/Later, Timeline, Theme-based templates, format selection guide
- `references/comms-templates.md` — Board, engineering, customer update templates, feature announcement framework, release notes guidance
