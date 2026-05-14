---
name: engineer
description: Full-stack engineering skill covering frontend (React/Next.js), backend (REST/GraphQL APIs), architecture design, debugging, and code quality enforcement. Auto-invoke when Bond asks to build a feature, scaffold a project, design system architecture, debug broken code, choose a tech stack, review code quality, or enforce Karpathy's coding discipline. Trigger phrases: "scaffold a project", "build this feature", "design the architecture", "debug this", "is this over-engineered", "what stack should I use", "create a component", "optimize this API", "review my code before I commit", "audit accessibility", "clean architecture", "monolith vs microservices".
---

# Engineer

Full-stack engineering from React components to system architecture. Five modes: **build**, **architect**, **debug**, **audit**, **review**.

---

## Mode 1 — Build (Frontend + Backend)

**Building a landing page or full SaaS scaffold?** → `references/build-variants.md`

**Responding to an RFP, building a competitive feature matrix, or planning a POC?** → `references/sales-engineering.md`

### Frontend — React / Next.js

**Project scaffold:**
```bash
# Next.js App Router + TypeScript + Tailwind
npx create-next-app@latest my-app --typescript --tailwind --app --src-dir

# Add key dependencies
npm install zod react-hook-form @tanstack/react-query lucide-react
npm install -D @testing-library/react vitest
```

**Stack decisions:**
| Need | Pick |
|------|------|
| SEO + SSR | Next.js App Router |
| SPA / dashboard | React + Vite |
| State management | Zustand (simple) or Jotai (atomic) |
| Forms + validation | React Hook Form + Zod |
| Data fetching | TanStack Query |
| UI primitives | Radix UI / shadcn/ui |
| Styling | Tailwind CSS + cn() utility |

**Component patterns:**

```tsx
// Server Component (default — no 'use client')
async function ProductPage({ params }: { params: { id: string } }) {
  const product = await getProduct(params.id);
  return (
    <div>
      <h1>{product.name}</h1>
      <AddToCartButton productId={product.id} />
    </div>
  );
}

// Client Component — only when you need events/state/effects
'use client';
function AddToCartButton({ productId }: { productId: string }) {
  const [adding, setAdding] = useState(false);
  return <button onClick={() => addToCart(productId)}>Add to cart</button>;
}
```

**Custom hook pattern:**
```tsx
function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}
```

**TypeScript patterns:**
```tsx
// Generic list component
interface ListProps<T> {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
  keyExtractor: (item: T) => string;
}
function List<T>({ items, renderItem, keyExtractor }: ListProps<T>) {
  return <ul>{items.map(item => <li key={keyExtractor(item)}>{renderItem(item)}</li>)}</ul>;
}
```

---

### Backend — REST / GraphQL APIs

**Express/Fastify API pattern:**
```typescript
// Route with Zod validation
import { z } from 'zod';

const CreateUserSchema = z.object({
  email: z.string().email().max(255),
  name: z.string().min(1).max(100),
});

app.post('/users', async (req, res) => {
  const data = CreateUserSchema.parse(req.body);  // throws ZodError if invalid
  const user = await userService.create(data);
  res.status(201).json({ data: user });
});
```

**API response format (standardized):**
```json
// Success
{ "data": { "id": 1, "name": "Bond" }, "meta": { "requestId": "abc-123" } }

// Error
{ "error": { "code": "VALIDATION_ERROR", "message": "Invalid email", "details": [{ "field": "email", "message": "must be valid email" }] } }
```

**HTTP status codes:**
| Code | When |
|------|------|
| 200 | GET/PUT/PATCH success |
| 201 | POST (created) |
| 204 | DELETE (no content) |
| 400 | Validation error |
| 401 | Not authenticated |
| 403 | Not authorized |
| 404 | Not found |
| 429 | Rate limited |
| 500 | Server error |

**Security hardening:**
```typescript
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';

app.use(helmet());
app.use('/api/', rateLimit({ windowMs: 15 * 60 * 1000, max: 100 }));
// Never hardcode secrets — always process.env.JWT_SECRET
// JWT: prefer RS256 (asymmetric), short expiry (1h), refresh token pattern
```

**Database index strategy:**
```sql
-- Equality lookup
CREATE INDEX idx_users_email ON users(email);
-- Multi-column (order: equality first, then range)
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
-- Partial (filtered)
CREATE INDEX idx_active_orders ON orders(created_at) WHERE status = 'active';
-- Covering (avoid table lookup)
CREATE INDEX idx_users_email_name ON users(email) INCLUDE (name);
```

---

## Mode 2 — Architect

### Architecture Pattern Selection

**Solo / small team (1-3 devs) → start with modular monolith:**
```
Modular Monolith
├── modules/
│   ├── users/     (controller + service + repo + types)
│   ├── payments/
│   └── products/
└── shared/        (db, auth, errors, logger)
```

**Scale signals to extract a service:**
1. Module has 10x different scaling need
2. Team needs independent deployment
3. Technology constraint forces separation

**Architecture pattern quick-pick:**
| Need | Pattern |
|------|---------|
| Rapid MVP | Modular Monolith |
| Independent team deploys | Microservices |
| Complex domain logic | DDD (Domain-Driven Design) |
| High read/write ratio gap | CQRS |
| Audit trail required | Event Sourcing |
| Third-party integrations | Hexagonal / Ports & Adapters |

