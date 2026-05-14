# Financial Forecasting & Budget Variance Analysis

## Driver-Based Revenue Forecasting

Break revenue into measurable drivers that can be independently forecast:

```
Revenue = Volume × Price × Mix

Or for SaaS:
Revenue = Active Customers × ARPU

Or for e-commerce:
Revenue = Sessions × Conversion Rate × Average Order Value

Or for marketplace:
Revenue = GMV × Take Rate
```

**Why driver-based:** Each driver has different assumptions, owners, and risk profiles. Aggregating to a single revenue number hides where uncertainty lives.

### Building the Forecast

**Step 1 — Identify the 3-5 key revenue drivers**
Interview the business team: "What would have to be true for revenue to be X?"

**Step 2 — Estimate each driver independently**
Use historical trends, market research, and management input. Disagree with hockey-stick assumptions.

**Step 3 — Assemble into scenarios**

| Driver | Bear | Base | Bull |
|--------|------|------|------|
| New customers/month | 50 | 80 | 120 |
| Churn rate | 4% | 2.5% | 1.5% |
| ARPU | $45 | $55 | $65 |
| **Implied ARR (12M)** | **$X** | **$X** | **$X** |

**Step 4 — State assumptions explicitly**
Every number should have a corresponding assumption. Unverified assumptions get a 🔴 flag.

---

## Scenario Modeling

**Base Case:** Most likely outcome given current trajectory. Not optimistic, not pessimistic.

**Bull Case:** Requires 2-3 things to go right simultaneously. Not the max possible.

**Bear Case:** Assumes headwinds materialize. Tests survivability (cash runway, covenant compliance).

### Scenario Structure

```
## Revenue Scenarios — FY[Year]

| | Bear | Base | Bull | Probability |
|---|---|---|---|---|
| Revenue | $X | $Y | $Z | 20% / 60% / 20% |
| EBITDA | | | | |
| FCF | | | | |

**Bear assumptions:**
- [Key assumption 1]
- [Key assumption 2]

**Base assumptions:**
- [Standard trajectory continues]

**Bull assumptions:**
- [Upside catalyst 1]
- [Upside catalyst 2]

**Expected Value (probability-weighted):**
E[Revenue] = 0.20 × $X + 0.60 × $Y + 0.20 × $Z = $[EV]
```

---

## Rolling 13-Week Cash Flow

Used for near-term liquidity management and burn rate tracking.

### Structure

```
Week | Opening Cash | Operating Inflows | Operating Outflows | Net Change | Closing Cash
  1  |    $X        |       $Y          |        $Z          |     ±$     |     $X'
  2  |    $X'       |       ...         |        ...         |     ±$     |     ...
 ...
 13  |    ...       |       ...         |        ...         |     ±$     |    $END
```

**Operating Inflows (collect separately):**
- Customer receipts (from accounts receivable schedule)
- Subscription renewal payments
- One-time project payments

**Operating Outflows (by category):**
- Payroll (exact dates — biweekly/monthly)
- Rent/facilities
- Vendor payments (from accounts payable schedule)
- Software/SaaS subscriptions
- Tax payments (quarterly estimated taxes)
- Loan/lease payments

**Critical outputs:**
- Minimum cash balance week (covenant floor check)
- Weeks with negative net change (cash shortfall warning)
- End-of-period cash vs target minimum

---

## Budget Variance Analysis

### Process

1. **Collect actuals** for the period (month, quarter, YTD)
2. **Align to budget format** (same line items, same period)
3. **Calculate variances** for each line:
   ```
   Variance ($) = Actual - Budget
   Variance (%) = (Actual - Budget) / |Budget| × 100
   F/U = Favorable if Variance > 0 for revenue / Variance < 0 for expense
   ```
4. **Apply materiality filter:** Flag only variances where BOTH:
   - Absolute variance > $50K (or user-defined threshold), AND/OR
   - Percentage variance > 10%
5. **Root cause analysis** for each flagged item

### Variance Report Template

```
## Budget Variance Report — [Period]

| Line Item | Actual | Budget | Prior Year | Var ($) | Var (%) | F/U | Flag |
|-----------|--------|--------|------------|---------|---------|-----|------|
| Revenue | | | | | | | |
| → Product A | | | | | | | |
| → Product B | | | | | | | |
| COGS | | | | | | | |
| Gross Profit | | | | | | | |
| Sales & Marketing | | | | | | | |
| G&A | | | | | | | |
| R&D | | | | | | | |
| EBITDA | | | | | | | |

**Flagged Variances (materiality threshold: >10% or >$50K):**

1. [Line Item] — [Actual] vs [Budget], [Var %] U/F
   Root Cause: [Specific explanation]
   Action: [Who does what by when]

2. [Line Item] — ...
```

### Variance Classification

| Type | What it means | Owner |
|------|--------------|-------|
| **Volume variance** | More/fewer units sold than planned | Sales / Operations |
| **Price variance** | Higher/lower price per unit than planned | Pricing / Sales |
| **Mix variance** | Different product/channel mix than assumed | Product / Sales |
| **Efficiency variance** | More/less resource use per unit | Operations |
| **Timing variance** | Revenue/expense in different period than planned | Finance / Accounting |
| **One-time item** | Not in budget (deal costs, severance, etc.) | Finance |

---

## Forecast Accuracy Targets

| Metric | Excellent | Good | Fair | Poor |
|--------|-----------|------|------|------|
| Revenue MAPE | <5% | 5-10% | 10-20% | >20% |
| Expense MAPE | <3% | 3-8% | 8-15% | >15% |
| EBITDA accuracy | <5% | 5-10% | 10-20% | >20% |

**MAPE = Mean Absolute Percentage Error:**
```
MAPE = (1/n) × Σ |Actual_t - Forecast_t| / |Actual_t| × 100
```

**Forecast bias (systematic over/under):**
```
Bias = Mean(Actual - Forecast)
Positive bias = consistently under-forecasting
Negative bias = consistently over-forecasting
```

---

## Forecasting Anti-Patterns

| Anti-Pattern | Why It's Wrong | Better Approach |
|---|---|---|
| **Hockey stick** | Revenue flat then shoots up with no driver change | Require specific catalyst that creates inflection |
| **Single-point estimate** | Creates false precision | Always model 3 scenarios |
| **Top-down only** | "Market is $10B, we'll get 1%" | Validate with bottom-up build (customer × ARPU) |
| **Ignoring seasonality** | Averages out peaks and troughs | Apply historical seasonality index per month |
| **Assuming constant margins** | Costs don't scale linearly with revenue | Model fixed vs variable cost separately |
| **Using last year's budget** | Anchors to irrelevant number | Start with clean-sheet driver model |
| **Not stress-testing** | Black swans not considered | Always run bear case at -30% to -50% revenue |

---

## Rolling Forecast vs Annual Budget

| | Annual Budget | Rolling Forecast |
|---|---|---|
| **Updated** | Once/year | Every quarter (or month) |
| **Horizon** | Fixed (Jan-Dec) | Rolling 12-18 months |
| **Purpose** | Target-setting + accountability | Decision-making + resource allocation |
| **Bias** | Political (sandbagging / stretch) | Accuracy-oriented |
| **Best for** | Compensation targets, board commitments | Operational planning, cash management |

**Best practice:** Maintain both. Annual budget for accountability; rolling forecast for reality.
