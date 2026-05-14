---
name: apple-hig
argument-hint: "[mode] — design / audit | [platform] — ios / macos / visionos"
description: >
  Apple Human Interface Guidelines expertise covering iOS, macOS, and visionOS design,
  Liquid Glass aesthetics (2026), accessibility-first design, and HIG compliance auditing.

  Auto-invoke when Bond asks: Apple HIG, iOS design, macOS design, visionOS design,
  Liquid Glass, SwiftUI design, HIG audit, Human Interface Guidelines, Apple design,
  SF Pro, SF Symbols, Dynamic Type, VoiceOver, tap target, semantic colors,
  navigation bar, tab bar, sidebar, sheet, ornament, spatial layout.
---

# Apple HIG Expert

Two modes for designing and auditing Apple platform interfaces.

---

## Mode Detection

| Input | Mode |
|---|---|
| "design for iOS/macOS/visionOS", "build Apple UI", "SwiftUI layout", "native app design" | **Design** |
| "HIG audit", "audit this design", "check Apple guidelines", "HIG compliance" | **Audit** |

---

## Mode 1 — Design

Three-phase workflow for designing Apple-native interfaces from scratch.

### Phase 1 — Navigation & Layout

**iOS Navigation Patterns**

| Pattern | When to use | SwiftUI |
|---|---|---|
| Tab Bar | 2–5 top-level destinations, peer content | `TabView` |
| Navigation Stack | Hierarchical, drill-down content | `NavigationStack` |
| Sheet / Modal | Focused task that interrupts flow | `.sheet` / `.fullScreenCover` |
| Split View | iPad — primary/secondary content | `NavigationSplitView` |

Tab bar rules:
- 2–5 tabs (never more than 5)
- Each tab = a distinct top-level destination (not a sub-view)
- Active tab: filled icon + label. Inactive: outline icon + label.
- No modals or sheets in tab bar items

**macOS Navigation Patterns**

| Pattern | When to use |
|---|---|
| Sidebar | Primary navigation, document/source list |
| Split View | Two-panel: list + detail (default for macOS apps) |
| Toolbar | Actions on current content — not global nav |
| Menu Bar | Global commands, not contextual actions |

