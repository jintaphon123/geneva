# Meeting Coaching Guide — Rewrites, Templates & Edge Cases

## Rewrite Examples by Pattern

### Hedging → Direct

| Original | Rewrite |
|----------|---------|
| "Maybe we could consider looking into a different approach?" | "I recommend we try [specific approach]. Here's why: [reason]." |
| "I don't know if this makes sense, but I was thinking..." | "Here's my proposal: [clear statement]. Does anyone see a flaw?" |
| "Sort of like what you were saying, but maybe slightly different?" | "I have a different take: [clear position]. It differs from yours in [specific way]." |
| "It might potentially be worth exploring..." | "Let's explore [option]. I'll own a quick analysis by [date]." |
| "I'm not sure if this is relevant, but..." | "[Your point directly]. If it's off-topic, tell me and I'll hold it." |

### Permission-Seeking → Confident

| Original | Rewrite |
|----------|---------|
| "If that's okay, I was thinking we should..." | "I'd like to [action]. Any objections?" |
| "I hope this isn't a silly question, but..." | "[Ask the question directly without preface]" |
| "I don't want to step on anyone's toes, but..." | "[Make your point directly]" |
| "Would it be alright if we tried..." | "Let's try [approach]. We can reassess in [timeframe]." |

### Conflict Avoidance → Direct Disagreement

| Original | Rewrite |
|----------|---------|
| "Yeah that's great..." (then changes subject) | "I actually see it differently. [Your position]. How do you think about [their concern]?" |
| "Whatever you think is best." | "I have a preference: [your choice] because [reason]. What's your thinking?" |
| "I'm flexible on that." | "I'd lean toward [option], but I want to understand your reasoning first." |
| Vague agreement: "Sure, yeah, definitely" | "I'll own that. I'll have [specific output] done by [date]." |

---

## Decision Clarity Formula

Every decision should end with:

```
"[Owner's name] will [specific action] by [specific date]."
```

**Examples:**

✅ Strong: "Sarah will send the revised proposal to the client by Thursday at 5pm."
✅ Strong: "We're going with Option B. James owns the implementation, first milestone by next Friday."

❌ Weak: "Let's move forward with the idea."
❌ Weak: "Someone should look into this."
❌ Weak: "We'll figure out the details offline."

**Test:** Can a person who wasn't in the meeting read this and know exactly what happens next, who does it, and when?

**Facilitation intervention:** When a meeting is ending without clear owners: "Before we close — for each action item, can we name one owner and a due date?"

---

## Report Tone & Style Guidelines

### Voice

- Direct coaching voice: address the person, not describe them in 3rd person
- Use "you" not "the speaker" in the feedback section
- Concrete, not vague: "You asked 8 closed questions and 1 open genuine question" not "your questions could be more open"
- Evidence-based: every finding supported by a direct quote with timestamp

### Do Not

- Don't use generic platitudes: "great awareness", "keep it up"
- Don't diagnose intent: "you seemed nervous" → "your filler rate increased from 2% to 7% after the VP joined"
- Don't moralize: avoid "you should be more confident"
- Don't soften findings to the point of uselessness

### Growth Opportunity Format

Each growth opportunity should follow this structure:

```
**[Specific behavior to change]**

What to change: [concrete behavior, not vague instruction]
Why: [impact — what it costs you or the meeting]
Try next time: "[Verbatim alternative phrasing or action]"
```

Example:
```
**Replace hedging with direct proposals**

What to change: Before making a suggestion, remove the hedge ("maybe", "I was thinking", "kind of"). State the recommendation directly.
Why: Hedging signals uncertainty and invites others to override your idea before evaluating it. Your ideas were solid — they just weren't landing with authority.
Try next time: Instead of "Maybe we could potentially consider a different timeline?", say: "I recommend we push the deadline to the 20th. Here's why: [reason]."
```

---

## Strengths Identification

For the Strengths section, look for:

