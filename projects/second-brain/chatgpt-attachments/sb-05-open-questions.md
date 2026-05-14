# Second Brain — Open Questions

> This file exists for one purpose: **these are the things we don't know yet.**
> Use this as the starting point for consulting sessions. Challenge every assumption here.

---

## Strategy Questions

### 1. Who is the real first paying customer?
University teams are free pilot users. But who is the first person or organization that pays before they have proof? What job are they actually hiring Second Brain for? Is it memory? Communication? Knowledge retention on exit? We haven't validated which pain point converts to payment.

### 2. Is "team" the right first unit — or is solo enough to sell?
The long-term vision is organizational. But solo users might have enough value to pay ฿699/month without ever needing a team feature. Should we delay building the team layer until solo value is proven? Or does the team pitch require both layers to be credible?

### 3. What's the actual competitive moat at the enterprise level?
The data moat and network effect arguments make sense at the conceptual level. But enterprise procurement asks: "What happens if you get acquired? If you shut down? If we want to switch?" We don't have a good answer yet beyond "your data is in `.md` files you own." Is that enough?

### 4. Does the AI Network feature create privacy/legal risk in Thailand?
PDPA requires explicit consent. The "manager queries team AI" scenario is powerful but potentially triggering. Have we pressure-tested this with anyone who understands Thai labor law? Is opt-in sufficient, or does this feature need to be structurally separated from the personal brain?

### 5. What's the right beachhead beyond universities?
Phase 2 is research labs, Phase 3 is Thai startups. But "Thai startups" is 10,000 companies. What's the one specific segment with the highest pain, fastest sales cycle, and most credible reference story? Consulting firms? Agencies? SaaS companies losing engineers to churn?

---

## Product Questions

### 6. What does a "good brain" look like at 6 months?
We know the onboarding ritual creates a starting brain. But what does a brain that's been running for 6 months actually contain? How much data? What structure? How do we know if it's working or just growing noise? No definition of "healthy brain" yet.

### 7. How do we prevent the brain from becoming a junk drawer?
If every conversation is auto-captured, the brain fills up with irrelevant content fast. What's the curation mechanism? Manual tagging? Automatic relevance scoring? How do we surface the right memory at the right time without overwhelming the context window?

### 8. What is the minimum viable AI-to-AI interaction?
The full vision is multi-agent, multi-team, async. But what's the simplest version that still delivers value? Is it just: "summarize your current work state and send it to one other person's AI"? Define the MVP of A2A before building the full vision.

### 9. How do we handle the cold-start for teams (not just individuals)?
The onboarding ritual solves cold-start for a single person. But when a new team forms, nobody has shared project context yet. How do we bootstrap the shared layer? Is there a "team onboarding ritual" that's separate from the personal one?

---

## Technical Questions

### 10. What's the right memory architecture for context window management?
At scale, a user's brain will have hundreds of `.md` files. We can't inject everything into every API call. What's the retrieval strategy? RAG on `.md` files? Hierarchical summary layers? This decision determines cost and quality at scale and hasn't been decided.

### 11. Should the brain be structured or freeform?
Current approach: freeform `.md` files. Benefit: flexible. Problem: hard to query reliably. Alternative: structured schema per memory type (decisions, project context, working style, etc.). Hybrid: freeform input, structured extraction at capture time. Which gives better retrieval without losing flexibility?

### 12. How does real-time auto-capture work without being annoying?
Auto-capture needs to run in the background without interrupting flow. But it also needs to ask clarifying questions sometimes ("Is this a decision or a note?"). What's the UX for background capture that feels helpful instead of intrusive?

---

## Build Priority Questions

### 13. What must be true for the pilot to succeed?
If we had to bet on one thing that makes or breaks the pilot, what is it? Is it onboarding quality? Session retention on Day 3? Whether the AI says something demonstrably useful from memory? Define the minimum requirement for "pilot success" before starting.

### 14. When do we stop building solo and start building team?
Week 1-2: solo brain. Week 3: A2A layer (if retention passes). But what if retention passes and we're not ready? What if it fails but users still love the solo feature? Define the decision rule before we hit that moment.
