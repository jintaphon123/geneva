---
name: financial-advisor
argument-hint: "[ratio analysis / DCF / forecast / SaaS metrics / investment decision]"
description: >
  Financial analysis and decision support. Auto-invoke when user asks about:
  financial ratios, ROE, ROA, profitability, liquidity, leverage, DCF, WACC,
  company valuation, terminal value, comparable companies, budget variance,
  revenue forecast, rolling forecast, scenario modeling, ARR, MRR, churn,
  LTV, CAC, NRR, Quick Ratio, SaaS metrics, unit economics, SaaS health,
  ROI, NPV, IRR, payback period, build vs buy, hire vs automate, capital
  allocation, investment decision.
---

# Financial Advisor

## Mode Detection

Detect the user's intent and load the matching mode:

| Mode | Trigger Keywords | Load |
|------|-----------------|------|
| **Ratio** | financial ratio, ROE, ROA, profitability, liquidity, leverage, current ratio, debt-to-equity, asset turnover, EV/EBITDA, P/E | references/ratio-analysis.md |
| **Valuation** | DCF, WACC, company valuation, terminal value, comparable companies, enterprise value, equity value, precedent transactions | references/valuation.md |
| **Forecast** | revenue forecast, budget variance, rolling forecast, scenario modeling, cash flow forecast, driver-based | references/forecasting.md |
| **SaaS Metrics** | ARR, MRR, churn, LTV, CAC, NRR, Quick Ratio, SaaS health, unit economics, SaaS metrics, retention | references/saas-metrics.md |
| **Investment** | ROI, NPV, IRR, payback, build vs buy, lease vs buy, hire vs automate, capital allocation, investment decision | references/investment-decisions.md |

If context matches multiple modes, ask: "Are you looking at [Mode A] or [Mode B]?"

---

## Ratio Mode

**Objective:** Analyze financial ratios to assess company health and benchmark performance.

**Process:**
1. Identify which ratio category applies (profitability / liquidity / leverage / efficiency / valuation)
2. Request the relevant financial statement figures if not provided
3. Calculate ratios using formulas in `references/ratio-analysis.md`
4. Compare against industry benchmarks from the same file
5. Flag ratios outside healthy ranges as red flags
6. Apply DuPont decomposition when ROE is the focus

**Output format:**
```
## Ratio Analysis — [Company Name]

| Ratio | Value | Benchmark | Status |
|-------|-------|-----------|--------|
| ROE | X% | 15-25% | 🟢/🟡/🔴 |

**DuPont Decomposition** (if ROE analyzed):
ROE = [Profit Margin]% × [Asset Turnover]x × [Leverage]x

**Key Findings:**
- [Finding with specific ratio + implication]

**Red Flags:**
- [Ratio outside benchmark + what it signals]
```

---

## Valuation Mode

**Objective:** Value a company using DCF, comparable companies, or precedent transactions.

**Process:**
1. Ask for: revenue projections (5 years), EBITDA margins, capex, D&A, net working capital change, debt, cash, shares outstanding
2. Build DCF using WACC from CAPM (load `references/valuation.md` for formulas)
3. Calculate terminal value using both Gordon Growth Model AND exit multiple — take average
4. Build sensitivity table (WACC × terminal growth rate)
5. Cross-check with comparable company analysis (EV/Revenue, EV/EBITDA multiples)
6. State implied valuation range, not a single point

**Output format:**
```
## Valuation Analysis — [Company Name]

**DCF Summary**
- Enterprise Value (DCF): $[X]M
- WACC: [X]%  |  Terminal Growth Rate: [X]%

**Sensitivity Table** (EV in $M)
[WACC rows × Terminal Growth columns]

**Comparable Companies**
| Company | EV/Revenue | EV/EBITDA |
[table]

**Implied Valuation Range:** $[X]M – $[Y]M

**Key Assumptions & Risks:**
- [Critical assumption + sensitivity]
```

---

## Forecast Mode

**Objective:** Build revenue forecasts, analyze budget variances, or model scenarios.

**Sub-tasks:**

**Budget Variance Analysis:**
- Request: actual vs budget vs prior year figures
- Apply materiality filter: flag variances >10% OR >$50K (whichever applies first)
- Classify as favorable (F) or unfavorable (U)
- Provide root cause hypothesis for each flagged item

