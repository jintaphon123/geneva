---
name: product-analytics
argument-hint: "[mode] — kpi / dashboard / cohort / experiment / interpret"
description: >
  Product analytics covering KPI framework design, metric dashboards, cohort and retention analysis,
  A/B test design, hypothesis writing, and results interpretation.

  Auto-invoke when Bond asks: KPI, metrics, North Star metric, AARRR, HEART framework,
  metric dashboard, health dashboard, retention analysis, cohort analysis, cohort matrix,
  A/B test, experiment design, hypothesis, sample size, MDE, minimum detectable effect,
  ICE scoring experiment, activation rate, churn rate, interpret results, what does this metric mean.
---

# Product Analytics

Five modes for the full analytics and experimentation workflow.

---

## Mode Detection

| Input | Mode |
|---|---|
| "KPI", "metrics", "North Star", "AARRR", "HEART", "what should we measure" | **KPI Setup** |
| "dashboard", "metric dashboard", "health dashboard", "build a dashboard" | **Dashboard** |
| "cohort analysis", "retention curve", "retention analysis", "week 1 retention" | **Cohort** |
| "A/B test", "experiment design", "hypothesis", "sample size", "MDE", "ICE scoring" | **Experiment** |
| "what does this mean", "interpret results", "read this data", "why is X dropping" | **Interpret** |

---

## Mode 1 — KPI Setup

Choose the right metric framework and define stage-appropriate KPIs.

### Framework Selection

| Framework | Use when |
|---|---|
| **AARRR** | Consumer / growth-stage / acquisition-heavy products |
| **North Star Metric** | Focused team, single core value exchange, want alignment |
| **HEART** | User experience quality, UX-driven products, qualitative + quantitative blend |

### AARRR (Pirate Metrics)

| Stage | Metric | Definition |
|---|---|---|
| **Acquisition** | New users / New signups | How many new users arrived? |
| **Activation** | Activation rate | % who completed the "aha moment" (first key action) |
| **Retention** | D7, D30, Week-N retention | % who return after N days |
| **Referral** | Viral coefficient / NPS | Do users bring others? |
| **Revenue** | MRR, ARPU, conversion rate | Is it a business? |

### North Star Metric

```
North Star = [1 metric that best represents value delivered to customers]

Supporting metrics (input metrics that drive the North Star):
- Metric A: [directly drives North Star]
- Metric B: [directly drives North Star]
- Metric C: [directly drives North Star]
```

North Star examples:
- Slack: Daily active users sending messages
- Spotify: Time listening per user per month
- Airbnb: Nights booked
- SaaS: Weekly active organizations

### HEART Framework

| Dimension | Definition | Example metric |
|---|---|---|
| **Happiness** | Satisfaction, perceived quality | CSAT, NPS, app store rating |
| **Engagement** | Depth and frequency of use | Sessions/week, features used/user |
| **Adoption** | New feature or user growth | % users using feature X, new signups |
| **Retention** | Users who return over time | D30 retention, renewal rate |
| **Task Success** | Can users complete the core job? | Task completion rate, error rate |

### KPIs by Product Stage

| Stage | Focus KPIs |
|---|---|
| **Pre-PMF** | Activation rate, Week-1 retention, Time-to-first-value, Problem-solution fit score |
| **Growth** | Funnel conversion rate, Monthly retained users, Feature adoption rate, Expansion MRR |
| **Mature** | NRR (net revenue retention), Power-user share, Churn risk score, Support deflection rate |

Full frameworks → `references/metrics-frameworks.md`

---

## Mode 2 — Dashboard

Design layered metric dashboards.

### 3-Layer Dashboard Architecture

**Layer 1 — Executive Dashboard (3–5 metrics)**
- Audience: CEO, board, leadership
- Refresh: weekly
- Content: North Star, MRR, churn rate, NPS, 1 operational health metric
- Format: numbers + trend (vs last week, vs last quarter)

**Layer 2 — Product Health Dashboard (15–20 metrics)**
- Audience: product team, engineering leads
- Refresh: daily
- Content: full funnel (acquisition → activation → retention → revenue), feature adoption, error rates
- Format: charts + anomaly flags

**Layer 3 — Feature Dashboard (per feature)**
- Audience: feature team
- Refresh: daily/real-time
- Content: adoption, engagement, retention impact, error rate, satisfaction signal
- Format: before/after if post-launch, funnel if onboarding

### Dashboard Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Vanity metrics (total signups, page views) | Looks good but doesn't drive decisions | Replace with active users, activation rate |
| Dashboard overload (50+ metrics) | No one knows what to act on | Cut to 3–5 per layer |
| No decision rules | Data watched but not acted on | Add explicit thresholds that trigger action |
| Blended metrics | Segments mask problems | Slice by cohort, plan, or channel |
| Ignoring seasonality | Week-over-week looks wrong | Compare same-week-last-year or use rolling average |

Full templates → `references/metrics-frameworks.md`

---

## Mode 3 — Cohort

Build and interpret cohort and retention analyses.

### Retention Cohort Matrix

Rows = cohorts (grouped by signup date). Columns = time periods (D1, D7, D30, D90...).

| Cohort | D1 | D7 | D30 | D90 |
|---|---|---|---|---|
| Jan 2026 | 85% | 52% | 28% | 18% |
| Feb 2026 | 83% | 55% | 31% | — |
| Mar 2026 | 87% | 60% | — | — |

Read vertically: Are newer cohorts better than older ones? (product improvement)
Read horizontally: At what point does retention stabilize? (product-market fit signal)

