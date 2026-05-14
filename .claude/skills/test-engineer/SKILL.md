---
name: test-engineer
description: >
  Test strategy, TDD workflow, unit/integration testing (Jest, Vitest, pytest), Playwright E2E automation,
  API test suite generation, coverage analysis, and flaky test diagnosis for React/Next.js and Python apps.

  Auto-invoke when Bond asks: write tests, unit tests, integration tests, TDD, red-green-refactor,
  test coverage, coverage gaps, E2E tests, Playwright, flaky tests, test this component, API tests,
  test this endpoint, mock this, test fixture, set up Jest, set up Vitest, configure testing,
  "how do I test", test strategy, improve test quality, generate tests, scaffold tests.
---

# Test Engineer

Four modes: **Unit/Integration** (Jest/Vitest/pytest), **E2E** (Playwright), **TDD** (red-green-refactor workflow), **API** (endpoint test suites).

Reference files:
- `references/testing-patterns.md` — unit/integration patterns, mocks, fixtures, coverage
- `references/playwright-patterns.md` — E2E setup, page objects, flaky fix, CI
- `references/api-testing.md` — API test matrix, auth coverage, contract testing

---

## Mode Detection

| Input | Mode |
|---|---|
| "unit test", "component test", "mock", "RTL", "pytest", "test this function" | **Unit/Integration** |
| "E2E", "Playwright", "browser test", "flaky", "end-to-end" | **E2E** |
| "TDD", "red-green", "write test first", "failing test" | **TDD** |
| "API test", "test this endpoint", "contract test", "route test" | **API** |
| Coverage report or gap analysis requested | **Unit/Integration** + analyze coverage |

---

## Mode 1 — Unit & Integration Testing

Read `references/testing-patterns.md` fully before executing.

**Stack defaults:**
- TypeScript/React → Jest + React Testing Library + MSW (for API mocks)
- Node.js backend → Vitest + Supertest
- Python → pytest + httpx + pytest-mock

**Workflow:**
1. Identify: component, hook, util, or service under test
2. Determine test types needed: render, interaction, data, error path
3. Generate test file with describe blocks → happy path → error cases → edge cases
4. Add MSW handlers if component fetches data
5. Run coverage check: flag untested branches

**Coverage thresholds:** Statements 80% | Branches 75% | Functions 85% | Lines 80%

---

## Mode 2 — E2E (Playwright)

Read `references/playwright-patterns.md` fully before executing.

**Setup sequence:** `npx playwright install` → generate config → write first smoke test → wire CI

**Workflow:**
1. Identify user flow to test (auth, checkout, critical path)
2. Map selectors: prefer `getByRole` > `getByLabel` > `getByTestId` > CSS (last resort)
3. Write test with Page Object if flow has 3+ interactions
4. Run locally headless (`npx playwright test`)
5. Wire CI: see `references/playwright-patterns.md` for GitHub Actions config

---

## Mode 3 — TDD

Read `references/testing-patterns.md` (TDD section) fully before executing.

**Strict cycle:** RED (write failing test) → GREEN (minimal code to pass) → REFACTOR (clean up)

**Rules:**
- Never write implementation before a failing test exists
- Green phase: write *exactly* enough code — no extras
- Refactor phase: behavior must not change, all tests must still pass
- One test at a time — don't batch RED steps

**Applicable to:** new features, bug fixes (write test that reproduces bug first), refactors

---

## Mode 4 — API Testing

Read `references/api-testing.md` fully before executing.

**Workflow:**
1. Scan routes: extract all endpoints, HTTP methods, auth requirements
2. Generate test matrix: happy path + auth failure + validation errors + edge cases
3. Output test file (Vitest+Supertest or pytest+httpx)
4. Verify: 400/401/403/404/422/500 covered for each route

---

## Global Rules

- Tests are documentation — names must describe behavior, not implementation (`renders correctly` → `shows error message when email is invalid`)
- Never test implementation details — test user-visible behavior
- One assertion per test is ideal; never more than 3
- No `any` type in TypeScript tests
- Deterministic only — no `Math.random()`, no `Date.now()` without mocking
