# Proposals & Contracts — Templates and Jurisdiction Rules

## Document Type Selection Guide

| Document | When to Use | Binding? | Length |
|----------|------------|---------|--------|
| **Proposal** | Early-stage — before agreement, to win the work | No | 2-5 pages |
| **Contract** | General services agreement, ongoing relationship | Yes | 4-8 pages |
| **SOW (Statement of Work)** | Specific project scope under existing MSA | Yes | 2-4 pages |
| **NDA** | Before sharing confidential info | Yes | 1-2 pages |
| **MSA (Master Service Agreement)** | Governs multiple ongoing engagements | Yes | 6-12 pages |
| **Partnership Agreement** | Referral, reseller, white-label, integration | Yes | 5-10 pages |

**Common flow:** NDA → Proposal → Contract or MSA → SOW per project

---

## Template A: Fixed-Price Development Contract

```
DEVELOPMENT SERVICES AGREEMENT

This Agreement is entered into as of [DATE] between:
Service Provider: [YOUR COMPANY NAME], [ADDRESS]
Client: [CLIENT COMPANY NAME], [ADDRESS]

1. SCOPE OF WORK
[Detailed description of deliverables]
See attached Statement of Work ("SOW") for complete specifications.

2. PROJECT TIMELINE
Start Date: [DATE]
Completion Date: [DATE]
Milestones: As defined in SOW

3. PAYMENT TERMS
Total Contract Value: $[AMOUNT]
Payment Schedule:
- 50% upon contract execution: $[AMOUNT]
- 25% upon [milestone]: $[AMOUNT]
- 25% upon final delivery and acceptance: $[AMOUNT]

Invoices due Net-30. Late payments subject to 1.5% monthly interest.

4. CHANGE ORDERS
Any scope changes require written Change Order signed by both parties before work begins.
Change Orders will adjust timeline and cost proportionally.

5. INTELLECTUAL PROPERTY
Upon receipt of full payment, Service Provider assigns to Client all right, title, and interest
in the Deliverables, including all copyrights and related IP rights.
Service Provider retains ownership of pre-existing tools, frameworks, and methodologies
("Background IP"). Client receives a perpetual license to use Background IP embedded in Deliverables.

6. ACCEPTANCE
Client has [10] business days to review and accept each deliverable.
Silence after [10] days constitutes acceptance.
Rejections must specify defects in writing; Service Provider has [5] business days to cure.

7. WARRANTIES
Service Provider warrants that Deliverables will conform to specifications for [90] days after acceptance.
Remedy: Service Provider will correct non-conforming work at no charge within [30] days.

8. LIMITATION OF LIABILITY
Total liability of either party shall not exceed the total fees paid under this Agreement.
Neither party liable for indirect, incidental, or consequential damages.

9. TERMINATION
For Cause: Either party may terminate with [14] days written notice if material breach not cured.
For Convenience: Client may terminate with [30] days notice; Client owes fees for work completed + 20% kill fee.

10. CONFIDENTIALITY
Both parties agree to keep confidential all non-public information for [3] years.
[Add GDPR DPA if EU data involved — see GDPR section below]

11. GOVERNING LAW & DISPUTE RESOLUTION
[US: This Agreement is governed by Delaware law. Disputes resolved by AAA arbitration.]
[EU: This Agreement is governed by [governing country] law. Disputes resolved by ICC arbitration.]
[UK: This Agreement is governed by English law. Disputes resolved by LCIA arbitration.]

12. ENTIRE AGREEMENT
This Agreement, including all attachments, constitutes the entire agreement between the parties.
Amendments must be in writing signed by both parties.

IN WITNESS WHEREOF:
Service Provider: _______________  Date: ___
Client: _______________  Date: ___
```

---

## Template B: Monthly Consulting Retainer

