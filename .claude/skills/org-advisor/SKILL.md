---
name: org-advisor
argument-hint: "[change to announce] or 'health-check' for org diagnostic"
description: >
  Team, culture, and organizational health framework covering change management,
  org health diagnostics, values design, culture code creation, and cultural rituals.
  For when Bond is building or scaling a team.

  Auto-invoke when Bond asks: building team culture, company values, culture code,
  team change, announcing a pivot, org restructure, reorg, managing resistance,
  team health check, cultural rituals, values to behaviors, or culture debt.
---

# Org Advisor

Three tools in one: Change Management (rolling out changes without chaos),
Org Health Diagnostic (spotting problems before they compound), and
Culture Architect (building culture as operational behavior, not wall posters).

## Context Auto-Load

Read `context/team.md` before responding.
Bond is currently solo. Apply frameworks at "founding team" scale (2–5 people) —
relevant when recruiting KU co-founders or hiring first employees.

---

## 1. Change Management (ADKAR for Startups)

Rolling out any significant change — pivot, new process, tool switch, team restructure.

**ADKAR Model (adapted for startups):**

| Stage | Question to answer | Failure symptom |
|---|---|---|
| **Awareness** | Do people know WHY the change is happening? | "Nobody told me" |
| **Desire** | Do people WANT to change? | Passive resistance |
| **Knowledge** | Do people know HOW to change? | Confusion, mistakes |
| **Ability** | Can people actually DO it? | Willing but struggling |
| **Reinforcement** | Is the change being sustained? | Relapse to old behavior |

**Communication template for any change announcement:**
```
WHAT is changing: [clear statement]
WHY we're changing: [honest reason — don't sugarcoat]
WHAT stays the same: [reassure on continuity]
WHAT you need to do: [specific actions required]
TIMELINE: [when this happens]
QUESTIONS: [how to ask them]
```

**Resistance patterns and responses:**
| Pattern | What it looks like | Response |
|---|---|---|
| Fear of loss | "This will make my role less important" | Acknowledge the loss explicitly |
| Disbelief | "This won't actually work" | Share the evidence behind the decision |
| Distrust | "Management always says this then does that" | Demonstrate commitment with actions, not words |
| Fatigue | "Another change? Really?" | Acknowledge change fatigue; explain why this one matters |

**Change fatigue warning:** If you've made 3+ significant changes in 6 months, the next one
needs extra justification and communication. The team's capacity to absorb change is finite.

---

## 2. Org Health Diagnostic

8-dimension traffic-light health check. Run before board reviews, when things feel off,
or quarterly.

| Dimension | 🟢 Healthy | 🟡 Watch | 🔴 Problem |
|---|---|---|---|
| **Strategy clarity** | Everyone can state the strategy | Some confusion at IC level | Different teams have different strategies |
| **Execution** | OKRs hit 60–80% consistently | OKRs hit < 50% or > 90% | OKRs exist but nobody tracks them |
| **Team trust** | People raise issues openly | Issues surface in 1:1s not meetings | Silent meetings, issues in Slack |
| **Leadership alignment** | Leadership agrees in public and private | Occasional misalignment | Leaders contradict each other |
| **Hiring health** | Hiring intentionally, cultural fit | Reactive hiring under pressure | Taking anyone who applies |
| **Retention** | Regrettable attrition < 10% | 10–20% regrettable attrition | > 20% or losing key people |
| **Communication** | News travels fast, accurate | Some people always out of loop | Rumor mill fills the gap |
| **Culture** | Values visible in daily decisions | Values stated but not practiced | "That's not really how we operate" |

**For Bond at solo/founding stage:** Focus on Strategy clarity, Execution, and Communication.
Other dimensions matter when team grows beyond 3.

---

## 3. Culture Architect

Culture is what people do when you're not in the room. It's set by founders, enforced by hiring,
and killed by bad decisions you don't address.

### Step 1: Define Values

**Good values are:**
- Behaviors, not adjectives ("We ship on Fridays even if it's not perfect" not "We're agile")
- Specific enough to make a hard decision with ("We choose customer value over internal comfort" — who wins when they conflict?)
- Uncomfortable when violated (if nobody ever gets called out for violating it, it's not real)

**Values workshop (1–2 hours with founding team):**
1. Each person writes 10 stories of the company at its best
2. Find the common behaviors across all stories
3. Name those behaviors as values (5 max)
4. For each value: "What does this look like in a hard situation?"

### Step 2: Translate to Behaviors

| Value | Behavior (what it looks like) | Anti-behavior (what violates it) |
|---|---|---|
| [Value] | "We do X even when Y" | "We don't do Z just because it's easier" |

### Step 3: Culture Health Check

Run quarterly. For each value:
- Can you name 3 recent decisions that expressed this value?
- Can you name 1 recent decision that violated it? How was it addressed?
- Would a new hire learn this value from watching us, or only from reading the wall poster?

### Stage-appropriate cultural rituals

| Stage | Ritual | Purpose |
|---|---|---|
| Founding (1–5 people) | Weekly team dinner / async retrospective | Build trust, surface issues early |
| Early (5–15) | Monthly all-hands, pair work | Spread information, break silos |
| Growing (15–50) | Quarterly values review, culture ambassador program | Preserve culture as new people join |

---

## 4. Internal Communications

Writing team updates, status reports, company announcements, or change communications.

**Writing a 3P update, status report, or company announcement?** → `references/internal-comms.md`

**Format selection:**
- Weekly team update to leadership → 3P Update (Progress/Plans/Problems)
- Company-wide news or milestones → Company Newsletter
- Project status to stakeholders → Status Report
- Something went wrong → Incident/Crisis Communication
- Org change announcement → Change Communication (ADKAR template above)

---

## Output Artifacts

| Request | Output |
|---|---|
| "Announce this pivot to the team" | Change communication from ADKAR template |
| "Team health check" | 8-dimension traffic-light scorecard |
| "Build our company values" | Values workshop facilitation + behavior translation |
| "Create a culture code" | Values → behaviors → rituals document |
| "Team is resisting X change" | Resistance pattern ID + response strategy |

## NotebookLM Deep Dive

For deeper culture and org frameworks, use `/consult` routed to:
- **Business Bibles** (`632f161b`) — culture building, management philosophy, org design (Horowitz's Hard Thing About Hard Things, Dalio's Principles)

Trigger: "I need a deeper culture/people framework → `/consult [specific question]`"

## References

- `references/internal-comms.md` — 3P updates, company newsletter, status reports, crisis communication, change announcement templates

## Language Rule

Match Bond's input language. Culture code / values docs for external use → English.
