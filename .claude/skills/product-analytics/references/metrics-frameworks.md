# Metrics Frameworks

## AARRR (Pirate Metrics)

Sequential funnel framework — best for consumer, growth-stage, acquisition-heavy products.

| Stage | What it measures | Key metrics |
|---|---|---|
| **Acquisition** | How users find you | New users, channel CAC, organic vs paid split |
| **Activation** | First value moment | Activation rate, time-to-activate, onboarding completion |
| **Retention** | Users who come back | D1/D7/D30 retention, churn rate, session frequency |
| **Referral** | Users who bring others | Viral coefficient (k-factor), NPS, referral conversion |
| **Revenue** | Business viability | MRR, ARPU, LTV, CAC:LTV ratio |

### Activation Event Definition

The activation event = the first action that predicts retention.
- Find it: segment users by D30 retention → what did retained users do in Day 1 that churners didn't?
- Examples: Slack = "sent 2000 messages", Twitter = "followed 30 accounts", Dropbox = "added 1 file"

### AARRR Funnel Conversion Targets (B2B SaaS reference)

| Stage | Benchmark |
|---|---|
| Visit → Signup | 2–5% |
| Signup → Activation | 20–40% |
| Activation → D30 retained | 15–30% |
| Free → Paid conversion | 2–5% (freemium) |

---

## North Star Metric

One metric that best represents the value your product delivers to customers. When it goes up, the business goes up. When it's flat, something is wrong.

### North Star Formula

```
North Star = [frequency] × [breadth] × [depth]

Where:
- Frequency: how often users engage (daily, weekly, monthly)
- Breadth: how many users engage
- Depth: how deeply they engage per session
```

### Supporting Metrics (Input Metrics)

3–5 metrics that directly drive the North Star.

```
North Star: Weekly active teams sending messages

Input Metrics:
├── New team signups (feeds breadth)
├── % of teams who activated (feeds breadth)
├── % of activated teams retained Week 4 (feeds frequency)
└── Messages per team per week (feeds depth)
```

### North Star Anti-Patterns

| Anti-Pattern | Why wrong |
|---|---|
| Revenue as North Star | Revenue is output — it doesn't explain why growth happened |
| Vanity metric (page views, downloads) | Doesn't measure value delivered to user |
| Too many "North Stars" | Defeats the purpose of a single organizing metric |
| North Star that only one team controls | Creates alignment failure |

---

## HEART Framework (Google)

For measuring user experience quality — combines quantitative and qualitative signals.

| Dimension | What it measures | Example metrics |
|---|---|---|
| **Happiness** | Subjective satisfaction | CSAT, NPS, app store rating, sentiment analysis |
| **Engagement** | Depth and frequency of use | Sessions/week, features used/user, active days |
| **Adoption** | Uptake of new features or users | % users using feature X, signups, installs |
| **Retention** | Users who return | D30/D90 retention, renewal rate, subscription length |
| **Task Success** | Can users complete the core job? | Task completion rate, error rate, time-on-task |

### HEART Grid (per feature or product area)

For each HEART dimension:
- Goals: what are we trying to change?
- Signals: what user behaviors indicate progress?
- Metrics: how do we measure those signals?

---

## KPIs by Product Stage

### Pre-PMF (0 → product-market fit)

| KPI | Target | Why |
|---|---|---|
| Activation rate | > 30% | Are users finding the value? |
| Week-1 retention | > 20% | Do they come back? |
| Time-to-first-value | < 10 min | Can they get value without help? |
| Problem-solution fit score | > 60% "very disappointed" | Sean Ellis test |
| Qualitative: interview themes | Consistent pain | Is the problem real? |

### Growth Stage (PMF → scaling)

| KPI | Why |
|---|---|
| Monthly retained users | Core growth signal |
| Feature adoption rate (key features) | Are users discovering value? |
| Funnel conversion (visit → paid) | Revenue engine efficiency |
| CAC by channel | Which channel to invest in? |
| Expansion MRR | Are happy users buying more? |

### Mature Stage (scaling → optimization)

| KPI | Why |
|---|---|
| NRR (net revenue retention) | > 100% = growth without new customers |
| Power-user share | % using 3+ core features weekly |
| Churn risk score (early warning) | Proactive retention |
| Support deflection rate | Product quality indicator |
| Infrastructure cost per user | Margin optimization signal |

---

## Retention Cohort Analysis

### Reading the Cohort Matrix

```
         D1      D7      D30     D90
Jan-26   85%     52%     28%     18%
Feb-26   83%     55%     31%     --
Mar-26   87%     60%     --      --
```

**Vertical read (by column):** Are newer cohorts retaining better? Signals product improvement.
- Feb > Jan at D7 (55% vs 52%) → onboarding improved
- Flat or declining → product isn't improving for this metric

**Horizontal read (by row):** At what point does retention stabilize? Signals habit formation.
- 18% floor at D90 → 18% are habitual users (retained core)
- Retention curve that keeps dropping → no habit formed

### Retention Curve Shapes

```
100% ─────────────────────────────────
      Sharp drop
      └──────────────────────── plateau ~18%  ← GOOD: habit formed
                                              
100% ─────────────────────────────────
      Continuous decline to 0             ← BAD: no habit
```

### Retention Analysis Questions

1. Are newer cohorts better than older ones? (product improvement signal)
2. Which acquisition channel has the best D30 retention? (channel quality)
3. Do users who use feature X retain at higher rates? (feature → retention correlation)
4. At what week does retention stabilize? (habit formation point — determines engagement strategy)
5. Does retention differ by plan tier? (value delivery by segment)

---

## Dashboard Architecture

### Layer 1 — Executive (3–5 metrics, weekly refresh)

| Metric | Baseline | Current | Target | Trend |
|---|---|---|---|---|
| [North Star] | | | | ↑↓→ |
| MRR | | | | |
| Churn rate | | | | |
| NPS | | | | |
| [1 operational health] | | | | |

### Layer 2 — Product Health (15–20 metrics, daily refresh)

Full AARRR funnel + feature adoption + error rates + support ticket volume.

### Layer 3 — Feature Dashboard (per feature, daily/real-time)

Adoption rate + engagement depth + retention impact + error rate + user satisfaction signal (NPS or CSAT specific to feature).

### Dashboard Quality Rules

- Every metric has a decision rule: "If X drops below Y, we investigate within Z hours"
- Metrics are segmented (never blended average across all users)
- Anomaly detection: flag > 20% week-over-week change automatically
- Ownership: every metric has a named owner who responds to anomalies
