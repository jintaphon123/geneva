---
name: competitive-intel
argument-hint: "[competitor name] or 'landscape' for full mapping / 'vs-page' to build comparison page"
context: fork
description: >
  Competitive intelligence covering systematic competitor tracking, battlecards,
  positioning maps, market analysis, deep product teardowns, and SEO comparison pages.
  Produces feature comparison matrices, SWOT analyses, win/loss frameworks, "vs competitor"
  SEO pages, "alternatives to" pages, and actionable competitive strategy.

  Auto-invoke when Bond asks: competitor analysis, who are we up against, battlecard,
  competitive positioning, win/loss, market positioning, competitive landscape,
  competitor launched X, how do we compare, competitive teardown, market mapping,
  vs competitor page, comparison page, alternatives to X, we compare to X.
---

# Competitive Intelligence

Systematic competitor knowledge that drives real decisions — not obsession.
Two modes: ongoing tracking (pulse) and deep teardown (one-time).

## Context Auto-Load

Read `context/work.md` before responding.
Bond's ventures: Second Brain (startup), Impact Arena Condo (rental OTA), TW EV (paused).
Frame competitive analysis for the relevant venture.

---

## Mode Detection

| Input | Mode |
|---|---|
| "Analyze [competitor]", "deep dive on X", quarterly review | **Teardown** — full structured analysis |
| "What did X ship?", "battlecard", "track competitor", ongoing monitoring | **Pulse** — tracking + quick output |

---

## Mode 1: Teardown (Deep Analysis)

### Step 1 — Identify Scope
List 2–4 competitors. Confirm primary focus. Define: direct (same ICP, same problem) vs. indirect (same budget, different solution) vs. future (adjacent space, funded).

### Step 2 — Collect Data (minimum 3 sources per competitor)
- **Website:** Pricing tiers, feature lists, CTAs, customer logos (→ ICP signals), trust badges
- **Reviews (G2, Capterra, App Store):** Praise (defend), Feature requests (opportunity gaps), Complaints (your advantage)
- **Job postings:** Engineering volume (scaling signal), tech stack mentions, data/ML roles (→ AI features incoming)
- **SEO signals:** Top keywords, publishing cadence, which pages rank
- **Social/PR:** Recent announcements, funding, partnerships

### Step 3 — Score (12 Dimensions, 1–5)

| # | Dimension | 1 (Weak) | 3 (Average) | 5 (Best-in-class) |
|---|---|---|---|---|
| 1 | Features | Core only | Solid | Comprehensive + unique |
| 2 | Pricing | Confusing | Market-rate | Transparent, flexible |
| 3 | UX | High friction | Functional | Delightful |
| 4 | Performance | Slow | Acceptable | Fast, reliable |
| 5 | Docs | Sparse | Decent | Comprehensive |
| 6 | Support | Email only | Chat + email | 24/7 fast |
| 7 | Integrations | 0–5 | 6–25 | 26+ |
| 8 | Security | None | SOC2 claimed | SOC2 Type II |
| 9 | Scalability | No enterprise | Mid-market | Enterprise-grade |
| 10 | Brand | Generic | Decent | Strong, differentiated |
| 11 | Community | None | Forum/Slack | Active, vibrant |
| 12 | Innovation | No releases | Quarterly | Frequent, meaningful |

