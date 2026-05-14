# SaaS Metrics — Formulas, Benchmarks & Health Scoring

## Core Metric Formulas

### Revenue Metrics

**MRR (Monthly Recurring Revenue)**
```
MRR = Σ(active subscriptions × monthly price)
ARR = MRR × 12
```

**MRR Components (for waterfall analysis):**
```
New MRR = MRR from new customers this month
Expansion MRR = MRR increase from existing customers (upsell/cross-sell)
Contraction MRR = MRR decrease from existing customers (downgrade)
Churned MRR = MRR lost from cancelled customers
Net New MRR = New MRR + Expansion MRR - Contraction MRR - Churned MRR
```

**MRR Growth Rate (MoM):**
```
MRR Growth % = (MRR_this_month - MRR_last_month) / MRR_last_month × 100
```

---

### Retention Metrics

**Gross Revenue Retention (GRR):**
```
GRR = (MRR_start - Churned MRR - Contraction MRR) / MRR_start × 100

Range: 0-100% (cannot exceed 100% — expansion not counted)
Target: >85% SMB / >90% Mid-Market / >95% Enterprise
```

**Net Revenue Retention / Net Dollar Retention (NRR/NDR):**
```
NRR = (MRR_start + Expansion MRR - Contraction MRR - Churned MRR) / MRR_start × 100

Can exceed 100% (expansion from existing customers offsets churn)
>100% = net positive — company grows revenue even with zero new customers
Target: >100% SMB / >110% Mid-Market / >120% Enterprise
```

**Customer Churn Rate:**
```
Logo Churn Rate = Customers lost / Customers at start of period × 100
Monthly churn target: <2% SMB / <1% Mid-Market / <0.5% Enterprise
Annual = (1 - (1 - Monthly Churn)^12) × 100
```

---

### Unit Economics

**CAC (Customer Acquisition Cost):**
```
CAC = Total S&M Spend (period) / New Customers Acquired (period)

Note: Use trailing period — e.g., Q4 spend / Q1 new customers (account for sales cycle lag)
Blended CAC: all customers
Paid CAC: exclude organic/referral customers for channel-level view
```

**LTV (Customer Lifetime Value):**
```
Simple LTV = ARPU / Monthly Churn Rate

Or contribution-based LTV:
LTV = (ARPU - COGS per customer) / Monthly Churn Rate

Or discounted LTV:
LTV = Σ[(Monthly Contribution Margin) / (1 + discount_rate)^t] for t = 1 to expected life
```

**LTV:CAC Ratio:**
```
LTV:CAC = LTV / CAC

>3:1 = Healthy (enough lifetime value to justify acquisition cost)
2:1-3:1 = Watch (marginal; optimize)
<2:1 = Critical (acquiring customers for less than they're worth)
```

**CAC Payback Period:**
```
CAC Payback (months) = CAC / Monthly Gross Margin per Customer
                     = CAC / (ARPU × Gross Margin %)

Target: <12 months (aggressive growth) / <18 months (sustainable) / <24 months (max)
```

---

### Efficiency Metrics

**Quick Ratio (Bessemer / Growth Efficiency):**
```
Quick Ratio = (New MRR + Expansion MRR) / (Churned MRR + Contraction MRR)

>4 = EXCELLENT (elite growth efficiency)
2-4 = HEALTHY
1-2 = WATCH (churn eating growth)
<1 = CRITICAL (contracting business)
```

**Magic Number (Go-to-Market Efficiency):**
```
Magic Number = Net New ARR (quarter) / S&M Spend (prior quarter)

>1.0 = Excellent (step on the gas)
0.75-1.0 = Good (invest steadily)
0.5-0.75 = Watch (optimize before scaling)
<0.5 = Poor (fix before increasing spend)
```

**Burn Multiple:**
```
Burn Multiple = Net Cash Burned / Net New ARR

<1x = Excellent
1-1.5x = Good
1.5-2x = Acceptable
>2x = Inefficient
```

**Rule of 40:**
```
Rule of 40 = Revenue Growth Rate % + EBITDA Margin %

>40 = Healthy balance of growth and profitability
20-40 = Monitor and optimize
<20 = Needs significant improvement

Note: Best for companies with >$50M ARR. Earlier stage prioritize growth over Rule of 40.
```

