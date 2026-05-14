# PRD Templates

## Standard PRD

```markdown
# [Feature / Product Name] — PRD

**Status:** Draft | In Review | Approved | Shipped
**Owner:** [PM Name]
**Date:** YYYY-MM-DD
**Version:** 1.0

---

## 1. Overview

**Problem:** [1–2 sentences — who is affected, what pain they experience, why it matters now]

**Solution:** [1–2 sentences — what we're building at a high level]

**Success Metrics:**
- Primary: [metric that would mean this worked — measurable, with baseline and target]
- Secondary: [supporting signal]
- Guardrail: [metric that must NOT get worse]

---

## 2. Background

- Why is this problem worth solving?
- What research or evidence do we have?
- What have we tried before?
- Why now? (market context, customer demand, strategic fit)

---

## 3. Goals

- G1: [Specific, measurable goal]
- G2: [Specific, measurable goal]

---

## 4. Non-Goals

Explicitly out of scope for this version:
- [Thing we decided not to build, and brief why]
- [Thing that could be confused with scope]

---

## 5. User Stories

Core scenarios this product must handle:

| As a | I want to | So that |
|---|---|---|
| [persona] | [action] | [outcome] |

---

## 6. Requirements

### Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | [What the system must do] | Must / Should / Could |
| FR-02 | | |

### Non-Functional Requirements

| Category | Requirement |
|---|---|
| Performance | [e.g., Page loads in < 1s at P95] |
| Security | [e.g., All data encrypted at rest and in transit] |
| Accessibility | [e.g., WCAG 2.2 AA compliant] |
| Availability | [e.g., 99.9% uptime SLA] |

---

## 7. UX Notes

- Key user flows (link to Figma / wireframes)
- Critical edge cases to handle
- Error states and empty states
- Mobile behavior (if different)

---

## 8. Technical Notes (optional)

- Known constraints
- API contracts that must be maintained
- Dependencies on other systems or teams
- Data migration requirements

---

## 9. Milestones

| Milestone | Date | Owner |
|---|---|---|
| Design complete | YYYY-MM-DD | |
| Engineering kickoff | YYYY-MM-DD | |
| Feature flag to 10% | YYYY-MM-DD | |
| Full rollout | YYYY-MM-DD | |

---

## 10. Open Questions

| Question | Owner | Status |
|---|---|---|
| [Unresolved decision] | [Name] | Open |
```

---

## One-Page PRD

For smaller features (< 2 weeks of work).

```markdown
# [Feature Name] — One-Pager

**Problem:** [Who is affected. What pain. Why it matters.]

**Solution:** [What we're building. What it does. What it doesn't do.]

**Success:** [1–3 metrics. Include baseline and target.]

**Out of scope:** [2–3 explicit exclusions to prevent scope creep.]

**Core stories:**
- As a [persona], I want to [action] so that [outcome].
- As a [persona], I want to [action] so that [outcome].

**Risks:**
1. [Risk] → [Mitigation]
2. [Risk] → [Mitigation]

**Timeline:** [Design done: date] → [Eng complete: date] → [Shipped: date]
```

---

## Feature Brief

Smallest unit. Use for single stories that need business context for engineering.

```markdown
# [Feature Name] — Feature Brief

**Feature:** [Name]
**Why:** [Problem being solved. 1 sentence.]
**What:** [What the feature does — behavior, not UI or implementation]
**Acceptance:** [How we know it's done — link to ACs or paste here]
**Dependencies:** [What else must ship first, or what this blocks]
**Owner:** [PM] | **Eng lead:** [Name]
```

---

## Agile Epic Template

```markdown
# Epic: [Name]

**Goal:** [What user outcome does this epic deliver?]
**Metric:** [How will we measure success?]
**Scope:** [Rough size in sprints or story points]

## Stories in this Epic

| ID | Story | Priority | Status |
|---|---|---|---|
| E01-S01 | As a..., I want to..., so that... | Must | Backlog |

## Epic Acceptance Criteria

- [ ] [High-level criterion 1]
- [ ] [High-level criterion 2]

## Dependencies

- Blocked by: [other epic / external team / third-party]
- Blocks: [downstream work]
```

---

## Reverse-PRD: prd/ Directory Format

Generated when running Reverse-PRD mode on a codebase.

### README.md (Executive Summary)

```markdown
# [App Name] — Product Documentation

**Generated:** YYYY-MM-DD
**Codebase:** [repo name / language / framework]
**Status:** Auto-generated — requires PM review

## App Summary

[2–3 sentence description of what the product does, who uses it, core workflow]

## Auth Model

[How authentication works: who can log in, how sessions are managed, roles/permissions]

## Page Index

| Page | URL / Route | Purpose | Primary Persona |
|---|---|---|---|
| Dashboard | /dashboard | Overview of... | Admin |

## Navigation Structure

[Top-level nav items and where they lead]
```

### pages/[page-name].md (Per-Page Docs)

```markdown
# [Page Name]

**Route:** `/path/here`
**Layout:** [parent layout name]
**Primary persona:** [who uses this page]

## Business Purpose

[What this page does in plain business language. No code references.]

## Field Inventory

| Field | Type | Required | Default | Validation | Business Meaning |
|---|---|---|---|---|---|
| | | | | | |

## Interactions

- [Action 1] → [What happens / state changes]
- [Action 2] → [What happens / navigation]

## API Dependencies

| Endpoint | When called | Data returned |
|---|---|---|
| GET /api/... | On page load | User profile data |

## Relationships

- **Navigates to:** [other pages]
- **Navigated from:** [entry points]
- **Depends on data from:** [other pages or flows]
```

### appendix/enum-dictionary.md

```markdown
# Enum Dictionary

All enumerated values in the system with their business meaning.

## [EntityName].[FieldName]

| Value | Business Meaning |
|---|---|
| `ACTIVE` | Customer is on a paid plan, has full access |
| `TRIALING` | Customer is within 30-day free trial period |
| `CANCELED` | Subscription ended, read-only access only |
```

### Business Language Rules (strict)

| Code reference | Business language |
|---|---|
| `billingAddress` state variable | Customer's billing address |
| `trial_days: 30` | 30-day trial period |
| `UNIQUE(org_id, email)` | Must be unique per organization |
| `status === 'active'` check | Customer has an active subscription |
| `user.role === 'admin'` | Only organization administrators |

Mark inferred intent with "(assumed)" when behavior isn't explicit in code.
