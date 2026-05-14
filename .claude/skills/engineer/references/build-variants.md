# Build Variants — Landing Page & SaaS Scaffold

Extended patterns for Mode 1 (Build) — activate when user asks for a full landing page or a SaaS boilerplate scaffold.

---

## Variant A: Landing Page (Next.js TSX + Tailwind)

### When to use
Trigger phrases: "build a landing page", "landing page for X", "marketing page", "hero section", "conversion page".

### Design Style Selection

| Style | When | Aesthetic |
|---|---|---|
| `dark-saas` | Dev tools, AI products, technical SaaS | Dark bg, neon accent, monospace |
| `clean-minimal` | Professional services, B2B, consulting | White bg, generous whitespace, serif headings |
| `bold-startup` | Consumer, Gen Z, playful brands | Saturated colors, large type, asymmetric layout |
| `enterprise` | Fortune 500, compliance-heavy, regulated | Navy/grey, structured grid, formal copy |

### Section Generator Checklist

Build sections in this order. Each is a separate TSX file in `components/landing/`.

```
1. Nav         → sticky header, logo, links, primary CTA button
2. Hero        → headline + subheadline + CTA + supporting visual
3. Features    → 3-6 feature cards (icon + title + 2-line description)
4. Testimonials → 3+ quotes with name, role, company
5. Pricing     → 2-4 tier cards with toggle (monthly/annual), highlighted recommended
6. FAQ         → accordion with JSON-LD schema for SEO
7. CTA         → final conversion section — repeat primary CTA
8. Footer      → links, legal, socials
```

### Hero Section Variants

**Pattern 1 — Problem-Solution:**
Headline names the painful problem. Subheadline states the outcome. CTA starts immediately.

**Pattern 2 — Outcome-First:**
Lead with measurable value ("Save 10 hours/week"). Clarify who it's for. CTA is action-specific.

**Pattern 3 — Authority:**
Headline + trust indicator (logos, proof metric, testimonial snippet). Use when category skepticism is high.

### Copy Frameworks

**PAS (Problem-Agitate-Solution):**
"Still [problem]? Stop [negative consequence] and start [desired outcome]."

**AIDA (Attention-Interest-Desire-Action):**
Headline pattern-interrupts → stakes → proof + benefits → concrete next step.

**4U Formula:**
"Get [specific result] in [timeframe] without [common pain]." (Useful + Urgent + Unique + Ultra-specific)

**BAB (Before-After-Bridge):**
Describe the before state → the after state → how the product bridges them.

### Performance Targets

| Metric | Target |
|---|---|
| LCP (Largest Contentful Paint) | < 1s |
| CLS (Cumulative Layout Shift) | < 0.1 |
| FID (First Input Delay) | < 100ms |
| TTFB | < 200ms |
| JS bundle | < 100KB |

Optimization checklist:
- [ ] Images: `next/image` with `priority` on hero image, `webp`/`avif` formats
- [ ] Fonts: `next/font` with `display: swap`, subset only used characters
- [ ] Dynamic imports: `next/dynamic` for below-fold heavy components
- [ ] No layout shift: explicit width/height on all images

### SEO Checklist

- [ ] `<title>` and `<meta description>` in `layout.tsx`
- [ ] `<h1>` appears exactly once
- [ ] FAQ section has JSON-LD schema (`@type: FAQPage`)
- [ ] `sitemap.xml` and `robots.txt` configured
- [ ] OG tags: `og:title`, `og:description`, `og:image`

---

## Variant B: SaaS Scaffold (Next.js 14+ App Router)

### When to use
Trigger phrases: "SaaS boilerplate", "scaffold a SaaS app", "Next.js + auth + Stripe", "production SaaS starter".

### Stack

| Layer | Choice |
|---|---|
| Framework | Next.js 14+ App Router + TypeScript |
| Auth | NextAuth v5 (Auth.js) with DrizzleAdapter |
| Database | Drizzle ORM + NeonDB (serverless PostgreSQL) |
| Payments | Stripe Checkout + Webhook handling |
| UI | shadcn/ui + Tailwind CSS |
| Email | Resend (transactional) |

### File Structure

```
my-saas/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx          # sidebar + header shell
│   │   ├── page.tsx            # dashboard home
│   │   ├── settings/page.tsx
│   │   └── billing/page.tsx
│   ├── (marketing)/
│   │   └── page.tsx            # landing page
│   ├── api/
│   │   ├── auth/[...nextauth]/route.ts
│   │   └── webhooks/stripe/route.ts
│   └── layout.tsx
├── components/
│   ├── ui/                     # shadcn primitives
│   ├── dashboard/              # dashboard-specific components
│   └── landing/                # marketing page sections
├── lib/
│   ├── auth.ts                 # NextAuth config
│   ├── db.ts                   # Drizzle client
│   ├── stripe.ts               # Stripe client
│   └── utils.ts                # cn(), formatDate(), etc.
├── db/
│   ├── schema.ts               # Drizzle schema
│   └── migrations/
├── middleware.ts               # route protection
└── .env.example
```

