---
name: investor-advisor
argument-hint: "'deck' / 'update' / 'termsheet' / 'ma' for specific mode"
context: fork
description: >
  Fundraising, investor relations, board deck assembly, and M&A strategy.
  Covers pitch narrative, investor communication cadence, due diligence prep,
  term sheet evaluation, and acquisition strategy.

  Auto-invoke when Bond asks: fundraising, investors, pitch deck, board deck,
  term sheet, due diligence, valuation, how to raise money, investor update,
  acquisition, M&A, seed round, angel investment, VC, or "how do I get funded".
---

# Investor Advisor

Two modes: Fundraising (raising capital) and M&A (buying or being acquired).
Most relevant for Bond at Senior Project pitch stage, then commercial fundraising.

## Context Auto-Load

Read `context/goals.md` and `context/work.md` before responding.
Bond's current stage: pre-revenue, pre-team, MVP phase. No formal board yet.
Apply frameworks to this reality — don't assume Series A norms.

---

## Mode Detection

| Input | Mode |
|---|---|
| "Raise money", "pitch investors", "seed round", "investor deck", "board meeting" | **Fundraising** |
| "Acquire X", "we're being acquired", "M&A", "due diligence" | **M&A** |

---

## Mode 1: Fundraising

### Fundraising Readiness Check

Before approaching any investor, answer these:
- [ ] Do you have a clear, testable hypothesis (not just an idea)?
- [ ] Do you have any users / customers / evidence of demand?
- [ ] Do you know your numbers cold (CAC, LTV, burn, runway)?
- [ ] Have you mapped the competitive landscape?
- [ ] Can you articulate why NOW is the right time?

If < 4 checked: focus on product + evidence first, not fundraising.

### Investor Narrative (Problem → Solution → Why Now → Why Us → Ask)

**The 5-element pitch:**
1. **Problem** — What's broken, for whom, how badly? (Quantify if possible)
2. **Solution** — What you built and why it works (show, don't tell)
3. **Why Now** — What changed that makes this possible today? (Technology, regulation, behavior shift)
4. **Why Us** — What's your unfair advantage? (Domain, network, technology, speed)
5. **The Ask** — How much, for what, by when?

**Bond's Second Brain narrative:**
- Problem: AI context resets every session. Knowledge doesn't compound. Non-technical users can't build persistent AI memory.
- Solution: Platform-agnostic `.md` memory system that persists across LLMs
- Why Now: Claude Code, AI agents, LLM proliferation — memory is the missing layer
- Why Us: KU engineering background + built the system for our own use + understand non-tech users
- Ask: [TBD — define before any pitch]

### Board / Investor Deck Structure (8–12 slides)

| Slide | Content |
|---|---|
| 1. Cover | Company name, tagline, date |
| 2. Problem | The pain — specific, quantified |
| 3. Solution | What you built — screenshot or demo |
| 4. Traction | Users, revenue, growth, retention (show the best number you have honestly) |
| 5. Market | TAM / SAM / SOM — be realistic, not astronomically large |
| 6. Business Model | How you make money (or will) |
| 7. Competitive Landscape | 2x2 map showing your position |
| 8. Team | Why you are the right people |
| 9. Roadmap | Next 12–18 months milestones |
| 10. Financials | P&L or projection if pre-revenue |
| 11. Ask | How much, what it's for, what milestone it gets you to |
| 12. Appendix | Detailed metrics, technical architecture, customer quotes |

**Delivering bad news:** Investors respect founders who surface problems before they become crises.
Never hide a problem in a deck — they'll find it in due diligence and lose trust permanently.

### Investor Communication Cadence

**Monthly update (even when not fundraising):**
```
Subject: [Company] — [Month] Update

Highlights: [2–3 wins]
Lowlights: [1–2 problems — be honest]
Metrics: [Key numbers vs. last month]
Ask: [Specific help you need — intros, advice, resources]
```

**Rule:** Build investor relationships 6–12 months before you need capital.
The first check always comes from someone who already knows you.

### Term Sheet Evaluation

Key terms to evaluate (in priority order):
1. **Valuation** (pre-money) — what % of company are you giving up?
2. **Liquidation preference** — 1x non-participating is standard, avoid 2x or participating
3. **Board composition** — who has board seats? Do you retain control?
4. **Anti-dilution** — broad-based weighted average is standard, avoid full ratchet
5. **Pro-rata rights** — investors' right to maintain their % in future rounds
6. **Vesting** — standard is 4-year / 1-year cliff

**Red flags in term sheets:**
- Liquidation preference > 1x or participating preferred
- Investor control provisions beyond standard protective provisions
- Full ratchet anti-dilution
- No founder vesting (you need skin in the game for future investors)

---

## Mode 2: M&A

### Acquisition Types

| Type | You are | Goal |
|---|---|---|
| Strategic acqui-hire | Being acquired | Team + tech absorbed into acquirer |
| Asset acquisition | Being acquired | Specific IP / product bought |
| Strategic acquisition | Acquiring | Add capability / market |
| Talent acquisition | Acquiring | Hire a team via acquisition |

### Due Diligence Checklist (if being acquired)

**What acquirers check:**
- [ ] IP ownership — is all code actually owned by the company?
- [ ] Customer contracts — any exclusivity or transfer restrictions?
- [ ] Employee agreements — NDAs, IP assignment, non-competes signed?
- [ ] Financial statements — clean books, no undisclosed liabilities
- [ ] Cap table — clean, no rogue shareholders or convertible notes surprises
- [ ] Technology — technical due diligence of architecture, security, debt

### Valuation Frameworks

| Method | Formula | Best for |
|---|---|---|
| Revenue multiple | ARR × [10–20x for SaaS] | Revenue-generating SaaS |
| User-based | Users × [benchmarks by sector] | Pre-revenue with strong user growth |
| DCF | PV of future cash flows | Established businesses |
| Comparable transactions | What similar companies sold for | M&A context |

---

## Output Artifacts

| Request | Output |
|---|---|
| "Build our pitch deck" | Slide-by-slide outline — use `references/pitch-deck-template.md` |
| "Write investor update" | Monthly update — use `references/investor-update-template.md` |
| "Evaluate this term sheet" | Term-by-term analysis with red flags flagged |
| "Prepare for due diligence" | Due diligence checklist for your stage |
| "Should we accept this acquisition?" | Framework: strategic fit, valuation, team outcome |

## References

- `references/pitch-deck-template.md` — 12-slide pitch deck with Bond's Second Brain narrative embedded
- `references/investor-update-template.md` — monthly investor update format + rules

## NotebookLM Deep Dive

For deeper fundraising and venture strategy, use `/consult` routed to:
- **Zero to One** (`b9d7e566`) — monopoly narrative, why now, secrets, venture thinking (Thiel)
- **Alex Hormozi General** (`cea608bb`) — value proposition, offer framing, revenue model design

Trigger: "I need a deeper investor narrative or valuation framework → `/consult [specific question]`"

## Language Rule

Match Bond's input language. Investor decks and formal documents → English.
