# Agile Capacity Planning & Advanced Prioritization

## WSJF — Weighted Shortest Job First

Use when: team is resource-constrained and you need to optimize sequence for maximum value delivery. Better than RICE when dependencies matter and time-sensitivity varies significantly across work items.

**Formula:**
```
WSJF = (User/Business Value + Time Criticality + Risk Reduction) / Job Size

Each factor scored 1-20 (Fibonacci: 1, 2, 3, 5, 8, 13, 20)
Higher WSJF = do first
```

### Factor Scoring Rubric (1-20 scale)

**User/Business Value:**
| Score | Meaning |
|-------|---------|
| 1-2 | Minimal: nice-to-have, affects few users |
| 3-5 | Low: addresses minor pain point |
| 8 | Medium: meaningful improvement for significant user segment |
| 13 | High: core user workflow, high adoption impact |
| 20 | Critical: blocks key business objective or major revenue |

**Time Criticality (cost of delay):**
| Score | Meaning |
|-------|---------|
| 1-2 | No urgency: delay by 6 months = no material impact |
| 3-5 | Low: minor inconvenience if delayed |
| 8 | Medium: opportunity cost grows weekly if delayed |
| 13 | High: deadline-driven, regulatory, or competitive window |
| 20 | Extreme: contract requirement, legal deadline, or market closes in weeks |

**Risk Reduction / Opportunity Enablement:**
| Score | Meaning |
|-------|---------|
| 1-2 | No risk reduction or new opportunity enabled |
| 3-5 | Small: reduces minor technical debt or unlocks low-value opportunities |
| 8 | Medium: removes a meaningful blocker or enables key integration |
| 13 | High: mitigates significant operational or security risk |
| 20 | Critical: prevents data loss, compliance failure, or enables strategic initiative |

**Job Size (effort, inverse — smaller = higher priority):**
| Score | Meaning |
|-------|---------|
| 1 | 1-2 days |
| 2 | 3-5 days (1 sprint item) |
| 3 | 1 sprint |
| 5 | 2-3 sprints |
| 8 | Full quarter |
| 13-20 | Multi-quarter program |

### WSJF Example

| Feature | Value | Time Crit | Risk Red | Size | WSJF | Priority |
|---------|-------|-----------|----------|------|------|----------|
| Auth bug fix | 13 | 20 | 13 | 2 | 23.0 | #1 |
| New dashboard | 8 | 5 | 3 | 8 | 2.0 | #3 |
| SSO integration | 13 | 13 | 8 | 5 | 6.8 | #2 |

### When to Use WSJF vs RICE

| Situation | Use |
|-----------|-----|
| Sprint planning with capacity constraints | WSJF |
| Customer-reach-based prioritization | RICE |
| Dependency ordering (order of implementation matters) | WSJF |
| Product roadmap across many features | RICE or ICE first, WSJF to sequence |
| Regulatory or deadline-driven work | WSJF (Time Criticality captures this) |

---

## Three Horizons Model for Product

Allocate product work across three time horizons to balance execution vs. growth vs. bets:

```
H1 — Core (70%): Today's revenue and retention
H2 — Growth (20%): Next year's competitive position  
H3 — Bets (10%): 2+ years, moonshots and market creation
```

### H1 — Core Features (70% of capacity)
- Bug fixes and reliability improvements
- Retention-critical features (reduce churn, increase engagement)
- Performance and scalability work
- Features that protect existing revenue
- **Goal:** Keep existing customers happy and growing

### H2 — Growth Initiatives (20% of capacity)
- Expand to adjacent customer segments
- Platform expansion (new integrations, APIs, channels)
- Features that unlock new revenue streams
- **Goal:** Build the features that will be H1 in 12 months

### H3 — Transformational Bets (10% of capacity)
- Experimental features with uncertain market fit
- New product categories or business models
- Fundamental technology bets (AI integration, new architecture)
- **Goal:** Explore without disrupting H1/H2

**How to apply in planning:**
```
Sprint capacity: 100 story points

H1 allocation: 70 points → core bug fixes, retention features, reliability
H2 allocation: 20 points → growth initiative sprint tasks
H3 allocation: 10 points → research spikes, prototypes, feasibility

If H3 items mature → promote to H2
If H2 items prove out → promote to H1
```

