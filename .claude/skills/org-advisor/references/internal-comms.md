# Internal Communications — Formats, Frameworks & Anti-Patterns

## Document Type Selection

| Situation | Use |
|-----------|-----|
| Weekly team update to leadership | 3P Update |
| Company-wide news, milestones, announcements | Company Newsletter |
| Project status for stakeholders | Status Report |
| Something went wrong, explaining impact | Incident/Crisis Communication |
| Rolling out an org change | Change Management Communication (see ADKAR in SKILL.md) |

---

## 3P Update (Progress / Plans / Problems)

**When to use:** Weekly team update to manager or leadership. 30-60 seconds to read.

**Format:**
```
[emoji] [Team Name] (Date Range — e.g., Apr 28 – May 1)

Progress: [1-3 sentences of accomplishments — shipped, milestones hit, tasks completed]

Plans: [1-3 sentences of next week's priorities]

Problems: [1-3 sentences of blockers — staffing gaps, bugs, external dependencies, decisions needed]
```

**Rules:**
- Data-driven: include specific metrics when available ("shipped feature X to 2,000 users")
- No vague language: "made progress on" → say what specifically was done
- Problems = real blockers only; not every difficulty counts
- Team-level granularity: don't list individual tasks
- Reading time target: ≤45 seconds

**Example:**
```
🚀 Product Engineering (Apr 28 – May 2)

Progress: Shipped payment webhook integration to production. Fixed 3 P1 bugs from last week's release. Onboarding conversion improved from 42% to 51% after signup flow change.

Plans: Complete Stripe billing migration by Thursday. Start API rate limiting implementation. Tech interview for senior backend role on Tuesday.

Problems: Auth service latency spiked after the Monday deploy — root cause identified (connection pool), fix in review. Need design approval on notification system before engineering can proceed.
```

---

## Company Newsletter

**When to use:** Bi-weekly or monthly all-company communication. 20-25 bullet points. Distributed via Slack + email.

**Audience:** Entire company. Only include information relevant to ≥50% of the team.

**Format:**
```
:megaphone: Company Newsletter — [Date]

:dart: Progress on Priorities
- [Company-level milestone or significant achievement]
- [Another major progress point]

:loudspeaker: Announcements
- [New hire joining — name, role, start date]
- [Policy change or process update]

:trophy: Wins This Week  
- [Customer story, deal closed, product milestone]

:calendar: Upcoming
- [Company event, milestone approaching, deadline]

:heart: Team Spotlights
- [Recognition of specific team or person]
```

**Style rules:**
- "We" tense — you are part of the company, not reporting on it
- Active voice: "We shipped" not "The feature was shipped"
- 1-2 sentences per bullet — no paragraphs
- Include links (Drive doc, Slack message, PR) when relevant
- Professional but human — not corporate-speak

**Exclusions (don't include):**
- Team-specific details that don't affect others → use 3P instead
- Individual task completion (too granular)
- Information already communicated in dedicated channels
- Information relevant to <3 people

---

## Status Report

**When to use:** Project status update to stakeholders, investors, or cross-functional partners.

**Format:**
```
## [Project Name] — Status Update — [Date]

**Status:** 🟢 On Track / 🟡 At Risk / 🔴 Off Track

**Summary (2 sentences):**
[What's happening and whether we're on track]

**Progress This Period:**
- [Specific milestone or deliverable completed]
- [Metric movement]

**Next Steps:**
- [Next milestone — owner — due date]

**Blockers:**
- [Blocker — who needs to act — timeline to resolve]

**Decisions Needed:**
- [Decision — from whom — by when]
```

**Status color rules:**
- 🟢 On Track: All milestones on time, no blockers threatening delivery
- 🟡 At Risk: 1-2 blockers that could delay if not resolved in 1 week
- 🔴 Off Track: Milestone already slipped or blocker with no clear resolution path

---

## Crisis & Incident Communication

**When to use:** Something broke, a commitment was missed, or bad news needs to reach the team or customers.

**Internal incident format:**
```
## Incident Update — [System/Area] — [Date Time]

**Status:** Ongoing / Resolved

**What happened:** [Plain language description — no technical jargon for non-technical audience]

**Impact:** [Who was affected, how many users, what they experienced]

**Root cause:** [Brief — "under investigation" is acceptable early]

**Action taken:** [What has been done so far]

**Next steps:** [What will happen in the next X hours/days]

**Point of contact:** [Name + how to reach them]
```

**Tone guidelines for crisis comms:**
- Factual, not defensive
- No blame language ("the team made an error" not "Person X caused this")
- Solution-forward: lead with what you're doing about it
- Acknowledge impact directly — don't minimize
- Commit to specific next update time: "We'll update by 3pm"

**What NOT to do:**
- Don't delay communicating while trying to fully understand the situation
- Don't use passive voice to obscure responsibility
- Don't over-explain technical details to business stakeholders
- Don't make promises you can't keep

---

## Change Management Communication

When rolling out any significant change to the team, follow ADKAR (in org-advisor SKILL.md).

**Change announcement template:**
```
Subject: [What is changing]

We're making a change to [area], and I want to explain why and what it means for you.

WHAT is changing:
[Clear, specific statement of the change]

WHY we're changing:
[Honest reason — don't sugarcoat, but don't alarm unnecessarily]
[Include data or context that led to this decision]

WHAT stays the same:
[Reassure on continuity — what they don't need to worry about]

WHAT you need to do:
[Specific actions required, if any — with timeline]

TIMELINE:
[When this change takes effect]

QUESTIONS:
[How to ask questions — Slack channel, office hours, email]

I'm happy to talk through this with anyone. [How to reach you]
```

**Change communication anti-patterns:**
| Anti-Pattern | Problem | Fix |
|---|---|---|
| "We're excited to announce..." for bad news | Tone-deaf | Match tone to the actual situation |
| Burying bad news with good news | Undermines trust | Lead with the hard thing; then provide context |
| "This was a tough decision" without explanation | Empty phrase | Say what was considered and what was decided |
| Asking for feedback when decision is final | False participation | "I'm sharing this decision" vs "I'd like your input" |

---

## Communication Anti-Patterns (All Types)

| Anti-Pattern | Why It Fails | Better Approach |
|---|---|---|
| **Passive voice for accomplishments** | Hides who did the work | "We shipped X" not "X was shipped" |
| **Invented/unverified metrics** | Destroys credibility when discovered | Only include numbers you can verify |
| **Walls of text** | Key information buried | Lead with headline, then details |
| **Wrong format for audience** | Engineer update in newsletter format = noise | Match format to audience and cadence |
| **Batching bad news with good news** | Bad news gets buried or ignored | Communicate bad news separately and directly |
| **"We're working on it"** (without specifics) | Creates anxiety, not reassurance | "We expect to resolve by [time] because [reason]" |
| **Too long** | Not read | If it takes >2 minutes to read, cut it |

---

## Communication Cadence Reference

| Format | Audience | Frequency | Owner |
|--------|----------|-----------|-------|
| 3P Update | Manager / leadership | Weekly | Team lead |
| Company Newsletter | All company | Bi-weekly | CEO / comms |
| Status Report | Stakeholders | Weekly or bi-weekly | Project lead |
| Incident Update | Affected parties | As needed | On-call / eng lead |
| All-hands | All company | Monthly | CEO |
| Board Update | Board | Monthly/quarterly | CEO + CFO |
