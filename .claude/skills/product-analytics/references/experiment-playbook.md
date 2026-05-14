# Experiment Playbook

## Experiment Brief Template

Complete before starting any A/B test.

```markdown
# Experiment: [Name]

**Status:** Draft | Running | Concluded
**Owner:** [Name]
**Start date:** YYYY-MM-DD
**Expected end date:** YYYY-MM-DD (based on sample size)

---

## Hypothesis

If we [specific intervention],
then [primary metric] will [increase/decrease] by [target magnitude],
because [behavioral mechanism — why users will respond this way].

## Metrics

**Primary metric:** [one metric — pre-commit, do not change mid-test]
**Guardrail metrics:** [metrics that must NOT get worse]
**Secondary metrics:** [supporting context, not decision drivers]

## Sample Size

- Baseline rate: [current conversion/retention/activation %]
- MDE (minimum detectable effect): [smallest lift worth shipping]
- Required sample per variant: [calculated]
- Expected duration: [days based on traffic]

## Variants

- Control: [exact current state]
- Treatment: [exact change being tested]

## Stopping Rules

- Stop when: sample size reached AND p < 0.05 (two-tailed)
- Early stop if: guardrail metric drops > [X%] OR critical bug detected
- Do NOT stop because: test is trending negative, business wants to ship early

## Decision Rules (pre-committed)

| Result | Decision |
|---|---|
| p < 0.05, effect > MDE | Ship the treatment |
| p < 0.05, effect < MDE | Don't ship — not business-significant |
| p ≥ 0.05 | Null result — don't ship, investigate |
| Guardrail violated | Roll back immediately, investigate |
```

---

## Hypothesis Writing

### Format

```
If we [intervention — specific and measurable],
then [primary metric] will [direction + magnitude],
because [behavioral mechanism].
```

### Quality Checklist

- [ ] Intervention is specific enough to build (not "improve onboarding")
- [ ] Metric is pre-specified and measurable
- [ ] Expected magnitude is explicit (not "will increase" but "will increase by ~10%")
- [ ] Mechanism is a real behavioral principle (not "users will like it")
- [ ] Primary metric aligns to a business outcome

### Mechanism Examples (behavioral principles)

| Principle | Applied to |
|---|---|
| Progress bias | Users who see progress are more likely to complete multi-step flows |
| Social proof | Users who see "X others did this" are more likely to do it too |
| Default effect | Users rarely change defaults — set defaults strategically |
| Commitment escalation | Small early commitments increase completion of larger requests |
| Friction reduction | Removing a step increases conversion more than adding persuasion |
| Loss aversion | "Don't miss out" framing outperforms "You'll gain X" |

---

## ICE Scoring for Experiment Prioritization

ICE Score = (Impact × Confidence × Ease) / 10

| Factor | 1 | 5 | 10 |
|---|---|---|---|
| **Impact** | Tiny metric move | Moderate lift (~5%) | Major outcome change (>15%) |
| **Confidence** | Pure hypothesis, no data | Some qualitative evidence | Strong quantitative signal |
| **Ease** | 2+ weeks eng, risky change | 1 week, some risk | < 1 day, low risk |

Run experiments in ICE order — highest score first.

**Tie-breaking:** if ICE scores are equal, prefer the experiment that provides more learning even on a null result.

---

## Common Pitfalls

### 1. Underpowered Tests

**Problem:** Sample too small → false negatives (you miss a real effect)
**Prevention:** Calculate required sample size BEFORE launching. Never start a test you know can't reach significance.
**Rule:** If getting to required sample size takes > 8 weeks, reconsider the metric or MDE.

### 2. Too Many Simultaneous Changes

**Problem:** Can't attribute effect to any single change
**Prevention:** One change per variant. If you need to test multiple things, run sequential tests or use a factorial design deliberately.

### 3. Mid-Test Implementation Changes

**Problem:** Invalidates the test — your control and treatment changed mid-flight
**Prevention:** Code freeze on tested surfaces during the experiment. If a critical bug fix is needed, stop the test first.

### 4. Stopping Early on Positive Spike

**Problem:** Early significance is often noise — regression to mean kills the lift
**Prevention:** Pre-commit to minimum test duration (usually 1–2 full business cycles). Don't check p-values daily.

### 5. Sample Ratio Mismatch (SRM)

**Problem:** If 50/50 split results in, e.g., 48% vs 52% assignment → bias in assignment
**Detection:** Run chi-squared test on sample sizes. If p < 0.05, the split is broken.
**Fix:** Investigate assignment bug before drawing any conclusions from results.

### 6. p-value Without Effect Size

**Problem:** p < 0.05 only means "this effect is probably real" — not that it's worth shipping
**Prevention:** Always report effect size and confidence interval alongside p-value.
**Decision rule:** Only ship if effect size is ≥ MDE AND p < 0.05.

---

## Interpreting Results

### Significant Positive Result
p < 0.05 AND effect ≥ MDE AND no guardrail violations → ship.

Before shipping: check for novelty effect (will it hold at D30?), segment the result (does it work for all users or just a subset?).

### Significant Negative Result
p < 0.05 AND effect is negative → don't ship. Investigate the mechanism — why did it hurt?

### Null Result (p ≥ 0.05)
No evidence the change matters. Do not ship (absence of evidence ≠ evidence of absence). Consider: was the MDE realistic? Was there enough traffic? Try a different intervention.

### Guardrail Violated
Immediate rollback. Investigate before any further experiments on that surface.

---

## Experiment Registry Template

Track all experiments in a single log.

| ID | Name | Hypothesis | Primary Metric | Status | Result | Decision |
|---|---|---|---|---|---|---|
| EXP-001 | [Name] | [Summary] | [Metric] | Running | — | — |
| EXP-002 | [Name] | [Summary] | [Metric] | Concluded | +8%, p=0.03 | Shipped |