---

## Velocity-Based Capacity Planning

### Baseline Velocity

Use 6-sprint rolling average as baseline:
```
Baseline Velocity = Average of last 6 sprints' completed story points
```

Never use planned points — only count completed, accepted points.

### Confidence Intervals for Roadmap Planning

Apply Monte Carlo confidence levels when estimating roadmap dates:

| Confidence | Sprint Commitment | Use for |
|-----------|------------------|---------|
| **P50** (50%) | 100% of baseline velocity | Internal estimation only — likely to slip |
| **P70** (70%) | 85% of baseline velocity | External commitment to stakeholders |
| **P85** (85%) | 75% of baseline velocity | Conservative promise to customers |
| **P95** (95%) | 65% of baseline velocity | Executive or investor timeline commitments |

**Sprint commitment rule:** Use **P70** (85% of baseline) as the sprint commitment ceiling. The remaining 15% acts as buffer for unexpected complexity, blockers, and interruptions.

### Sprint Commitment Health Metrics

| Metric | Calculation | Healthy | Watch | Critical |
|--------|------------|---------|-------|---------|
| Commitment Reliability | Completed / Committed × 100 | >85% | 70-85% | <70% |
| Scope Stability | 1 - (mid-sprint changes / committed points) | >90% | 80-90% | <80% |
| Velocity Volatility (CV) | σ/μ of 6-sprint velocity | <20% | 20-30% | >30% |

### 6-Sprint Roadmap Forecast Template

```
Baseline velocity: [X] points/sprint
P70 commitment ceiling: [X × 0.85] points/sprint

Feature backlog prioritized:
| Feature | Size (points) | Sprint (P70) | Sprint (P85) |
|---------|--------------|--------------|--------------|
| Feature A | 30 | Sprint 1 | Sprint 1 |
| Feature B | 50 | Sprint 2 | Sprint 2 |
| Feature C | 80 | Sprint 3-4 | Sprint 4-5 |

Committed roadmap (P70): Features A + B by [date], C by [date+1 month]
Conservative roadmap (P85): Features A + B by [date+1], C by [date+2 months]
```

---

## Tuckman Stage → Delivery Impact

Apply a buffer to velocity estimates based on team's current maturity stage:

| Stage | Characteristics | Velocity Adjustment |
|-------|----------------|---------------------|
| **Forming** | New team, heavy process-learning, high dependency on PM/SM | Use 70% of baseline; add 30% buffer to all estimates |
| **Storming** | Conflict and role clarification; delivery is erratic | Use 80% of baseline; add 20% buffer |
| **Norming** | Process established, collaboration working | Use 100% of baseline; no additional buffer |
| **Performing** | Self-managing, high trust, consistent delivery | Can increase to 110-115% — team can take on stretch goals |

**How to assess current stage:**
- Forming: Team asking basic process questions; significant PM involvement in daily decisions
- Storming: Disagreements visible in planning/retros; velocity has high variance sprint-to-sprint
- Norming: Consistent velocity, team self-corrects, retrospectives generate real action items
- Performing: Team proactively improves process, low PM intervention needed, predictable delivery

**Adjustment example:**
```
Baseline velocity: 60 points/sprint
Team stage: Storming → apply 0.80 multiplier

Adjusted velocity for planning: 60 × 0.80 = 48 points
P70 commitment ceiling: 48 × 0.85 = 41 points/sprint
```

---

## Prioritization Framework Selection Guide

| Question | Best Framework |
|----------|---------------|
| Which features to build across a quarter? | RICE (reach-based) |
| How to sequence work already in backlog? | WSJF (time sensitivity + size) |
| What to do when behind on roadmap? | WSJF (optimize for value density) |
| What not to cut when scope must shrink? | MoSCoW (protect Must-Haves) |
| Which bets to fund with limited R&D budget? | Three Horizons (70/20/10) |
| Quick gut-check prioritization in team meeting? | ICE (fast, collaborative) |
