---
name: gtm-advisor
argument-hint: "[product to launch] or 'pricing' for monetization / 'icp' for customer definition / 'referral' for referral program"
description: >
  Go-to-market strategy covering product launches, pricing design, monetization,
  channel selection, ICP definition, product positioning, referral program design,
  and price increase strategy.

  Auto-invoke when Bond asks: launch plan, go-to-market, GTM, pricing tiers,
  monetization, how to price this, price increase, packaging, freemium, value metric,
  Product Hunt, beta launch, early access, waitlist, feature release, announcement
  strategy, how to make money from this, ICP, ideal customer, who is our customer,
  customer profile, positioning statement, referral program, referral loop, word of mouth.
---

# GTM Advisor

Two modes: Launch (how to get to market) and Pricing (how to monetize it).
Often used together — a launch without pricing is incomplete.

## Context Auto-Load

Read `context/work.md` before responding.
Bond's current GTM priority: Second Brain MVP → KU team pitch → commercial launch.
Zero budget — every strategy must be executable with ฿0 paid spend.

---

## Mode Detection

| Input | Mode |
|---|---|
| "Launch plan", "Product Hunt", "how to announce", "beta", "waitlist" | **Launch Mode** |
| "Pricing", "how much to charge", "tiers", "value metric", "monetization" | **Pricing Mode** |
| "ICP", "ideal customer", "who is our customer", "positioning statement" | **ICP & Positioning Mode** |
| "Referral program", "referral loop", "word of mouth growth" | **Referral Mode** |
| Multiple topics together | Run all relevant modes — pricing + ICP before launch |

---

## Mode 1: Launch Strategy

### Launch Types
| Type | Scope | Channels | Timeline |
|---|---|---|---|
| Full product launch | New product to market | All ORB channels | 6–8 weeks prep |
| Major feature | Significant capability | Owned + borrowed | 2–4 weeks |
| Minor update | Incremental improvement | Owned only | 1 week |
| Product Hunt | Major launch event | Full playbook | 4–6 weeks prep |

### ORB Channel Strategy

