# Story Templates

## User Story Format

```
As a [persona],
I want to [action],
So that [benefit / outcome].
```

**Persona:** A specific user type (not "user" — "admin user", "first-time visitor", "enterprise buyer").
**Action:** What they want to do — not how the system does it.
**Benefit:** Why it matters — the outcome they're trying to achieve.

---

## INVEST Checklist

Before accepting a story into the sprint, verify all 6:

| Criterion | Check | Fix if failing |
|---|---|---|
| **I**ndependent | Can be developed without depending on another unfinished story | Reorder or split |
| **N**egotiable | The "how" is open to discussion with engineering | Remove implementation details |
| **V**aluable | Delivers value to the user or business | Combine with related story or cut |
| **E**stimable | Engineering can estimate effort | Add more context or spike first |
| **S**mall | Fits within one sprint | Apply epic splitting techniques |
| **T**estable | Has clear acceptance criteria | Add Given-When-Then ACs |

---

## Acceptance Criteria (Given-When-Then)

```
Given [precondition / starting state]
When [user action or system event]
Then [expected observable outcome]
```

### Good AC Rules

- One observable outcome per criterion (no "and" in Then)
- Testable: someone reading this can write a test case
- Unambiguous: no room for interpretation on what "success" means
- No implementation details: doesn't tell engineering HOW to build it

### AC Count by Story Size

| Story Points | Minimum AC | If exceeds max → |
|---|---|---|
| 1–2 | 3–4 | Fine, ship |
| 3–5 | 4–6 | Fine, ship |
| 8 | 5–8 | Consider splitting |
| 13+ | — | Must split before sprint |

### Example Story + AC

**Story:**
> As a first-time user, I want to reset my password without contacting support, so I can regain access to my account immediately.

**Acceptance Criteria:**
> Given I am on the login page
> When I click "Forgot password" and enter my email
> Then I receive a reset email within 2 minutes

> Given I click the reset link in the email
> When the link is less than 24 hours old
> Then I am taken to a page where I can set a new password

> Given I click the reset link in the email
> When the link is more than 24 hours old
> Then I see an error message and a prompt to request a new link

---

## Epic Splitting — 5 Techniques

### Technique 1: By Workflow Step

Split the epic into individual steps of the user's workflow.

Epic: "User can manage team members"
→ Story 1: User can invite a team member by email
→ Story 2: Invited member can accept and join the team
→ Story 3: Admin can remove a team member
→ Story 4: Admin can change a member's role

### Technique 2: By Persona

Different user types get different stories for the same feature.

Epic: "User can export data"
→ Story 1: Admin user can export all organization data as CSV
→ Story 2: Regular user can export only their own data as CSV

### Technique 3: By Data Type / Variation

Handle each data variation as a separate story.

Epic: "Import customer data"
→ Story 1: Import from CSV file
→ Story 2: Import from Google Sheets
→ Story 3: Import from HubSpot API

### Technique 4: By CRUD Operation

Separate create, read, update, delete.

Epic: "Manage product catalog"
→ Story 1: Admin can create a new product
→ Story 2: Any user can view product details
→ Story 3: Admin can update product information
→ Story 4: Admin can archive (soft-delete) a product

### Technique 5: Happy Path First

Ship the core flow, then handle edge cases in follow-up stories.

Epic: "User can pay with credit card"
→ Story 1: User can pay with Visa/Mastercard (happy path — card works)
→ Story 2: User sees a clear error if card is declined
→ Story 3: User can save card for future payments
→ Story 4: User can remove a saved card

---

## Sprint Planning

### Capacity Calculation

```
Sprint Capacity = Team Velocity (rolling 3-sprint average) × Sprint Length

Available capacity per person:
- Subtract: meetings, on-call, reviews, planned PTO
- Rule of thumb: 6 focused hours per 8-hour day for engineering

Total sprint capacity (story points) = sum across all contributing engineers
```

### Loading Rules

| Bucket | Allocation | Purpose |
|---|---|---|
| Committed | 85% of capacity | Stories team commits to finish |
| Stretch | 15% of capacity | If committed finishes early |
| Buffer | Never fill 100% | For unplanned work, bug fixes |

### Backlog Health Checks

- Sprint backlog: all stories have ACs, estimated, and groomed
- Top of backlog: next 2 sprints fully groomed
- Mid-backlog: roughly estimated, may need refinement
- Far backlog: ideas only — no estimation needed yet

### Definition of Ready (before a story enters sprint)

- [ ] Story written in As a / I want / So that format
- [ ] Acceptance criteria in Given/When/Then format
- [ ] Story estimated in points
- [ ] Dependencies identified
- [ ] Design/mocks linked (if UI change)
- [ ] No blocking technical questions unresolved

### Definition of Done (before story is marked complete)

- [ ] All ACs pass
- [ ] Code reviewed and merged
- [ ] Tests written and green
- [ ] Deployed to staging (or prod if CD)
- [ ] PM/stakeholder reviewed and accepted
