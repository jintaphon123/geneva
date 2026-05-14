# Customer Success — Health Scoring, Churn Risk & Expansion

## Health Score Framework

### 4 Dimensions + Weights

| Dimension | Weight | What it Measures |
|-----------|--------|-----------------|
| **Usage** | 30% | Product engagement: login frequency, feature adoption, DAU/MAU |
| **Engagement** | 25% | Business relationship: meeting attendance, NPS/CSAT, responsiveness |
| **Support** | 20% | Account health: ticket volume, escalation rate, resolution time |
| **Relationship** | 25% | Strategic depth: executive sponsor, multi-threading, renewal sentiment |

### Scoring Each Dimension (0-100)

**Usage (30%)**

| Signal | Score |
|--------|-------|
| Daily active use, full feature adoption, DAU/MAU >40% | 80-100 |
| 3-4x/week use, core features used, DAU/MAU 20-40% | 60-79 |
| 1-2x/week, limited features, DAU/MAU 10-20% | 40-59 |
| <Weekly, minimal features, DAU/MAU <10% | 20-39 |
| No logins 14+ days | 0-19 |

**Engagement (25%)**

| Signal | Score |
|--------|-------|
| Attends all meetings, NPS 9-10, responds within 24h | 80-100 |
| Attends most meetings, NPS 7-8, responds within 48h | 60-79 |
| Misses some meetings, NPS 5-6, slow response | 40-59 |
| Avoids meetings, NPS <5, unresponsive | 0-39 |

**Support (20%)**

| Signal | Score |
|--------|-------|
| 0-1 tickets/month, no escalations, <24h resolution | 80-100 |
| 2-3 tickets/month, 1 escalation max, <48h resolution | 60-79 |
| 4-6 tickets/month, recurring issues, escalations | 40-59 |
| 7+ tickets/month, multiple escalations, open issues >30 days | 0-39 |

**Relationship (25%)**

| Signal | Score |
|--------|-------|
| Executive sponsor active, 3+ stakeholders, positive renewal signals | 80-100 |
| Mid-level sponsor, 2 stakeholders, neutral on renewal | 60-79 |
| No exec sponsor, single contact, no renewal discussions | 40-59 |
| Lost executive sponsor, stakeholder turnover, cancellation signals | 0-19 |

### Health Classification

```
Total Score = (Usage × 0.30) + (Engagement × 0.25) + (Support × 0.20) + (Relationship × 0.25)

GREEN  (75-100): Customer achieving value — continue standard cadence
YELLOW (50-74):  Needs attention — increase check-in frequency, identify blockers
RED    (0-49):   At risk — immediate intervention required
```

---

## Churn Risk Assessment

### Churn Signal Weights

| Signal Category | Weight | Key Indicators |
|----------------|--------|----------------|
| Usage Decline | 30% | Login frequency drop, feature disengagement |
| Engagement Drop | 25% | Meeting cancellations, NPS decline, response delays |
| Support Issues | 20% | Escalation volume, unresolved tickets, recurring bugs |
| Relationship Signals | 15% | Champion departure, stakeholder turnover, budget pressure signals |
| Commercial Factors | 10% | Renewal date proximity, industry headwinds, competitive threats |

### Churn Risk Tiers + Actions

| Tier | Score | Response | Timeline |
|------|-------|----------|----------|
| **Critical** | 80-100 | Immediate executive escalation — VP/CEO involvement, emergency account review | <24 hours |
| **High** | 60-79 | Urgent CSM intervention — discovery call to surface root issues, recovery plan | <48 hours |
| **Medium** | 40-59 | Proactive outreach — check-in call, value reinforcement, support offer | <7 days |
| **Low** | 0-39 | Standard monitoring — maintain cadence, log signals | Monthly review |

### Churn Pre-Warning Signals

Flag proactively when any of these detected:

| Signal | Action |
|--------|--------|
| Usage decline >20% MoM (any dimension) | Escalate to High risk regardless of score |
| Executive sponsor departure | Escalate to High — new relationship must be built |
| Support escalations >3 in 30 days | Flag as Medium minimum |
| No login in 14+ days (SaaS) | Flag for outreach immediately |
| Renewal within 90 days + any Yellow/Red | Prioritize — cannot afford to lose this quarter |
| Competitor mentioned in meeting | Log and prepare battle card |
| "Evaluating alternatives" | Escalate to High immediately |
| Budget freeze or layoffs at customer | Prepare lower-tier retention offer |