```
CONSULTING SERVICES RETAINER AGREEMENT

1. RETAINER SERVICES
Service Provider will provide consulting services in [DOMAIN] on a retainer basis.
Scope: [DESCRIPTION OF SERVICES]

2. RETAINER TERMS
Monthly Retainer Fee: $[AMOUNT]/month
Included Hours: [X] hours/month
Rollover Policy: Unused hours roll over for [1] month maximum, then expire.
Overflow Rate: $[RATE]/hour for hours exceeding monthly allocation (requires prior approval).

3. PAYMENT
Due: 1st of each month
Method: [Wire / ACH / Credit Card]
Auto-renewal: Agreement renews monthly unless either party provides [30] days written notice.

4. DELIVERABLES & COMMUNICATION
Weekly status update: [Yes/No]
Monthly report: [Yes/No]
Response time SLA: [24/48] hours on business days

5. INTELLECTUAL PROPERTY
Work product created under this retainer is assigned to Client upon payment.
Service Provider retains rights to methodologies and frameworks.

[Continue with standard IP, confidentiality, termination, liability, governing law clauses]
```

---

## Template C: SaaS Partnership Agreement

```
PARTNERSHIP AGREEMENT

Partnership Type: [Referral / Reseller / White-Label / Technology Integration]

REFERRAL PARTNERSHIP:
- Partner refers qualified leads to Company
- Company pays [X]% commission on closed deals referred by Partner
- Commission paid [30] days after client payment received
- Commission on renewals: [X]% for [Y] years
- Minimum activity: [X] qualified referrals per quarter to maintain partner status

RESELLER PARTNERSHIP:
- Partner purchases licenses at [X]% discount from list price
- Partner sets own end-customer pricing (suggested but not required)
- Partner responsible for first-line customer support
- Company provides partner training and certification program
- Minimum revenue commitment: $[AMOUNT]/year

WHITE-LABEL PARTNERSHIP:
- Company provides [Product] under Partner's brand
- Partner pays platform fee of $[AMOUNT]/month + [X]% of GMV
- Company provides: uptime SLA [99.9%], API access, white-label documentation
- Partner owns customer relationships and billing

TECHNOLOGY INTEGRATION PARTNERSHIP:
- Joint integration of [PARTNER PRODUCT] with [COMPANY PRODUCT]
- Both parties invest [X] engineering hours in initial integration
- Joint marketing: [co-blog posts, webinars, case studies]
- Revenue share on jointly sourced deals: [X]%

[Standard terms: IP, confidentiality, termination, liability]
```

---

## GDPR Data Processing Addendum (Art. 28)

Attach when: EU client, EU data subjects, or EU personal data processed.

```
DATA PROCESSING ADDENDUM ("DPA")

This DPA supplements the main Agreement between [CONTROLLER] ("Client")
and [PROCESSOR] ("Service Provider") and governs personal data processing.

1. DEFINITIONS
"Personal Data" means any information relating to an identified or identifiable natural person.
"Processing" means any operation on Personal Data.
"Controller" means the party that determines purposes and means of processing.
"Processor" means the party that processes data on behalf of the Controller.

2. SUBJECT MATTER
Service Provider processes Personal Data solely to perform services under the Agreement.
Categories of data subjects: [employees / customers / end users]
Categories of personal data: [names, emails, usage data, etc.]
Purpose of processing: [service delivery]
Duration: Term of Agreement + [90] days for deletion

3. PROCESSOR OBLIGATIONS
Service Provider shall:
- Process data only on documented Controller instructions
- Ensure confidentiality of authorized processors
- Implement appropriate technical and organizational security measures (Art. 32 GDPR)
- Assist Controller with data subject rights requests within [30] days
- Delete or return all Personal Data upon termination
- Make available information to demonstrate compliance

4. SUB-PROCESSORS
Service Provider may engage sub-processors with [30] days prior notice.
Current sub-processors: [list hosting, analytics, support tools]
Client may object; if unresolved, Client may terminate without penalty.

5. SECURITY MEASURES
Service Provider implements: encryption in transit and at rest, access controls,
regular security testing, incident response plan.

6. DATA BREACH NOTIFICATION
Service Provider will notify Client within [48] hours of discovering a breach.
Notification includes: nature, categories affected, likely consequences, measures taken.

7. DATA TRANSFERS
Personal Data transferred outside EU/EEA only with: adequacy decision, Standard
Contractual Clauses (SCCs), or Binding Corporate Rules.

8. AUDIT RIGHTS
Client may audit compliance with [30] days notice, at Client's expense.
```

