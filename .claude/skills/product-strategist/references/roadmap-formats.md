# Roadmap Formats

## Format Selection Guide

| Situation | Format |
|---|---|
| Early-stage, high uncertainty, priorities shift often | Now / Next / Later |
| Committed delivery dates, partner contracts, marketing launches | Timeline |
| Outcome-led planning, themes matter more than specific features | Theme-based |
| Executive audience who wants strategy not features | Theme-based or Now/Next/Later |
| Engineering team planning dependencies | Timeline |
| Customer-facing communication | Theme-based (never share internal timelines) |

---

## Format 1: Now / Next / Later

Best for: uncertainty, startup stage, agile teams, internal alignment.

```markdown
# [Product Name] — Roadmap [Quarter Year]

**Updated:** YYYY-MM-DD

---

## NOW (This quarter — committed)

- **[Feature/Initiative]:** [2-line description — what it does and why]
  - Success metric: [how we'll know this worked]
  - Owner: [team]

- **[Feature/Initiative]:** [description]

---

## NEXT (Next quarter — planned, not committed)

- **[Feature/Initiative]:** [description — may change based on what we learn]
- **[Feature/Initiative]:** [description]

---

## LATER (6+ months — directional only)

- **[Theme]:** [strategic area, not specific feature]
- **[Theme]:** [strategic area]

---

_Items in NEXT and LATER will shift based on learning from NOW._
```

**Rules:**
- NOW items are committed: engineering has started or is about to start
- NEXT items are planned: high confidence they'll happen, but not locked
- LATER items are directional: signal intent without commitment
- Never put specific dates in Now/Next/Later — that's what Timeline is for

---

## Format 2: Timeline Roadmap

Best for: committed delivery, coordinated marketing launches, partner dependencies.

```markdown
# [Product Name] — Timeline Roadmap

| Feature | Q1 | Q2 | Q3 | Q4 | Notes |
|---|---|---|---|---|---|
| [Feature A] | ████ | | | | Depends on auth revamp |
| [Feature B] | | ████ | | | GA in Q2 |
| [Feature C] | | | ████ | | Needs design sign-off |

---

### Q1 — [Milestone name]
- **[Feature A]:** [Description] | Owner: [Team] | Depends on: [X]
- **[Feature B]:** [Description]

### Q2 — [Milestone name]
- **[Feature C]:** [Description] | Owner: [Team]

---

_Confidence: Q1 = High | Q2 = Medium | Q3+ = Directional_
```

**Rules:**
- Label confidence per quarter: High / Medium / Directional
- Note dependencies explicitly — unresolved deps invalidate dates
- Never share with customers without removing internal estimates and caveats

---

## Format 3: Theme-Based Roadmap

Best for: external communication, outcome-led planning, executive audiences.

```markdown
# [Product Name] — Strategic Roadmap [Year]

---

## Theme 1: [Strategic outcome — e.g., "Make onboarding 3x faster"]

**Why:** [1-2 sentences — what customer pain this solves]

| Horizon | What we're doing |
|---|---|
| Now | [Specific initiative this quarter] |
| Next | [What follows in the next quarter] |
| Later | [Direction — not specific features] |

---

## Theme 2: [Strategic outcome]

**Why:** [Customer pain]

| Horizon | What we're doing |
|---|---|
| Now | |
| Next | |
| Later | |

---

_Themes may shift as we learn more. Features within themes are directional._
```

**Rules:**
- Themes should map to customer outcomes, not internal engineering areas
- Max 3–4 themes per roadmap — more = no strategic focus
- Suitable for sharing with customers (removes date commitment pressure)

---

## Communication Quality Checklist

Before sharing any roadmap:

- [ ] Audience-appropriate format selected
- [ ] Confidence levels labeled (committed / planned / directional)
- [ ] Each item has a clear outcome or "why" (not just a feature name)
- [ ] Dependencies and risks are transparent
- [ ] No internal metrics, costs, or staffing info leaked to external audiences
- [ ] Next actions specified for the audience (what should they do with this?)
- [ ] Re-publishing cadence set (quarterly minimum)

---

## Roadmap Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Feature list without "why" | No strategic signal | Add customer outcome per item |
| Dates on items in uncertainty | Creates false expectations | Use Now/Next/Later instead |
| Sharing internal timeline with customers | Date misses damage trust | Create a customer-facing version |
| Never updated | Roadmap diverges from reality | Republish every quarter minimum |
| Everything is "Now" | No actual prioritization | Apply MoSCoW before building roadmap |
| Roadmap driven by competitor features | Reactive, not strategic | Root each item in customer research |
