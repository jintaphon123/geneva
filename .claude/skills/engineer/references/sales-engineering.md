# Sales Engineering — RFP Analysis, Competitive Positioning & POC Planning

## Bid / No-Bid Decision Framework

### Decision Matrix (100 points total)

| Dimension | Weight | 1 (Weak) | 3 (Moderate) | 5 (Strong) |
|-----------|--------|----------|--------------|------------|
| **Technical fit** | 25% | <50% requirement coverage | 60-75% coverage | >85% coverage |
| **Relationship strength** | 20% | Cold outreach only | Known contact | Executive sponsor inside |
| **Competitive position** | 20% | 3+ strong competitors | 1-2 competitors | Clear differentiation |
| **Deal value vs effort** | 15% | Low value, high effort | Balanced | High value, manageable scope |
| **Strategic importance** | 10% | No strategic fit | Useful reference | Perfect ICP + logo value |
| **Win probability** | 10% | <25% | 40-60% | >75% |

**Scoring:**
```
Bid if weighted score >70 AND technical fit ≥3 AND ≤3 Must-Have gaps
Conditional bid (50-70): proceed only if conditions addressed (e.g., partner to fill gap)
No-Bid if <50 OR technical fit <2 OR >3 Must-Have gaps
```

---

## RFP Coverage Analysis

### Coverage Classification

| Coverage | Definition | How to handle |
|----------|-----------|--------------|
| **Full** | Feature/requirement fully met out-of-box | State capability clearly, link to docs |
| **Partial** | Feature met with configuration or workaround | Describe what's included, what's not |
| **Planned** | On roadmap within customer's evaluation window | State ETA; don't commit if uncertain |
| **Gap** | Not supported, not planned | Acknowledge; offer workaround or partner |

### Priority Weighting

```
Must-Have (M): Weight = 3x — critical to business process; no substitute
Should-Have (S): Weight = 2x — important but workaround exists
Nice-to-Have (N): Weight = 1x — desirable; not decision-blocking

Coverage Score = Σ(Coverage % × Requirement Weight)
Target: >70% weighted coverage to bid
```

### RFP Response Structure

```
## [Requirement Name]

**Coverage: Full / Partial / Planned / Gap**

**Our Approach:**
[Specific description of how the capability works]

**Evidence:**
- Documentation link: [URL]
- Customer reference: [if available]
- Demo available: Yes/No

**Limitations (if Partial or Gap):**
[Honest description of what is NOT covered]

**Workaround/Mitigation:**
[How the customer can address the gap]
```

---

## Competitive Feature Matrix

### Matrix Structure

Build a grid: Features (rows) × Competitors (columns) × Coverage rating

**Coverage ratings:**
- ✅ Full native support
- 🔶 Partial / workaround required
- 🔜 Roadmap (with ETA)
- ❌ Not available

| Feature | Us | Competitor A | Competitor B | Competitor C |
|---------|-----|-------------|-------------|-------------|
| [Feature 1] | ✅ | 🔶 | ❌ | ✅ |
| [Feature 2] | ✅ | ✅ | 🔜 Q3 | ❌ |
| [Feature 3] | 🔶 | ✅ | ✅ | ✅ |

**Strength scoring (1-5 per feature):**
- 5: Best-in-class, unique capability
- 4: Strong, at par with best competitors
- 3: Adequate, meets requirement
- 2: Partial, workaround needed
- 1: Weak or absent

### Win Theme Identification

From the competitive matrix, identify:

1. **Clear differentiators** (we score 4-5, competitors score 1-2): Lead with these in proposal
2. **Feature parity** (all score 3+): Acknowledge but don't focus — shift to value/support/roadmap
3. **Competitive gaps** (we score 1-2, they score 4-5): Prepare objection handling; lead with mitigations
4. **Landmines** (competitors score 5, we score 1): Disqualify if Must-Have; reframe if Should-Have

### Battlecard per Competitor

