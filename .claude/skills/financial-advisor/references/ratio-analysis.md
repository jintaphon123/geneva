# Financial Ratio Analysis

## Ratio Categories

### 1. Profitability Ratios

| Ratio | Formula | Healthy Range | Red Flag |
|-------|---------|---------------|----------|
| **Gross Margin** | (Revenue - COGS) / Revenue | >40% (SaaS) / >25% (Manufacturing) | Declining YoY |
| **Operating Margin** | EBIT / Revenue | >15% mature / >0% growth | Negative + shrinking |
| **Net Profit Margin** | Net Income / Revenue | >10% mature | Consistently negative |
| **ROE** | Net Income / Shareholders' Equity | 15–25% | <10% or >35% (unsustainable leverage) |
| **ROA** | Net Income / Total Assets | >5% | <2% |
| **EBITDA Margin** | EBITDA / Revenue | >20% strong | <10% |
| **ROCE** | EBIT / (Total Assets - Current Liabilities) | >15% | <WACC (value-destroying) |

**Gross Margin by sector benchmarks:**
- SaaS: 70-80%
- E-commerce: 30-50%
- Manufacturing: 20-35%
- Professional services: 50-65%
- Retail: 25-40%

---

### 2. Liquidity Ratios

| Ratio | Formula | Healthy Range | Red Flag |
|-------|---------|---------------|----------|
| **Current Ratio** | Current Assets / Current Liabilities | 1.5–3.0x | <1.0 (liquidity crisis) |
| **Quick Ratio** | (Cash + Short-term Investments + Receivables) / Current Liabilities | 1.0–2.0x | <0.75 |
| **Cash Ratio** | Cash & Equivalents / Current Liabilities | 0.5–1.0x | <0.2 |
| **Operating Cash Flow Ratio** | Operating Cash Flow / Current Liabilities | >0.5x | Negative OCF |

**Interpretation:**
- Current ratio 2.0x+ in mature business may indicate poor capital allocation (too much cash/inventory)
- Quick ratio better than current ratio for businesses with slow-moving inventory
- Cash ratio most conservative — use when assessing immediate solvency

---

### 3. Leverage / Solvency Ratios

| Ratio | Formula | Healthy Range | Red Flag |
|-------|---------|---------------|----------|
| **Debt-to-Equity** | Total Debt / Shareholders' Equity | <1.0x (conservative) / 1–2x (moderate) | >3x |
| **Net Debt / EBITDA** | (Total Debt - Cash) / EBITDA | <2x (low risk) / 2-4x (moderate) | >5x |
| **Interest Coverage** | EBIT / Interest Expense | >3x | <1.5x (can't service debt) |
| **Debt-to-Assets** | Total Debt / Total Assets | <0.5 | >0.7 |
| **Equity Multiplier** | Total Assets / Total Equity | 1–3x | >5x without profit |

**Leverage by sector:**
- SaaS (no debt): D/E <0.5x
- Real estate/utilities: D/E 2-4x (normal for asset-heavy)
- Manufacturing: D/E 0.5-1.5x

---

### 4. Efficiency Ratios

| Ratio | Formula | Healthy Range | Interpretation |
|-------|---------|---------------|----------------|
| **Asset Turnover** | Revenue / Total Assets | >0.5x (most sectors) | Higher = assets working harder |
| **Inventory Turnover** | COGS / Average Inventory | >4x (general) | Low = slow-moving inventory |
| **Days Inventory Outstanding (DIO)** | (Inventory / COGS) × 365 | <60 days | >90 = capital locked |
| **Days Sales Outstanding (DSO)** | (Receivables / Revenue) × 365 | <45 days | >90 = collection problem |
| **Days Payable Outstanding (DPO)** | (Payables / COGS) × 365 | 30-60 days | <30 = paying too fast |
| **Cash Conversion Cycle** | DIO + DSO - DPO | Minimize | Negative = business funded by suppliers |

**Cash Conversion Cycle (CCC):**
```
CCC = DIO + DSO - DPO
Target: as low or negative as possible
Amazon: negative CCC (customers pay before suppliers do — float advantage)
```

---

### 5. Valuation Ratios

| Ratio | Formula | Healthy Range | Notes |
|-------|---------|---------------|-------|
| **P/E (Price-to-Earnings)** | Market Cap / Net Income | 15-25x mature / 30-60x growth | Meaningless if negative earnings |
| **EV/EBITDA** | Enterprise Value / EBITDA | 6–12x mature / 15-30x growth | Most universally applicable |
| **EV/Revenue** | Enterprise Value / Revenue | 1-3x mature / 5-15x SaaS growth | Use when EBITDA negative |
| **Price-to-Book** | Market Cap / Book Value of Equity | 1-3x | >5x = premium to assets |
| **Price-to-Sales** | Market Cap / Revenue | 1-5x | Context-dependent |

**EV/EBITDA by sector benchmarks:**
- Technology (SaaS): 15-30x
- Consumer goods: 8-15x
- Manufacturing: 6-10x
- Utilities: 8-12x
- Retail: 5-9x

---

## DuPont Decomposition

Breaks ROE into its three drivers to diagnose the source of performance:

```
ROE = Net Profit Margin × Asset Turnover × Equity Multiplier

ROE = (Net Income / Revenue) × (Revenue / Assets) × (Assets / Equity)

Example:
Company A: ROE = 18% = 6% margin × 1.5x turnover × 2.0x leverage
Company B: ROE = 18% = 12% margin × 3.0x turnover × 0.5x leverage

A relies on leverage; B relies on efficiency — very different risk profiles
```

**Three-part DuPont (standard):**
- Margin → profitability of operations
- Turnover → efficiency of asset use
- Multiplier → degree of financial leverage

**Five-part DuPont (deeper):**
```
ROE = (EBIT/Revenue) × (Revenue/Assets) × (Assets/Equity) × (EBT/EBIT) × (Net Income/EBT)
    = Operating margin × Asset turnover × Leverage × Interest burden × Tax burden
```

---

## Red Flag Checklist

Run before delivering any ratio analysis:

- [ ] ROE > 35% without asset-light model → likely unsustainable leverage
- [ ] Current ratio < 1.0 → immediate liquidity risk
- [ ] Net Debt/EBITDA > 5x → debt service strain
- [ ] Interest coverage < 1.5x → cannot service debt from operations
- [ ] DSO > 90 days → collection issues, receivables quality concern
- [ ] Operating margin declining 3+ years in a row → structural problem
- [ ] CCC worsening (increasing) year over year → working capital inefficiency
- [ ] ROCE < WACC → company destroying value, not creating it

---

## Industry Benchmark Quick Reference

| Metric | SaaS | Manufacturing | Retail | Services |
|--------|------|---------------|--------|----------|
| Gross Margin | 70-80% | 25-40% | 25-45% | 50-65% |
| Operating Margin | 15-25% | 8-15% | 3-8% | 15-25% |
| ROE | 15-30% | 10-20% | 12-22% | 15-25% |
| Current Ratio | 2-4x | 1.5-2.5x | 1.2-2.0x | 1.5-3.0x |
| Asset Turnover | 0.3-0.8x | 0.8-1.5x | 1.5-3.0x | 0.5-1.2x |
| EV/EBITDA | 15-30x | 6-10x | 5-9x | 8-15x |
