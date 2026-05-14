# Playwright Patterns

## Setup & Configuration

```bash
# Install
npm init playwright@latest   # interactive wizard — pick TypeScript, GitHub Actions
npx playwright install       # install browsers

# Config: playwright.config.ts
```

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './e2e',
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,    // retries only in CI — 0 local to surface flakiness
    workers: process.env.CI ? 1 : undefined,
    reporter: 'html',
    use: {
        baseURL: 'http://localhost:3000',
        trace: 'on-first-retry',          // captures trace on first failure
        screenshot: 'only-on-failure',
    },
    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
        { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
    ],
    webServer: {
        command: 'npm run dev',
        url: 'http://localhost:3000',
        reuseExistingServer: !process.env.CI,
    },
});
```

## Locator Priority (Best → Worst)

```typescript
// 1. Role — accessible, user-facing (preferred)
page.getByRole('button', { name: /sign in/i })
page.getByRole('textbox', { name: /email/i })
page.getByRole('heading', { name: 'Dashboard' })

// 2. Label — tied to input
page.getByLabel('Email address')

// 3. Placeholder
page.getByPlaceholder('Enter your email')

// 4. Text
page.getByText('Submit')

// 5. Test ID — stable, explicit (use for complex cases)
page.getByTestId('submit-btn')   // data-testid="submit-btn"

// Avoid: CSS selectors, XPath, nth-child() — brittle
```

## Page Object Model (3+ interactions → extract POM)

```typescript
// e2e/page-objects/LoginPage.ts
import { Page, expect } from '@playwright/test';

export class LoginPage {
    readonly page: Page;

    constructor(page: Page) { this.page = page; }

    async goto() {
        await this.page.goto('/login');
    }

    async login(email: string, password: string) {
        await this.page.getByLabel('Email').fill(email);
        await this.page.getByLabel('Password').fill(password);
        await this.page.getByRole('button', { name: /sign in/i }).click();
    }

    async expectError(message: string) {
        await expect(this.page.getByText(message)).toBeVisible();
    }
}

// e2e/auth.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from './page-objects/LoginPage';

test('redirects to dashboard on valid login', async ({ page }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.login('bond@example.com', 'password123');
    await expect(page).toHaveURL('/dashboard');
});
```

## Authentication — Save State

```typescript
// e2e/auth.setup.ts — run once, saves auth state
import { test as setup } from '@playwright/test';

setup('authenticate', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill(process.env.TEST_EMAIL!);
    await page.getByLabel('Password').fill(process.env.TEST_PASSWORD!);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await page.waitForURL('/dashboard');
    await page.context().storageState({ path: 'e2e/.auth/user.json' });
});

// playwright.config.ts — reuse for all tests
projects: [
    { name: 'setup', testMatch: /.*\.setup\.ts/ },
    {
        name: 'authenticated',
        use: { storageState: 'e2e/.auth/user.json' },
        dependencies: ['setup'],
    },
],
```

## Flaky Test Diagnosis & Fixes

| Symptom | Root Cause | Fix |
|---|---|---|
| `TimeoutError: Locator not found` | Element not yet in DOM | Use `waitFor: 'visible'` or `expect(locator).toBeVisible()` |
| Passes locally, fails in CI | Race condition | Add explicit `waitFor` before assertion |
| Fails on specific browser | CSS/JS difference | Check cross-browser; add `--project chromium` flag locally |
| Passes alone, fails in suite | Test isolation problem | Clear state in `beforeEach`; check shared storage |
| Random order failures | Hard dependency on test order | Each test must be independent; no `test.describe.serial` |

```typescript
// Anti-pattern: raw waits
await page.waitForTimeout(2000);  // NEVER — timing dependency

// Fix: condition-based wait
await expect(page.getByText('Loaded')).toBeVisible();
await page.waitForURL('**/dashboard');
await page.waitForResponse(resp => resp.url().includes('/api/data'));
```

## GitHub Actions CI

```yaml
# .github/workflows/playwright.yml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: 'npm' }
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test
        env:
          TEST_EMAIL: ${{ secrets.TEST_EMAIL }}
          TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
      - uses: actions/upload-artifact@v4
        if: ${{ !cancelled() }}
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```
