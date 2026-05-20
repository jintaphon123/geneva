# UI-8 Responsive, Polish, Production QA

Run this checklist before marking UI-8 complete.

## Required Viewports

- Desktop 1440x900, light and dark.
- Mobile 375x812, light and dark.
- Narrow mobile 320x700 for overflow stress.
- Tall desktop with chat, project workspace, settings, memory, artifacts, and skills open.

## Acceptance Checks

- No horizontal overflow on `document.documentElement` or any primary app surface.
- No overlapping text, icons, headers, composer controls, or sidebar triggers.
- Mobile can start chat, open Search, open a Project, open Settings, and return to chat.
- Mobile sidebar drawer opens, closes from backdrop, and closes after navigation.
- Project right rail bottom sheet opens from `Project context`, closes from backdrop/Escape/close, and does not stack as a second rail under the main content.
- Composer active chips show one or two visible context modes, then `+N` for overflow.
- Settings stays full-screen on mobile, including the Memory Browser modal.
- Memory Browser mobile filters open as a drawer and the memory list remains readable behind it.
- Deep Research report and artifact detail text wrap without clipped lines or hidden source URLs.
- Loading, empty, error, and retry states are visible without layout jumps.
- Desktop remains the primary polished experience with the project rail visible at the right side.

## Visual Smoke Coverage

- `npm run visual:smoke` captures desktop/mobile chat, Open Source, Skills, Project, Project context sheet, and Project chat screenshots.
- `npm run check:ui8` validates the static responsive contract before broad production QA.
- `npm run qa:production` includes the UI-8 guard before backend and visual smoke checks.
