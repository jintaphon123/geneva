---
name: meeting-analyzer
argument-hint: "[transcript file or paste transcript]"
description: >
  Meeting transcript analysis and communication coaching. Auto-invoke when user:
  uploads a meeting transcript (.vtt, .srt, .txt, .docx, .json, .md),
  asks about meeting analysis, speaking ratio, filler words, communication habits,
  interruptions, facilitation quality, how they come across in meetings,
  mentions Otter/Fireflies/Granola/Zoom transcripts, or asks to compare communication
  across multiple meetings.
---

# Meeting Analyzer

Analyzes meeting transcripts to surface speaking dynamics, communication patterns, and actionable coaching insights.

---

## Trigger Detection

Activate when:
- User uploads or pastes any meeting transcript (any format)
- User says: "analyze my meetings", "how do I come across?", "my speaking ratio", "filler words", "do I interrupt?"
- User mentions: Otter, Fireflies, Granola, Zoom transcript, Teams transcript

---

## Step 1: Ingest & Normalize

**Detect format:**

| Format | Parser |
|--------|--------|
| `.vtt` or `.srt` | Parse cue blocks: timestamp → speaker → text |
| Plain `.txt` | Look for `Name:` or `[Name]` speaker label patterns |
| `.md` | Strip formatting, treat as plain text |
| `.docx` | Extract text content |
| `.json` | Expect `{speaker, timestamp_sec, text}[]` (Otter/Fireflies format) |
| Pasted text | Detect speaker labels from line patterns |

**Extract for each turn:**
- Speaker name
- Start timestamp (seconds)
- Text content
- Duration (if available)

**If no speaker labels detected:**
→ Inform user: "No speaker labels found — I can analyze text patterns but not per-speaker metrics. For per-speaker analysis, re-export from your tool with speaker diarization enabled."
→ Continue with text-level analysis only.

**If user not identified:**
→ Ask: "Which speaker is you? (e.g., 'I'm Speaker A' or '[Your name]')"
→ Do not guess.

---

## Step 2: Run Analysis Modules

Run all applicable modules. Load detailed patterns from `references/analysis-modules.md`.

### Module A — Speaking Dynamics

For each speaker:
- Word count + percentage of total
- Turn count + average turn length (words)
- Longest monologue (duration/word count)
- Interruption count (turn starting within 2 seconds of prior turn ending)

**Red flags to flag immediately:**
| Signal | Threshold | Label |
|--------|-----------|-------|
| Dominance | One speaker >60% of words | "Dominating" |
| Facilitator disengagement | Organizer <15% of words | "Disengaged facilitator" |
| Excluded voice | Speaker <2% of words | "Voice not heard" |
| Monologue | Single turn >200 words or >60 seconds | "Extended monologue" |

### Module B — Conflict & Directness

Scan for hedging, permission-seeking, and conflict avoidance patterns.

**Pattern detection:**
- **Hedging:** "maybe", "kind of", "I guess", "sort of", "potentially", "I think it might"
- **Permission-seeking:** "if that's okay", "would it be alright", "I don't know if this makes sense but"
- **Deflection:** "whatever you think", "I'm flexible", "you know better than I do"
- **Conflict avoidance:** Topic change immediately after someone pushes back; agreement followed by inaction ("Sure, yeah, definitely" without commitment)

Rate each pattern: **Low** (1-2 instances), **Medium** (3-5), **High** (6+)

For High-severity patterns: provide rewrite example for each.
See `references/coaching-guide.md` for rewrite templates.

### Module C — Filler Words

**Filler dictionary:** um, uh, like (non-comparative), you know, actually (filler use), basically, literally (hyperbolic), right? (verbal tic), so yeah, I mean (filler use), kind of

**Threshold:** Only flag if >3 fillers per 100 words. Below that — not worth flagging.

Calculate: filler rate per speaker (fillers / total words × 100)

**Contextual spikes:** Check if filler rate increases when:
- Speaking to senior stakeholders
- Receiving negative feedback
- Answering unprepared questions

### Module D — Question Quality & Listening

