# Discovery Frameworks

## Opportunity Solution Tree (OST)

Teresa Torres' framework for continuous product discovery. Prevents jumping from problem to solution.

### Structure

```
Desired Outcome (measurable, business-level metric)
├── Opportunity 1 (unmet customer need / pain point / desire)
│   ├── Solution A
│   │   ├── Experiment 1a (tests riskiest assumption of Solution A)
│   │   └── Experiment 1b
│   └── Solution B
│       └── Experiment 2
├── Opportunity 2
│   └── Solution C
│       └── Experiment 3
└── Opportunity 3
    └── (no solutions yet — need more research)
```

### OST Building Rules

- One outcome at a time — multi-outcome trees cause confused prioritization
- Opportunities come from customers (interviews, support, reviews) — never from internal brainstorming alone
- Solutions should be small and testable — if it takes >2 weeks to test, break it down
- Map experiments to the single riskiest assumption of each solution

### OST Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Solution disguised as opportunity | Narrows solution space | Restate as customer need |
| Output as outcome | Unmeasurable | Add a metric (%, count, time) |
| No experiments | Assumption risk unvalidated | Add a fake door or prototype |
| Too many simultaneous outcomes | Team unfocused | Pick one for the quarter |

---

## Jobs-to-be-Done (JTBD)

### Job Statement Format

"When [situation], I want to [motivation / job], so I can [outcome / benefit]."

**Example:**
"When I'm reviewing a candidate after an interview, I want to quickly share my notes with the hiring team, so I can make a decision before they accept another offer."

### Three Job Types

| Type | Definition | Example |
|---|---|---|
| Functional | What they're trying to accomplish | "Organize my project files" |
| Emotional | How they want to feel doing it | "Feel confident I won't lose work" |
| Social | How they want to appear to others | "Look organized to my team" |

### JTBD Interview Protocol

1. Recruit people who have recently done the relevant job
2. Ask about the last time they did it — not hypotheticals
3. Explore: what triggered the need? what did they try first? what did they switch from?
4. Look for workarounds — they signal unmet functional or emotional jobs
5. Never lead with your solution — let the job emerge from their story

---

## Kano Model

Classify features by the relationship between implementation and customer satisfaction.

### Categories

| Category | Customer reaction | Investment rule |
|---|---|---|
| **Must-be (Basic)** | Dissatisfied without it, neutral with it | Ship it — table stakes |
| **Performance (Linear)** | More = more satisfied, less = less | Invest proportional to ROI |
| **Delight (Excitement)** | Unexpected joy, creates loyalty | Build selectively — high cost-to-satisfaction |
| **Indifferent** | No reaction either way | Don't build |
| **Reverse** | Subset of customers actively dislikes it | Investigate — segment before deciding |

### Kano Survey Question Pair

For each feature ask:
1. "If [feature] were present, how would you feel?" (Functional form)
2. "If [feature] were absent, how would you feel?" (Dysfunctional form)

Answers: Love it / Expect it / Neutral / Can tolerate / Dislike it

Kano evaluation table maps functional × dysfunctional response to category.

---

## Assumption Prioritization Matrix

### Four Assumption Types

| Type | Question it answers |
|---|---|
| **Desirability** | Do customers want this? |
| **Viability** | Will this work as a business? |
| **Feasibility** | Can we build this? |
| **Usability** | Can customers figure out how to use it? |

### Prioritization Grid

```
High Risk
     │
     │  VALIDATE FIRST    │  Monitor
     │  (riskiest)        │  (safe to proceed but watch)
     │                    │
─────┼────────────────────┼──────────────────────
     │                    │
     │  Background risk   │  Ignore for now
     │  (not urgent)      │
     │                    │
Low Risk
     └────────────────────┴──────────────────────
              Low Certainty         High Certainty
```

Validate first: High Risk + Low Certainty. These are the experiments to run in this sprint.

### Assumption Card Format

```
Assumption: [We believe that X]
Type: Desirability / Viability / Feasibility / Usability
Risk if wrong: High / Medium / Low
Current certainty: High / Medium / Low
Evidence we have: [what supports this]
Validation method: [fake door / prototype / interview / analytics]
```

---

## 10-Day Discovery Sprint

### Structure

| Day | Activity | Output |
|---|---|---|
| 1 | Define desired outcome. Map current product state. | Outcome statement + baseline metric |
| 2–3 | Customer interviews × 3–5 | Raw interview notes |
| 4 | Synthesize interviews → opportunity map | Updated OST (opportunities only) |
| 5 | Assumption mapping — list all assumptions for top 3 opportunities | Prioritized assumption list |
| 6 | Generate solutions per top opportunity (diverge — no judgment) | Long list of solutions |
| 7 | Select top 3 solutions. Design lowest-fidelity experiment for each. | Experiment briefs |
| 8 | Run experiments with 3–5 customers per experiment | Raw experiment results |
| 9 | Synthesize evidence. What learned? Confidence change? | Updated assumption cards |
| 10 | Decision meeting: build / iterate / kill each solution | Next sprint commitments |

### Interview Script Template

```
Opening: "Tell me about the last time you [relevant job]. Walk me through what happened."

Probe sequence:
1. "What triggered that situation?"
2. "What did you do first?"
3. "What was the hardest part?"
4. "How did you handle that?"
5. "What did you wish existed?"
6. "Have you tried other solutions? What happened?"
7. "What would make your life significantly easier here?"

Closing: "Is there anything I didn't ask that you think is important?"
```

### Evidence Quality Levels

| Level | Definition | Weight |
|---|---|---|
| Behavioral | Observed what they actually did | Highest |
| Behavioral-verbal | What they said they did (recounted) | High |
| Attitudinal | What they said they would do | Medium |
| Hypothetical | What they think they might prefer | Low |
