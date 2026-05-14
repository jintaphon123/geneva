# Analysis Module Reference — Detailed Patterns & Thresholds

## Module A: Speaking Dynamics — Full Specification

### Metrics to Calculate

| Metric | Formula | Unit |
|--------|---------|------|
| Word count | Count all words per speaker | Words |
| Word share | Speaker words / Total words × 100 | % |
| Turn count | Number of distinct speaking turns | Count |
| Average turn length | Total words / Turn count | Words/turn |
| Longest monologue | Maximum single turn length | Words or minutes |
| Interruption count | Turns starting within 2 sec of prior speaker ending | Count |

### Threshold Table

| Signal | Threshold | Flag Label | Action |
|--------|-----------|------------|--------|
| One speaker >60% of words | >60% share | "Dominating" | Flag in Top Findings |
| Organizer <15% (when they should facilitate) | <15% when organizer role | "Facilitator absent" | Flag |
| Speaker <2% of words | <2% share | "Voice not heard" | Flag — investigate exclusion |
| Single turn >200 words | >200 words | "Extended monologue" | Flag with timestamp |
| Interruptions >5 per meeting | >5 interruptions | "High interruption pattern" | Flag with specific instances |
| Equal participation | All speakers 15-35% | — | Strength to note |

### Healthy Balance Benchmarks

| Meeting type | Dominant speaker | Others |
|-------------|-----------------|--------|
| Decision meeting (5-8 people) | 25-40% | 10-25% each |
| Brainstorm (3-5 people) | 25-45% | 15-25% each |
| 1:1 (2 people) | 45-60% | 40-55% |
| Interview | 30-40% (interviewer) | 60-70% (candidate) |
| Presentation | 60-80% (presenter) | 20-40% (Q&A) |

---

## Module B: Conflict & Directness — Pattern Dictionary

### Hedging Patterns

**Language signals:**
- "maybe we could...", "perhaps it might be...", "I don't know if..."
- "kind of", "sort of", "somewhat", "a little bit" (as qualifiers)
- "I guess", "I suppose", "I think maybe"
- "it could potentially be worth considering"
- "would it make sense if we..."

**Severity scale:**
| Count in meeting | Severity | Action |
|----------------|----------|--------|
| 1-2 instances | Low | Note; don't flag |
| 3-5 instances | Medium | Flag with examples |
| 6+ instances | High | Flag + rewrite examples |

### Permission-Seeking Patterns

**Language signals:**
- "if that's okay with everyone", "if you don't mind"
- "I'm not sure if I should say this, but..."
- "I don't want to step on anyone's toes, but..."
- "Would it be alright if..."
- "I hope this isn't a silly question, but..."

**Appropriate use:** Once at the start of a meeting when genuinely asking to add agenda item.

**Flag when:** More than 1-2 instances in a single meeting, OR used before making a recommendation that should be stated confidently.

### Conflict Avoidance Patterns

**Language signals:**
- Topic change immediately after pushback (without addressing the concern)
- "Whatever works for the group"
- "I'm flexible" (when you actually have a preference)
- "Yeah, that makes sense" immediately followed by contradictory behavior
- Verbal agreement without named commitment: "Sure, yeah, absolutely" with no owner + date

**Detection:**
Look for: pushback from Speaker A → Speaker B changes topic without response, or agrees without action assignment.

### Rewrite Principles

| Original (hedged) | Rewrite (direct) |
|---|---|
| "Maybe we could consider looking into..." | "I recommend we [action]." |
| "I don't know if this makes sense, but..." | "Here's what I think: [clear position]." |
| "If that's okay, I was thinking..." | "I'd like to [action]. Does anyone see a problem with that?" |
| "I guess we could try..." | "Let's try [option]. If it doesn't work in 2 weeks, we'll revisit." |
| "Sort of like what you said, but maybe..." | "I have a different angle: [specific position]." |

---

## Module C: Filler Words — Full Dictionary

### Filler Word List

```
um, uh, er, ah (pause fillers)
like (non-comparative: "I was like, going to...")
you know (rhetorical)
right? (verbal tic, not genuine question)
so... (filler at start of response)
basically, essentially (when used loosely)
literally (hyperbolic: "I literally just...")
actually (softener: "actually, I think...")
obviously (condescending filler)
honestly (sincerity filler)
I mean (recalibration filler)
sort of, kind of (hedging as filler)
you know what I mean
at the end of the day
going forward
touch base, circle back
leverage (business jargon filler)
synergy, pivot, bandwidth (jargon fillers)
```

