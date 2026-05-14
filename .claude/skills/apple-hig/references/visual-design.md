# Visual Design — Apple HIG

## Liquid Glass (2026)

Apple's 2026 design language introduces Liquid Glass as the primary surface material across iOS, macOS, and visionOS.

### Core Properties

**Translucency:** Content behind the surface is visible through an optical blur + tint system. The effect is physically accurate — glass refracts and shifts the background.

**Depth:** Materials create visual hierarchy through transparency levels:
- More transparent = lower hierarchy (background chrome)
- Less transparent = higher hierarchy (active surfaces, overlays)

**Fluid response:** The glass tint shifts based on dominant colors in the background content — the material "samples" what's behind it.

### Material Hierarchy

| Material | Appearance | Use case |
|---|---|---|
| `.ultraThinMaterial` | Near-transparent, barely tinted | Notification banners, tooltip backgrounds |
| `.thinMaterial` | Light glass, subtle blur | Floating panels, popovers |
| `.regularMaterial` | Standard glass, clear blur | Sidebars, sheets, cards |
| `.thickMaterial` | Opaque-leaning glass, high contrast | Critical alerts, accessibility mode |
| `.ultraThickMaterial` | Near-opaque | Rarely needed — use for maximum readability |

### SwiftUI Implementation

```swift
// Card with Liquid Glass background
RoundedRectangle(cornerRadius: 16)
    .fill(.regularMaterial)
    .overlay(
        RoundedRectangle(cornerRadius: 16)
            .strokeBorder(.white.opacity(0.2), lineWidth: 1) // glass border
    )
    .shadow(color: .black.opacity(0.08), radius: 8, y: 4)

// Full-screen glass overlay
Color.clear
    .background(.thinMaterial)
    .ignoresSafeArea()
```

### When to Use Glass

✅ Navigation bars, tab bars, sidebars
✅ Sheets and modals backgrounds
✅ Floating cards over content
✅ Toolbars
✅ Control center, notification banners

❌ Primary content areas (article body, main canvas)
❌ Form fields and inputs
❌ Tables / list rows (use system background instead)
❌ Any surface where contrast is critical and content behind is unpredictable

### Glass + Accessibility

Always validate contrast in two conditions:
1. Light content behind glass (e.g., white dashboard)
2. Dark content behind glass (e.g., photo or map)

Use `.accessibilityHighContrastPreference` to provide a non-glass fallback:
```swift
@Environment(\.colorSchemeContrast) var contrast
// if contrast == .increased → use opaque surface instead of glass
```

---

## Typography — San Francisco

### System Type Scale

| Style | Size | Weight | SwiftUI |
|---|---|---|---|
| largeTitle | 34pt | Regular | `.largeTitle` |
| title | 28pt | Regular | `.title` |
| title2 | 22pt | Regular | `.title2` |
| title3 | 20pt | Regular | `.title3` |
| headline | 17pt | Semibold | `.headline` |
| body | 17pt | Regular | `.body` (default) |
| callout | 16pt | Regular | `.callout` |
| subheadline | 15pt | Regular | `.subheadline` |
| footnote | 13pt | Regular | `.footnote` |
| caption | 12pt | Regular | `.caption` |
| caption2 | 11pt | Regular | `.caption2` |

**Rule:** Always use named text styles (`.body`, `.headline`), never `.font(.system(size: 17))`. Named styles scale with Dynamic Type automatically.

### SF Pro vs SF Compact

- **SF Pro:** iOS, macOS, tvOS — proportional spacing
- **SF Compact:** watchOS — tighter spacing for small displays
- **SF Mono:** code, fixed-width data, terminal output

### SF Symbols Integration

SF Symbols are the Apple icon system — use for all standard actions.

```swift
// Standard usage
Image(systemName: "trash")
    .font(.body)                    // matches surrounding text weight
    .imageScale(.medium)           // .small / .medium / .large
    .symbolRenderingMode(.hierarchical) // .monochrome / .palette / .multicolor

// Variable color (for progress, volume, signal)
Image(systemName: "wifi", variableValue: 0.75)

// Animated symbols (iOS 17+)
Image(systemName: "checkmark.circle")
    .symbolEffect(.bounce, value: isComplete)
```

Never create a custom icon for: share, trash, compose, back, forward, search, settings, home, camera, mail, phone, location. SF Symbols covers all of these.

---

## Semantic Color System

### Never Use Hardcoded Colors

All colors must be semantic — they automatically adapt to light/dark mode, high contrast, and accessibility modes.

```swift
// ✅ Correct — semantic colors
Text("Hello")
    .foregroundStyle(.primary)              // adapts to mode

Rectangle()
    .fill(Color(.systemBackground))         // white in light, dark in dark

// ❌ Wrong — hardcoded hex
Text("Hello")
    .foregroundStyle(Color(hex: "#000000")) // breaks in dark mode
```

### Text Colors

| Token | Light mode | Dark mode | Use |
|---|---|---|---|
| `.primary` | ~black | ~white | Main content |
| `.secondary` | 60% gray | 60% gray | Supporting text |
| `.tertiary` | 30% gray | 30% gray | Placeholder, hints |
| `.quaternary` | 18% gray | 18% gray | Hairlines, separators |

### Background Colors

```swift
Color(.systemBackground)          // primary bg (white / system black)
Color(.secondarySystemBackground) // slightly offset (cards, grouped sections)
Color(.tertiarySystemBackground)  // third level
Color(.systemGroupedBackground)   // grouped table background
```

### Accent Color

`.accentColor` — the tappable highlight color. Set once in Assets.xcassets, applies everywhere.
- Default: system blue
- Override: set your brand color in Xcode Assets catalog

---

## Depth Hierarchy

Surfaces in the z-axis communicate information hierarchy:

```
Level 4: Alerts, action sheets (highest — demands attention)
Level 3: Modals, sheets
Level 2: Floating cards, popovers
Level 1: Navigation chrome (sidebar, toolbar, tab bar)
Level 0: Content background (lowest)
```

Each level gets progressively more prominent material:
- Level 0: `.systemBackground`
- Level 1: `.regularMaterial` (glass)
- Level 2: `.thinMaterial` + shadow
- Level 3: `.thickMaterial` + stronger shadow
- Level 4: Full opacity + system tint

---

## Motion Principles

### When to Animate

- State transitions: showing/hiding, loading, completion
- Feedback: success, error, warning
- Spatial: navigation between views (push, pop, present, dismiss)

### When NOT to Animate

- Static data display (a table row appearing doesn't need animation)
- Background operations the user didn't trigger
- Anything that blocks input for > 300ms

### Animation Values

| Transition type | Duration | Easing |
|---|---|---|
| View navigation | 350ms | `easeInOut` |
| Sheet presentation | 400ms | `spring(0.7, 0.5)` |
| Icon state change | 150ms | `easeOut` |
| Progress updates | 200ms | `linear` |
| Success feedback | 250ms | `spring(0.6, 0.8)` |

Respect `.reduceMotion` preference:
```swift
@Environment(\.accessibilityReduceMotion) var reduceMotion
// if reduceMotion → use .opacity transition only, no positional animation
```
