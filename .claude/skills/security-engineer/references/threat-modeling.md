# Threat Modeling

## STRIDE Framework

| Threat | What It Means | Example |
|---|---|---|
| **S**poofing | Impersonating another actor/system | Forged JWT, stolen session token |
| **T**ampering | Modifying data in transit or at rest | Request body manipulation, DB record edit |
| **R**epudiation | Denying an action occurred | No audit log, unverifiable transactions |
| **I**nformation Disclosure | Unauthorized data exposure | API returns other users' data, verbose error messages |
| **D**enial of Service | Making system unavailable | Rate limit bypass, resource exhaustion |
| **E**levation of Privilege | Gaining higher permissions | IDOR, JWT role manipulation |

## Data Flow Diagram Elements

```
[External Actor] → (Process) → [Data Store]
         ↕
  ─ ─ ─ ─ ─ ─  Trust Boundary
         ↕
(External Service)
```

**Trust boundary rule:** Every time data crosses a trust boundary, it must be validated and authorized.

## STRIDE Analysis Template

For each component in the system, apply all 6 threats:

```
Component: User Authentication Service
Data flows:
  - Browser → API (login credentials)
  - API → Database (user lookup)
  - API → JWT issuer (token creation)
  - API → Redis (session cache)

Trust boundaries:
  - Internet → API server (boundary 1)
  - API server → Database (boundary 2)

STRIDE Analysis:
  S - Spoofing: Can someone forge a valid JWT? → Sign with strong secret, RS256 preferred
  T - Tampering: Can JWT payload be modified? → Validate signature, don't trust unverified claims
  R - Repudiation: Are login attempts logged with IP/timestamp? → Yes: add audit log
  I - Disclosure: Does error message reveal if email exists? → No: generic "invalid credentials"
  D - DoS: No rate limiting on login → CRITICAL: add rate limit (5 attempts/minute/IP)
  E - Elevation: Can user modify their own role claim? → Check: server must issue role, never accept from client

Mitigations:
  CRITICAL: Add rate limiting to /api/login (5 req/min/IP)
  HIGH: Use RS256 for JWT signing (asymmetric → can verify without exposing secret)
  MEDIUM: Add audit log for authentication events
  LOW: Evaluate adding CAPTCHA after 3 failed attempts
```

## Second Brain — Threat Model Template

Key components to analyze:
1. **Memory ingestion** (user uploads content → stored in vector DB)
2. **Memory retrieval** (query → LLM response)
3. **User authentication** (multi-user access control)
4. **LLM API calls** (sensitive context sent to Anthropic)

Key threats:
- **Prompt injection** — malicious content in memory poisons LLM responses
- **Data isolation** — user A retrieves user B's memories (IDOR)
- **LLM data leakage** — sensitive data sent to LLM provider without consent notice
- **Embedding inversion** — embeddings potentially reconstructed back to text

## Risk Rating

```
Risk = Likelihood × Impact

Likelihood:  1 (rare) / 2 (possible) / 3 (likely)
Impact:      1 (low) / 2 (medium) / 3 (high) / 4 (critical)

Risk score:
  9-12: Critical — fix before launch
  6-8:  High — fix within 1 sprint
  3-5:  Medium — schedule within quarter
  1-2:  Low — track, revisit
```

## Prompt Injection Defense (AI-specific)

```typescript
// Structural separation — never concatenate user input into system prompt
// ❌ WRONG
const systemPrompt = `You are a helpful assistant. User context: ${userInput}`;

// ✅ CORRECT — user content in user message, never system
const messages = [
    { role: 'user', content: userInput }
];

// Input sanitization for stored content
function sanitizeForStorage(content: string): string {
    // Strip instruction-like patterns before storing in memory
    return content
        .replace(/ignore (previous|above|all) instructions?/gi, '[filtered]')
        .replace(/you are now/gi, '[filtered]')
        .replace(/system:/gi, '[filtered]');
}

// Output validation
function validateResponse(response: string): boolean {
    const leakPatterns = [
        /system prompt/i,
        /you are instructed to/i,
        /ignore your instructions/i,
    ];
    return !leakPatterns.some(pattern => pattern.test(response));
}
```