### Key Code Patterns

**Auth config (NextAuth + DrizzleAdapter):**
```typescript
// lib/auth.ts
import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import { DrizzleAdapter } from "@auth/drizzle-adapter";
import { db } from "@/lib/db";

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: DrizzleAdapter(db),
  providers: [Google],
  callbacks: {
    session: ({ session, user }) => ({
      ...session,
      user: { ...session.user, id: user.id },
    }),
  },
});
```

**Database schema (core entities):**
```typescript
// db/schema.ts
import { pgTable, text, timestamp, boolean } from "drizzle-orm/pg-core";

export const users = pgTable("users", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  name: text("name"),
  email: text("email").notNull().unique(),
  emailVerified: timestamp("email_verified"),
  image: text("image"),
  stripeCustomerId: text("stripe_customer_id"),
  subscriptionStatus: text("subscription_status").default("free"),
  createdAt: timestamp("created_at").defaultNow(),
});
```

**Stripe Checkout route:**
```typescript
// app/api/checkout/route.ts
import { auth } from "@/lib/auth";
import { stripe } from "@/lib/stripe";

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user?.id) return new Response("Unauthorized", { status: 401 });

  const checkoutSession = await stripe.checkout.sessions.create({
    customer_email: session.user.email!,
    line_items: [{ price: process.env.STRIPE_PRICE_ID, quantity: 1 }],
    mode: "subscription",
    success_url: `${process.env.NEXT_PUBLIC_URL}/dashboard?upgraded=true`,
    cancel_url: `${process.env.NEXT_PUBLIC_URL}/billing`,
    metadata: { userId: session.user.id },
  });

  return Response.json({ url: checkoutSession.url });
}
```

**Stripe webhook (idempotent handling):**
```typescript
// app/api/webhooks/stripe/route.ts
import { stripe } from "@/lib/stripe";
import { db } from "@/lib/db";
import { users } from "@/db/schema";
import { eq } from "drizzle-orm";

export async function POST(req: Request) {
  const body = await req.text();
  const sig = req.headers.get("stripe-signature")!;

  let event;
  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch {
    return new Response("Invalid signature", { status: 400 });
  }

  if (event.type === "checkout.session.completed") {
    const session = event.data.object;
    await db.update(users)
      .set({ subscriptionStatus: "active", stripeCustomerId: session.customer as string })
      .where(eq(users.id, session.metadata!.userId));
  }

  if (event.type === "customer.subscription.deleted") {
    const subscription = event.data.object;
    await db.update(users)
      .set({ subscriptionStatus: "canceled" })
      .where(eq(users.stripeCustomerId, subscription.customer as string));
  }

  return new Response("OK");
}
```

**Middleware (route protection):**
```typescript
// middleware.ts
import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const isDashboard = req.nextUrl.pathname.startsWith("/dashboard");

  if (isDashboard && !isLoggedIn) {
    return NextResponse.redirect(new URL("/login", req.url));
  }
});

export const config = { matcher: ["/dashboard/:path*"] };
```

### Environment Variables

```bash
# .env.example
DATABASE_URL=postgresql://...
NEXTAUTH_SECRET=generate-with-openssl-rand-base64-32
NEXTAUTH_URL=http://localhost:3000
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
NEXT_PUBLIC_URL=http://localhost:3000
RESEND_API_KEY=re_...
```

### 5-Phase Scaffold Checklist

| Phase | Tasks | Validate |
|---|---|---|
| **1. Foundation** | Init Next.js, install deps, configure Tailwind + shadcn | `npm run dev` starts |
| **2. Database** | Set up Drizzle schema, run first migration, verify connection | `db.select()` returns [] |
| **3. Authentication** | Configure NextAuth, test sign-in flow, protect routes | Can sign in and see dashboard |
| **4. Payments** | Stripe Checkout route, webhook handler, update user status | Checkout completes, status updates |
| **5. UI** | Dashboard shell, sidebar, settings page, billing page | All routes render correctly |

### Multi-Tenant Considerations (when needed)

- Add `tenantId` column to all user-data tables — enforce in all queries
- Row-level security (RLS) in PostgreSQL: `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`
- Audit logs include `tenant_id` + `user_id` + `action` + `timestamp`
- Backups preserve tenant boundaries

### SaaS Database Schema Additions (beyond core auth)

```typescript
export const subscriptions = pgTable("subscriptions", {
  id: text("id").primaryKey(),
  userId: text("user_id").references(() => users.id),
  stripeSubscriptionId: text("stripe_subscription_id").unique(),
  status: text("status").notNull(), // active | canceled | past_due | trialing
  planId: text("plan_id"),
  currentPeriodEnd: timestamp("current_period_end"),
  createdAt: timestamp("created_at").defaultNow(),
});
```
