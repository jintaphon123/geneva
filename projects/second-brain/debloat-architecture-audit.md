# Session 8 — Debloat + File Architecture Cleanup

Date: 2026-05-13
Verdict: CONCERNS

## Executive Assessment

Session 8 moved Second Brain out of the most dangerous "everything lives in one file" phase. The web app now has clearer ownership boundaries for app orchestration, chat helpers, stream event mapping, theme state, modal surfaces, skill lifecycle state, CSS surface modules, and backend request security.

The result is materially healthier, but not production-frozen yet. The first pass removed the most dangerous frontend bloat, and the follow-up loop split the API client, chat canvas, project CSS, skill CSS, and project support surfaces. The remaining large files are now the behavior-heavy ones: `session.py`, `web_runtime.py`, `App.tsx`, `ProjectView.tsx`, and `MemoryBrowser.tsx`. Those need CI-backed regression coverage before deeper behavior-aware splitting.

## Before / After

| Area | Before | After | Result |
|------|--------|-------|--------|
| `sb-ui/src/App.tsx` | 1,598 lines | 959 lines | App shell became orchestration instead of modal/helper dumping ground |
| `sb-ui/src/components/SkillBrowser.tsx` | 1,195 lines | 696 lines | Skill list/control surface separated from modal and lifecycle helpers |
| `sb-ui/src/index.css` | 7,150 lines | 10 import lines | CSS split into surface modules while preserving cascade order |
| `src/second_brain/web_api.py` | 637 lines | 508 lines | Security policy extracted to shared backend module |
| `src/second_brain/web_security.py` | new | 148 lines | Local web boundary is now reusable across HTTP/FastAPI entrypoints |
| `sb-ui/src/lib/api.ts` | 1,087 lines | 8 facade lines | API client split into domain modules; largest new API module is 274 lines |
| `sb-ui/src/components/ChatCanvas.tsx` | 969 lines | 248 lines | Chat canvas split into message, markdown, activity, rail, empty-state, and status components |
| `sb-ui/src/components/ProjectView.tsx` | 977 lines | 813 lines | Project modals/support helpers extracted; main state machine remains in place |
| `sb-ui/src/styles/project.css` | 1,738 lines | 3 import lines | Project CSS split into sidebar/chat, workspace, and command surface modules |
| `sb-ui/src/styles/skills.css` | 1,150 lines | 2 import lines | Skill CSS split into control-plane and modal modules |

## Architecture Changes

- Extracted Open Source, tool permission, and view loading surfaces from `App.tsx`.
- Moved chat message construction, branch transcript logic, command matching, context formatting, and project detection into `sb-ui/src/lib/chat-message.ts`.
- Moved stream event parsing, activity timeline merging, tool trace merging, and public error copy into `sb-ui/src/lib/agent-events.ts`.
- Moved theme mode and ghost mode storage constants/helpers into `sb-ui/src/lib/theme.ts`.
- Moved skill activation/readiness/error-copy logic into `sb-ui/src/lib/skill-state.ts`.
- Extracted Skill Detail and Build Skill modals into `sb-ui/src/components/SkillModals.tsx`.
- Split `index.css` into:
  - `foundation.css`
  - `chat.css`
  - `memory-rail.css`
  - `composer-markdown.css`
  - `open-source-permission.css`
  - `skills.css`
  - `settings.css`
  - `project.css`
  - `memory-browser.css`
  - `responsive.css`
- Extracted backend security policy into `src/second_brain/web_security.py`.
- Added line-budget checks to `sb-ui/scripts/production-static-check.mjs` so architecture bloat fails the production gate instead of being noticed manually.
- Split `sb-ui/src/lib/api.ts` into domain clients under `sb-ui/src/lib/api/`.
- Split `ChatCanvas.tsx` into dedicated chat subcomponents:
  - `ChatActivityPanel.tsx`
  - `ChatEmptyState.tsx`
  - `ChatMarkdown.tsx`
  - `ChatMessageBubble.tsx`
  - `ChatProgressRail.tsx`
  - `ChatStatusLine.tsx`
- Extracted Project info/delete modals, project notices, project date/title helpers, and constants into `ProjectViewSupport.tsx`.
- Split the largest project/skill CSS modules again and ratcheted line budgets downward.

## Verification

- `npm run build` in `scratch/clawd-code/sb-ui` — pass
- `npm run lint` in `scratch/clawd-code/sb-ui` — pass
- `node scripts/production-static-check.mjs` in `scratch/clawd-code/sb-ui` — pass
- `python -m pytest tests/test_second_brain_web.py -q` — 39 passed, 8 skipped
- `PYTHONPATH=/tmp/second-brain-fastapi-test:$PWD python -m pytest tests/test_second_brain_web.py -q` — 47 passed, 2 warnings
- `python -m pytest tests/test_second_brain_web.py tests/test_second_brain_skills.py tests/test_second_brain_services.py tests/test_providers.py -q` — 95 passed, 8 skipped
- `PYTHON=python npm run qa:production` in `scratch/clawd-code/sb-ui` — pass
- `git diff --check` for touched Session 8 files — pass
- Visual smoke screenshots generated: 24 files under `sb-ui/test-results/visual-smoke/`
- Second cleanup loop QA: `PYTHON=python npm run qa:production` — pass in 73.0s
- Second cleanup loop contracts: `python -m pytest tests/test_second_brain_web.py tests/test_second_brain_skills.py tests/test_second_brain_services.py tests/test_providers.py -q` — 95 passed, 8 skipped

## Current Line Budget Watchlist

| File | Lines | Current Status |
|------|-------|----------------|
| `src/second_brain/session.py` | 1,247 | Too large; split ReAct/session orchestration next |
| `src/second_brain/web_runtime.py` | 1,028 | Too large; split request adapters from runtime orchestration |
| `sb-ui/src/App.tsx` | 959 | Still dense; split app orchestration hooks after CI gate |
| `sb-ui/src/components/ProjectView.tsx` | 813 | Still dense; split project command/progress/memory panels later |
| `sb-ui/src/components/MemoryBrowser.tsx` | 791 | Still dense; should split conflict/timeline/detail surfaces later |
| `sb-ui/src/styles/skills-control-plane.css` | 867 | Scoped but still large; acceptable until Skill surface changes again |

## Production Gaps Remaining

- Architecture budgets are local script checks, not CI-owned yet.
- Python dependency audit still needs a first-class repeatable gate in Session 9.
- `session.py` and `web_runtime.py` still carry too much Agent Harness orchestration in one place.
- Frontend API access is now domain-split, but tests should import the domain clients directly in Session 9 where useful.
- Project view is improved but still too large for confident long-term iteration.
- App-level orchestration should be split into hooks after CI gates exist, not before.

## Next Action

Move into `Session 9 — Production Test Matrix + CI Gate` and make the release gates repeatable: CI-style command ownership, dependency audit, smoke artifact retention, line-budget ratcheting, and regression matrix documentation.
