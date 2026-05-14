---
name: scenario-planner
argument-hint: "[plan or decision to stress-test]"
description: >
  Adversarial stress-testing and what-if scenario modeling. Finds holes in plans
  before the board does, models compound risk scenarios, forces honest post-mortems,
  and dissects decisions with no good options.

  Auto-invoke when Bond asks: stress-test this plan, what could go wrong, what if
  X and Y both happen, worst case, devil's advocate, post-mortem, I can't decide
  between X and Y, play devil's advocate, or poke holes in this.

  NOTE: For full strategic consulting with research + recommendation → use /consult instead.
  This skill is for quick, focused adversarial analysis only.
---

# Scenario Planner

Two modes: Stress-Test (find what's wrong with a plan) and War Room (model compound risk).
Fast, adversarial, no padding. Designed for pre-decision checks, not full consultations.

---

## Mode Detection

| Input | Mode |
|---|---|
| "Stress-test this", "poke holes", "what am I missing", "devil's advocate" | **Stress-Test** |
| "What if X and Y both happen", "worst case", "compound risk", "scenario planning" | **War Room** |
| "Post-mortem on X", "what went wrong" | **Post-Mortem** |

---

## Mode 1: Stress-Test

Given a plan, find the critical flaws before the plan is executed.

### Step 1 — State the plan back in one sentence
Confirm you understand what's being stress-tested. If unclear, ask ONE question.

### Step 2 — Attack from 5 angles

| Angle | Question to answer |
|---|---|
| **Assumptions** | What is this plan assuming that hasn't been verified? |
| **Resources** | Does Bond have the time, money, skills, and people this requires? |
| **Market** | Does the customer actually want this? Is the market timing right? |
| **Execution** | What's the hardest part to execute? What breaks first? |
| **Second-order** | If this works, what problem does it create? |

### Step 3 — Assign verdicts

- ✅ **STRONG** — Survives all 5 attacks. Proceed with confidence.
- ⚠️ **CONDITIONAL** — Valid only if [specific condition]. Name the condition.
- ❌ **WEAK** — Has a critical unresolved flaw. Name it. Suggest the fix.

### Output format

```
## Stress-Test: [Plan name]

Critical flaws found: [X]

❌ [Flaw 1 name]
   Problem: [what specifically is wrong]
   Impact: [what happens if this isn't fixed]
   Fix: [what would resolve this]

❌/⚠️ [Flaw 2 name]
   [same format]

✅ Strengths that survive:
- [What held up under pressure]

Verdict: [PROCEED / PROCEED WITH CAUTION: fix [X] first / DO NOT PROCEED until [X] resolved]
```

**Rules:**
- Minimum 2 specific named flaws — "may have risks" is not a flaw
- Every flaw needs: what's wrong + why it matters + how to fix it
- If no flaws found: you didn't look hard enough — try harder

---

## Mode 2: War Room (Compound Risk)

Unlike single-assumption stress testing, War Room models what happens when multiple
bad things happen simultaneously.

### Step 1 — Map the scenario space

For Bond's venture, identify:
- **Demand risk:** What if users don't adopt?
- **Supply risk:** What if key input (time, tools, partner) is cut?
- **Competitive risk:** What if a well-funded competitor copies this?
- **Execution risk:** What if Bond gets sick, fails exams, or runs out of time?
- **External risk:** What if regulations change? Economy tanks? Key platform bans the use case?

### Step 2 — Build compound scenarios

**Compound scenario format:** "What if [Risk A] AND [Risk B] happen in the same quarter?"

Most companies plan for A or B. War Room plans for A + B simultaneously.

**Triage matrix:**

| Scenario | Probability | Impact | Response |
|---|---|---|---|
| [A + B] | Low/Med/High | Low/Med/High | Accept / Mitigate / Avoid / Transfer |
| [A + C] | ... | ... | ... |

### Step 3 — Output

```
## War Room: [Context]

Compound Scenarios Modeled:

Scenario 1: [Name] — [Risk A] + [Risk B]
Probability: [Low/Med/High]
Impact if it happens: [Specific consequences]
Early warning signs: [What to watch for before it hits]
Response if it happens: [What to do immediately]

Scenario 2: ...

Highest-priority scenario to prepare for: [#X]
Recommended pre-commitment: [What to set up now to be ready]
```

---

## Mode 3: Post-Mortem

Honest analysis of what went wrong and why.

### Step 1 — Establish facts (not blame)

- What was the intended outcome?
- What actually happened?
- When did it become clear this was going wrong?

### Step 2 — Root cause analysis (5 Whys)

"Why did X happen?"
→ "Because Y."
"Why did Y happen?"
→ "Because Z."
[Continue until the root cause — not the symptom — is named]

### Step 3 — Learnings and changes

```
## Post-Mortem: [Event]

What happened: [facts only]
Root cause: [the real reason, not the surface symptom]

What we assumed that wasn't true:
- [Assumption 1]
- [Assumption 2]

What we'll do differently:
- [Specific change 1]
- [Specific change 2]

What we'd do the same:
- [What actually worked despite the failure]
```

---

## Relationship to /consult

| Need | Use |
|---|---|
| Quick: "Find the holes in this plan" | `/scenario-planner` |
| Full: "Should I do X? Research + recommendation" | `/consult` |
| Both: Deep consultation that includes stress-testing | `/consult` (devil's advocate phase handles it) |

## Language Rule

Match Bond's input language.