### Rate Calculation

```
Filler Rate = (Total fillers / Total words) × 100

Only flag to user if: Rate > 3 fillers per 100 words

For a 1,000-word speaking contribution:
- 30 fillers = 3% rate → flag
- 15 fillers = 1.5% rate → don't flag
```

### Contextual Spike Detection

Compare filler rate in different contexts within the same meeting:

- **With peers vs. senior stakeholders**: Rate spike when VP/director joins?
- **After negative feedback**: Rate increase after critical comment?
- **Unprepared topics**: Rate spike when asked off-agenda question?

Flag when filler rate increases >2× in specific context vs. baseline.

---

## Module D: Question Quality — Classification Rules

### Question Type Decision Tree

```
Is it answerable with Yes/No?
├── Yes → CLOSED
└── No → Is the answer embedded in the question?
    ├── Yes → LEADING ("Wouldn't it be better to...?")
    └── No → Is it seeking clarification?
        ├── Yes → CLARIFYING ("When you say X, do you mean Y?")
        └── No → Does it reference something previously said?
            ├── Yes → BUILDING ("Following on Sarah's point about X...")
            └── No → OPEN GENUINE ("What are the risks we haven't considered?")
```

### Quality Benchmark

| Ratio | Assessment |
|-------|-----------|
| Open genuine + Clarifying + Building > 60% | Strong listening and engagement |
| Closed questions > 60% | May be interrogating rather than exploring |
| Leading questions > 20% | Seeking confirmation, not information |
| Zero open genuine questions | Missing exploration entirely |

### Listening Quality Indicators

**Strong listening signals:**
- "Building on what [Name] said earlier..."
- Paraphrasing before responding: "If I understand correctly, you're saying..."
- Referencing specific numbers or details from earlier in the meeting
- Asking a follow-up question that only makes sense if they heard the prior answer

**Poor listening signals:**
- Asking for information already shared in the meeting
- Response doesn't reference what was just said
- Waiting to speak rather than listening (detectable by: immediately disagreeing without paraphrasing)
- Asking same question as someone asked 10 minutes ago

---

## Module E: Facilitation — Detailed Rubric

### Agenda Adherence

| Rating | Criteria |
|--------|---------|
| Strong | Met >80% of agenda items; any deviation was productive |
| Adequate | Met 60-80% of agenda items; some off-topic time |
| Weak | Met <60% of agenda; significant rabbit holes |

Rabbit hole detection: >10 consecutive turns on a topic that wasn't on the agenda.

### Decision Clarity Test

For every decision made in the meeting, test:
```
✅ "[Owner name] will [specific action] by [date]"
❌ "We'll figure that out later"
❌ "Someone should look into this"
❌ "Let's discuss next time"
```

Count: decisions with owner + action + date vs. total decisions made.
Target: 100% of decisions have all three elements.

### Inclusion Scoring

| Participant | % of words | Status |
|-------------|-----------|--------|
| Speaking ≥15% | — | Included |
| Speaking 5-15% | — | Minimal participation |
| Speaking <5% | — | Flag: excluded or disengaged |

If facilitator controls who speaks: note whether they called on quieter participants.

### Parking Lot Discipline

Parking lot = capturing off-topic items without derailing the current discussion.

Good facilitation: "Good point — let's put that in the parking lot and come back to it at the end."
Missing facilitation: Discussion goes 5+ minutes off-agenda with no redirect.

---

## Module F: Sentiment & Energy — Detection Guide

### Sentiment Markers

**Positive markers:**
- "Great idea", "exactly", "love that", "that's exactly what we need"
- Agreement + expansion: "Yes, and..."
- Enthusiasm: "I'm excited about this", "this is promising"

**Negative markers:**
- "I'm not sure about that", "that concerns me", "I disagree"
- Qualification: "but...", "however...", "on the other hand..."
- Deflection: "I'll have to think about it", "let's revisit"

**Neutral markers:**
- Information sharing without evaluation
- Process questions: "When is the deadline?", "Who's responsible?"

### Energy Drop Detection

Compare turn characteristics in second half of meeting vs. first half per speaker:

| Signal | Threshold |
|--------|-----------|
| Average turn length decreases | >40% reduction |
| More closed responses | Shifting from elaboration to yes/no |
| Fewer questions asked | Question rate drops by >50% |
| Slower response initiation | Pauses become longer (if timestamp resolution allows) |

**Flag when:** Energy drop correlates with specific event (critical feedback, stakeholder entry, topic change).
