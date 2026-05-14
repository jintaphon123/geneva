# Statistics Reference

## Sample Size Calculation

### Required Inputs

| Input | Definition | Typical value |
|---|---|---|
| Baseline rate | Current conversion/activation/retention % | From analytics |
| MDE | Minimum detectable effect — smallest lift worth shipping | 5–20% relative |
| α (alpha) | Significance level — probability of false positive | 0.05 (95% confidence) |
| 1-β (power) | Probability of detecting a true effect | 0.80 (80% power) |

### Quick Reference Table (two-tailed, α=0.05, power=0.80)

| Baseline | 5% rel. MDE | 10% rel. MDE | 20% rel. MDE |
|---|---|---|---|
| 5% | ~120,000/variant | ~31,000/variant | ~8,000/variant |
| 10% | ~57,000/variant | ~14,500/variant | ~3,700/variant |
| 20% | ~24,000/variant | ~6,200/variant | ~1,600/variant |
| 30% | ~14,000/variant | ~3,700/variant | ~960/variant |
| 50% | ~7,400/variant | ~1,900/variant | ~490/variant |

Rule of thumb: Larger baseline → fewer users needed. Smaller MDE → more users needed.

### Formula

```
n = (z_α/2 + z_β)² × [p1(1-p1) + p2(1-p2)] / (p1 - p2)²

Where:
- p1 = baseline rate
- p2 = baseline rate + MDE (absolute)
- z_α/2 = 1.96 (for 95% confidence, two-tailed)
- z_β = 0.84 (for 80% power)
```

### Duration Estimation

```
Test duration (days) = n per variant × 2 / daily eligible visitors
```

If duration > 8 weeks: increase MDE, reduce power to 70%, or find a higher-traffic surface.

---

## Statistical Significance

### p-value Interpretation

| p-value | Interpretation |
|---|---|
| p < 0.01 | Strong evidence against null hypothesis |
| p < 0.05 | Conventional significance threshold — standard for shipping decisions |
| 0.05 ≤ p < 0.10 | Marginal — often not actionable |
| p ≥ 0.10 | Insufficient evidence — null result |

**What p-value means:** Probability of seeing this result (or more extreme) if the null hypothesis were true.
**What p-value does NOT mean:** Probability that your hypothesis is correct.

### Two-tailed vs One-tailed

- **Two-tailed (default):** Tests if effect is either positive OR negative. Use this.
- **One-tailed:** Only tests if effect is in one direction. Higher power but invalidated if effect goes the other way. Only use if you have a very strong prior that effect can only go one direction.

### Confidence Interval

```
Effect estimate ± margin of error

Example: "Conversion rate increased by 2.3% (95% CI: 0.8% to 3.8%)"
```

A CI that doesn't cross zero = statistically significant. The width shows precision — wide CI = high uncertainty.

---

## Effect Size

### Why Effect Size Matters

A test with 1,000,000 users can be statistically significant for a 0.001% lift. That's real but not worth shipping.
Always check: is the effect size ≥ your pre-specified MDE?

### Effect Size Metrics

**Relative lift:** (treatment - control) / control × 100
Example: control = 20%, treatment = 22% → relative lift = 10%

**Absolute lift:** treatment - control
Example: control = 20%, treatment = 22% → absolute lift = 2 percentage points

**Practical significance rule:** Ship if absolute lift is economically meaningful given the cost to build and maintain the change.

### Cohen's d (for continuous metrics like revenue, time)

| d | Interpretation |
|---|---|
| 0.2 | Small effect |
| 0.5 | Medium effect |
| 0.8 | Large effect |

---

## Sample Ratio Mismatch (SRM)

If your 50/50 split results in unequal group sizes, the test is invalid.

### Detection

Run a chi-squared test on the sample counts:
```
Expected: 50% control / 50% treatment (or your intended split)
Observed: actual counts

χ² = Σ (observed - expected)² / expected

If χ²-test p < 0.05 → SRM detected → investigate before analyzing results
```

### Common SRM Causes

- Filtering users after assignment (e.g., only counting users who complete an action)
- Cache or CDN serving old variant to some users
- Botbot or crawler traffic polluting one variant
- Assignment bug in feature flag logic
- Early stopping that cut off one variant

---

## Multiple Testing Correction

If you run many experiments simultaneously or check multiple metrics, false positive rate increases.

### Bonferroni Correction (conservative)

Use corrected α = 0.05 / number of tests.
Example: 5 simultaneous tests → use α = 0.01 per test instead of 0.05.

### When to Apply

- You have 1 pre-specified primary metric → no correction needed
- You're testing multiple variants simultaneously → apply correction
- You're doing data mining post-hoc → results are exploratory only, require replication

---

## Quick Decision Tree

```
Run experiment
    │
    ▼
Sample size reached?
    │
    ├── No → keep running (do not peek at significance)
    │
    └── Yes → check p-value
                │
                ├── p < 0.05 AND effect ≥ MDE AND no guardrail violation
                │       → SHIP ✅
                │
                ├── p < 0.05 AND effect < MDE
                │       → NULL (significant but not business-meaningful) ❌
                │
                ├── p ≥ 0.05
                │       → NULL RESULT ❌ — don't ship
                │
                └── Guardrail violated
                        → ROLLBACK + INVESTIGATE 🚨
```