**Owned** (you control, zero cost): Email list, blog, social profiles, in-app messaging, community
**Rented** (you pay, less control): Paid ads, sponsored content — Bond skips this at zero budget
**Borrowed** (partner's audience): Guest posts, podcast appearances, co-marketing, influencer

**Bond's zero-budget ORB priority:**
1. Owned: Email/LINE/community (most controllable)
2. Borrowed: KU network, engineering communities, maker spaces
3. Rented: Later, once revenue exists

### Phased Launch Framework

```
Phase 1 — Alpha (2–4 weeks)
  Target: 5–20 hand-picked users (KU classmates, trusted contacts)
  Goal: Find the top 3 things that break before public eyes see it
  Success: Users use it again without being asked

Phase 2 — Beta (2–4 weeks)
  Target: 20–200 users via waitlist + word of mouth
  Goal: Validate core value proposition, get first testimonials
  Success: Users recommend it without prompting

Phase 3 — Public Launch
  Target: Everyone in target ICP
  Goal: Capture attention, drive signups, establish positioning
  Success: Organic word-of-mouth begins
```

### Product Hunt Playbook (if applicable)
- Build hunter relationships 4–6 weeks before launch
- Collect 50+ emails of people to notify on launch day
- Schedule for Tuesday–Thursday (highest traffic)
- First comment = your story, not product description
- Engage every single comment launch day

### Launch Checklist

**Pre-launch (T-2 weeks):**
- [ ] Landing page live with clear value proposition
- [ ] Waitlist / signup flow tested end-to-end
- [ ] First 10 users confirmed for day-1 engagement
- [ ] Launch copy written for all channels
- [ ] Support/FAQ ready for common questions

**Launch day:**
- [ ] Publish simultaneously across all channels at 9am target timezone
- [ ] Personal outreach to warm contacts (not mass email)
- [ ] Respond to every comment/reply within 2 hours
- [ ] Share first metrics at end of day

**Post-launch (T+7 to T+30):**
- [ ] Comparison/alternatives page published
- [ ] Follow-up email to waitlist with results
- [ ] Identify top 3 users for testimonials
- [ ] Retarget with use-case specific content

---

## Mode 2: Pricing Strategy

### The Three Axes (lock in this order)

```
1. Value Metric → what do you charge for?
2. Packaging   → what's in each tier?
3. Price Point → how much?
```

Skipping to price point first is the most common pricing mistake.

### Value Metric Selection

The value metric scales with the customer's success. Good metrics grow naturally as they get more value.

| Metric type | Example | Good for |
|---|---|---|
| Per seat | $X/user/month | Team tools, collaboration |
| Usage-based | $X per API call | Infrastructure, AI tools |
| Outcome-based | $X per [result] | High-value B2B |
| Feature-gated | Free/Pro/Business tiers | Consumer + SMB |
| Flat rate | $X/month all-in | Simple tools, low ASP |

**For Second Brain:** Feature-gated tiers (Free = personal use, Pro = multi-LLM sync, Business = team)

### Packaging (Good–Better–Best)

| Tier | Contains | Target user | Goal |
|---|---|---|---|
| Free | Core value, limited | Individual, evaluator | Acquisition + word of mouth |
| Pro | Full value, single user | Power user | Primary revenue |
| Business/Team | Full value + collaboration | Team lead | Expansion revenue |

**Rules:**
- Free tier must deliver real value — not a trial, not crippled
- Pro should be an obvious upgrade (clear pain of staying free)
- Business should have at least one feature that only makes sense for teams

### Price Point Research

**Van Westendorp questions (ask 5+ potential customers):**
1. At what price is this too cheap to trust? (Floor)
2. At what price is this a bargain? (Ideal low)
3. At what price is this expensive but worth it? (Ideal high)
4. At what price would you not buy it? (Ceiling)

**Price point rule:** Most products are underpriced. Start at the high end of your range. You can discount; you can't easily raise.

**Competitor anchor:** Know competitor prices. Your price is a positioning statement.
- Price below → "budget option" (hard to shake)
- Price at parity → compete on features
- Price above → must be able to justify every extra baht

### Price Increase Strategy

If raising prices:
1. Announce value improvements first (give before you take)
2. Grandfather existing customers for 6–12 months
3. Explain the reason honestly ("we've added X, Y, Z")
4. Give 30–60 days notice minimum
5. Offer annual lock-in at current price before increase

---

---

## Mode 3: ICP & Positioning (April Dunford methodology)

The goal is to define who exactly benefits most from your product, then position it so that audience self-selects in.

### Step 1 — ICP Definition (3 attributes)

**Firmographic:** What kind of company / person are they?
- Company size, industry, geography, stage (for B2B)
- OR: demographic, job title, income level (for B2C/prosumer)

**Behavioral:** What do they DO that signals they're a fit?
- Tools they use, workflows they follow, content they consume
- Behaviors that correlate with needing your product

**Pain profile:** What specific problem are they actively trying to solve?
- The problem must be real (they're already trying to solve it, just badly)
- Must be solvable by your product (not just adjacent)

### Step 2 — Positioning Statement (Dunford Format)

```
For [ICP] who [behavioral trigger],
[Product] is a [market category]
that [key differentiator / unique capability].
Unlike [primary alternative],
[Product] [key advantage that matters to ICP].
```

**Example (Second Brain):**
```
For knowledge workers and founders who use multiple AI tools daily,
Second Brain is a persistent context system
that remembers everything across every AI conversation.
Unlike each AI's built-in memory,
Second Brain works across all LLMs simultaneously.
```

### Step 3 — Messaging Hierarchy

```
Category claim: [What category are we in? Define it your way.]
Primary differentiator: [The one thing that makes us different from everything else]
Proof points (3-5): [Specific, verifiable evidence for the differentiator]
For the ICP: [Why this matters specifically to the ICP's situation]
```

**Rules:**
- One claim per message level — don't stack benefits
- Proof points must be specific (numbers, names, examples — not adjectives)
- Test: can a competitor honestly say the same thing? If yes → not a differentiator

---

## Mode 4: Referral Program Design

Referral = your customers do your acquisition. Only works when the product already has word-of-mouth momentum (people recommend it unprompted).

### Referral Loop Design

```
Referrer → shares → Referee sees offer → Referee converts → Both get reward
```

**Key decision: what incentive?**
| Incentive type | Works when | Example |
|---|---|---|
| Cash / credits | Product has recurring cost | "Get ฿200 credit for every friend who upgrades" |
| Extended access | Subscription product | "Give 1 month free, get 1 month free" |
| Social status | Community-driven product | "Early adopter badge + exclusive feature access" |
| Discount on upgrade | Freemium product | "Refer 3 friends → unlock Pro free for 3 months" |

**The referral incentive rule:** Incentive must feel meaningful relative to product price. $1 off a $100/month product = noise. 1 free month off $20/month = signal.

### Referral Mechanics

1. **Trigger moment:** Ask for referral at the peak of customer satisfaction (after first "aha moment", after a positive review, after a milestone)
2. **Friction:** Make sharing 1 click (unique link, not a form). Pre-write the message.
3. **Tracking:** Each referrer gets a unique code. Track: shares, signups, conversions.
4. **Reward delivery:** Immediate on referee conversion — delay kills motivation.
5. **Virality coefficient K:** K = (invites per user) × (conversion rate of invitees). K > 1 = viral growth.

### Minimum viable referral program
```
Step 1: Add "Invite a friend" to dashboard (unique link)
Step 2: Pre-written message: "I use [Product] for X. Here's ฿[X] off your first month: [link]"
Step 3: When referee converts → auto-apply reward to referrer's next bill
Step 4: Track weekly: invites sent, signups from invites, conversion rate
```

---

## Output Artifacts

| Request | Output |
|---|---|
| "Launch plan for [product]" | Phased plan with channels, timeline, checklist |
| "Product Hunt strategy" | Full PH playbook with pre-launch timeline |
| "How should I price this?" | Value metric selection + tier design + price range |
| "Redesign our pricing" | Audit + Good-Better-Best structure + pricing page layout |
| "Plan a price increase" | Announcement strategy + grandfathering plan + timeline |
| "Define our ICP" | 3-attribute ICP + positioning statement (Dunford) + messaging hierarchy |
| "Design referral program" | Incentive design + referral loop + MVP implementation |

## NotebookLM Deep Dive

For deeper domain wisdom, use `/consult` routed to:
- **Alex Hormozi General** (`cea608bb`) — Grand Slam Offer, pricing psychology, value stacking, unit economics
- **NopPongsatorn General** (`c835310c`) — Thai market positioning, brand strategy, competitive context

Trigger: "I need a deeper offer/pricing framework → `/consult [specific question]`"

## Language Rule

Match Bond's input language. Launch copy / pricing pages → English unless Thai market focus.
