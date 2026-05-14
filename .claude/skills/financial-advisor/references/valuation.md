# Company Valuation — DCF, Comparables, Precedent Transactions

## Discounted Cash Flow (DCF)

### Step 1: Project Free Cash Flows (5 years)

```
Free Cash Flow (FCF) = EBITDA - Taxes - ΔWorking Capital - Capex

Or from EBIT:
FCF = EBIT × (1 - Tax Rate) + D&A - ΔWorking Capital - Capex
```

**Input requirements:**
- Revenue growth rate by year
- EBITDA margin by year (or gross margin + OpEx structure)
- Effective tax rate
- D&A as % of revenue (or absolute)
- Capex as % of revenue
- Net working capital change (typically 5-10% of revenue growth)

**Projection table template:**
| | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 |
|---|---|---|---|---|---|
| Revenue | | | | | |
| EBITDA | | | | | |
| EBIT (after D&A) | | | | | |
| Taxes | | | | | |
| NOPAT | | | | | |
| + D&A | | | | | |
| - ΔWorking Capital | | | | | |
| - Capex | | | | | |
| **Free Cash Flow** | | | | | |

---

### Step 2: Calculate WACC

```
WACC = (E/V × Re) + (D/V × Rd × (1 - T))

Where:
  E = Market value of equity
  D = Market value of debt
  V = E + D (total capital)
  Re = Cost of equity (from CAPM)
  Rd = Cost of debt (pre-tax)
  T = Effective tax rate

CAPM: Re = Rf + β × (Rm - Rf)
  Rf = Risk-free rate (use 10-year government bond yield)
  β = Equity beta (use comparable company betas, un-lever then re-lever)
  Rm - Rf = Equity risk premium (typically 5-7% for developed markets)
```

**Typical WACC ranges:**
- Large-cap mature company: 7-10%
- Mid-cap growth company: 10-14%
- Early-stage startup: 15-25%+
- High-risk/emerging market: add 3-5% country risk premium

**Un-levering / re-levering beta:**
```
β_unlevered = β_levered / (1 + (1 - T) × D/E)
β_relevered = β_unlevered × (1 + (1 - T) × D/E_target)
```

---

### Step 3: Terminal Value

Calculate using BOTH methods and take a weighted average (50/50 or note which is more appropriate):

**Method A — Gordon Growth Model (Perpetuity Growth):**
```
Terminal Value = FCF_Year5 × (1 + g) / (WACC - g)

Where g = long-term growth rate (typically GDP growth rate, 2-3%)
g must be < WACC or formula breaks
```

**Method B — Exit Multiple:**
```
Terminal Value = EBITDA_Year5 × Exit Multiple

Use current EV/EBITDA range from comparable companies
Apply a slight discount to current trading multiples (assume some multiple compression)
```

---

### Step 4: Enterprise Value and Equity Value

```
Enterprise Value = PV(FCFs Years 1-5) + PV(Terminal Value)

PV(FCF_t) = FCF_t / (1 + WACC)^t

Equity Value = Enterprise Value - Net Debt
Net Debt = Total Debt - Cash & Equivalents

Implied Share Price = Equity Value / Diluted Shares Outstanding
```

---

### Step 5: Sensitivity Analysis

Build a 2-dimensional sensitivity table (WACC × Terminal Growth Rate):

```
          Terminal Growth Rate
WACC      1.5%   2.0%   2.5%   3.0%   3.5%
 8.0%     [EV]   [EV]   [EV]   [EV]   [EV]
 9.0%     [EV]   [EV]   [EV]   [EV]   [EV]
10.0%     [EV]   [EV]   [EV]   [EV]   [EV]
11.0%     [EV]   [EV]   [EV]   [EV]   [EV]
12.0%     [EV]   [EV]   [EV]   [EV]   [EV]
```

Or WACC × Exit Multiple:
```
           Exit Multiple
WACC      8x    10x    12x    14x    16x
```

State the valuation range implied by the ±1σ range of assumptions.

---

## Comparable Company Analysis (Trading Comps)

### Process

1. Select 5-10 publicly traded peers (similar size, geography, business model, growth profile)
2. Pull LTM (last twelve months) financials for each
3. Calculate EV multiples for each peer
4. Apply median or 25th-75th percentile range to subject company

### Key Multiples

| Multiple | Formula | Use when |
|----------|---------|----------|
| EV/Revenue | EV / LTM Revenue | Early stage, negative EBITDA, SaaS |
| EV/EBITDA | EV / LTM EBITDA | Profitable mature companies |
| EV/EBIT | EV / LTM EBIT | Capex-intensive businesses |
| P/E | Share Price / EPS | When capital structure is stable |
| EV/Gross Profit | EV / Gross Profit | High-growth SaaS with different margin profiles |

### Comp Table Template

| Company | EV ($M) | Revenue | EBITDA | EV/Rev | EV/EBITDA | Growth |
|---------|---------|---------|--------|--------|-----------|--------|
| Peer A | | | | | | |
| Peer B | | | | | | |
| **Median** | | | | | | |
| **Subject Co** | | | | | | |

**Implied EV from comps:**
```
Implied EV = Subject EBITDA × Median EV/EBITDA
Implied Equity Value = Implied EV - Net Debt
```

### Adjustments to Apply
- Size premium/discount: smaller company → discount 10-20%
- Growth premium: faster growth than peers → premium on multiples
- Profitability discount: lower margins than peers → discount
- Control premium (for acquisitions): add 25-35% vs public market multiples

---

## Precedent Transactions

Used for M&A valuation — reflects prices paid for control of similar companies.

**Process:**
1. Find acquisitions of comparable companies in last 3-5 years
2. Calculate transaction multiples (EV/Revenue, EV/EBITDA at time of deal)
3. Apply to subject company — generally higher than trading comps due to control premium

**Control premium:** Typically 25-35% above pre-announcement share price.

**Transaction comps table:**
| Target | Acquirer | Date | Deal Size | EV/Rev | EV/EBITDA | Premium |
|--------|---------|------|-----------|--------|-----------|---------|

---

## Valuation Synthesis

State a range, never a single number. Present results across three methods:

```
## Valuation Summary — [Company Name]

| Method | Implied EV | Implied Equity Value | $/Share |
|--------|-----------|---------------------|---------|
| DCF (base case) | $X-YM | $X-YM | $X-Y |
| Trading comps (median) | $XM | $XM | $X |
| Transaction comps | $XM | $XM | $X |

**Valuation Range:** $X – $Y per share / $X – $Y enterprise value

**Most weight on:** [DCF / Trading comps / Transaction comps] because [reason]

**Key value drivers:**
- [Driver 1 — sensitivity]
- [Driver 2 — sensitivity]

**Key risks to valuation:**
- [Risk — impact direction]
```

---

## Common DCF Mistakes to Flag

- Terminal value > 80% of total EV → model is too sensitive to TV assumptions
- Growth rate in terminal value > WACC → math error (infinite value)
- Using optimistic management projections without downside check
- Ignoring stock-based compensation in FCF (should be deducted as a cash cost)
- Not adjusting for off-balance sheet items (operating leases, pension obligations)
- Using book value of debt instead of market value for WACC
