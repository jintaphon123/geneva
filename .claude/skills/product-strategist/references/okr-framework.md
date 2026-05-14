# OKR Framework

## What Makes a Good OKR

**Objective:** Qualitative, aspirational, inspiring. No metrics. Should answer "where are we going?"
- Bad: "Increase user growth" (metric, not objective)
- Good: "Become the go-to tool for freelance designers"

**Key Result:** Specific, measurable, time-bound. Should answer "how will we know we got there?"
- Bad: "Improve retention" (not measurable)
- Good: "Increase 30-day retention from 32% to 45% by end of Q2"

Max 3–5 KRs per objective. More than 5 = unfocused.

---

## OKR Cascade Structure

### Company-Level OKRs (set by CEO / board)

```
O1: [Company strategic objective — 1 quarter]
  KR1.1: [Measurable outcome — company level]
  KR1.2: [Measurable outcome]

O2: [Company strategic objective]
  KR2.1: [Measurable outcome]
```

### Product-Level OKRs (support company OKRs)

```
O-P1: [Product objective — supports O1]
  KR-P1.1: [Product metric — contributes to KR1.1]
  KR-P1.2: [Product metric — contributes to KR1.2]

O-P2: [Product objective — supports O2]
  KR-P2.1: [Product metric]
```

### Team-Level OKRs (support product OKRs)

```
[Team Name] — supports O-P1
  O-T1: [Team objective]
    KR-T1.1: [Team metric that moves KR-P1.1]
    KR-T1.2: [Team metric]
```

---

## Alignment Scoring

### Vertical Alignment
% of product KRs that are explicitly linked to a company KR.
Target: > 90%
Formula: (# of product KRs with company KR link) / (total product KRs) × 100

### Horizontal Alignment
% of team KRs that are explicitly linked to a product KR.
Target: > 75%
Formula: (# of team KRs with product KR link) / (total team KRs) × 100

### Coverage
% of company KRs that have at least one product KR supporting them.
Target: > 80%
Formula: (# company KRs with ≥1 product KR) / (total company KRs) × 100

### Balance
No single team responsible for > 40% of product KRs.
Flag: if any team owns > 40% → risk of bottleneck and unfair load.

---

## 5 Strategy Types with Sample OKRs

### 1. Growth Strategy (scale user base)

```
O: Become the fastest-growing [category] tool for [ICP]
  KR1: Grow monthly active users from [X] to [Y] by [date]
  KR2: Reduce time-to-activate from [X days] to [Y days]
  KR3: Launch [N] new acquisition channels with > [X] signups each
```

### 2. Retention Strategy (reduce churn)

```
O: Build the stickiest product in [category]
  KR1: Increase 30-day retention from [X%] to [Y%]
  KR2: Reduce monthly churn from [X%] to [Y%]
  KR3: Increase NPS from [X] to [Y]
```

### 3. Revenue Strategy (increase ARPU / expansion)

```
O: Make [Product] a significant revenue engine
  KR1: Grow MRR from $[X] to $[Y]
  KR2: Increase ARPU from $[X] to $[Y]
  KR3: Grow expansion revenue (upgrades + add-ons) to [X%] of total MRR
```

### 4. Innovation Strategy (differentiate)

```
O: Ship differentiated capabilities competitors can't replicate in 6 months
  KR1: Launch [N] features rated "can't live without" by > [X%] of users
  KR2: Achieve [X%] feature adoption within 30 days of launch
  KR3: Reduce competitive loss rate from [X%] to [Y%]
```

### 5. Operational Strategy (efficiency)

```
O: Ship faster without increasing bugs or debt
  KR1: Reduce median time-to-ship from [X days] to [Y days]
  KR2: Reduce P1/P2 bug count from [X/quarter] to [Y/quarter]
  KR3: Increase test coverage from [X%] to [Y%]
```

---

## OKR Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Objectives with metrics | Conflates direction with measurement | Rewrite: "Become X" not "Grow X by Y" |
| KRs that are tasks not outcomes | Measures output not impact | "Launch feature X" → "X% of users use feature X" |
| Too many OKRs | Everything is priority = nothing is priority | Max 3 objectives per level, 3–5 KRs each |
| KRs set without baseline data | Can't score without a starting point | Establish baseline before locking KRs |
| OKRs never reviewed mid-quarter | Drift without accountability | Monthly OKR check-in — score current progress |
| Score inflation | Teams sandbagging to hit 1.0 | Calibrate: 0.7 is target, 1.0 may mean too easy |

---

## OKR Scoring

At quarter end, score each KR 0.0–1.0:

| Score | Meaning |
|---|---|
| 1.0 | 100% achieved — evaluate if target was ambitious enough |
| 0.7 | Target — ambitious and approximately achieved |
| 0.5 | Partial — acceptable if context changed significantly |
| 0.3 | Below target — investigate root cause for retrospective |
| 0.0 | Not started — requires explanation |

Objective grade = average of its KR scores.

**Grade interpretation:**
- 0.7–1.0: Success zone
- 0.5–0.69: Partial — discuss in retrospective
- < 0.5: Investigate — systemic problem or wrong objective
