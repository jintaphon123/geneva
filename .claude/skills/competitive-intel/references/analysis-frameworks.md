# Advanced Competitive Analysis Frameworks

Use when the standard 12-dimension scoring + SWOT isn't enough — for market-level questions, strategic positioning, and whitespace identification.

---

## Porter's Five Forces

Assess competitive intensity of the market — use before entering a new segment or when pricing is under pressure.

### The Five Forces

**1. Threat of New Entrants**
- Barriers to entry: capital requirements, regulation, network effects, brand loyalty
- Speed of competitor replication
- Strength: Low barriers = high threat → compress margins over time

**2. Bargaining Power of Suppliers**
- Dependency on core infrastructure vendors (cloud, APIs, data sources)
- Concentration of key technical providers
- Strength: Few suppliers = they can raise prices or cut access

**3. Bargaining Power of Buyers**
- Customer switching costs and procurement complexity
- Buyer concentration (one customer = 30%+ of revenue → high risk)
- Strength: Many alternatives + low switching cost = buyers set the price

**4. Threat of Substitutes**
- Adjacent alternatives solving the same job-to-be-done
- DIY and internal build options
- Strength: Strong substitutes cap what you can charge

**5. Rivalry Among Existing Competitors**
- Number and similarity of competitors
- Market growth rate (shrinking market = zero-sum competition)
- Price competition and differentiation pressure

### Five Forces Scoring Table

| Force | Current Pressure | Evidence | Strategic Response |
|---|---|---|---|
| New Entrants | Low / Med / High | | |
| Supplier Power | Low / Med / High | | |
| Buyer Power | Low / Med / High | | |
| Substitutes | Low / Med / High | | |
| Rivalry | Low / Med / High | | |
| **Overall Industry Attractiveness** | **Score 1–10** | | |

### Interpretation
- 8–10: Very attractive — high margins, sustainable position
- 5–7: Competitive — need differentiation to stay profitable
- <5: Difficult — structural pressure, rethink or niche down

---

## Blue Ocean Strategy Canvas

Use when deciding what to build, drop, or invent — especially for positioning against incumbent competitors.

### ERRC Grid (Eliminate–Reduce–Raise–Create)

| Action | Description | Your Decision |
|---|---|---|
| **Eliminate** | Remove table-stakes features not valued by target users | |
| **Reduce** | Dial back costly features with weak adoption | |
| **Raise** | Double down on differentiators tied to target job-to-be-done | |
| **Create** | Invent new value dimensions competitors ignore entirely | |

### Strategy Canvas Steps

1. List the key competing factors in your market (price, ease of use, integrations, support, etc.)
2. Plot your value curve vs. each competitor's value curve (1–5 per factor)
3. Identify where curves overlap → commodity zone
4. Apply ERRC: diverge from the commodity zone deliberately
5. Test: can you describe your product in one sentence that no competitor could claim?

### Strategy Canvas Checklist

- [ ] Value curves plotted for all tier-1 competitors
- [ ] Target segment is explicit (not "everyone")
- [ ] At least one factor is Eliminated (cost reduction)
- [ ] At least one factor is Created (new differentiation)
- [ ] Every choice ties to a measurable outcome (not vibes)

---

## Feature Comparison Matrix (Weighted)

For structured scoring that weights what buyers actually care about.

| Dimension | Weight | Your Product | Competitor A | Competitor B | Notes |
|---|---:|---:|---:|---:|---|
| Core workflow coverage | 25% | | | | |
| Ease of implementation | 15% | | | | |
| Performance / reliability | 15% | | | | |
| Integrations / ecosystem | 15% | | | | |
| Security / compliance | 15% | | | | |
| Pricing / TCO | 15% | | | | |
| **Weighted Total** | 100% | | | | |

Scoring scale: 1–5 (weak to strong). Multiply each score × weight, sum for final score.

---

## When to Use Which Framework

| Question | Framework |
|---|---|
| "Should we enter this market?" | Porter's Five Forces |
| "How do we differentiate from incumbents?" | Blue Ocean Strategy Canvas |
| "How do we score vs. competitors on what buyers care about?" | Feature Comparison Matrix (Weighted) |
| "What are each competitor's real strengths and gaps?" | SWOT (in core SKILL.md) |
| "How are competitors positioned relative to each other?" | Positioning Map (in core SKILL.md) |
