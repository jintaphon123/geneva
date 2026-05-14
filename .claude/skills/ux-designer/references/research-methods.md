# Research Methods

## Persona Methodology

### Research Sources (priority order)

1. **Behavioral data** (highest weight): analytics clusters, usage patterns, feature adoption segments
2. **Interview data**: transcripts from 5+ user interviews per persona
3. **Survey data**: quantitative validation of qualitative findings
4. **Support tickets**: real language, real frustrations at scale
5. **Sales call recordings**: objections, comparison language, decision factors

### Persona Validation

A persona is valid when:
- Supported by at least 3 independent data sources
- Represents a real, meaningful segment (not a hypothetical "edge case")
- Has distinguishable behaviors from other personas (not just demographic differences)
- A team member can answer: "Would this person use feature X?" without hesitation

### Persona Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Demographic personas | Age/gender don't predict behavior | Use behavioral and motivational attributes instead |
| "Average user" persona | Averages don't represent anyone | Identify distinct segments, create one per segment |
| Too many personas | Team can't keep them in mind | Max 3–4 active personas per product |
| Aspirational personas | Describes the user you want, not the one you have | Ground every attribute in observed data |
| No design implications | Decorative, not useful | Every persona must drive at least 2 design decisions |

---

## Journey Map Guide

### Stage Definition

Good stages are named from the user's perspective (not product):
- "Discover" not "Homepage"
- "Evaluate" not "Trial signup"
- "Get started" not "Onboarding flow"
- "Master" not "Advanced features"

Typical stage sequence for a SaaS product:
```
Awareness → Evaluate → Sign up → Activate → Use habitually → Expand → Refer/Renew
```

### Emotion Mapping

Use 1–5 scale with emoji anchors:
- 1 😫 Very frustrated / confused
- 2 😟 Slightly frustrated
- 3 😐 Neutral
- 4 😊 Satisfied
- 5 😄 Delighted

Record the emotion the user feels during the stage — not what you want them to feel.

### Pain Point Extraction from Research

Listen for language signals:
- "I always have to..." (workaround behavior)
- "I wish I could..." (unmet need)
- "It's annoying when..." (friction point)
- "I never bother with..." (abandoned feature)
- "I end up using [other tool] for that" (job not being done)

### Opportunity Framing

Convert pain to opportunity as a How Might We (HMW) statement:
```
Pain: "I don't know what to do after I log in for the first time"
Opportunity: "HMW make the first session feel guided without being hand-holdy?"

Pain: "I forget to come back unless something's broken"
Opportunity: "HMW create a compelling reason to return weekly?"
```

### Journey Map Quality Checklist

- [ ] Every stage has at least one pain point (no stages are "all good")
- [ ] Emotions are plotted per stage (visible dip = design opportunity)
- [ ] Opportunities are actionable (not "improve UX")
- [ ] Map is based on research, not internal assumptions
- [ ] Map covers end-to-end (from trigger to renewal/churn, not just onboarding)

---

## Usability Test Structures

### Session Structure (Moderated)

```
0:00 – 0:05  Welcome, consent, "think aloud" instruction
0:05 – 0:10  Warm-up questions (background, relevant context)
0:10 – 0:45  Tasks (3–5 tasks, timed, think-aloud)
0:45 – 0:55  Post-task interview (open-ended, follow-up on observations)
0:55 – 1:00  SUS questionnaire + close
```

### Think-Aloud Coaching

Tell participants: "As you work through each task, please say out loud what you're thinking, what you're looking for, and any reactions you have. There are no wrong answers — we're testing the product, not you."

If they go silent: "What's going through your mind right now?"
Never say: "You're doing great" or validate any action — it biases behavior.

### Task Severity Scale

| Severity | Definition | Action |
|---|---|---|
| **Critical** | User cannot complete task; blocks their core job | Fix before launch |
| **Major** | User completes task with significant struggle or error | Fix before launch |
| **Minor** | User completes task but with friction or confusion | Fix in next sprint |
| **Cosmetic** | User notices issue but it doesn't affect completion | Backlog |

### SUS (System Usability Scale)

10-question standardized questionnaire. Score 0–100. Industry average: 68.
- > 80: Excellent (A)
- 68–80: Good (B/C)
- 51–67: OK — needs work (D)
- < 51: Poor — significant UX issues (F)

Questions alternate positive/negative — score each 1–5 before converting.

---

## Research Synthesis Guide

### Affinity Mapping (digital or physical)

1. Write each observation on a separate card/note (one observation per card)
2. Silently sort cards into groups that "feel related"
3. Name each group with a theme label (verb + noun: "Users struggle with navigation")
4. Identify super-groups (themes of themes)
5. Count cards per group — size = signal strength

### Insight Statement Structure

```
We observed that [behavior / quote].
This suggests that [underlying need / mental model].
Therefore, we should consider [design / product opportunity].
```

Example:
```
We observed that 4 of 5 users tried to click the logo to go home, and felt frustrated 
when it didn't work.
This suggests that users have a strong mental model that logos = home navigation.
Therefore, we should make the logo a clickable home link.
```

### Prioritizing Insights

| Criteria | Weight |
|---|---|
| Frequency (how many users) | 40% |
| Severity (how much it blocks progress) | 35% |
| Strategic fit (how aligned to product goals) | 25% |

### Research Synthesis Checklist

- [ ] Every insight grounded in ≥ 3 data points (not a single outlier)
- [ ] Insights stated as needs, not solutions
- [ ] Insights prioritized (not a flat list of equal weight)
- [ ] Quotes included as evidence (verbatim, not paraphrased)
- [ ] Known unknowns documented ("we don't have data on X")
- [ ] Findings shared within 48 hours of last session (memory degrades fast)
