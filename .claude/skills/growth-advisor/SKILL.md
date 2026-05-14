---
name: growth-advisor
argument-hint: "'churn' for retention / 'aso' for app store / 'free-tool' for SEO tool strategy"
description: >
  Retention, app store optimization, and free tool strategy for Bond's ventures.
  Covers churn prevention (cancel flows, save offers, dunning emails, win-back),
  app store optimization (ASO title/screenshots/keywords), and free tool SEO strategy
  (building tools that rank and generate leads).

  Auto-invoke when Bond asks: reduce churn, cancel flow, save offer, win-back
  campaign, dunning email, payment recovery, involuntary churn, user retention,
  keep users, app store optimization, ASO, app keywords, app screenshots,
  free tool SEO, build a free tool for leads, calculator tool, tool that ranks.
---

# Growth Advisor

Three modes (single-pass each): Churn Prevention / App Store Optimization / Free Tool Strategy.
Mini quality check: 90/100 threshold before delivery.

## Context Auto-Load

Read `context/work.md` before responding.
Bond's current retention context: Second Brain (future — prevent early churn once users exist), Impact Arena Condo (prevent guest cancellation on OTA platforms).

---

## Mode Detection

| Input | Mode |
|---|---|
| "Reduce churn", "cancel flow", "save offer", "win-back", "dunning", "payment failed" | **Churn Prevention** |
| "App store", "ASO", "app keywords", "screenshots", "app ranking" | **ASO** |
| "Free tool", "SEO tool", "build a calculator", "tool that ranks" | **Free Tool Strategy** |

---

## Mode 1: Churn Prevention

### Types of Churn
| Type | Cause | Solution |
|---|---|---|
| **Voluntary** | User decides to leave | Cancel flow + save offer |
| **Involuntary** | Payment failure | Dunning email sequence |
| **Passive** | User stops using but doesn't cancel | Re-engagement + activation nudge |

### Cancel Flow Design (5 stages)
```
Stage 1 — Pause offer: "Pause for 1 month?" (reduces cancellation ~20%)
Stage 2 — Downgrade offer: "Switch to Free plan?" (saves users who can't afford)
Stage 3 — Exit survey: "Tell us why you're leaving" (4 options max, 1 click)
Stage 4 — Save offer: Based on exit reason:
  - "Too expensive" → discount or extended trial
  - "Not using it" → offer onboarding help
  - "Missing feature" → roadmap preview
  - "Found alternative" → direct comparison + our advantage
Stage 5 — Confirmation: "Account cancelled. You can reactivate anytime."
```

### Dunning Sequence (involuntary churn — payment failed)
```
Day 0: Payment fails → send "We couldn't charge your card" (soft, no blame)
  - Link to update payment method
  - Retry in 3 days

Day 3: Retry + email "Action needed: your account"
  - Urgency: "Your access pauses in 4 days"
  - Direct link to update card

Day 7: Final retry + email "Last chance to keep your account"
  - Higher urgency, clear deadline
  - Offer: "Need help?" (live chat or reply)

Day 10: Payment final failure → downgrade or pause
  - Email: "Your account is paused"
  - Clear path to reactivate
```

### Win-Back Sequence (churned users)
```
Week 2 after churn: "We miss you" — no pressure, share what's improved
Week 6 after churn: Share biggest new feature or improvement
Month 3 after churn: Special reactivation offer (one-time discount)
Month 6+: Remove from win-back, move to dormant list
```

### Churn Impact Model
```
Monthly Revenue at Risk = MRR × Monthly Churn Rate
Annual Churn Cost = Monthly Revenue at Risk × 12

If churn rate is 5%/month:
  Net Revenue Retention = ~54% (annual)
  Goal: < 2%/month → NRR > 78%
```

---

## Mode 2: App Store Optimization (ASO)

### Core ASO Signals (iOS App Store + Google Play)
| Signal | Weight | What to Optimize |
|---|---|---|
| App title | Very high | Include primary keyword naturally |
| Subtitle / Short description | High | Include secondary keyword + value prop |
| Keywords field (iOS) | High | 100 chars, comma-separated, no spaces |
| Description | Medium | First 3 lines visible before "more" |
| Screenshots | High | First 3 screenshots = conversion rate |
| Ratings & reviews | Very high | Volume + recency + star average |
| Download velocity | High | Can't directly control — affect via launch |

### Title Formula
`[Brand Name]: [Primary Keyword] [Benefit]`
Example: "Second Brain: AI Memory for Work"

### Screenshot Strategy (6 screenshots)
```
Screenshot 1: Hero — biggest benefit in one line + app interface
Screenshot 2: Feature 1 — most-used or most-valued feature
Screenshot 3: Feature 2 — second differentiator
Screenshot 4: Social proof — ratings, user count, or testimonial
Screenshot 5: Feature 3 or use case
Screenshot 6: CTA — "Start for free" / "Download now"
```

### Review Generation Strategy
- In-app prompt: ask after a success moment (completed task, positive outcome) — NOT on first launch
- Never ask for 5 stars; ask "Do you love [app]?" → if yes → review prompt; if no → feedback form
- Respond to all reviews (shows engagement, influences algorithm)

---

## Mode 3: Free Tool SEO Strategy

Free tools generate leads because they rank for high-intent queries and collect emails via output delivery.

### Tool Selection Criteria
Good free tool ideas = tools that:
1. Solve a concrete problem (not "AI idea generator" — too vague)
2. Produce a specific output (a number, a report, a score)
3. Require an email to receive the output (optional but recommended)
4. Connect naturally to your paid product's value proposition

**Second Brain-relevant examples:**
- "AI Context Calculator" — how much context you lose vs. using persistent memory
- "Prompt Quality Scorer" — score your AI prompts for context completeness
- "Meeting Notes Summarizer" — paste notes, get structured summary (→ shows value of memory system)

### Tool Launch Playbook
```
1. Build MVP: single-purpose, instant output (< 5 minutes to use)
2. Landing page: H1 = "[Tool Name]" (keyword), explain exactly what it does
3. Embed tool on page: no separate URL needed
4. Email capture: optional — "Get results emailed to you"
5. Share: post to relevant communities (Reddit, Hacker News, Facebook Groups)
6. Build links: reach out to bloggers covering the topic for inclusion
7. Iterate: build 3-5 related tools → cross-link them for internal authority
```

### Ranking Strategy
- Target the keyword "[category] calculator" / "[category] tool" / "free [category] checker"
- Optimize the tool page like any SEO article (definition block, FAQ schema)
- Tools rank on: usefulness signal (time-on-page, repeat visits) + links

---

## Quality Check (Mini — 90/100 threshold)

Score across 4 dimensions (25 pts each):
1. **Specificity** — generic advice vs. implementable steps?
2. **Context fit** — recommendations match Bond's specific venture and stage?
3. **Completeness** — all requested elements covered?
4. **Actionability** — Bond can execute without follow-up?

If < 90: fix, then deliver. Flag any remaining weak areas explicitly.

---

## Output Artifacts

| Request | Output |
|---|---|
| "Reduce churn" | Cancel flow (5 stages) + save offer mapping + dunning sequence |
| "Win-back campaign" | 3-email win-back sequence with timing |
| "App store optimization" | Title + subtitle + keyword field + screenshot strategy |
| "Free tool SEO" | Tool idea selection + landing page spec + launch playbook |

## Language Rule

Match Bond's input language. App store copy → English (international standard). OTA content → Thai if targeting Thai market.
