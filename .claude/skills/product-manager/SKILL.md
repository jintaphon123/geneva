---
name: product-manager
argument-hint: "[mode] — discover / prioritize / story / prd / reverse-prd"
description: >
  Product management covering discovery sprints, feature prioritization, user stories,
  PRD writing, and reverse-engineering codebases into documentation.

  Auto-invoke when Bond asks: discovery sprint, validate assumption, JTBD, opportunity solution tree,
  OST, RICE prioritization, prioritize features, product backlog, MoSCoW, user story,
  acceptance criteria, epic breakdown, sprint planning, write PRD, product spec,
  feature brief, product vision, code to PRD, reverse engineer codebase, document this app.
---

# Product Manager

Five modes covering the full PM workflow — from discovery through shipping.

---

## Mode Detection

| Input | Mode |
|---|---|
| "discovery sprint", "validate assumption", "JTBD", "OST", "opportunity" | **Discover** |
| "RICE", "prioritize features", "backlog", "MoSCoW", "ICE score", "WSJF", "weighted shortest job first", "velocity-based capacity", "Three Horizons", "sprint capacity", "team velocity" | **Prioritize** |
| "user story", "acceptance criteria", "epic breakdown", "sprint planning" | **Story** |
| "write PRD", "product spec", "feature brief", "product vision" | **PRD** |
| "code to PRD", "reverse engineer", "document this codebase", "document this app" | **Reverse-PRD** |

---

## Mode 1 — Discover

Build a shared understanding of the problem space before committing to solutions.

### OST (Opportunity Solution Tree)

```
Desired Outcome (measurable, business-level)
└── Opportunity 1 (unmet customer need)
    ├── Solution A
    │   └── Experiment 1
    └── Solution B
        └── Experiment 2
└── Opportunity 2
    └── ...
```

**Steps:**
1. Define the desired outcome — measurable, not a feature ("increase weekly active users by 20%")
2. Map opportunities from customer interviews, support tickets, usage data
3. Propose solutions per opportunity (not the other way around)
4. Design experiments to test the riskiest assumption per solution

### JTBD (Jobs-to-be-Done)

Frame every opportunity as a job: "When [situation], I want to [motivation], so I can [outcome]."

