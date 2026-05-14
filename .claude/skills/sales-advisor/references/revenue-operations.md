# Revenue Operations — Pipeline, Forecast & GTM Efficiency

## Pipeline Metrics Hierarchy

5 levels, each enabling the next:

```
Level 5 (Strategic)   Revenue efficiency, market position
Level 4 (Efficiency)  GTM metrics — Magic Number, LTV:CAC, Burn Multiple
Level 3 (Revenue)     ARR, NRR, GRR — what you earned and kept
Level 2 (Pipeline)    Coverage, velocity, conversion — what's coming
Level 1 (Activity)    Calls, demos, meetings — what drove pipeline
```

Weak Level 1 → weak Level 2 → weak Level 3. Problems compound upward.

---

## Pipeline Health Metrics

### Pipeline Coverage Ratio

```
Pipeline Coverage = Total Pipeline Value / Quota for Period

Critical (<2x): Almost certain to miss — immediate pipeline build required
At Risk  (2-3x): Likely to miss — aggressive outbound + partner acceleration
Healthy  (3-4x): On track — maintain current activity
Strong   (4x+):  Well-positioned — qualify more aggressively (not all will close)
```

**By stage coverage (more precise):**
```
Weighted Pipeline = Σ (Deal Value × Close Probability by Stage)
Compare to quota for realistic view
```

### Sales Velocity

```
Sales Velocity = (# Opportunities × Average Deal Size × Win Rate) / Sales Cycle (days)
Unit: $/day of pipeline converted to revenue

Increase velocity by:
- # Opportunities: more pipeline volume
- Avg Deal Size: move upmarket or expand scope
- Win Rate: better qualification, stronger positioning, competitive win rate
- Sales Cycle: earlier decision-makers, clearer value prop, reduce approval steps
```

### Deal Aging

Flag deals by days in stage vs benchmark:

| Stage | Expected Days | Yellow Flag | Red Flag |
|-------|--------------|-------------|----------|
| Prospecting | <14 days | 14-30 days | >30 days |
| Qualified | <21 days | 21-45 days | >45 days |
| Demo/Evaluation | <30 days | 30-60 days | >60 days |
| Proposal/Negotiation | <21 days | 21-45 days | >45 days |
| Closed | — | — | — |

### Deal Concentration Risk

```
Concentration Risk = Largest deal / Total pipeline

>30% = Dangerous (business plan depends on one deal)
20-30% = Watch (significant exposure)
<20% = Healthy (diversified pipeline)
```

---

## Forecast Accuracy

### MAPE (Mean Absolute Percentage Error)

```
MAPE = (1/n) × Σ |Actual_t - Forecast_t| / |Actual_t| × 100

Target: <15% is good; <10% is excellent
```

| Rating | MAPE | Interpretation |
|--------|------|---------------|
| Excellent | <10% | Highly reliable forecasting |
| Good | 10-15% | Acceptable for planning |
| Fair | 15-25% | Significant uncertainty — add buffer |
| Poor | >25% | Forecast unreliable — redesign methodology |

### Forecast Bias

```
Bias = Mean(Actual - Forecast)
Positive bias = consistently under-forecasting (too conservative)
Negative bias = consistently over-forecasting (too optimistic, miss targets)
```

Target: bias close to 0 over rolling 6 months.

### Improving Forecast Accuracy

1. **Standardize stage definitions** — every rep must use same criteria to advance deals
2. **Use commit/upside/pipeline buckets** (not just one number)
3. **Track forecast vs actual by rep** — identify systematic biases per rep
4. **Run weekly inspection calls** — remove deals that shouldn't be in forecast
5. **Apply MEDDIC/BANT qualification** — reduce stale unqualified deals

---

## GTM Efficiency Metrics

### Magic Number (Primary GTM Signal)

```
Magic Number = Net New ARR (quarter) / S&M Spend (prior quarter)

Note: Use prior quarter S&M because deals close with lag after spending

>1.0 = Excellent — every $1 of S&M generates $1+ of ARR. Step on gas.
0.75-1.0 = Good — efficient GTM; invest steadily
0.5-0.75 = Watch — optimize conversion before scaling spend
<0.5 = Poor — fix GTM engine before adding more budget
```

**Action matrix:**
- Magic Number <0.5 and declining: stop increasing S&M, diagnose ICP/positioning
- Magic Number >1.0 consistently: increase S&M budget aggressively
- Magic Number volatile quarter-to-quarter: investigate seasonal effects or large deal skew

### LTV:CAC Ratio

