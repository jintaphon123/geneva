# Investment & Capital Allocation Decisions

## Core Financial Metrics

### ROI (Return on Investment)
```
ROI = (Net Gain / Total Investment) × 100
Net Gain = Total Benefits - Total Costs (over investment life)

Use: Quick comparison between options. Ignores time value of money.
Limitation: Different investment periods make ROI misleading.
```

### Payback Period
```
Payback = Total Investment / Annual Net Cash Flow

Discounted Payback = time until cumulative discounted cash flows = investment

Target: <24 months (operational) / <36 months (strategic)
Red flag: Payback period > useful life of the asset
```

### NPV (Net Present Value)
```
NPV = Σ [CF_t / (1 + r)^t] - Initial Investment

Where:
  CF_t = Cash flow in period t
  r = Discount rate (company's cost of capital or hurdle rate)
  t = Time period

Decision rule: Invest if NPV > 0. Higher NPV = better investment.
```

### IRR (Internal Rate of Return)
```
IRR = discount rate at which NPV = 0
Solve numerically (Excel: =IRR(cash_flow_range))

Decision rule: Invest if IRR > hurdle rate
```

### Hurdle Rates by Risk Profile

| Risk Level | Hurdle Rate | Examples |
|-----------|-------------|----------|
| Low (stable, recurring) | 8-12% | Replace existing equipment, cost-saving automation |
| Medium (growth, market-dependent) | 15-20% | New market entry, product expansion |
| High (uncertain, speculative) | 25-35% | New technology, unproven market |
| Very high (startup/venture) | 35%+ | Moonshots, pre-revenue experiments |

---

## 6-Dimension Investment Scoring Rubric

Score each dimension 1-5, total out of 30:

| Dimension | 1 (Poor) | 3 (Moderate) | 5 (Strong) |
|-----------|---------|--------------|------------|
| **ROI** | <10% | 15-25% | >35% |
| **Payback Period** | >36 months | 18-36 months | <12 months |
| **Strategic Fit** | No alignment | Indirect support | Core to strategy |
| **Risk Level** | High + unmitigable | Medium, manageable | Low, well-understood |
| **Reversibility** | Sunk cost trap | Partial recovery | Fully reversible |
| **Cash Flow Impact** | Worsens cash position | Neutral | Improves cash timing |

**Score interpretation:**
- 6-12: Don't do it — financial case doesn't support this investment
- 13-20: Needs more analysis — proceed only with specific conditions met
- 21-30: Strong investment — clear case to proceed

---

## Decision Frameworks

### Build vs Buy vs Partner

**Build** (develop internally):
- Full control over IP and roadmap
- High time-to-market risk
- Ongoing maintenance burden
- Best when: core capability, strong internal expertise, long-term competitive advantage needed

**Buy** (purchase solution):
- Faster deployment
- Vendor dependency risk
- Ongoing licensing/subscription cost
- Best when: vendor does ≥80% of what you need at <50% of build cost

**Partner** (integrate/OEM):
- Shared risk + shared reward
- Less control
- Best when: complementary strengths, neither party can win alone

**Decision matrix:**
```
IF vendor does ≥80% as well AND costs <50% of build → BUY
IF core IP / competitive moat → BUILD
IF market move required quickly → BUY (or partner)
IF long-term strategic asset → BUILD
IF one-time need → BUY or outsource
```

### Lease vs Buy

**Buy** when:
- Asset used >60% of its useful life
- Asset retains/appreciates in value
- Tax depreciation benefit is significant
- Full operational control required

**Lease** when:
- Asset needed <40% of useful life
- Technology obsolescence risk (equipment upgrades frequent)
- Capital preservation is a priority
- Off-balance-sheet treatment preferred

### Hire vs Automate vs Outsource

| Factor | Hire | Automate | Outsource |
|--------|------|----------|-----------|
| **Task type** | Judgment, relationships, creativity | Repetitive, rules-based, high-volume | Variable demand, specialized expertise |
| **Control need** | High | High | Low-Medium |
| **Speed** | Slow (recruiting) | Slow (build) | Fast |
| **Cost structure** | Fixed + high | Fixed (then near-zero marginal) | Variable |
| **IP risk** | None | None | Medium-High |
| **Best for** | Strategic functions | Internal processes | Non-core / peak demand |

---

## Budget Allocation Framework

When evaluating multiple competing investments:

1. **Rank by IRR** (highest to lowest) — pure financial return ordering
2. **Check strategic fit** — override IRR rank if strategic alignment is critical
3. **Fund highest-IRR investments first** until budget exhausted
4. **Exception: Quick wins** — fund any investment with payback <6 months regardless of rank (frees up capital fast)
5. **Exception: Mandatory investments** — regulatory compliance, security, safety are non-optional
6. **Only fund negative-NPV investments** with explicit strategic justification (e.g., loss-leader to enter market)

### Opportunity Cost Rule

Always compare against the best alternative use of capital:
```
True cost of Investment A = Cost of A + Foregone return from not doing B
```

If Investment A has 15% IRR but Investment B has 25% IRR, the opportunity cost of A is -10% IRR.

---

## Output Format

```
## Investment Decision — [Investment Name]

**RECOMMENDATION: Proceed / Proceed with conditions / Do Not Proceed**

THE NUMBERS
| Metric | Value | Threshold | Pass? |
|--------|-------|-----------|-------|
| ROI | X% | >20% | ✅/❌ |
| Payback | X months | <24 months | ✅/❌ |
| NPV (at X% discount rate) | $X | >$0 | ✅/❌ |
| IRR | X% | >[hurdle]% | ✅/❌ |

Investment Score: [X]/30 → [Don't do it / Needs more analysis / Strong investment]

KEY ASSUMPTIONS
- [Assumption] 🟢 High confidence
- [Assumption] 🟡 Medium confidence — key uncertainty
- [Assumption] 🔴 Low confidence — validate before proceeding

UPSIDE CASE: $[X] NPV — requires [what must be true]
DOWNSIDE CASE: $[X] NPV — triggered by [what breaks]

RISKS
- [Specific risk] — Probability: High/Medium/Low — Impact: $X — Mitigation: [action]

NEXT STEP: [Single concrete action with owner and date]
```

---

## Proactive Triggers

Flag these before or during analysis — do not wait to be asked:

| Signal | What to do |
|--------|-----------|
| Payback period > useful life | "This investment never pays back within the asset's life. Recommend Do Not Proceed unless strategic value justifies." |
| Revenue assumptions show hockey stick (flat then sudden jump) | "Run downside at 50% of projected revenue to stress-test the case." |
| Single customer generates >40% of projected returns | "High concentration risk — what happens if this customer churns?" |
| Sunk cost reasoning ("we already spent $X, so we should continue") | "Sunk costs are irrelevant to the forward-looking decision. Analyze marginal benefits vs marginal costs from this point." |
| Debt-financed investment without interest included in cash flows | "Add interest cost to cash flow model. Current NPV is overstated." |
| No downside case modeled | "Model a bear case — what's the NPV if key assumptions are 30-50% worse?" |