```
## Battlecard — vs [Competitor Name]

**Why we win:**
- [Differentiator 1 with specific proof]
- [Differentiator 2 with specific proof]

**Their strengths (honest):**
- [Competitor strength — don't dismiss, acknowledge and redirect]

**Their weaknesses (factual only):**
- [Weakness — back with customer evidence, not marketing claims]

**Common objections and responses:**
| Objection | Response |
|-----------|----------|
| "Competitor X has feature Y" | "[What we offer instead + why it's better for their use case]" |
| "Competitor X is cheaper" | "[Total cost of ownership / value delivered comparison]" |

**Our win conditions:**
[Scenario where we win: which customer profile, which priorities]

**Their win conditions:**
[Scenario where they win: be honest — better to walk away than lose badly]
```

---

## POC (Proof of Concept) Planning

### 5-Week POC Timeline

**Week 1: Setup & Provisioning**
- Environment provisioning (tenant setup, SSO configuration, data migration test)
- Kickoff meeting: confirm success criteria, stakeholders, and weekly cadence
- Technical discovery: integration requirements, security review, compliance checklist
- Deliverable: POC environment accessible and demo-ready

**Weeks 2-3: Core Use Case Testing**
- Execute primary use cases (those with Must-Have requirements)
- Integration testing (API connections, data sync, authentication)
- Stakeholder-specific demos (by role: end user / admin / executive)
- Document issues: severity (P1 Blocker / P2 High / P3 Medium / P4 Low)
- Deliverable: Core use case results documented

**Week 4: Advanced & Edge Cases**
- Edge case testing (high volume, error handling, failure modes)
- Performance testing if applicable (response time, concurrency)
- Security review (penetration test results, SOC 2, access controls)
- Deliverable: Full test coverage documented

**Week 5: Evaluation & Go/No-Go**
- Compile POC scorecard (see below)
- Stakeholder debrief session
- Formal go/no-go decision
- Deliverable: POC scorecard + recommendation

---

### POC Success Scorecard

Score each dimension 0-100. Go if total ≥ 60% across all dimensions.

| Dimension | Score | Notes |
|-----------|-------|-------|
| Functional requirements met | /100 | % of Must-Haves fully covered |
| Performance targets met | /100 | Response time, uptime, error rate |
| Integration success | /100 | APIs, SSO, data sync working |
| User acceptance | /100 | End user feedback rating |
| Admin/IT satisfaction | /100 | Setup complexity, manageability |
| Security & compliance | /100 | All checklist items cleared |

**Overall POC Score:** [X]%

| Result | Score | Recommendation |
|--------|-------|---------------|
| Go | ≥60% all dimensions | Proceed to proposal and commercial negotiation |
| Conditional Go | ≥60% total but <60% in 1-2 dimensions | Address conditions before contract signing |
| No-Go | <60% in any critical dimension | Document gaps; discuss whether roadmap commitment can help |

---

## Technical Proposal Structure

After successful POC, write the technical proposal in this order:

```
## Technical Proposal — [Customer Name]

### 1. Executive Summary (1 page)
- Business problem we're solving
- Our proposed solution in 3 sentences
- POC outcome summary
- Investment required

### 2. Solution Design (2-3 pages)
- Architecture diagram
- How our solution maps to their requirements
- Integration architecture (systems + APIs)
- Data flow and security model

### 3. POC Results (1 page)
- POC scorecard summary
- Key findings (wins + identified gaps + mitigations)
- Customer team feedback

### 4. Implementation Plan (1 page)
Phase 1 (Weeks 1-4): [Core implementation]
Phase 2 (Weeks 5-8): [Integration + training]
Phase 3 (Weeks 9-12): [Full rollout + optimization]

Success criteria for each phase.

### 5. Pricing & Commercial Terms (1 page)
- License model
- Implementation cost
- Ongoing support/success
- Total Year 1 / Year 2 / Year 3

### 6. References & Next Steps
- 2-3 relevant customer references
- Proposed timeline to contract
- Next steps with owners
```

---

## Pre-Sales Qualification Checklist

Before investing significant pre-sales effort, confirm:

- [ ] Budget identified and approved (or in budget cycle)
- [ ] Decision-maker identified and willing to engage
- [ ] Timeline is real (not "we'll look at it next year")
- [ ] Requirements are documented (or can be documented in kickoff)
- [ ] Technical evaluation criteria are defined
- [ ] Competitors have been identified (know who we're competing against)
- [ ] Success criteria for POC are agreed in advance

If any of these fail → discuss with sales rep before proceeding to POC.