Sidebar rules:
- Use `.navigationSplitViewStyle(.prominentDetail)` for full-width detail on iPad
- Sidebar icons: SF Symbols, 20pt, secondary color
- Selection: system selection highlight (don't custom-color it)

**visionOS Navigation Patterns**

| Element | Purpose |
|---|---|
| Ornament | Contextual controls attached to a window |
| Volume | 3D content anchored in space |
| Window | Flat 2D surface in spatial environment |
| Portal | Immersive experience with visible background |

---

### Phase 2 — Visual Styling

**Liquid Glass (2026)**

Liquid Glass is the signature material of Apple's 2026 design language. It replaces frosted vibrancy with a new optical depth system.

Key properties:
- **Translucency:** Background content shows through with optical blur + tint
- **Depth hierarchy:** thin-material < regular-material < thick-material (increasing opacity)
- **Fluid response:** shape and tint subtly shift with content beneath
- **Ultra-thin material:** for overlays that must remain nearly transparent (notification banners)

Materials hierarchy:
```
ultraThinMaterial   → Most transparent — overlay info only
thinMaterial        → Light overlays, floating panels
regularMaterial     → Default for sidebars, sheets, cards
thickMaterial       → Highest contrast — critical UI, accessibility mode
```

When NOT to use glass: primary content areas (article body, form fields, main canvas). Glass = container, chrome, overlay.

**Typography — San Francisco**

SF Pro is system-default on all Apple platforms. Never embed it — it's licensed as a system font.

| Style | Size | Weight | Usage |
|---|---|---|---|
| Large Title | 34pt | Regular | First screen heading |
| Title 1 | 28pt | Regular | Section titles |
| Title 2 | 22pt | Regular | Subsection titles |
| Title 3 | 20pt | Regular | Group headers |
| Headline | 17pt | Semibold | List headers, emphasis |
| Body | 17pt | Regular | Primary content |
| Callout | 16pt | Regular | Secondary content |
| Subheadline | 15pt | Regular | Supplementary info |
| Footnote | 13pt | Regular | Captions, metadata |
| Caption 1 | 12pt | Regular | Labels |
| Caption 2 | 11pt | Regular | Smallest text |

**Always use text styles (not point sizes)** — they scale with Dynamic Type automatically.

**Semantic Colors**

Never hardcode hex colors. Use semantic system colors:
```swift
// Text
Color.primary        // Primary content
Color.secondary      // Secondary content
Color.tertiary       // Tertiary / placeholder

// Backgrounds
Color(.systemBackground)        // Primary background
Color(.secondarySystemBackground) // Secondary background
Color(.tertiarySystemBackground)  // Cards, grouped content

// Accent
Color.accentColor    // Tappable items, active state

// Status
Color(.systemRed / .systemGreen / .systemBlue / .systemOrange)
```

**SF Symbols**

Use SF Symbols for all iconography. Never create custom icons for actions SF Symbols covers.
- Weight: match surrounding text weight
- Scale: .small / .medium / .large
- Rendering: .hierarchical (preferred) / .palette / .multicolor / .monochrome

---

### Phase 3 — Accessibility First

**VoiceOver Semantic Labeling**

Every interactive element needs an accessibility label:
```swift
Button(action: { }) {
    Image(systemName: "trash")
}
.accessibilityLabel("Delete item")
.accessibilityHint("Double tap to permanently delete this item")
```

Rules:
- Labels: short noun phrase ("Delete item", not "This button deletes the item")
- Hints: describe result of action, start with a verb ("Double tap to...")
- Don't repeat the label in the hint

**Tap Target Size**

Minimum: 44×44pt. Non-negotiable on iOS.
- Small visual elements (toggle, star): expand hit target with `.contentShape()`
- List rows: full-width tappable (default row behavior handles this)

```swift
Image(systemName: "star")
    .frame(width: 44, height: 44)  // or use .contentShape(Rectangle())
```

**Dynamic Type**

All text must scale with Dynamic Type:
- Use `.font(.body)` not `.font(.system(size: 17))`
- Test at xSmall through xxxLarge + accessibility sizes (AX1–AX5)
- Never truncate body text — use `.lineLimit(nil)` for important content
- Layouts must reflow (not overflow) at large text sizes

**Contrast on Translucent Backgrounds**

Liquid Glass backgrounds shift with content behind them. Always check contrast at minimum:
- Default appearance (light bg behind glass)
- Dark appearance (dark bg behind glass)
- High Contrast mode (accessibility)

Use `.accessibilityDifferentiateWithoutColor` to never rely on color alone.

---

## Mode 2 — Audit

Systematic HIG compliance scan — produces a HIG Scorecard (0–100) with prioritized fixes.

### Audit Checklist

**Navigation (20 points)**
- [ ] Tab bar: 2–5 tabs, correct icons, correct label visibility
- [ ] Navigation hierarchy: appropriate for content depth
- [ ] Back button: present when navigating into hierarchy, system-styled
- [ ] Modal usage: only for focused tasks that interrupt flow

**Visual Design (25 points)**
- [ ] Typography: using text styles (not hardcoded sizes)
- [ ] Colors: using semantic colors (not hardcoded hex)
- [ ] SF Symbols: used for standard actions (not custom icons for share, trash, etc.)
- [ ] Material: Liquid Glass used appropriately (chrome, not content)
- [ ] Density: sufficient breathing room — no overcrowded layouts

**Accessibility (30 points)**
- [ ] VoiceOver: all interactive elements have labels
- [ ] Tap targets: all interactive elements ≥ 44×44pt
- [ ] Dynamic Type: all text scales correctly through AX5
- [ ] Color not sole indicator: status shown with icon + color (not color alone)
- [ ] Contrast: meets 4.5:1 on all text, including on glass backgrounds

**Platform Conventions (25 points)**
- [ ] Platform-native navigation (tab bar on iOS, sidebar on macOS)
- [ ] System gestures: swipe-to-go-back not blocked
- [ ] Keyboard support on iPad and macOS
- [ ] Context menus: available for long-press (iOS) and right-click (macOS)
- [ ] System sounds and haptics: used appropriately, not overridden

### HIG Scorecard

| Range | Grade | Action |
|---|---|---|
| 90–100 | A | Ship. Minor polish only. |
| 75–89 | B | Fix accessibility and platform issues before launch. |
| 60–74 | C | Significant rework needed. Block launch. |
| < 60 | D/F | Fundamental redesign required. |

### Proactive Triggers (always flag without being asked)

- Tap target < 44pt on any interactive element
- Text not using Dynamic Type text styles
- Hardcoded hex color instead of semantic color
- Custom icon where SF Symbol exists
- Tab bar with > 5 tabs
- Modal for content that should be a navigation push
- Contrast below 4.5:1 on any text

---

## References

- `references/visual-design.md` — Liquid Glass materials, SF typography scale, semantic colors, depth hierarchy, fluid motion, 2026 aesthetic
- `references/platform-specifics.md` — iOS navigation paradigms, macOS patterns, visionOS spatial design, platform-specific conventions
- `references/accessibility.md` — VoiceOver labeling, Dynamic Type scale, tap target rules, contrast requirements, High Contrast and Reduce Motion support