---

## Segment Benchmarks

### By Company Stage

| Metric | Early (<$1M ARR) | Growth ($1-10M ARR) | Scale ($10-50M ARR) | Mature (>$50M ARR) |
|--------|-----------------|---------------------|---------------------|---------------------|
| MoM Growth | 15-25% | 10-20% | 5-10% | 3-7% |
| Gross Margin | >60% | >65% | >70% | >70% |
| GRR | >75% | >80% | >85% | >90% |
| NRR | >90% | >100% | >110% | >115% |
| CAC Payback | <24 mo | <18 mo | <15 mo | <12 mo |
| LTV:CAC | >2x | >3x | >3x | >4x |
| Quick Ratio | >2 | >2 | >2 | >1.5 |

### By Segment (Market)

| Metric | SMB | Mid-Market | Enterprise | PLG |
|--------|-----|-----------|-----------|-----|
| GRR target | >85% | >90% | >95% | >80% |
| NRR target | >100% | >110% | >120% | >100% |
| Logo churn (annual) | <15% | <10% | <5% | <20% |
| CAC Payback | <12 mo | <18 mo | <24 mo | <6 mo |
| Magic Number | >0.75 | >0.75 | >0.5 | >1.0 |

---

## Health Scoring Output Format

```
## SaaS Health Report — [Company / Period]

| Metric | Value | Benchmark ([Segment]) | Status |
|--------|-------|----------------------|--------|
| ARR | $X | — | — |
| MRR Growth (MoM) | X% | Y% | 🟢/🟡/🔴 |
| Gross Revenue Retention | X% | >85% | 🟢/🟡/🔴 |
| Net Revenue Retention | X% | >100% | 🟢/🟡/🔴 |
| Blended CAC | $X | — | — |
| LTV | $X | — | — |
| LTV:CAC Ratio | Xx | >3x | 🟢/🟡/🔴 |
| CAC Payback | X mo | <18 mo | 🟢/🟡/🔴 |
| Quick Ratio | X | >2 | 🟢/🟡/🔴 |
| Magic Number | X | >0.75 | 🟢/🟡/🔴 |
| Rule of 40 | X% | >40% | 🟢/🟡/🔴 |

**Overall Health: HEALTHY / WATCH / CRITICAL**
[One sentence why]

**Priority Issues (max 3, ranked by urgency):**
1. [Metric] at [value] vs [benchmark] — [root cause hypothesis] — [specific fix]
2. ...
3. ...

**Strengths:**
- [Metric] at [value] — [what this means]

**90-Day Focus Metric:** [metric] — target [value] by [date]
```

---

## Proactive Trigger Flags

Flag immediately if any of the following detected:

| Signal | Threshold | Implication | Action |
|--------|-----------|-------------|--------|
| **NDR < 100%** | Any | Net revenue shrinking without new customers | Churn emergency — root cause immediately |
| **Churned MRR > New MRR** | Any | Company contracting | Stop growth spend; fix retention first |
| **Quick Ratio < 1.0** | Any | Contraction faster than growth | Severe signal — executive attention |
| **CAC Payback > 24 months** | >24 mo | Unsustainable acquisition | Reduce CAC or increase ARPU |
| **LTV:CAC < 2x** | <2x | Unit economics broken | Cannot scale profitably |
| **Magic Number < 0.5** | <0.5 | S&M not converting | Optimize GTM before more spend |
| **Burn Multiple > 3x** | >3x | Burning too much cash per $ARR | Reduce burn or grow faster |

---

## MRR Waterfall Example

```
Opening MRR (Jan 1):           $500,000
+ New MRR:                      +$40,000   (80 new customers × $500 ARPU)
+ Expansion MRR:                +$15,000   (upgrades from existing)
- Contraction MRR:               -$8,000   (downgrades)
- Churned MRR:                  -$12,000   (lost customers)
= Closing MRR (Jan 31):        $535,000

Net New MRR: +$35,000
MoM Growth: +7%
Quick Ratio: ($40K + $15K) / ($8K + $12K) = 2.75 → HEALTHY
```