### Retention Curve Interpretation

**Sharp drop → stable plateau:** Users who find value keep it. The plateau = your true retained users. PMF signal.

**Continuous decline to 0:** No habit formed. Product doesn't have a regular use case or triggers.

**High D1, low D7:** Activation works, habit doesn't. Fix: improve Day 1 experience to surface core value faster.

**Low D1:** Activation is broken. Fix: onboarding before anything else.

**Target benchmarks (consumer):** D1 >40%, D7 >20%, D30 >10% — varies heavily by category.

### Cohort Types

| Cohort Type | Group by | Use for |
|---|---|---|
| Acquisition cohort | Signup date | Default — track onboarding and retention |
| Behavioral cohort | First key action date | Track users from "aha moment" |
| Plan cohort | Subscription tier | Compare retention across pricing plans |
| Channel cohort | Acquisition channel | Identify which channel brings best users |

### Analysis Questions

1. Do newer cohorts retain better than older ones? (product improvement)
2. Which channels have the highest D30 retention? (acquisition quality)
3. Does feature X usage correlate with higher retention? (engagement → retention driver)
4. At what period does retention stabilize? (habit formation point)

Full analysis guide → `references/metrics-frameworks.md`

---

## Mode 4 — Experiment

Design rigorous A/B tests before building.

### Hypothesis Format

```
If we [intervention — specific change],
Then [primary metric] will [direction and magnitude — e.g., "increase by 10%"],
Because [behavioral mechanism — why users will respond this way].
```

Example:
"If we add a progress bar to the onboarding flow, then activation rate will increase by 8%, because users who see progress are more likely to complete multi-step flows (completion bias)."

### Metric Selection

- **Primary metric:** The one metric this experiment is designed to move. One only. Pre-commit.
- **Guardrail metrics:** Metrics that must NOT get worse (revenue, core retention, error rate)
- **Secondary metrics:** Supporting signals that provide context but don't determine success

### Sample Size Estimation

Required inputs:
- Baseline rate (current conversion/activation/retention)
- MDE (minimum detectable effect) — smallest lift worth shipping for
- Significance level: α = 0.05 (95% confidence — standard)
- Statistical power: 1-β = 0.80 (80% power — standard)

Rule of thumb: to detect a 10% relative lift on a 20% baseline requires ~4,000 users per variant.
Use a sample size calculator for precise numbers → `references/statistics-reference.md`

### ICE Scoring for Experiment Prioritization

ICE Score = (Impact × Confidence × Ease) / 10

- **Impact:** How much will this move the metric if it works? (1–10)
- **Confidence:** How strong is the evidence it will work? (1–10)
- **Ease:** How fast and cheap to run? (1–10)

Prioritize by ICE score — run high-score experiments first.

### Stopping Rules

- Decide stop criteria BEFORE launching (no peeking)
- Stop when: sample size reached AND statistical significance reached
- Early stop conditions: significant harm to guardrail metrics, catastrophic bug
- Do NOT stop because: it's trending negative, you're impatient, the business wants to ship

### 6 Common Pitfalls

1. **Underpowered tests** — sample too small → false negatives (miss real effects)
2. **Too many simultaneous changes** — can't attribute the effect
3. **Mid-test implementation changes** — invalidates the test
4. **Stopping early on positive spike** — regression to mean will kill it
5. **Ignoring sample ratio mismatch** — assignment bug creating selection bias
6. **Reporting p-value without effect size** — statistically significant ≠ business significant

Full playbook → `references/experiment-playbook.md`

---

## Mode 5 — Interpret

Read data and decide what action to take.

### Interpretation Checklist

Before drawing conclusions:
- [ ] Is the date range long enough to exclude anomalies? (minimum 2 weeks for weekly patterns)
- [ ] Are we comparing like-for-like? (same cohort, same time period, same segment)
- [ ] Is there a seasonal or external factor? (holidays, marketing campaigns, outages)
- [ ] Are the metrics segmented? (blended data masks segment-level problems)
- [ ] What is the statistical significance? (don't act on noise)

### Decision Rules

| Signal | Action |
|---|---|
| Metric drops > 20% week-over-week | Immediate investigation — likely a bug, outage, or data pipeline issue |
| Metric drops 5–20% week-over-week | Investigate — check for product changes, cohort mix shift, or seasonality |
| Metric improves after launch | Validate it's not novelty effect — check retention at D30 |
| Experiment shows p < 0.05 but tiny effect | Check practical significance — is the effect size worth shipping? |
| Retention plateau is rising across cohorts | Signal of product improvement — report to leadership with context |

### Anti-Pattern Diagnosis

| Symptom | Likely Cause | Investigation |
|---|---|---|
| High activation, low D7 retention | Feature doesn't create habit | Check day 2-6 engagement events |
| Good D30 retention, low ARPU | Monetization gap | Upgrade funnel and paywall analysis |
| High churn after first renewal | Expectation mismatch at signup | Win/loss interviews with churned users |
| Flat NPS despite feature launches | Features aren't solving real pain | Customer interviews + JTBD analysis |

---

## References

- `references/metrics-frameworks.md` — AARRR, North Star, HEART, KPIs by stage, dashboard architecture, cohort analysis guide
- `references/experiment-playbook.md` — hypothesis format, ICE scoring, stopping rules, 6 pitfalls, experiment template
- `references/statistics-reference.md` — sample size formula, significance/power, effect size, p-value interpretation, SRM detection
