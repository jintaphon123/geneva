---
name: ops-advisor
argument-hint: "[challenge to solve] or 'okrs' to design quarterly goals"
description: >
  Operations and execution framework covering OKR design, strategy-to-execution
  cascade, process design, operational cadence, bottleneck analysis, team alignment,
  and operating system selection (EOS, OKR-native, hybrid).

  Auto-invoke when Bond asks: OKRs, execution plan, how to run this operationally,
  process design, weekly rhythm, team alignment, strategy not being executed,
  team pulling in different directions, bottleneck, scaling operations, meeting
  cadence, accountability, quarterly planning, or 90-day rocks.
---

# Ops Advisor

Turns strategy into execution. Three layers: Operating System (how the company runs),
OKR Cascade (how strategy becomes tasks), and Alignment (how you find and fix drift).

## Context Auto-Load

Read `context/work.md` and `context/current-priorities.md` before responding.
Bond is currently solo — apply frameworks at 1-person scale first, then show how they
scale when KU team joins.

---

## 1. Operating System Selection

How a company runs day-to-day — meeting rhythm, accountability, issue resolution.

| Framework | Best for | Core mechanic |
|---|---|---|
| EOS (Entrepreneurial OS) | < 250 people, founder-led | L10 meetings, Rocks, Scorecard, V/TO |
| Scaling Up (Rockefeller) | 50–500 people, growth stage | Priorities, Data, Rhythm, People |
| OKR-native | Tech companies, fast iteration | Quarterly OKRs, weekly check-ins |
| Hybrid | Early startups | OKRs + L10 meeting rhythm |

**Bond's recommendation:** OKR-native with L10 weekly meeting rhythm.
Simple, scales from 1 person to 20 without restructuring.

### L10 Weekly Meeting (55 min)

| Segment | Time | Purpose |
|---|---|---|
| Segue (good news) | 5 min | Start positive |
| Scorecard review | 5 min | Review KPIs — red flag anything off track |
| Rock review | 5 min | 90-day priorities — on track / off track / done |
| Customer/people headlines | 5 min | Good/bad news |
| To-do list review | 5 min | Last week's todos — done or not done |
| IDS (Issues) | 30 min | Identify, Discuss, Solve top issues |
| Conclude | 5 min | Recap todos, rate the meeting |

**For Bond solo:** Run this as a personal weekly review — same segments, solo.

---

## 2. OKR Design

**Structure:**
- **Objective:** Qualitative, inspiring, directional ("Build the most useful AI memory system for non-tech users")
- **Key Results:** Quantitative, measurable, 3–5 per objective ("100 active users by July 2026", "avg session > 10 min")

**OKR Cascade (when team exists):**
```
Company OKRs (quarterly)
    └── Team OKRs (align to company)
          └── Individual OKRs (align to team)
```

**Rules:**
- 1–3 objectives per quarter (Bond: 1 objective, 3–4 KRs)
- KRs are outcomes, not tasks ("Users return weekly" not "Build notification system")
- 70% attainment = good. 100% = too easy. < 50% = wrong goal or wrong resource.
- Weekly check-in: update confidence score (0–100%) per KR, not completion %

**Bond's current OKR template:**
```
Objective: [what we're trying to achieve this quarter]

KR1: [measurable outcome] — target: [X] — current: [Y] — confidence: [%]
KR2: [measurable outcome] — target: [X] — current: [Y] — confidence: [%]
KR3: [measurable outcome] — target: [X] — current: [Y] — confidence: [%]

Blockers: [what's in the way]
This week's top priority: [single most important task]
```

---

## 3. Strategy-to-Execution Cascade

The gap between strategy and execution is almost always a communication problem.

**Cascade check:**
1. Can you state the company strategy in one sentence?
2. Can every person on the team state it in one sentence?
3. Does their weekly work connect to it?

**Orphan goal detection:** Any task that can't be traced to a KR is an orphan.
Orphans aren't always bad — but they should be conscious choices, not accidents.

**Alignment red flags:**
- Teams "hitting their OKRs" but company not moving → KRs wrong, not tasks
- Different teams optimizing at each other's expense → silo problem, needs cross-functional OKR
- OKRs set once and never reviewed → disconnect between plan and reality

---

## 4. Bottleneck Analysis

**Theory of Constraints (TOC) — find the one constraint that limits everything:**
1. Identify the system's constraint (where does work pile up?)
2. Exploit the constraint (maximize throughput of the bottleneck)
3. Subordinate everything else (don't optimize non-constraints)
4. Elevate the constraint (add capacity if needed)
5. Repeat (once constraint fixed, find the next one)

**Common early-stage constraints:**
- Founder as decision bottleneck → delegation problem
- No clear process → everyone reinvents the wheel
- Wrong priority → working hard on the wrong thing
- Missing skill → team can't execute even if direction is clear

---

## 5. Scaling Process Design

When to document a process: when you've done something 3+ times and will do it again.
When NOT to document: one-off tasks, tasks that will change soon, tasks that require judgment not process.

**Process template:**
```
Process: [name]
Owner: [who runs this]
Trigger: [what starts this process]
Steps:
  1. [action] → [output] → [owner]
  2. [action] → [output] → [owner]
Done when: [clear completion signal]
Review: [how often to revisit this process]
```

---

## Output Artifacts

| Request | Output |
|---|---|
| "Set up OKRs for this quarter" | OKR structure — use `references/okr-template.md` |
| "My team isn't executing" | Alignment audit + cascade check + bottleneck ID |
| "How should we run our weekly meetings?" | L10 meeting structure customized to team size |
| "Design a process for X" | Process template with owner, steps, done-when |
| "What operating system should we use?" | Framework recommendation with rationale |

## References

- `references/okr-template.md` — Bond's quarterly OKR format with weekly check-in cadence

## NotebookLM Deep Dive

For deeper operational frameworks, use `/consult` routed to:
- **Business Bibles** (`632f161b`) — team execution, scaling ops, management systems (Grove's High Output Management, Dalio's Principles)

Trigger: "I need a deeper execution/management framework → `/consult [specific question]`"

## Language Rule

Match Bond's input language. Formal operational docs → English.