Distinguish: functional job (what they're trying to do) vs. emotional job (how they want to feel) vs. social job (how they want to be perceived).

### Kano Classification (for features)

| Category | Signal | Action |
|---|---|---|
| Must-be | Dissatisfied without it, not excited with it | Ship without fanfare |
| Performance | More = better, less = worse | Invest based on ROI |
| Delight | Unexpected value, creates loyalty | Build selectively |
| Indifferent | No reaction either way | Don't build |
| Reverse | Actively disliked by some | Research who |

### Assumption Prioritization

Map every assumption on 2 axes: **Risk** (if wrong, how bad?) × **Certainty** (how confident are we?).

Priority order: High Risk + Low Certainty → validate first (run experiments). High Risk + High Certainty → monitor. Low Risk → deprioritize.

Types: Desirability (do they want it?), Viability (will the business work?), Feasibility (can we build it?), Usability (can they use it?).

### Discovery Sprint Structure (10 days)

```
Day 1:  Define outcome + map current state
Day 2:  Customer interviews × 3 (minimum)
Day 3:  Synthesize interviews → opportunity map
Day 4:  Generate solutions (diverge)
Day 5:  Prioritize solutions → select top 3
Day 6-7: Build lowest-fidelity test for each
Day 8:  Run tests with 3-5 customers
Day 9:  Synthesize evidence
Day 10: Decision — build, iterate, or kill
```

Full frameworks → `references/discovery-frameworks.md`

---

## Mode 2 — Prioritize

Score and rank features before committing engineering capacity.

### RICE Scoring

**Formula:** RICE = (Reach × Impact × Confidence) / Effort

| Factor | Definition | Scale |
|---|---|---|
| Reach | Users affected per quarter | # of users |
| Impact | Effect on the outcome | 3=massive, 2=significant, 1=low, 0.5=minimal, 0.25=tiny |
| Confidence | How confident in the estimates | 100% / 80% / 50% |
| Effort | Person-months to build | # person-months |

**Thresholds:**
- 1000+ → High priority (quick win or big bet)
- 500–999 → Medium priority
- 100–499 → Low priority
- <100 → Deprioritize

### MoSCoW

- **Must:** Without this, the product fails. Non-negotiable.
- **Should:** High value, important but not critical for launch.
- **Could:** Nice-to-have. Include if time allows.
- **Won't:** Explicitly out of scope for this cycle.

Cap Must at 60% of sprint capacity. Never negotiate Must with engineering without re-prioritizing something else out.

### ICE Scoring

ICE Score = (Impact × Confidence × Ease) / 10

Use for quick relative scoring when RICE estimates aren't available.

### Value vs. Effort Matrix

| | High Effort | Low Effort |
|---|---|---|
| **High Value** | Big Bets (plan carefully) | Quick Wins (do first) |
| **Low Value** | Hard Nos (avoid) | Fill-ins (if capacity exists) |

Full frameworks → `references/prioritization-frameworks.md`

**WSJF, velocity-based capacity, Three Horizons, or sprint commitment metrics?** → `references/agile-capacity.md`

---

## Mode 3 — Story

Write clear, testable user stories and acceptance criteria.

### Story Format (INVEST)

```
As a [persona],
I want to [action],
So that [benefit / outcome].
```

INVEST checklist: **I**ndependent · **N**egotiable · **V**aluable · **E**stimable · **S**mall · **T**estable

### Acceptance Criteria (Given-When-Then)

```
Given [precondition / context]
When [action / event]
Then [expected outcome]
```

Minimum AC counts by story size:
- 1–2 points: 3–4 AC
- 3–5 points: 4–6 AC
- 8 points: 5–8 AC (consider splitting if 8+)
- 13+ points: must split before sprint

### Epic Splitting (5 Techniques)

1. **By workflow step:** Each step in the process becomes its own story
2. **By persona:** Different users get different stories for the same feature
3. **By data type/variation:** Handle each data variant separately
4. **By operation:** CRUD split — create, read, update, delete as separate stories
5. **Happy path first:** Core flow ships, edge cases follow in next sprint

### Sprint Planning

- Capacity = team velocity (rolling 3-sprint average) × number of sprints
- Allocation: 85% committed + 15% stretch goals
- Weight: Business Value 40% + User Impact 30% + Risk Reduction 15% + Effort Inverse 15%

Full templates → `references/story-templates.md`

---

## Mode 4 — PRD

Write product requirements that engineering actually uses.

### Standard PRD Structure

```
1. Overview        — TL;DR, problem statement, success metrics
2. Background      — Context, research, why now
3. Goals           — What we're trying to achieve (measurable)
4. Non-goals       — Explicit scope exclusions
5. User Stories    — Key scenarios the product must handle
6. Requirements    — Functional (what it does) + Non-functional (performance, security)
7. UX Notes        — Key flows, edge cases, wireframe links
8. Technical Notes — Constraints, dependencies, API contracts (optional)
9. Milestones      — Key checkpoints and dates
10. Open Questions — Unresolved decisions with owners
```

### One-Page PRD (for smaller features)

```
Problem: [1 sentence — who is affected and how]
Solution: [1 sentence — what we're building]
Success: [1–3 metrics that would mean this worked]
Out of scope: [explicit exclusions]
Stories: [3–5 core stories]
Risks: [top 2 risks and mitigations]
Timeline: [milestone → date]
```

### Feature Brief (smallest unit)

```
Feature: [Name]
Why: [Problem being solved]
What: [What the feature does — behavior, not UI]
Acceptance: [How we know it's done]
Dependencies: [What else must ship first]
```

Full templates → `references/prd-templates.md`

---

## Mode 5 — Reverse-PRD

Analyze a codebase and generate structured product documentation.

### 3-Phase Workflow

**Phase 1 — Global Scan:**
- Identify project structure (routes, pages, components, API)
- Build page inventory with URL, component name, layout
- Map global context: auth model, navigation, shared state, error handling

**Phase 2 — Page-by-Page Analysis:**
For each page/screen:
- Business purpose (in non-technical language)
- Field inventory (exhaustive table: field, type, required, default, validation, business meaning)
- Interactions and state changes
- API dependencies (endpoints called, data shapes)
- Relationships to other pages

**Phase 3 — Generate prd/ Directory:**

```
prd/
├── README.md                    # Executive summary, page index, auth model
├── pages/
│   ├── [page-name].md           # Per-page documentation
│   └── ...
└── appendix/
    ├── enum-dictionary.md       # All enum values with business meaning
    ├── page-relationships.md    # Page dependency map
    └── api-inventory.md         # All endpoints with request/response shapes
```

**Field Inventory Table Format:**

| Field | Type | Required | Default | Validation | Business Meaning |
|---|---|---|---|---|---|
| email | string | yes | — | RFC 5322 | Login identifier, used for billing comms |

**Business language rules:**
- Say "customer's billing address" not "`billingAddress` state variable"
- Say "30-day trial period" not "`trial_days: 30`"
- Say "must be unique per organization" not "`UNIQUE(org_id, email)`"
- Mark uncertainty with: "(assumed)" when inferring intent from code alone

Full templates → `references/prd-templates.md`

---

## References

- `references/discovery-frameworks.md` — OST, JTBD, Kano, assumption matrix, sprint structure
- `references/prioritization-frameworks.md` — RICE, MoSCoW, ICE, Value/Effort matrix
- `references/story-templates.md` — INVEST, GWT, AC count table, epic splitting, sprint loading
- `references/prd-templates.md` — Standard PRD, One-Page PRD, Feature Brief, Reverse-PRD directory format
- `references/agile-capacity.md` — WSJF, Three Horizons, velocity-based capacity planning, Tuckman delivery buffers