```
LTV:CAC = Customer Lifetime Value / Customer Acquisition Cost

>4x = Excellent (high return on acquisition)
3-4x = Healthy (acceptable payback)
2-3x = Watch (marginal unit economics)
<2x = Critical (losing money acquiring customers)
```

### CAC Payback Period

```
CAC Payback (months) = CAC / Monthly Gross Margin per Customer
                     = CAC / (ARPU × Gross Margin %)

<12 months: Excellent (fast capital recovery)
12-18 months: Good
18-24 months: Acceptable
>24 months: Too long — reduce CAC or increase ARPU
```

### Burn Multiple

```
Burn Multiple = Net Cash Burned (quarter) / Net New ARR (quarter)

<1x = Excellent (growing efficiently)
1-1.5x = Good
1.5-2x = Acceptable
>2x = Inefficient (burning too much per dollar of ARR added)
```

### Rule of 40

```
Rule of 40 = Revenue Growth Rate (%) + EBITDA Margin (%)

>40 = Healthy balance of growth and profitability
20-40 = Monitor — acceptable for stage
<20 = Needs improvement

Notes:
- Most relevant at $10M+ ARR
- Pre-$10M: prioritize growth rate over Rule of 40
- Measure with free cash flow margin instead of EBITDA for more accurate picture
```

### Net Dollar Retention (NDR) / Net Revenue Retention (NRR)

```
NDR = (MRR_start + Expansion - Contraction - Churn) / MRR_start × 100

>120% = Excellent (land-and-expand working)
110-120% = Strong
100-110% = Acceptable
<100% = Critical (existing base shrinking — no amount of new logos fixes this)
```

---

## Review Cadences

### Weekly Pipeline Review (30-45 min)

**Agenda:**
1. Pipeline additions this week vs target (pipeline generation rate)
2. Stage movement — deals advancing or stalling?
3. Deals at-risk (aging, executive disengagement, competitive threat)
4. Forecast confidence (commit vs upside vs pipeline breakdown)
5. Actions for next week

**Questions to ask each rep:**
- "What's the next step and date for [top 3 deals]?"
- "What's the risk that [deal] doesn't close this quarter?"
- "What do you need to advance this deal?"

### Monthly Forecast Accuracy Review (60 min)

**Review:**
- MAPE for the month vs rolling 3/6-month average
- Forecast bias: were we systematically over/under?
- Best-case vs worst-case spread (are forecasts too confident?)
- Per-rep analysis: identify systematic biases
- Action: adjust methodology if MAPE >15% for 2+ consecutive months

### Quarterly GTM Efficiency Audit (2 hours)

**Review all GTM metrics:**
1. Magic Number vs prior 4 quarters (trend)
2. LTV:CAC by segment and channel
3. CAC Payback by cohort
4. Pipeline coverage and velocity
5. Win/loss analysis (top 5 wins + top 5 losses — common themes)
6. CAC by channel (paid / organic / referral / outbound / events)

**Output:** One-page GTM health scorecard with recommendation to increase/maintain/reduce S&M by segment/channel.

---

## Pipeline Coverage Calculation Example

```
Current pipeline by stage:
- Prospecting:    $500K × 10% close probability = $50K weighted
- Qualified:      $800K × 20% = $160K weighted
- Demo:           $600K × 35% = $210K weighted
- Proposal:       $400K × 60% = $240K weighted
- Negotiation:    $200K × 80% = $160K weighted
Total pipeline:   $2.5M
Weighted pipeline: $820K

Quarterly quota: $700K

Pipeline Coverage Ratio: $2.5M / $700K = 3.6x (HEALTHY ✅)
Weighted Coverage: $820K / $700K = 1.17x (close to quota — Watch for mid-quarter review)
```

---

## Proactive Flags for RevOps Analysis

| Signal | Flag Message |
|--------|-------------|
| Pipeline coverage <2x | "CRITICAL: Pipeline insufficient to hit quota even with perfect execution. Immediate outbound campaign required." |
| Forecast MAPE >25% | "Forecast methodology unreliable. Recommend implementing commit/upside/pipeline buckets and weekly rep inspection calls." |
| Magic Number <0.5 | "GTM too inefficient to justify more S&M spend. Fix qualification or conversion before adding budget." |
| NDR <100% | "Net revenue shrinking from existing base. Growing new logos cannot compensate for net churn. Fix retention first." |
| Deal concentration >30% | "One deal represents >30% of pipeline. Model assumes it closes — validate urgency and executive engagement." |
| Burn Multiple >3x | "Burning $3+ per $1 of ARR added. Either grow faster or cut burn significantly." |
