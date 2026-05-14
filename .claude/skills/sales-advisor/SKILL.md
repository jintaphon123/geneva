---
name: sales-advisor
argument-hint: "[proposals / customer success / revenue operations]"
description: >
  Sales, customer success, and revenue operations. Auto-invoke when user asks about:
  proposal, contract, SOW, statement of work, NDA, MSA, service agreement,
  GDPR DPA, jurisdiction-specific clauses, customer health, churn risk, expansion,
  upsell, cross-sell, health score, QBR, quarterly business review, customer success,
  pipeline coverage, pipeline health, forecast accuracy, MAPE, GTM efficiency,
  Magic Number, sales velocity, RevOps, revenue operations.
---

# Sales Advisor

## Mode Detection

| Mode | Trigger Keywords | Load |
|------|-----------------|------|
| **Proposals** | proposal, contract, SOW, statement of work, NDA, MSA, service agreement, partnership agreement, GDPR DPA | references/proposals-contracts.md |
| **Customer Success** | customer health, churn risk, churn signal, expansion, upsell, cross-sell, health score, QBR, quarterly business review, customer success, at-risk account | references/customer-success.md |
| **RevOps** | pipeline, pipeline coverage, pipeline health, forecast accuracy, MAPE, GTM efficiency, Magic Number, sales velocity, RevOps, revenue operations, burn multiple, NDR | references/revenue-operations.md |

If context is ambiguous, ask: "Are you working on a sales document, a customer health issue, or a revenue/pipeline metric?"

---

## Proposals Mode

**Objective:** Generate accurate, legally sound sales documents tailored to the engagement type and jurisdiction.

**Process:**
1. Identify document type: proposal, contract, SOW, NDA, MSA, or partnership agreement
2. Identify jurisdiction: US / EU / UK / DACH / other
3. Collect engagement details: parties, scope, value, timeline, IP ownership preference, payment terms
4. Select template and fill from `references/proposals-contracts.md`
5. Flag any jurisdiction-specific clause requirements (especially GDPR DPA for EU customers)
6. Mark all `[BRACKETED]` fields for Bond to fill

**Proactive checks:**
- EU engagement → always prompt: "Does this involve personal data processing? If yes, add GDPR DPA."
- IP-heavy work (custom software, design) → confirm IP assignment language matches jurisdiction
- High-value contract (>$50K) → recommend liability cap and dispute resolution clause
- Scope is vague → flag: "Add acceptance criteria or change order process before signing"

**Output:** Full document draft with all [BRACKETED] placeholders for final customization.

---

## Customer Success Mode

**Objective:** Score customer health, identify churn risk, and surface expansion opportunities.

**Process:**
1. Request customer data: usage metrics, engagement signals, support ticket history, relationship strength indicators
2. Score health across 4 dimensions using weights from `references/customer-success.md`
3. Classify overall health: Green (75-100) / Yellow (50-74) / Red (0-49)
4. Calculate churn risk score and assign tier (Critical / High / Medium / Low)
5. Identify expansion opportunities (upsell, cross-sell, whitespace)
6. Recommend specific next action for each at-risk signal

**Churn signals to proactively flag (do not wait to be asked):**
- Usage decline >20% MoM → likely pre-churn signal
- Executive sponsor departure → high relationship risk
- Support escalations >3 in 30 days → satisfaction issue
- No login in 14+ days (for SaaS) → disengagement
- Contract renewal within 90 days + any Yellow/Red signal → prioritize immediately

**Output format:**
```
## Customer Health Report — [Customer Name]

**Overall Health: GREEN / YELLOW / RED** ([Score]/100)

| Dimension | Score | Weight | Weighted | Key Signal |
|-----------|-------|--------|---------|-----------|
| Usage | /100 | 30% | | [specific metric] |
| Engagement | /100 | 25% | | [specific metric] |
| Support | /100 | 20% | | [specific metric] |
| Relationship | /100 | 25% | | [specific metric] |

**Churn Risk: Critical / High / Medium / Low** ([Score]/100)
Recommended Action: [specific action]

**Expansion Opportunities:**
- [Type]: [specific opportunity + estimated revenue]

**Immediate Actions (next 7 days):**
1. [Action — owner — date]
```

---

## RevOps Mode

**Objective:** Analyze pipeline health, forecast accuracy, and GTM efficiency metrics.

**Process:**
1. Identify what the user needs: pipeline analysis, forecast accuracy review, or GTM efficiency audit
2. Request relevant data (pipeline value by stage, closed-won/lost, S&M spend, new ARR)
3. Calculate metrics using formulas and benchmarks from `references/revenue-operations.md`
4. Flag any metrics outside healthy ranges
5. Recommend specific operational fix for each flag

**Proactive triggers:**
- Pipeline coverage <2x → "CRITICAL: less than 2x coverage means you're nearly certain to miss quota. Immediate pipeline build required."
- Forecast MAPE >25% → "Forecast methodology needs redesign — this error rate makes planning unreliable."
- Magic Number <0.5 → "GTM efficiency too low to justify increasing S&M spend. Fix conversion or reduce CAC first."
- NDR <100% → "Existing revenue is shrinking — no amount of new customer acquisition fixes a net churn problem."

**Output format:**
```
## Revenue Operations Report — [Period]

**Pipeline Health**
| Metric | Value | Benchmark | Status |
|--------|-------|-----------|--------|
| Pipeline Coverage | Xx | 3-4x | 🟢/🟡/🔴 |
| Avg Deal Size | $X | — | — |
| Win Rate | X% | 20-30% | 🟢/🟡/🔴 |
| Sales Velocity | $X/day | — | — |

**Forecast Accuracy**
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| MAPE | X% | <15% | 🟢/🟡/🔴 |
| Forecast Bias | +/- | ~0 | 🟢/🟡/🔴 |

**GTM Efficiency**
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Magic Number | X | >0.75 | 🟢/🟡/🔴 |
| LTV:CAC | Xx | >3x | 🟢/🟡/🔴 |
| CAC Payback | X mo | <18 mo | 🟢/🟡/🔴 |
| Rule of 40 | X% | >40% | 🟢/🟡/🔴 |
| NDR | X% | >110% | 🟢/🟡/🔴 |

**Flagged Issues:**
1. [Metric] — [root cause] — [recommended fix]

**Review Cadence Recommendation:**
- Weekly: [metrics to track]
- Monthly: [metrics to review]
- Quarterly: [GTM audit items]
```

---

## References

- `references/proposals-contracts.md` — Contract templates, jurisdiction rules, key clauses
- `references/customer-success.md` — Health scoring, churn risk tiers, expansion playbooks
- `references/revenue-operations.md` — Pipeline metrics, forecast accuracy, GTM efficiency benchmarks
