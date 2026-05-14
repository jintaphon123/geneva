---
name: api-architect
description: >
  REST API design review, MCP server scaffolding from OpenAPI specs, and Stripe payment integration.
  Covers API conventions, breaking change detection, versioning strategy, rate limiting design,
  and production-grade MCP tool definitions.

  Auto-invoke when Bond asks: API design, REST API review, API conventions, versioning, API contract,
  breaking changes, OpenAPI, MCP server, build an MCP server, MCP tool, expose API to Claude,
  Stripe, payment integration, Stripe webhook, Stripe checkout, billing, subscription, payment flow,
  "design this API", "is this API good", "how should I version", "MCP for this API".
---

# API Architect

Three modes: **Design** (REST review + conventions), **MCP** (server scaffolding), **Stripe** (payment integration).

Reference files:
- `references/api-design-patterns.md` — REST conventions, versioning, pagination, error responses
- `references/mcp-patterns.md` — MCP tool definitions, schema quality, auth strategy, evolution

---

## Mode Detection

| Input | Mode |
|---|---|
| "API design", "REST", "endpoint", "breaking change", "OpenAPI", "API review" | **Design** |
| "MCP server", "MCP tool", "expose API to Claude", "build MCP" | **MCP** |
| "Stripe", "payment", "checkout", "subscription", "webhook", "billing" | **Stripe** |

---

## Mode 1 — API Design Review

Read `references/api-design-patterns.md` fully before executing.

**Review checklist:**
1. Resource naming — plural nouns, kebab-case, no verbs in URLs
2. HTTP method semantics — GET safe/idempotent, POST create, PUT full replace, PATCH partial, DELETE
3. Status codes — correct use of 200/201/204/400/401/403/404/409/422/500
4. Pagination — cursor-based (preferred) or offset for small datasets
5. Versioning strategy — URL versioning (`/v1/`) or header (`Accept-Version`)
6. Error response consistency — same shape across all endpoints
7. Breaking change detection — removed fields, changed types, renamed endpoints

**For each issue:** Location (endpoint) + Severity + Impact + Fix

---

## Mode 2 — MCP Server

Read `references/mcp-patterns.md` fully before executing.

**Workflow:**
1. Start from OpenAPI spec (or describe endpoints if no spec)
2. Map operations → MCP tool definitions (name, description, input_schema)
3. Generate server scaffold (TypeScript or Python)
4. Design auth strategy: API key header injection vs OAuth token forwarding
5. Add validation + error mapping (HTTP errors → MCP error codes)

**Quality rules for tool definitions:**
- Name: verb_noun format (`get_user`, `create_order`, `search_documents`)
- Description: what it does + when to use it (not just restating the name)
- input_schema: every parameter typed + described, required[] explicit
- Never: expose internal IDs in tool names, leak implementation details in descriptions

---

## Mode 3 — Stripe Integration

**Stripe integration checklist:**

```
□ Server-side only: Stripe secret key NEVER in frontend
□ Webhook signature verification on every webhook handler
□ Idempotency keys on all payment-creation calls
□ Handle async events: payment_intent.succeeded, invoice.payment_failed
□ Store Stripe customer ID in your DB (don't recreate on each call)
□ Test with Stripe test mode + card numbers before going live
```

**Stack:** Stripe SDK + Next.js webhook handler — see code patterns below

### Checkout Session (one-time payment)
```typescript
import Stripe from 'stripe';
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

// Create checkout session
const session = await stripe.checkout.sessions.create({
    payment_method_types: ['card'],
    line_items: [{ price: priceId, quantity: 1 }],
    mode: 'payment',  // or 'subscription'
    success_url: `${process.env.NEXT_PUBLIC_URL}/success?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${process.env.NEXT_PUBLIC_URL}/pricing`,
    customer_email: user.email,
    metadata: { user_id: user.id },
});

return { url: session.url };  // redirect client to session.url
```

### Webhook Handler (Next.js App Router)
```typescript
// app/api/webhooks/stripe/route.ts
import { headers } from 'next/headers';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);
const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;

export async function POST(req: Request) {
    const body = await req.text();
    const sig = headers().get('stripe-signature')!;

    let event: Stripe.Event;
    try {
        event = stripe.webhooks.constructEvent(body, sig, webhookSecret);
    } catch {
        return new Response('Webhook signature verification failed', { status: 400 });
    }

    switch (event.type) {
        case 'checkout.session.completed': {
            const session = event.data.object as Stripe.Checkout.Session;
            await activateUserSubscription(session.metadata!.user_id);
            break;
        }
        case 'invoice.payment_failed': {
            const invoice = event.data.object as Stripe.Invoice;
            await handlePaymentFailure(invoice.customer as string);
            break;
        }
    }

    return new Response('OK');
}
```

---

## Global Rules

- API contract = public commitment: never remove a field without a deprecation cycle
- All mutation endpoints require auth — GET endpoints check auth on sensitive resources
- Stripe webhooks: always verify signature, always return 200 quickly (async processing)
- Pagination: always include total count and has_next_page in response
