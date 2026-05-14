# Production Readiness Audit — Session 6 Surface Loop

Date: 2026-05-13

Scope: Session 1 — Production Error + Token Budget Firewall through Session 10 — Production QA Harness, before entering Session 7 — Security + Local Production Hardening.

## Verdict

The Session 6 web surface is materially stronger than the earlier prototype and now has a repeatable production QA gate. It is ready to enter `Session 7 — Security + Local Production Hardening`, but it is not a release candidate yet because security, accessibility tooling, CI, and the real Open Source registry/reuse backend are still missing.

## Gap List

| ID | Area | Problem | Production Impact | Fix Direction |
|---|---|---|---|---|
| P0-01 | Settings / Secrets | Saving the API-key field with an empty value can wipe the stored provider key. | User loses model access by clicking Save with an empty password field. | Disable blank secret saves in UI and ignore blank API-key updates server-side unless an explicit clear action exists. |
| P0-02 | Settings / Secrets | API-key UI uses redacted config as placeholder state instead of a clear stored/not-stored indicator. | Feels unsafe and can train the UI to surface secret-like strings. | Replace secret placeholder with `Paste key to replace` and a non-sensitive status pill. |
| P0-03 | Settings / Errors | Settings load/save/import/rebuild/reload paths do not consistently show user-facing errors. | Network/API failures look like dead controls. | Add inline settings notice and preserve draft values on failure. |
| P1-01 | QA Harness | Production QA lacks static checks for dead-browser APIs such as `window.confirm`, `alert`, `debugger`, and secret placeholders. | Prototype patterns can creep back in without failing CI. | Add `production-static-check.mjs` into `qa:production`. |
| P1-02 | QA Harness | Production QA has no bundle budget. | Vite build can silently become slow while still passing tests. | Add gzip bundle budget checks against built static assets. |
| P1-03 | QA Harness | Visual smoke fixture is too small for project/skill clutter. | Sidebar/Skills regressions appear only once real data accumulates. | Seed high-volume project and skill fixtures and assert count/containment. |
| P1-04 | QA Harness | No accessibility-adjacent gate for modal/menu basics. | Dialogs and menus can regress keyboard/screen-reader affordances. | Static + visual assertions for dialog role, modal marker, menu options, labels, and close controls. |
| P2-01 | Open Source | Open Source is still a control-plane preview, not a registry-backed workflow. | The product vision is visible but not usable. | Later build registry schema, publish queue, metadata, scope, and reuse search API. |
| P2-02 | Architecture | `App.tsx`, `SkillBrowser.tsx`, `ProjectView.tsx`, `ChatCanvas.tsx`, and `index.css` remain very large. | Future sessions will create accidental coupling and slow reviews. | Session 8 debloat: split state machines, panels, and CSS modules after security hardening. |
| P2-03 | Session 1 | Provider/token errors are sanitized, but QA does not force provider-failure fixtures through UI. | Raw provider errors could return in a future code path. | Add provider-failure visual/API fixture later. |
| P2-04 | Session 2 | Activity panel is smoke-tested from restored traces, not live multi-tool streaming. | Live streaming regressions can still slip. | Add mocked SSE stream fixture with tool timeout/permission events. |
| P2-05 | Session 3 | Composer contract is tested for empty/typed send state, but attachment overflow is not stress-tested. | Large filenames and many attachments can break composer layout. | Add attachment fixture and overflow assertions. |
| P2-06 | Session 4 | Scroll stability is tested, but not while tokens stream into a long answer. | User can still be yanked around under live generation. | Add stream fixture with delayed chunks and user-scroll assertion. |
| P2-07 | Session 5 | Message actions exist, but QA does not click copy/edit/retry/fork/remember in a full loop. | Action handlers can silently regress. | Add action interaction matrix. |
| P2-08 | Session 6 | Context rail shows ledger, but token pressure states are not visually threshold-tested. | Critical context pressure may look calm. | Add high-pressure ledger fixture. |
| P2-09 | Session 7 | Project surface handles errors, but project archival/recovery control plane is absent. | Users can lose project visibility after archive/delete flows. | Build archive/recovery view later. |
| P2-10 | Session 8 | Skill Builder still lacks provider-failure and 20+ skill dataset tests. | Skill creation can feel broken under real model failures. | Add larger skill fixture now; provider fixture later. |
| P2-11 | Session 9 | Theme/Open Source improved, but QA did not enforce future no-regression around explicit theme menu until now. | Theme can return to ambiguous cycle UX. | Keep visual/static theme assertions in production gate. |
| P2-12 | Session 10 | QA gate is local-only; no CI config yet. | Humans must remember to run it. | Session 9 Production Test Matrix + CI Gate should wire this into CI. |

## Loop Plan

### Loop 1 — Trust + Secret-Safe Settings
- Harden API-key save behavior.
- Add Settings error notices.
- Add backend regression that blank key updates do not erase stored provider access.
- Run targeted backend tests and frontend lint/build.

### Loop 2 — Production QA Gate Expansion
- Add static production checker.
- Add gzip bundle budget gate.
- Enforce no browser-default destructive dialogs.
- Seed higher-volume visual fixtures for projects and skills.
- Extend visual smoke assertions for high-volume data and Open Source/menu affordances.

### Loop 3 — Full Gate + Visual Review
- Run `npm run qa:production`.
- Inspect fresh screenshots.
- Patch any regression immediately.
- Update session summary and decision log.

## Loop Results

### Loop 1 — Completed
- API-key save is secret-safe in the Settings UI: blank password input cannot be submitted as a replacement key.
- Backend `update_settings()` ignores blank secret updates, so an empty payload cannot wipe stored provider access.
- Settings operations now show inline user-facing error notices for load/save/rebuild/import/reload failures.
- Settings writes now use temp file then replace, avoiding partially written `settings.json`.
- Regression tests cover blank secret update preservation and nonblank secret replacement.

### Loop 2 — Completed
- Added `sb-ui/scripts/production-static-check.mjs`.
- `npm run qa:production` now runs static production checks after build.
- Static gate scans source for `confirm`, `alert`, `debugger`, `dangerouslySetInnerHTML`, secret placeholders, literal API-key patterns, and bundle budget drift.
- Bundle budget is enforced against built gzip assets: largest JS, total JS, and largest CSS.
- Visual smoke now seeds 37 projects and 25 skills, asserting pagination, high-volume skill rendering, Open Source dialog semantics, and context ledger viewport containment.

### Loop 3 — Completed
- Full production QA passed: lint, build, static checks, backend web/skill/service contracts, desktop/mobile visual smoke, and whitespace diff check.
- Screenshot review caught a real Context Ledger rail overflow that tests initially missed.
- Fixed Radix ScrollArea width expansion inside the Memory/Context rail, then added visual assertions for ledger card/chip viewport containment.

### Deferred Into Session 7+
- Real Open Source registry backend.
- Authentication/local production hardening.
- Accessibility audit tooling.
- Debloat/file architecture cleanup.
- CI gate and release candidate matrix.
