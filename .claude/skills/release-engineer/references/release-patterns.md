# Release Patterns

## Semantic Versioning (SemVer)

```
MAJOR.MINOR.PATCH  →  2.1.3

MAJOR: breaking changes (remove endpoint, change required field, rename type)
MINOR: new features, backward-compatible (new endpoint, new optional field)
PATCH: bug fixes only (behavior unchanged, just correct)

Pre-release: 2.0.0-alpha.1, 2.0.0-beta.3, 2.0.0-rc.1
Initial development: 0.x.x — anything can change, no stability guarantee
First public API: 1.0.0 — stability contract begins
```

### Version Bump Decision Tree
```
git log v1.2.3..HEAD --oneline | ask:

1. Any BREAKING CHANGE in any commit message? → MAJOR
2. Any feat: or feature: commit? → MINOR  
3. Only fix:, chore:, docs:, refactor:, perf: commits? → PATCH

Special:
  - Security patch only → PATCH (even if it changes behavior slightly)
  - New dependency that requires runtime upgrade → MAJOR
  - Performance improvement with no API change → PATCH
```

### Git Tags
```bash
# Create annotated tag (preferred — includes message + author)
git tag -a v1.3.0 -m "Release v1.3.0: Memory search improvements"

# Push tag to remote
git push origin v1.3.0

# List recent tags
git tag -l "v*" | sort -V | tail -10

# Get last tag
git describe --tags --abbrev=0
```

## Conventional Commits

**Format:** `<type>(<optional scope>): <description>`

```
feat: add semantic search to memory retrieval
fix: correct cursor pagination for empty results
feat!: remove legacy v1 API endpoints     ← ! = breaking change
fix(auth): resolve JWT expiry edge case
chore: update dependencies
docs: add API authentication guide
perf: reduce memory retrieval latency by 40%
refactor: extract search logic into service class
test: add integration tests for payment webhook
ci: add security scan to CI pipeline
```

**Footer for breaking changes:**
```
feat!: rename users endpoint to accounts

BREAKING CHANGE: /api/users is now /api/accounts.
Migration: update all client references from /api/users to /api/accounts.
```

### Parsing Commits for Changelog
```bash
# Commits since last tag
git log $(git describe --tags --abbrev=0)..HEAD --pretty=format:"%h %s"

# Group by type (manual or with standard-version)
git log v1.2.0..HEAD --oneline | grep "^feat"   # features
git log v1.2.0..HEAD --oneline | grep "^fix"    # fixes
git log v1.2.0..HEAD --oneline | grep "BREAKING" # breaking changes
```

## Changelog Format (Keep a Changelog standard)

```markdown
# Changelog

All notable changes to this project will be documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]
### Added
- [description of unreleased features]

## [1.3.0] — 2026-05-01
### Added
- Memory search now supports tag filtering (#42)
- Export to PDF for shared note bundles (#38)

### Changed
- Memory retrieval 40% faster via improved vector indexing
- Dashboard now shows last 7 days of activity by default

### Deprecated
- `/api/v1/search` — use `/api/v2/search` instead. Will be removed in 2.0.0.

### Fixed  
- Fixed crash when uploading empty files (#45)
- Correct pagination cursor on empty result sets (#41)

### Security
- Updated axios 1.6.0 → 1.7.4 (patches CVE-2024-12345)

## [1.2.3] — 2026-04-15
### Fixed
- Correct rate limiting behavior for authenticated users

[Unreleased]: https://github.com/user/repo/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/user/repo/compare/v1.2.3...v1.3.0
```

**Writing rules:**
- Write for the person upgrading, not the developer who coded it
- "Added", "Changed", "Deprecated", "Removed", "Fixed", "Security" — these 6 categories only
- Describe what it does, not how it was implemented
- Link to issue numbers where relevant
- Breaking changes in "Removed" + migration note

## Release Checklist

```markdown
## Pre-Release
- [ ] All tests passing in CI (unit + integration + E2E)
- [ ] CHANGELOG.md updated with this version's changes
- [ ] Version bumped in package.json / pyproject.toml
- [ ] Breaking changes have migration guide
- [ ] Dependent services notified (if API changes)
- [ ] Runbook written for this deployment

## Release
- [ ] Tag created: `git tag -a v1.3.0 -m "Release v1.3.0"`
- [ ] Tag pushed: `git push origin v1.3.0`
- [ ] GitHub Release created from tag (copy CHANGELOG section)
- [ ] Docker image tagged and pushed

## Post-Release
- [ ] Deployment verified in production (health check + smoke test)
- [ ] Error rate normal for 30min
- [ ] Key user flows tested in production
- [ ] Notify users/team of release (if significant)
```

## Git Flow — Simplified (Solo/Small Team)

```
main         — production, tagged releases only
feature/X    — individual features, merge to main via PR
hotfix/X     — emergency fixes, merge directly to main + tag

Release process:
  1. feature/memory-search → PR → code review → merge to main
  2. Bump version in package.json
  3. Update CHANGELOG.md  
  4. Commit: "chore: release v1.3.0"
  5. Tag: git tag -a v1.3.0 -m "Release v1.3.0"
  6. Push: git push && git push --tags
  7. CI deploys from tag
```