---

## Intervention Playbooks

### Critical (80-100 Churn Risk)

**Week 1:**
- Day 1: CSM + VP of CS call to customer executive — "executive business review"
- Surface: What specific outcomes are not being achieved?
- Offer: Success plan reset, dedicated support, potential concession

**Week 2:**
- Present recovery plan with specific milestones and owners
- Offer executive sponsorship from your side (VP/CEO involvement)

**Week 3-4:**
- Track recovery milestones weekly
- If no improvement after 30 days, begin win-back planning for after cancellation

### High (60-79 Churn Risk)

**Week 1:**
- CSM discovery call: "I want to make sure you're getting the most value..."
- Diagnose: usage, onboarding gaps, unresolved support issues
- Offer: re-onboarding, feature training, business review

**Week 2-4:**
- Present value recap (ROI they've achieved)
- Introduce relevant new features or use cases
- Schedule monthly check-in cadence

### Medium (40-59 Churn Risk)

- Proactive outreach: "How is [product] working for your team?"
- Share relevant content (best practices, customer stories)
- Offer optional health check or optimization call

---

## Expansion Opportunity Identification

### Expansion Types

| Type | Trigger | Revenue Potential |
|------|---------|-----------------|
| **Upsell** | Customer hitting plan limits, requests premium feature | +30-100% ACV |
| **Cross-sell** | Customer using Product A, relevant Product B exists | +20-50% ACV |
| **Seat expansion** | New team members onboarded, growing usage | +5-20% ACV per seat |
| **Whitespace** | Departments not yet using product | 2-5× current ACV |

### Expansion Scoring

Look for these indicators before proposing expansion:

| Indicator | What it signals |
|-----------|----------------|
| DAU/MAU >50% and growing | High engagement → ready for more |
| NPS 9-10 | Promoter — will advocate for expanded investment |
| Hitting plan limits | Natural upsell moment |
| Multiple departments asking for access | Whitespace opportunity |
| New use case mentioned in QBR | Cross-sell opening |
| Executive expressing growth plans | Timing aligns with expansion |

**Expansion timing:** Never propose expansion to Yellow/Red accounts. Fix health first.

---

## QBR (Quarterly Business Review) Template

```
## Quarterly Business Review — [Customer] — [Quarter]

**Attendees:** [CSM], [Customer Success Manager], [Customer Executive Sponsor]
**Duration:** 60 minutes

---

### 1. Executive Summary (5 min)
- Overall health: [GREEN/YELLOW/RED]
- One-sentence status: [What's going well and what needs attention]

### 2. Goals Review (15 min)
| Goal Set Q[X] | Status | Evidence |
|---------------|--------|---------|
| [Goal 1] | ✅/🟡/❌ | [metric] |

### 3. Usage & Value Metrics (15 min)
| Metric | Q[X-1] | Q[X] | Trend |
|--------|--------|------|-------|
| Active Users | | | ↑/↓/→ |
| Feature Adoption | | | |
| [Key Metric] | | | |

### 4. Support & Issues (10 min)
- Open tickets: [count]
- Resolved this quarter: [count]
- Notable issues: [1-2 bullets]

### 5. Risks & Blockers (10 min)
| Risk | Impact | Mitigation |
|------|--------|-----------|
| [Risk] | H/M/L | [Action] |

### 6. Next 90-Day Plan (5 min)
| Goal | Owner | Target Date |
|------|-------|-------------|
| [Goal] | [Owner] | [Date] |
```

---

## Benchmarks by Segment

| Metric | SMB | Mid-Market | Enterprise |
|--------|-----|-----------|-----------|
| GRR target | >85% | >90% | >95% |
| NRR target | >100% | >110% | >120% |
| Annual logo churn | <15% | <10% | <5% |
| NPS target | >30 | >40 | >50 |
| QBR cadence | Quarterly | Quarterly | Monthly |
| CSM:Account ratio | 1:50-100 | 1:20-50 | 1:5-20 |
| Time-to-value target | <14 days | <30 days | <60 days |