**Advanced market-level frameworks (Porter's Five Forces, Blue Ocean Canvas):** → `references/analysis-frameworks.md`

### Step 4 — Generate Outputs

**Feature Comparison Matrix:** Your product vs. 2–3 competitors, scored 1–5 per feature.

**Positioning Map (2×2):**
Choose axes that show YOUR differentiation (Price vs. Feature Depth; SMB vs. Enterprise; Easy vs. Configurable).
Place each competitor. Bubble size = market share / funding.

**SWOT (per competitor):**
- Strengths: Where do they win? What do customers love?
- Weaknesses: Where do they lose? What do customers complain about?
- Opportunities (for us): What gap can we exploit?
- Threats (to us): What could they do that would hurt us?

**Action Items:**
| Horizon | Examples |
|---|---|
| Quick wins (0–4 wks) | Add comparison page, fix messaging gap |
| Medium-term (1–3 mo) | Build feature that appears in their weakness data |
| Strategic (3–12 mo) | Enter segment they're ignoring |

---

## Mode 2: Pulse (Ongoing Tracking)

### 8 Tracking Dimensions

| Dimension | Sources | Cadence |
|---|---|---|
| Product moves | Changelog, reviews, Twitter | Monthly |
| Pricing changes | Pricing page, sales intel | Triggered |
| Funding | Crunchbase, press | Triggered |
| Hiring signals | LinkedIn job postings | Monthly |
| Partnerships | Press releases, co-marketing | Triggered |
| Customer wins | Case studies, review sites | Monthly |
| Customer losses | Win/loss interviews | Ongoing |
| Messaging shifts | Homepage, ad library | Quarterly |

### Triggered Response Times
- Competitor raises funding → assess within 48 hours
- Major feature launch → product + sales response within 1 week
- Pricing change → analyze and respond within 1 week

---

## Win/Loss Analysis

Highest-signal competitive data. Run after every significant lost deal or churned customer.

**Interview questions:**
1. "Walk me through your evaluation process"
2. "Who else were you considering?"
3. "What were the top 3 criteria?"
4. "Where did we fall short?"
5. "What was the deciding factor?"
6. "What would have changed your decision?"

**Aggregate monthly:** Win reasons (ranked), loss reasons (ranked), competitor win rates by segment.

---

## Battlecard Format (per competitor)

```
## [Competitor Name] Battlecard

Threat level: LOW / MEDIUM / HIGH / CRITICAL
Our win rate vs them: [X%]

**Their pitch:** [1 sentence what they say]
**Their real strength:** [what they actually do well]
**Their real weakness:** [what customers actually complain about]

**When we win:** [specific conditions]
**When they win:** [specific conditions]

**Key objection handles:**
- "They have X feature" → [response]
- "They're cheaper" → [response]
- "They're more established" → [response]

**Landmines to avoid:** [what not to say]
```

---

## Balance: Intelligence Without Obsession

**Over-tracking signs:** Roadmap driven by "they just shipped X", pricing starts with "well they charge X", team morale drops when competitors fundraise.

**Under-tracking signs:** AEs blindsided on calls, missed major launches, pricing unchanged 12+ months despite market moves.

**Right posture:** Know competitors well enough to win. Don't let them set your agenda. Roadmap led by customer problems, informed by competitive gaps.

---

---

## Mode 3: SEO Comparison Pages

High-intent SEO content that captures users actively comparing alternatives. Two formats: "vs" pages and "alternatives" pages.

### Format 1: "[Brand] vs [Competitor]" Page

**URL pattern:** `/[your-brand]-vs-[competitor]/`
**Target keyword:** "[brand] vs [competitor]" — high commercial intent, clear buyer stage

**Page structure:**
```
H1: [Brand] vs [Competitor]: Which is right for you? (or "A real comparison")

TL;DR box (top of page — get cited by AI search):
"[Brand] is best for [specific use case]. [Competitor] is better for [different use case]. Choose based on [key deciding factor]."

Section 1: Quick comparison table
[Feature | Your brand | Competitor | Who wins]

Section 2: Where [Your brand] wins
[2-3 specific advantages with evidence — not marketing claims]

Section 3: Where [Competitor] wins (BE HONEST)
[1-2 things they genuinely do better — builds trust, not weakness]

Section 4: Who should choose [Your brand]
[Specific ICP — be narrow. "People who X" not "everyone"]

Section 5: Who should choose [Competitor]
[Narrow ICP for the competitor — honest positioning]

FAQ: "Is [Brand] cheaper than [Competitor]?" / "Can [Brand] replace [Competitor]?"

CTA: "Try [Brand] free — see for yourself"
```

**Honest positioning rule:** If you lie about competitor weaknesses, people who switched will churn immediately and leave negative reviews. Acknowledge their strengths. Win on specificity of fit.

### Format 2: "Best alternatives to [Competitor]" Page

**URL pattern:** `/alternatives-to-[competitor]/`
**Target keyword:** "alternatives to [competitor]" — users already unhappy with competitor

**Page structure:**
```
H1: Best [Competitor] alternatives in [Year]

Opening (AI-extractable definition block):
"Looking for [Competitor] alternatives? The top alternatives are [list your brand + 3-4 others]. [Your brand] is best for [ICP]. Here's the full comparison."

For each alternative (including yours):
[Name | Best for | Price | Key difference from Competitor]

Section: Why people leave [Competitor]
[Top 3 complaints from reviews — cited from G2/Capterra. Be specific.]

Section: Why [Your brand] is the best alternative for [specific use case]
[Your strongest differentiator — with proof]

FAQ: "Is [Your brand] free?" / "How does [Your brand] compare to [Competitor]?"
```

**SEO note:** Listing other alternatives (competitors of the competitor) signals objectivity and gets cited by AI search. Don't be the only option listed — rank them honestly.

---

## Output Artifacts

| Request | Output |
|---|---|
| "Analyze [competitor]" | Full teardown: scorecard + SWOT + positioning map + action plan |
| "Battlecard for [competitor]" | One-page pre-call battlecard — use `references/battlecard-template.md` |
| "Competitive landscape" | 2x2 map + tier-1/tier-2/tier-3 competitor list |
| "What did [competitor] ship?" | Pulse update + implication analysis |
| "Why are we losing to X?" | Win/loss analysis framework + interview questions |
| "vs page for [competitor]" | Full "[Brand] vs [Competitor]" page structure with honest positioning |
| "Alternatives page for [competitor]" | "Best alternatives to [competitor]" page structure |

## Quality Gate (Teardown mode only)

After completing Steps 1–4, run the quality check from `references/teardown-quality-check.md`
before delivering output. All 7 checks must pass. If any fail: gather missing data or flag explicitly.

## References

- `references/battlecard-template.md` — pre-call battlecard format (fill per competitor)
- `references/teardown-quality-check.md` — 7-point quality gate for Teardown mode
- `references/analysis-frameworks.md` — Porter's Five Forces, Blue Ocean ERRC grid, weighted Feature Comparison Matrix

## Language Rule

Match Bond's input language. External artifacts (sales battlecards, board slides) → English.