1. **Strong question quality:** If Open genuine + Clarifying + Building questions exceed 60% — name it specifically with an example
2. **Good listening signals:** If speaker referenced prior points or paraphrased before responding — name the instance
3. **Clear decision-making:** If speaker assigned clear owners + dates — quote the specific decision
4. **Facilitating inclusion:** If speaker called out quiet participants or used parking lot effectively
5. **Energy maintenance:** If speaker maintained consistent turn length and engagement throughout
6. **Direct disagreement:** If speaker disagreed respectfully and specifically — this is a strength

Format:
```
1. **[Strength label]** — "[Direct quote as evidence]" ([timestamp])
   [One sentence explaining why this matters]
```

---

## Edge Case Handling

### No Speaker Labels

**Detection:** No consistent "Name:" or "[Name]" pattern in transcript.

**Response to user:**
> "I couldn't find speaker labels in this transcript. I can analyze text-level patterns (question quality, decision clarity, filler words, sentiment arc), but I won't be able to give per-speaker metrics.
>
> For per-speaker analysis next time, re-export from your recording tool with speaker diarization enabled:
> - Otter.ai: Auto speaker labels → enable in settings
> - Fireflies: Transcript → Speaker view
> - Zoom: Enable speaker identification in recording settings
> - Granola: Uses system audio → speaker labels depend on your system setup
>
> Continuing with text-level analysis..."

### Meeting Under 5 Minutes or 500 Words

**Response prefix:**
> "This is a short meeting (under 5 minutes). The patterns I identify may not be representative of your overall communication style. Take these findings with more skepticism than you would for a longer session."

### Non-English Transcript

**Response:**
> "This transcript appears to be in [language]. My filler word dictionary is English-centric, so I'll skip that module.
>
> I can still analyze: question types (structural), facilitation quality (decision clarity, inclusion), sentiment arc (broad markers), and speaking dynamics (word share, turn patterns).
>
> Proceeding with structural analysis..."

### Single Meeting vs. Corpus

- **Single meeting:** Do not use trend language ("you've been improving at...", "compared to before...")
- **Multiple meetings:** Include trend section + note which meetings are in the corpus

### User Not Identified

Before proceeding with per-user analysis:
> "Which speaker is you? (e.g., 'I'm Speaker 2' or 'My name is Bond in the transcript')"

Do not guess. Without this, provide general meeting analysis only.

---

## Output Template Quick Reference

```markdown
# Meeting Insights Report

**Period:** [date or date range]
**Meetings analyzed:** [count]
**Total words:** [count]
**Your speaking share (avg):** [X%]

---

## Top 3 Findings

1. **[Title]** — [2-3 sentences]. Evidence: "[Quote]" ([Speaker], [timestamp])
2. **[Title]** — [2-3 sentences]. Evidence: "[Quote]" ([Speaker], [timestamp])
3. **[Title]** — [2-3 sentences]. Evidence: "[Quote]" ([Speaker], [timestamp])

---

## Detailed Analysis

### Speaking Dynamics
[Stats table] + [Red flags if any]

### Directness & Conflict Patterns
[Patterns found, severity, rewrite examples for High severity]

### Verbal Habits
[Only if >3/100 words — filler rate, contextual spikes]

### Listening & Questions
[Question type breakdown %, good/poor listening examples]

### Facilitation
[Only if applicable — dimension scores, gaps]

### Energy & Sentiment
[Arc, energy drops, correlation to events]

---

## Strengths
1. **[Strength]** — "[Quote]" ([timestamp]) — [Why it matters]
2. **[Strength]** — "[Quote]" ([timestamp]) — [Why it matters]
3. **[Strength]** — "[Quote]" ([timestamp]) — [Why it matters]

---

## Growth Opportunities
1. **[Behavior to change]**
   What to change: [specific]
   Why: [impact]
   Try next time: "[verbatim alternative]"

2. **[Behavior to change]** ...
3. **[Behavior to change]** ...

---

## Comparison to Previous Period
[Only include if prior analysis exists]
| Metric | Previous | Current | Trend |
|--------|---------|---------|-------|
| [Metric] | [X] | [Y] | ↑/↓/→ |
```