**Classify each question:**
| Type | Definition | Example |
|------|-----------|---------|
| Closed | Yes/No answer invited | "Did you finish it?" |
| Leading | Embeds the answer | "Wouldn't it be better to...?" |
| Open genuine | Invites exploration | "What would make this better?" |
| Clarifying | Seeks understanding | "When you say X, do you mean...?" |
| Building | References prior contribution | "Following up on what Sarah said..." |

Good question ratio target: Open genuine + Clarifying + Building > 60% of all questions asked.

**Listening quality signals:**

Good listening:
- References something said earlier in the meeting
- Paraphrases before responding: "So what I'm hearing is..."
- Asks clarifying or building questions

Poor listening:
- Asks a question already answered earlier in the meeting
- Response doesn't connect to what was just said
- Restates own position without acknowledging others

### Module E — Facilitation (only if user is the meeting organizer)

**Run if:** User is meeting organizer OR user asks for facilitation feedback.

| Dimension | Good | Flag |
|-----------|------|------|
| Agenda adherence | Meeting follows stated agenda | >20% time off-topic |
| Time management | Meets or ends within 5 min of scheduled end | >15 min overrun |
| Inclusion | All participants speak ≥10% | Any speaker <5% |
| Decision clarity | Every decision: owner + action + date | "Let's figure it out" endings |
| Action items | Each item: who, what, by when | Vague action items |
| Parking lot | Off-topic items captured for later | Rabbit holes not flagged |

**Decision clarity test:** Does every decision stated in the meeting follow the format?
`"[Owner] will [specific action] by [date]"`

### Module F — Sentiment & Energy

- Track sentiment arc: Positive / Negative / Neutral markers across the meeting timeline
- Flag energy drops: When any speaker's turns become significantly shorter and less substantive compared to their earlier baseline
- Note correlation: Do energy drops follow certain events (stakeholder entering, critical feedback, specific topic)?

---

## Step 3: Generate Report

```markdown
# Meeting Insights Report

**Period:** [date or date range]
**Meetings analyzed:** [count]
**Total words:** [count]
**Your speaking share (avg):** [X%]

---

## Top 3 Findings

[Rank by impact. Each finding: 2-3 sentences + direct quote with timestamp]

1. **[Finding title]** — [Description]. Evidence: "[Quote]" ([Speaker], [timestamp])

---

## Detailed Analysis

### Speaking Dynamics
[Stats table per speaker + red flags flagged]

### Directness & Conflict Patterns
[Grouped by pattern type — severity + quote + rewrite]

### Verbal Habits
[Only if rate >3/100 words — filler rate + spike contexts]

### Listening & Questions
[Breakdown by question type % + specific examples of good/poor listening]

### Facilitation
[Only if applicable — dimension scores + specific gaps]

### Energy & Sentiment
[Arc description + energy drops with timestamps]

---

## Strengths
[3 specific things done well — with evidence quote and timestamp]

1. **[Strength]** — "[Quote]" ([timestamp])

---

## Growth Opportunities
[3 ranked by impact]

1. **[Opportunity]** — What to change: [specific]. Why: [impact]. Try next time: "[concrete alternative phrasing or behavior]"

---

## Comparison to Previous Period
[Only if prior analysis exists — delta on key metrics]
```

---

## Edge Cases

| Situation | How to handle |
|-----------|--------------|
| **No speaker labels** | Text-level analysis only; skip per-speaker metrics; suggest re-export with diarization |
| **Meeting <5 min or <500 words** | Analyze but caveat: "Short meeting — patterns may not be representative" |
| **Non-English transcript** | Note that filler dictionary is English-centric; focus on structural analysis (questions, decisions, facilitation) |
| **Single meeting** | Skip trend language ("you've been improving at...") — focus on this meeting only |
| **Multiple meetings uploaded** | Analyze corpus; include per-meeting breakdown + trend analysis |
| **User not identified** | Ask first; don't guess speaker identity |

---

## References

- `references/analysis-modules.md` — Detailed patterns, thresholds, and detection rules for all modules
- `references/coaching-guide.md` — Rewrite examples, decision clarity formula, output templates
