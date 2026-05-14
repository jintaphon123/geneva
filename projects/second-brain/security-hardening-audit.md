# Session 7 — Security + Local Production Hardening

Date: 2026-05-13

## Verdict

Session 7 closed the biggest local-production security holes in the Second Brain web surface. The app now treats the browser UI as a local-only control plane: loopback host/client only, explicit remote-bind override, trusted mutation header, JSON-only mutation bodies, bounded request size, and security response headers on JSON, SSE, and static responses.

Verdict remains **CONCERNS**, not CLEAN, because this is still a local desktop security boundary. A future LAN/cloud deployment still needs real authentication, session authorization, CI-owned dependency audit, and packaged install verification.

## Critical Findings Fixed

1. Local web API trusted Host too much.
   - Fixed with Host validation against `localhost`, `127.0.0.0/8`, and `::1`.
   - Missing Host now fails closed.
   - Bad Host such as `evil.example` or `0.0.0.0` is rejected.

2. Web server could be bound to every network interface.
   - Fixed with `is_bind_host_allowed()`.
   - `--host 0.0.0.0` now raises unless `SECOND_BRAIN_ALLOW_REMOTE_BIND=1` is explicitly set.

3. Browser mutations had no trusted-request contract.
   - `POST`, `PUT`, and `DELETE` now require `X-Second-Brain-Request: 1`.
   - UI `jsonFetch`, chat SSE, research SSE, and visual smoke fixtures now send the same header.

4. Mutation bodies were not bounded or content-type-gated.
   - Body size is capped at 1 MB.
   - `POST` and `PUT` with a body must use JSON content.
   - Invalid `Content-Length` fails as an oversized request.

5. HTTP responses lacked a production security header baseline.
   - Added `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`, COOP, CORP, `Permissions-Policy`, and CSP.
   - Applied to JSON, SSE, static files, FastAPI responses, and error responses.

6. Python dependency audit found a real vulnerability.
   - `pip-audit -r requirements.txt` found `pyjwt 2.8.0` vulnerable via `CVE-2026-32597`.
   - Root cause: latest `zhipuai` still pins `pyjwt>=2.8.0,<2.9.0`, blocking the audited fix range.
   - Removed `zhipuai` from core dependencies.
   - Reworked `GLMProvider` to use the existing OpenAI-compatible client against GLM's OpenAI-style endpoint.
   - Added static gate protection so `zhipuai` cannot be reintroduced through manifests unnoticed.

## Files Changed

- `scratch/clawd-code/src/second_brain/web_api.py`
- `scratch/clawd-code/src/second_brain/web_server.py`
- `scratch/clawd-code/src/second_brain/fastapi_app.py`
- `scratch/clawd-code/sb-ui/src/lib/api.ts`
- `scratch/clawd-code/sb-ui/scripts/visual-smoke.mjs`
- `scratch/clawd-code/sb-ui/scripts/production-static-check.mjs`
- `scratch/clawd-code/src/providers/glm_provider.py`
- `scratch/clawd-code/pyproject.toml`
- `scratch/clawd-code/requirements.txt`
- `scratch/clawd-code/tests/test_second_brain_web.py`
- `scratch/clawd-code/tests/test_providers.py`

## Verification

- `python -m pytest tests/test_second_brain_web.py -q` — 39 passed, 8 skipped before temp FastAPI install
- `PYTHONPATH=/tmp/second-brain-fastapi-test:$PWD python -m pytest tests/test_second_brain_web.py -q` — 47 passed, 2 warnings
- `python -m pytest tests/test_second_brain_web.py tests/test_second_brain_skills.py tests/test_second_brain_services.py tests/test_providers.py -q` — 95 passed, 8 skipped
- `npm run lint` — pass
- `node scripts/production-static-check.mjs` — pass, 40 source/manifest files scanned
- `npm audit --omit=dev --audit-level=high --json` — 0 vulnerabilities
- `PYTHONPATH=/tmp/second-brain-pip-audit python -m pip_audit -r requirements.txt` — no known vulnerabilities found
- `PYTHON=python npm run qa:production` — pass

## Remaining Production Gaps

1. Local-only protection is not authentication.
   - The app is now safer for desktop local use, but a network deployment still needs signed local sessions or an auth token flow.

2. Dependency audit is proven manually, not yet first-class in the committed QA command.
   - Add a CI/dev dependency path for `pip-audit` before release candidate.

3. Requirements still use broad lower bounds.
   - Session 8/9 should introduce a lockfile or reproducible install path.

4. Open Source remains a control-plane preview.
   - It still needs real registry, publish queue, reuse search, and permission model.

5. Electron/Tauri/native wrapper hardening is not done.
   - No packaged-app sandbox, protocol allowlist, or update-signature policy yet.
