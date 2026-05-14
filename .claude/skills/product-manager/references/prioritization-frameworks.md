# Prioritization Frameworks

## RICE Scoring

### Formula

```
RICE Score = (Reach × Impact × Confidence) / Effort
```

### Factor Definitions

**Reach** — How many users will this affect per quarter?
- Count: unique users (not pageviews, not team members)
- Timeframe: per quarter (standardize across all features)
- Source: analytics data, customer count, survey reach

**Impact** — How much does this move the target metric per user?
| Score | Meaning |
|---|---|
| 3 | Massive impact |
| 2 | Significant impact |
| 1 | Low impact |
| 0.5 | Minimal impact |
| 0.25 | Tiny impact |

**Confidence** — How confident are you in these estimates?
| % | Meaning |
|---|---|
| 100% | High confidence — data-backed |
| 80% | Medium — educated estimate |
| 50% | Low — gut feel only |

Apply confidence to the whole row, not individual factors.

**Effort** — How many person-months to build and ship?
- Include: design, eng, QA, PM coordination
- Don't include: ongoing maintenance

### Thresholds

| Score | Priority |
|---|---|
| 1000+ | High — quick win or major bet |
| 500–999 | Medium — plan for next 2 quarters |
| 100–499 | Low — backlog |
| <100 | Deprioritize — cut unless strategic |

### Portfolio View

| Quadrant | Profile | Action |
|---|---|---|
| Quick Wins | High RICE, Low Effort | Ship now |
| Big Bets | High RICE, High Effort | Sequence carefully, milestone |
| Time Sinks | Low RICE, High Effort | Avoid or defer |
| Fill-ins | Low RICE, Low Effort | Only if capacity remains |

---

## MoSCoW

### Definitions

**Must Have:** Non-negotiable. Without this, the product/release fails or is unusable.
- Legal requirements, core user job, minimum viable experience
- Never negotiate Must without removing something of equal scope

**Should Have:** High value, important but not critical for this release.
- Significantly improves experience, workarounds exist but are painful
- First thing to cut if capacity is tight

**Could Have:** Nice-to-have. Include if time allows.
- Improves satisfaction in small ways
- Second thing to cut

**Won't Have (this time):** Explicitly out of scope for this cycle.
- Documents intent without commitment
- Prevents scope creep via "but you said..."

### Capacity Rule

| Category | Max % of Sprint Capacity |
|---|---|
| Must | 60% |
| Should | 20% |
| Could | 20% |

If Must exceeds 60% → descope Must items or extend timeline. Never compress Should/Could to make it fit.

---

## ICE Scoring

Fast relative scoring when RICE estimates aren't available.

### Formula

```
ICE Score = (Impact × Confidence × Ease) / 10
```

| Factor | 1 | 5 | 10 |
|---|---|---|---|
| Impact | Minimal upside | Moderate benefit | Major outcome move |
| Confidence | Pure gut feel | Some evidence | Strong data |
| Ease | Complex, slow | Moderate build | Quick, low-risk |

Use for: quick backlog ranking, comparing small features, early-stage discovery when reach is unknown.

Don't use for: cross-team dependencies, features with widely different reach, roadmap commitments.

---

## Value vs. Effort Matrix

### Grid

| | **High Effort** | **Low Effort** |
|---|---|---|
| **High Value** | Big Bets — plan carefully, break into phases | Quick Wins — do first |
| **Low Value** | Hard Nos — avoid entirely | Fill-ins — only if slack exists |

### Plotting Rules

- Plot value on customer benefit, not internal benefit
- Effort includes full delivery (design + eng + QA), not just coding
- Get 2+ people to independently estimate before combining — anchoring bias is real
- Re-plot quarterly as estimates change

---

## Choosing the Right Framework

| Situation | Use |
|---|---|
| Quarterly roadmap planning with data | RICE |
| Sprint scoping with stakeholders | MoSCoW |
| Quick relative ranking of 10+ features | ICE |
| Visual alignment in a meeting | Value/Effort Matrix |
| Comparing features with very different reach | RICE only |
| No analytics data yet (pre-launch) | ICE or MoSCoW |

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Prioritizing by stakeholder seniority | Loudest voice wins | Show RICE scores in the room |
| Must = everything | No actual priority | Cap Must at 60% of capacity |
| RICE scores without confidence adjustment | Overestimates features with gut-feel data | Always apply confidence multiplier |
| Sorting only by score, ignoring dependencies | Shipping B before A breaks A | Check dependency graph before finalizing |
| Never re-prioritizing | Last quarter's priorities run forever | Re-score every quarter minimum |