---

## Key Clauses Reference

### Payment Terms
| Type | Structure | Notes |
|------|-----------|-------|
| **Net-30** | Invoice due in 30 days | Standard for services |
| **Milestone** | 50/25/25 at start/mid/completion | Best for projects |
| **Monthly retainer** | Due 1st of month | Ongoing services |
| **Net-60** | Enterprise clients | Common for large cos |

### IP Ownership
| Situation | Clause |
|-----------|--------|
| Custom work for client | Full assignment upon payment |
| SaaS platform access | License only; IP stays with provider |
| Joint development | Co-ownership or negotiate upfront |
| EU client | Written assignment deed required (work-for-hire insufficient) |

### Liability Cap
- Standard: 1× total fees paid under agreement
- High-risk (data breach, personal injury): 3× total fees
- Enterprise: negotiate higher caps with indemnification

### Termination
| Type | Notice | Who can invoke |
|------|--------|---------------|
| For Cause | 14 days (with cure period) | Either party |
| For Convenience | 30-90 days | Either or Client only |
| Non-payment | 15 days | Service Provider |

---

## Jurisdiction Rules

### US (Delaware)
- Work-for-hire doctrine applies → IP created by independent contractor belongs to contractor unless written assignment
- **Action:** Always include explicit IP assignment clause
- Arbitration: AAA (American Arbitration Association) preferred
- Non-compete: Enforceable in most states (California exception: not enforceable)

### EU (General GDPR)
- IP: Written assignment deed required in some EU member states (work-for-hire insufficient)
- **Action:** Add "hereby assigns all rights" with written signature
- GDPR Data Processing Addendum: Mandatory when processing EU personal data
- Arbitration: ICC (International Chamber of Commerce) or local chamber
- Non-compete: Generally 2-year max; must be compensated in some countries

### UK (Post-Brexit)
- Governed by UK GDPR (same structure as EU GDPR but separate from EU enforcement)
- Governing law: English law
- Arbitration: LCIA (London Court of International Arbitration)
- Non-compete: 12 months reasonable; courts will blue-pencil excessive ones

### DACH (Germany/Austria/Switzerland)
- Governed by BGB (Bürgerliches Gesetzbuch)
- **Written form clauses required** — oral amendments are not binding
- Authors retain moral rights in Germany/Austria; assignment of moral rights not possible, only licensing
- Non-compete: Maximum 2 years; must provide compensation (typically 50% of last salary)
- Data protection: DSGVO (= German implementation of GDPR)
- Arbitration: DIS (German Institution of Arbitration)

---

## Common Pitfalls

| Pitfall | Why It Fails | Fix |
|---------|-------------|-----|
| No IP assignment in EU | Work-for-hire insufficient | Add explicit written assignment |
| Vague acceptance criteria | Disputes on "done" definition | Define specific acceptance tests and pass/fail criteria |
| No change order process | Scope creep with no mechanism to re-price | Add change order clause with written approval requirement |
| Jurisdiction mismatch | Laws of client and provider conflict | Negotiate agreed governing law upfront |
| Missing liability cap | Unlimited exposure on minor contracts | Always cap at 1-3× contract value |
| Oral amendments | "We agreed on the call" unenforceable | All modifications must be in writing, signed |
| GDPR oversight | EU client with no DPA | Attach DPA before any data processing begins |
