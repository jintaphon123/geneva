---
name: release-engineer
description: >
  Release management covering semantic versioning, changelog generation from conventional commits,
  runbook creation, zero-downtime migration planning, and spec-driven development workflow.

  Auto-invoke when Bond asks: release, version bump, semantic versioning, semver, changelog, what changed,
  how to version this, prepare release, release notes, runbook, deployment runbook, rollback plan,
  migration plan, zero-downtime migration, spec-driven, write spec first, PRD, feature spec,
  conventional commits, "ready to release", "what version should this be", "generate changelog".
---

# Release Engineer

Five modes: **Version** (SemVer + bumping), **Changelog** (from git history), **Runbook** (deployment + rollback), **Migrate** (zero-downtime plan), **Spec** (spec-driven feature workflow).

Reference files:
- `references/release-patterns.md` — SemVer rules, conventional commits, changelog format, versioning decisions

---

## Mode Detection

| Input | Mode |
|---|---|
| "version", "semver", "what version", "major/minor/patch", "bump" | **Version** |
| "changelog", "what changed", "release notes", "commit history" | **Changelog** |
| "runbook", "deployment plan", "rollback", "deploy steps" | **Runbook** |
| "migration plan", "zero-downtime", "database migration strategy" | **Migrate** |
| "spec", "spec-driven", "write spec first", "PRD", "feature spec" | **Spec** |

---

## Mode 1 — Version

Read `references/release-patterns.md` fully before executing.

**Decision logic:**
```
Any breaking change? → MAJOR (1.0.0 → 2.0.0)
New feature, backward-compatible? → MINOR (1.2.0 → 1.3.0)
Bug fix only? → PATCH (1.2.3 → 1.2.4)

Breaking change examples:
  - Removed API endpoint or field
  - Changed response shape
  - Required new environment variable
  - Changed CLI argument behavior
  
Minor examples:
  - New API endpoint
  - New optional field
  - New feature behind flag
  
Patch examples:
  - Bug fix (behavior unchanged, just correct now)
  - Performance improvement
  - Documentation update
```

**Commit analysis:** Look at commits since last tag → classify each → determine bump level → draft version

---

## Mode 2 — Changelog

Read `references/release-patterns.md` (Changelog section) fully before executing.

**Workflow:**
```bash
# Get commits since last tag
git log $(git describe --tags --abbrev=0)..HEAD --oneline

# Or last N commits
git log --oneline -20
```

**Changelog format:** Keep a Changelog standard (keepachangelog.com)

```markdown
## [1.3.0] — 2026-05-01

### Added
- Memory search now supports semantic similarity filtering (#42)
- Export to PDF feature for shared notes

### Changed  
- Improved response time for memory retrieval by 40%

### Fixed
- Fixed crash when uploading empty files
- Corrected pagination cursor for empty result sets

### Security
- Updated dependencies: axios 1.6.0 → 1.7.4 (CVE-2024-xxxxx)
```

---

## Mode 3 — Runbook

**Runbook template (generate this for every production deployment):**

```markdown
# Deployment Runbook — v[VERSION] — [DATE]

## Pre-deployment Checklist
- [ ] All tests passing in CI
- [ ] Staging deployment verified
- [ ] Database migrations reviewed (if any)
- [ ] Feature flags configured
- [ ] Rollback plan confirmed

## Deployment Steps
1. [Step with exact command]
2. [Step with exact command]
3. Verify: [what to check post-deploy — URL, metric, log line]

## Post-deployment Verification
- [ ] Health check endpoint returns 200: `curl /api/health`
- [ ] [Key user flow] works in production
- [ ] Error rate normal (< 0.1%) for 10min post-deploy

## Rollback Procedure
**Trigger:** Error rate > 1% or [specific symptom]

1. [Exact rollback command]
2. Verify: [how to confirm rollback succeeded]
3. Alert: [who to notify]

## Contacts
- On-call: [name/handle]
- Escalation: [name/handle]
```

---

## Mode 4 — Migrate

Zero-downtime migration uses the **Expand-Contract** pattern. Full patterns in `database-architect` skill.

**Decision: can this be done zero-downtime?**
```
Adding nullable column     → YES, expand phase only
Adding NOT NULL column     → REQUIRES backfill (3 phases)
Renaming column            → REQUIRES 3 phases (old + new name coexist during transition)
Dropping column            → REQUIRES 3 phases (remove from code first)
Adding index               → YES, use CONCURRENTLY (non-blocking)
Changing column type       → USUALLY requires 3 phases (verify compatibility)
```

**Output:** 3-phase migration plan (Expand → Backfill → Contract) with go/no-go criteria between phases.

---

## Mode 5 — Spec-Driven

**Spec template (write before coding — not after):**

```markdown
# Feature Spec: [Feature Name]

## Problem
[One paragraph: what user pain does this solve?]

## Goal
[Measurable outcome: "User can do X without Y friction"]

## Non-Goals
[Explicitly what we are NOT building in this version]

## User Stories
- As a [user type], I want to [action] so that [benefit]
- As a [user type], I want to [action] so that [benefit]

## Acceptance Criteria
- [ ] [Testable behavior 1]
- [ ] [Testable behavior 2]
- [ ] [Edge case handled]

## Technical Approach
[2-3 sentences on implementation strategy — not full design doc]

## Open Questions
- [Unresolved decision 1] — Owner: Bond — Due: [date]

## Rollout
- Phase 1: [subset of functionality]
- Phase 2: [full functionality]
```

**Rule:** No implementation begins until acceptance criteria are written and reviewed.

---

## Global Rules

- Every release has a runbook — no exceptions for production
- Breaking changes require MAJOR bump — never sneak them into MINOR
- Changelog is user-facing: write for the person upgrading, not the developer who coded it
- Migration plans must include explicit rollback criteria (not just rollback steps)