**Driver-Based Forecast:**
- Break revenue into: Volume × Price × Mix
- Model base / bull / bear scenarios
- Rolling 13-week cash flow if requested
- State accuracy target: ±5% revenue, ±3% expenses

**Output format:**
```
## Forecast / Variance Report

**Budget Variance Summary**
| Line Item | Actual | Budget | Variance | % Var | F/U | Flag |
[table — only materially significant rows]

**Revenue Forecast — Base/Bull/Bear**
| Scenario | Q1 | Q2 | Q3 | Q4 | FY |
[table]

**Key Drivers:**
- Volume: [assumption]
- Price: [assumption]
- Mix: [assumption]

**Risks to Forecast:**
- [Specific risk + impact direction]
```

---

## SaaS Metrics Mode

**Objective:** Calculate SaaS unit economics, score business health, identify priority issues.

**Process:**
1. Request: MRR (new/expansion/churned/contraction), CAC (S&M spend + new customers), LTV inputs (ARPU + churn rate)
2. Calculate all metrics using formulas in `references/saas-metrics.md`
3. Compare against segment benchmarks (Enterprise / Mid-Market / SMB / PLG)
4. Score overall health: HEALTHY / WATCH / CRITICAL
5. Output max 3 priority issues (ranked by impact)
6. State 90-day focus metric

**Proactive triggers — flag immediately if detected:**
- NDR < 100% → net revenue churn (existential signal)
- CAC Payback > 24 months → unsustainable acquisition
- LTV:CAC < 2x → unit economics broken
- Quick Ratio < 1.0 → contracting faster than growing

**Output format:**
```
## SaaS Health Report — [Company Name / Period]

| Metric | Value | Benchmark ([Segment]) | Status |
|--------|-------|----------------------|--------|
| MRR | $X | — | — |
| MRR Growth | X% | 15-20% (SMB) | 🟢/🟡/🔴 |
[all metrics]

**Overall Health: HEALTHY / WATCH / CRITICAL**

**Priority Issues (max 3):**
1. [Issue — specific metric + root cause + fix]

**90-Day Focus Metric:** [metric + target]
```

---

## Investment Mode

**Objective:** Evaluate whether a specific investment, purchase, or hire decision makes financial sense.

**Process:**
1. Gather: investment amount, expected cash flows (by year), useful life, discount rate preference (or use industry default)
2. Calculate ROI, Payback, NPV, IRR using formulas in `references/investment-decisions.md`
3. Score against 6-dimension rubric (ROI / Payback / Strategic fit / Risk / Reversibility / Cash flow impact)
4. Apply relevant decision framework (Build vs Buy / Lease vs Buy / Hire vs Automate)
5. Model upside and downside scenarios
6. State RECOMMENDATION clearly

**Proactive triggers — flag before proceeding:**
- Payback period > useful life → investment never pays back
- Revenue projections show hockey stick without justification → run downside at 50%
- Single customer dependency → concentration risk
- Sunk cost reasoning detected → redirect to marginal analysis
- Debt-financed investment without interest cost factored in → recalculate

**Output format:**
```
## Investment Decision — [Investment Name]

**RECOMMENDATION: Proceed / Proceed with conditions / Do Not Proceed**

**THE NUMBERS**
| Metric | Value | Threshold | Pass? |
|--------|-------|-----------|-------|
| ROI | X% | >20% | ✅/❌ |
| Payback | X months | <36 months | ✅/❌ |
| NPV | $X | >0 | ✅/❌ |
| IRR | X% | >[hurdle rate]% | ✅/❌ |

**Investment Score:** [X]/30 → [Don't do it / Needs analysis / Strong]

**KEY ASSUMPTIONS**
- [Assumption] 🟢 High confidence / 🟡 Medium / 🔴 Low

**UPSIDE CASE:** $[X] NPV — [what has to be true]
**DOWNSIDE CASE:** $[X] NPV — [what breaks]

**RISKS:**
- [Specific risk + mitigation]

**NEXT STEP:** [Single concrete action]
```

---

## References

- `references/ratio-analysis.md` — 50+ ratio formulas, DuPont, industry benchmarks
- `references/valuation.md` — DCF, WACC, terminal value, comparable companies
- `references/forecasting.md` — Driver-based forecasting, budget variance, scenario modeling
- `references/saas-metrics.md` — SaaS formulas, segment benchmarks, health scoring
- `references/investment-decisions.md` — ROI/NPV/IRR, scoring rubric, decision frameworks
