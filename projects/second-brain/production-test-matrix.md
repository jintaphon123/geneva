# Production Test Matrix + CI Gate — 2026-05-14

Session 9 freezes the production gate for Second Brain Web Surface. The release command is now one command, repeatable locally and in CI:

```bash
cd /Users/jintaphon/Documents/Code/MyBrain/scratch/clawd-code/sb-ui
PYTHON=python npm run qa:production
```

## Current Verdict

**CONCERNS**: the gate is now real enough to block regressions, but this is not a final release candidate yet. The remaining production risks are reproducible Python dependency locking, lingering TestClient deprecation warnings, backend runtime size, authentication/packaged-local boundary, and final product polish.

## Production Matrix

| Gate | Command | Production failure it blocks | Latest result |
|------|---------|------------------------------|---------------|
| Frontend lint | `npm run lint` | Dead imports, hook mistakes, syntax drift, unsafe frontend edits | Pass |
| Frontend build + bundle | `npm run build` | TypeScript failures and production bundle breakage | Pass |
| Frontend dependency audit | `npm audit --omit=dev --audit-level=high` | High/critical production npm vulnerabilities | Pass, 0 vulnerabilities |
| Python dependency audit | `python scripts/python-dependency-audit.py` | Known CVEs in `requirements.txt` | Pass, no known vulnerabilities |
| Static production checks | `node scripts/production-static-check.mjs` | Bundle budgets, line budgets, unsafe browser APIs, secret placeholders, bloat regression | Pass, 81 files scanned |
| FastAPI gateway contracts | `python scripts/run-fastapi-contracts.py` | Web contract drift hidden by skipped TestClient tests | Pass, 47 tests, 0 skips |
| Backend contracts | `python -m pytest tests/test_second_brain_skills.py tests/test_second_brain_services.py tests/test_providers.py -q` | Skill/service/provider regressions | Pass, 56 tests |
| Visual smoke | `npm run visual:smoke` | Desktop/mobile/light/dark/project/skill/open-source/context regressions | Pass, 24 screenshots |
| Whitespace diff check | `git diff --check -- ...` | Dirty patch hygiene and trailing whitespace | Pass |

## CI Ownership

- Workflow: `/Users/jintaphon/Documents/Code/MyBrain/scratch/clawd-code/.github/workflows/second-brain-production.yml`
- Local gate: `/Users/jintaphon/Documents/Code/MyBrain/scratch/clawd-code/sb-ui/scripts/production-qa.mjs`
- Static gate: `/Users/jintaphon/Documents/Code/MyBrain/scratch/clawd-code/sb-ui/scripts/production-static-check.mjs`
- FastAPI no-skip helper: `/Users/jintaphon/Documents/Code/MyBrain/scratch/clawd-code/scripts/run-fastapi-contracts.py`
- Python audit helper: `/Users/jintaphon/Documents/Code/MyBrain/scratch/clawd-code/scripts/python-dependency-audit.py`
- Visual artifacts: `/Users/jintaphon/Documents/Code/MyBrain/scratch/clawd-code/sb-ui/test-results/visual-smoke/`
- QA report: `/Users/jintaphon/Documents/Code/MyBrain/scratch/clawd-code/sb-ui/test-results/production-qa/summary.json`

## Latest Verification

```text
PYTHON=python npm run qa:production
Pass in 55.6s
9/9 checks passed
24 visual screenshots generated
```

Important detail: the FastAPI gate now installs TestClient-only dependencies into `.qa-cache/fastapi-contracts` and fails if web tests still skip. This closes the previous false-green gap where `tests/test_second_brain_web.py` could pass while skipping FastAPI coverage.

Skipped production checks are also treated as failures. The gate can be slower, but it must not be fake-green.

## Remaining Risks

1. **Python dependency reproducibility is still weaker than npm.**
   `requirements.txt` uses broad ranges; `pip-audit` catches known CVEs, but CI still does not prove exact lock reproducibility.

2. **FastAPI/httpx deprecation warnings remain in contract tests.**
   The gate passes, but the warnings should be eliminated before release candidate so CI noise does not train the team to ignore warning output.

3. **Visual smoke is comprehensive but slow.**
   Current full gate takes about 56 seconds, mostly visual smoke. This is acceptable for PR/release gate, but Session 10 should consider splitting a quick PR gate from a full release gate only after coverage is preserved.

4. **Security is local-hardened, not authenticated product-grade.**
   Host/client/origin/mutation header controls exist, but a packaged commercial surface still needs auth/session boundary and desktop wrapper hardening.

5. **Backend runtime split is still deferred.**
   `session.py` and `web_runtime.py` remain high-risk architecture surfaces. They should be split only now that Session 9 has a gate capable of catching behavior drift.

## Blocked Until Fixed

- Do not ship without `npm run qa:production` passing.
- Do not accept FastAPI web changes if `run-fastapi-contracts.py` reports skipped tests.
- Do not add dependencies without both npm audit and Python audit passing.
- Do not merge project/chat/skill/sidebar UI changes unless visual smoke produces the 24 screenshot set.
