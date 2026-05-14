---
name: security-engineer
description: >
  Application security covering threat modeling (STRIDE), secure code review (OWASP), dependency
  vulnerability scanning (CVE), and secrets management. For web apps, APIs, and AI systems.

  Auto-invoke when Bond asks: security review, threat model, STRIDE, vulnerability, CVE, security audit,
  OWASP, injection attack, SQL injection, XSS, CSRF, authentication security, authorization, JWT security,
  dependency audit, npm audit, snyk, secrets in code, secret leak, env file, .env security, rate limiting,
  password hashing, encryption, secure architecture, zero trust, penetration test considerations,
  "is this secure", "how do I secure", secure this API, protect against attacks.
---

# Security Engineer

Four modes: **Threat Model** (STRIDE + data flow), **Code Audit** (OWASP checklist), **Dependency Scan** (CVE triage), **Secrets Audit** (detection + remediation).

Reference files:
- `references/threat-modeling.md` — STRIDE framework, data flow diagrams, trust boundaries
- `references/secure-coding.md` — OWASP Top 10 patterns, auth/crypto, input validation

---

## Mode Detection

| Input | Mode |
|---|---|
| "threat model", "STRIDE", "data flow", "attack surface", "trust boundary" | **Threat Model** |
| "security review", "OWASP", "injection", "XSS", "is this secure", code pasted | **Code Audit** |
| "dependency", "CVE", "npm audit", "snyk", "vulnerable package" | **Dependency Scan** |
| "secret", ".env", "API key in code", "credential", "secret leak" | **Secrets Audit** |

---

## Mode 1 — Threat Model

Read `references/threat-modeling.md` fully before executing.

**Workflow:**
1. Map the system: external actors → processes → data stores → external services
2. Identify trust boundaries: where data crosses trust zones
3. Apply STRIDE to each component: Spoofing / Tampering / Repudiation / Info Disclosure / DoS / Elevation
4. Rate each threat: Likelihood × Impact (High/Medium/Low)
5. Output: threat list with mitigations, prioritized by risk

---

## Mode 2 — Code Audit

Read `references/secure-coding.md` fully before executing.

**Checklist order (highest risk first):**
1. Injection (SQL, command, LDAP) — input reaches query without sanitization?
2. Broken authentication — JWT weak signing? Session fixation? Missing expiry?
3. Sensitive data exposure — PII/tokens in logs? Unencrypted storage? Weak crypto?
4. Missing access control — can user A access user B's data?
5. Insecure defaults — debug mode in prod? Verbose errors to client?
6. Secrets in code — hardcoded credentials, API keys?

**For every finding:** report Location (file:line) + Severity (Critical/High/Medium/Low) + Exploit scenario + Fix

---

## Mode 3 — Dependency Scan

```bash
# Node.js
npm audit --audit-level=high    # fail on high+ severity
npx snyk test                   # richer CVE context

# Python
pip-audit                        # pip install pip-audit
safety check                     # safety check -r requirements.txt

# Docker image scan
trivy image my-app:latest
```

**Triage priority:**
1. Critical/High + exploitable remotely → fix immediately (block deployment)
2. High + requires local access → patch within 1 sprint
3. Medium + has fixed version available → schedule in next sprint
4. Low → log, revisit quarterly

**Resolution options:** update to patched version → add override if false positive → replace library if no fix

---

## Mode 4 — Secrets Audit

```bash
# Scan for secrets in codebase
npx detect-secrets scan .        # Yelp detect-secrets
git secrets --scan               # AWS git-secrets
trufflesecurity/trufflehog .     # TruffleHog — scans git history

# If secret found in git history
# 1. Rotate the secret IMMEDIATELY (before cleaning history)
# 2. Clean history: git filter-repo --replace-text replacements.txt
# 3. Force push (coordinate with team)
# 4. Verify: rescan after cleanup
```

**Secret storage patterns (most → least secure):**
1. AWS Secrets Manager / GCP Secret Manager / Azure Key Vault
2. Doppler / HashiCorp Vault
3. CI/CD environment secrets (GitHub Actions Secrets)
4. `.env` local dev only — gitignored, never in repo
5. Hardcoded → **never acceptable**

---

## Global Rules

- Security findings rated Critical/High block deployment — not optional
- Never store PII in logs — mask before logging (`email@***.com`, `token: [REDACTED]`)
- Auth checks at every layer: route middleware + service layer + DB query level (defense in depth)
- Dependency audit runs in CI on every PR — automated, not manual
- NEVER commit `.env` files. If already committed, treat as breached: rotate secret first, then clean history