**Database selection:**
```
PostgreSQL → Default. Structured data, ACID, complex queries.
MongoDB    → Flexible schema, document-oriented, rapid iteration.
Redis      → Cache, sessions, rate limits, pub/sub.
DynamoDB   → Serverless, auto-scaling, AWS-native.

Scale thresholds:
<1M rows     → PostgreSQL, single instance
1M-100M rows → PostgreSQL + read replicas
>100M rows   → CockroachDB / DynamoDB / Cassandra
```

**ADR template (Architecture Decision Record):**
```markdown
## ADR-001: [Title]
**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Superseded

**Context:** [Problem being solved]
**Decision:** [What was decided]
**Rationale:** [Why this option]
**Trade-offs:** [What we accept]
**Alternatives considered:** [What was rejected and why]
```

---

## Mode 3 — Debug

### Systematic debug loop (Karpathy discipline)

**Before touching code — state assumptions first:**
```
1. What behavior do I expect?
2. What behavior am I seeing?
3. What assumption might be wrong?
4. Where is the first point of divergence?
```

**Karpathy's 4 coding principles — apply before every commit:**

| Principle | Check |
|-----------|-------|
| **Think before coding** | Did I state my assumptions? Any silent interpretation choices? |
| **Simplicity first** | Could a senior engineer say this is overcomplicated? |
| **Surgical changes** | Does every changed line trace to the user's request? |
| **Goal-driven** | Do I have verifiable success criteria? |

**Debug workflow:**
```bash
# 1. Reproduce: write a failing test first
# 2. Isolate: binary search — is it the input, transport, or logic?
# 3. Check assumptions: log the actual values, not what you think they are
# 4. Fix: minimum change to make the test pass
# 5. Verify: re-run full test suite
```

**N+1 query detection:**
```typescript
// BAD — N+1
const users = await db.query('SELECT * FROM users');
for (const user of users) {
  user.orders = await db.query('SELECT * FROM orders WHERE user_id = ?', [user.id]);
}

// GOOD — single join or DataLoader
const users = await db.query(`
  SELECT u.*, json_agg(o.*) as orders
  FROM users u
  LEFT JOIN orders o ON o.user_id = u.id
  GROUP BY u.id
`);
```

---

## Mode 4 — Audit

### Bundle analysis checklist
```
Heavy dependencies to replace:
moment (290KB)    → date-fns (12KB) or dayjs (2KB)
lodash (71KB)     → lodash-es with tree-shaking
axios (14KB)      → native fetch or ky (3KB)
@mui/material     → shadcn/ui or Radix UI

Next.js config optimization:
experimental.optimizePackageImports: ['lucide-react', '@heroicons/react']
images.formats: ['image/avif', 'image/webp']
```

### Accessibility audit (WCAG 2.2)

**Critical checks:**
```tsx
// 1. Semantic HTML
<button type="button">  // not <div onClick>
<nav>, <main>, <section aria-label="...">

// 2. Keyboard accessibility
className="focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none"

// 3. ARIA for icon-only buttons
<button aria-label="Close dialog">
  <XIcon aria-hidden="true" />
</button>

// 4. Skip link
<a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4">
  Skip to main content
</a>

// 5. Color contrast: 4.5:1 minimum for normal text, 3:1 for large text
```

### Code quality scoring

| Score | Grade | Action |
|-------|-------|--------|
| 90-100 | A | Ship it |
| 80-89 | B | Minor cleanup |
| 70-79 | C | Refactor before next feature |
| <70 | D/F | Stop. Fix now. |

---

## Mode 5 — Review

### Pre-commit review checklist

Run before every non-trivial commit:

- [ ] Every changed line traces to the request (no drive-by refactors)
- [ ] No abstractions for single-use code
- [ ] No error handling for impossible scenarios
- [ ] No hardcoded secrets (`process.env.*` only)
- [ ] Input validated at the boundary (Zod, not manual checks)
- [ ] No `any` types in TypeScript without justification
- [ ] N+1 queries eliminated
- [ ] Tests cover the new behavior

### Complexity red flags
```
Cyclomatic complexity > 10 → extract or simplify
Nesting depth > 4 → refactor
File > 300 lines → split by concern
Function > 30 lines → extract helpers
```

---

## Quick Reference

### Next.js config
```js
const nextConfig = {
  images: {
    remotePatterns: [{ hostname: 'cdn.example.com' }],
    formats: ['image/avif', 'image/webp'],
  },
  experimental: {
    optimizePackageImports: ['lucide-react'],
  },
};
```

### Tailwind cn() pattern
```tsx
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Usage
<button className={cn('px-4 py-2 rounded', variant === 'primary' && 'bg-blue-500', disabled && 'opacity-50')} />
```

### Fullstack stack decision matrix
| Project type | Stack |
|---|---|
| SEO-critical SaaS | Next.js App Router + Prisma + PostgreSQL |
| Internal tool / dashboard | React + Vite + Express + PostgreSQL |
| API-first backend | FastAPI (Python) or Fastify (Node) |
| MVP with auth | Next.js + Auth.js + Neon (serverless PG) |
| Real-time features | Next.js + Socket.io or Supabase Realtime |

---

## References

- [React & Next.js patterns](references/react-nextjs-patterns.md)
- [API design & backend patterns](references/backend-patterns.md)
- [Architecture patterns & ADR guide](references/architecture-patterns.md)
- [Karpathy coding principles](references/karpathy-principles.md)
- [Landing page & SaaS scaffold variants](references/build-variants.md)
- [RFP analysis, competitive matrix & POC planning](references/sales-engineering.md)
