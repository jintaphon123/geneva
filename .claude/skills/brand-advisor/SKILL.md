---
name: brand-advisor
argument-hint: "'audit' to check existing brand / 'build' to create from scratch / 'psychology' for persuasion"
description: >
  Brand identity, voice, and marketing psychology for Bond's ventures. Covers brand
  voice guidelines, tone matrix, visual identity standards, behavioral science for
  persuasion, and brand consistency auditing.

  Auto-invoke when Bond asks: brand, brand voice, tone of voice, visual identity,
  brand guidelines, brand audit, how should we sound, what's our brand, style guide,
  marketing psychology, persuasion, cognitive bias in copy, loss aversion, social proof,
  anchoring, consistency check, does this sound on-brand.
---

# Brand Advisor

Builds and maintains brand identity systems. Applies behavioral science to copy and UX.

## Context Auto-Load

Read `context/work.md` and `context/me.md` before responding.
Bond's ventures: Second Brain (startup → non-tech users), Impact Arena Condo (rental OTA), TW EV (paused).
Each venture has distinct audiences and brand personalities — apply frameworks to the relevant venture.

---

## Mode Detection

| Input | Mode |
|---|---|
| "Audit our brand", "are we consistent?", "review this asset" | **Audit** — gap check against existing guidelines |
| "Build brand guidelines", "define our voice", "we have no brand" | **Build** — create system from scratch |
| "Psychology for this copy", "persuasion", "cognitive bias", "why isn't this converting?" | **Psychology** — behavioral science applied to asset |

---

## Mode 1: Brand Audit

Run against any asset (landing page, social post, pitch deck, email):

### Quick Audit Checklist
- [ ] Colors match approved palette (no off-brand variations)
- [ ] Typography: correct typeface + weight
- [ ] Body text meets contrast (WCAG AA: 4.5:1 minimum)
- [ ] Imagery style consistent with brand
- [ ] Tone matches defined voice attributes
- [ ] CTAs use brand-defined action language
- [ ] No prohibited styles or patterns

**Output:** Gap table — dimension / current state / should be / priority fix

---

## Mode 2: Brand Build

### Step 1 — Foundation (answer before designing)
1. What does the brand stand for? (Mission in 1 sentence)
2. Who is the primary audience? (Demographic + psychographic + pain point)
3. Brand personality: choose 3 adjectives (e.g., bold / technical / approachable)
4. Reference tier: 3 brands outside your category that "feel right"
5. Anti-brief: 3 brands that feel wrong and why

### Step 2 — Voice & Tone Matrix

| Context | Tone | Do | Don't |
|---|---|---|---|
| Marketing copy | Energetic, direct | "Your AI brain that never forgets" | "Our platform optimizes information management" |
| Product UI | Clear, calm | "Saved. 12 notes synced." | "Your content has been successfully processed" |
| Error messages | Calm, helpful | "Something went wrong. Refresh and try again." | "An unexpected error occurred (ERR_4XX)" |
| Support docs | Patient, precise | "Click Settings → Privacy → Enable Context" | "Navigate to the settings section" |

### Step 3 — Visual Identity System

| Element | Decision | Rule |
|---|---|---|
| Primary color | Hex + rationale | Must pass WCAG AA contrast |
| Secondary palette | 2-3 supporting | Complement, don't compete |
| Typography | Heading + body pair | Heading: personality; body: readability |
| Spacing base | 8px grid | Consistency across components |
| Photography | 3 adjective style description | Real people vs abstract; bright vs moody |

### Step 4 — Output
→ Use `references/brand-voice-template.md` as the final brand mini-doc format

---

## Mode 3: Marketing Psychology

Apply behavioral science to increase persuasion in copy, UX, or pricing.

### Most-Used Models

**For conversion:**
- **Loss Aversion** — People feel losses 2× more than gains. "Never lose context again" beats "Always keep context."
- **Social Proof** — Show customer count, logos, or testimonials before asking for action.
- **Anchoring** — Show a higher/premium option first; your target price feels smaller by comparison.
- **Scarcity** — Limited availability increases desire — but only if real. Fake urgency destroys trust.
- **Decoy Effect** — Add a dominated middle tier to make your target plan feel like the obvious choice.

**For copy:**
- **Specificity** — "Cut reporting from 4 hours to 15 minutes" beats "save time."
- **Reciprocity** — Give value first (free guide, free audit, free tool). People feel compelled to return.
- **Framing** — "95% uptime" vs "down 18 days/year." Same fact. Choose deliberately.
- **Endowment Effect** — Let people own something before paying (free trial, saved progress). Loss aversion activates once they've used it.
- **IKEA Effect** — People value what they help build. Guided setup > automatic setup for activation.

**Quick reference by goal:**
| Goal | Models to Apply |
|---|---|
| Landing page conversion | Loss Aversion, Social Proof, Anchoring, Specificity |
| Pricing page | Charm Pricing ($49 not $50), Decoy Effect, Good-Better-Best framing |
| Email engagement | Reciprocity, Zeigarnik Effect (open loops), Goal-Gradient |
| Onboarding activation | IKEA Effect, Goal-Gradient, Default Effect |
| Reduce churn | Endowment Effect, Sunk Cost awareness, Switching Cost framing |
| Referral program | Reciprocity, Social Proof, Network Effects |

---

## Quality Check (Mini — 90/100 threshold)

Before delivering, self-score across 4 dimensions (25 pts each):
1. **Completeness** — all sections requested are present?
2. **Specificity** — implementable spec vs. abstract advice?
3. **Brand fit** — recommendations match Bond's specific venture context?
4. **Actionability** — can Bond execute without follow-up questions?

If < 90: fix, then deliver. Flag any remaining weak areas explicitly.

---

## Output Artifacts

| Request | Output |
|---|---|
| "Audit our brand" | Gap table: dimension / current / target / priority |
| "Build brand guidelines" | Brand mini-doc → `references/brand-voice-template.md` |
| "Tone of voice for Second Brain" | Voice matrix (4 contexts × do/don't) + 5 example phrases |
| "Apply psychology to this page" | 3-5 applicable models + concrete before/after copy rewrites |
| "Why isn't this converting?" | Behavioral audit: models violated + specific fixes |
| "Pricing psychology audit" | Tier-by-tier analysis: charm pricing, decoy, anchoring |

## NotebookLM Deep Dive

- **Alex Hormozi General** (`cea608bb`) — offer framing, value proposition, direct marketing psychology

Trigger: "deeper brand or persuasion framework → `/consult [specific question]`"

## Language Rule

Match Bond's input language. Brand guidelines and formal documents → English.
