# Communications Templates

## Board / Executive Update Template

For: quarterly business review, investor update, board meeting prep.
Format: outcome and risk — no feature lists, no build updates.

```markdown
Subject: [Product] Q[N] Update — [1-line headline that captures the most important thing]

**Period:** Q[N] YYYY | **Prepared by:** [Name] | **Date:** YYYY-MM-DD

---

### Headline

[2–3 sentences: the most important thing that happened and what it means for the business]

---

### Key Results

| Metric | Last Quarter | This Quarter | Target | Status |
|---|---|---|---|---|
| [North Star] | | | | 🟢 / 🟡 / 🔴 |
| MRR | | | | |
| [Retention metric] | | | | |
| NPS | | | | |

---

### Highlights (what went well)

- [Outcome — metric moved, milestone hit, insight gained]
- [Outcome]

### Risks & Challenges (what's at risk)

- **[Risk]:** [Context] → [What we're doing about it]
- **[Risk]:** [Context] → [Mitigation]

---

### Q[N+1] Focus

[3-bullet preview of what the product team is focused on next quarter — outcomes, not features]

---

### Asks

- [Specific decision needed from this group]
- [Resource or unblocking action]
```

---

## Engineering Update Template

For: sprint review, weekly eng standup update, cross-team sync.
Format: scope, status, dependencies.

```markdown
**Sprint [N] — [Start Date] → [End Date]**

### Shipping This Sprint

| Feature | Status | Notes |
|---|---|---|
| [Feature] | In review / Merged / Deployed | |
| [Feature] | In progress | |

### Blocked

- **[Feature]:** Needs [dependency] from [team/person] by [date]
  - Impact if not resolved: [sprint delay / unshippable feature]

### Coming Next Sprint

- [Feature] — [brief scope description]
- [Feature]

### Technical Health

- [1 tech debt item worth flagging]
- [1 reliability or performance note]
```

---

## Customer Update Template

For: product newsletter, in-app announcement, email blast.
Format: value narrative + timing. No internal roadmap or date commitments.

```markdown
Subject: [What's new in Product] — [Month Year]

---

Hi [Name / everyone],

[1–2 sentences: lead with why this update matters to them — benefit first, not feature first]

---

**What's new:**

🔹 **[Feature name]**
[What it does for them in 1–2 sentences. Focus on the outcome, not the mechanics.]
→ [CTA: Try it / Learn more / Link]

🔹 **[Feature name]**
[Same format]

---

**Coming soon:**
[Theme or outcome — not specific feature names unless committed]
[1–2 sentences of direction — signal intent without date commitment]

---

[CTA: biggest action you want them to take]

[Signature]
```

---

## Feature Announcement Framework

Use for major new feature releases — internal launch doc, press release, blog post, or in-app announcement.

```markdown
# [Feature Name] — Launch Communication

## 1. Problem Context
[Why this problem mattered. What users couldn't do or had to do in a frustrating way.]

## 2. What Changed
[What we built — 1 clear sentence. Feature name + core behavior.]

## 3. Why It Matters
[Concrete benefit — time saved, error reduced, revenue unlocked, friction removed.]

## 4. Who Benefits
[Specific user type / use case — be narrow. Not "everyone" but "developers who..."]

## 5. How to Get Started
[Step-by-step: go here, click this, do that. No ambiguity.]

## 6. Call to Action
[One action. Link. Button. Not multiple options.]
```

---

## Release Notes Guidance

### User-Facing Release Notes
- Lead with the user benefit, not the technical change
- Use plain language — no internal code names, API terms, or stack references
- Format: **[Feature name]:** [What users can now do] | [Link to docs if relevant]
- Group by: New features / Improvements / Bug fixes
- Omit: internal refactors, dependency bumps, config changes users don't see

### Internal / Engineering Release Notes
- Include: deployment details, migration steps, breaking changes, rollback plan
- Flag: any database migrations, feature flag changes, API contract changes
- Format: changelog-style with semantic versioning

### Release Note Examples

**User-facing:**
> **Export to PDF:** You can now export any dashboard as a PDF from the Share menu. Works on all paid plans.

**Engineering:**
> **[BREAKING] Auth middleware updated:** JWT expiry reduced from 7 days to 24h. Clients must handle 401s with refresh-token flow. See migration guide in Notion.

---

## Communication Cadence

| Audience | Update type | Cadence |
|---|---|---|
| Board / Investors | Quarterly business review | Once per quarter |
| Executive team | Product metrics + OKR progress | Monthly |
| Engineering | Sprint review | Every sprint |
| Customers | What's new / feature announcements | Monthly or per major release |
| Sales / CS | Battlecard updates, new capabilities | Per significant release |
