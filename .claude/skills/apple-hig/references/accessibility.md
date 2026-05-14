# Accessibility — Apple HIG

## VoiceOver

VoiceOver is the screen reader built into all Apple platforms. When activated, users navigate by swiping and double-tapping instead of tapping directly.

### Semantic Labeling Rules

Every interactive element needs an `accessibilityLabel`. Every action needs an `accessibilityHint`.

```swift
// Icon-only button
Button(action: deleteItem) {
    Image(systemName: "trash")
}
.accessibilityLabel("Delete item")
.accessibilityHint("Removes this item from your list")

// Image with content
Image("userAvatar")
    .accessibilityLabel("Profile photo of \(user.name)")

// Decorative image (skip by VoiceOver)
Image("decorativeBackground")
    .accessibilityHidden(true)

// Custom control
Slider(value: $volume, in: 0...1)
    .accessibilityLabel("Volume")
    .accessibilityValue("\(Int(volume * 100)) percent")
```

### Label Writing Rules

| ✅ Good | ❌ Bad |
|---|---|
| "Delete item" | "trash icon" |
| "Send message" | "Button" |
| "3 unread notifications" | "badge" |
| "More options for this post" | "more" |

- **Labels:** short noun phrase, describe the content/function
- **Hints:** describe the result of the action, start with a verb
- Never repeat the label in the hint
- Never include the word "button" in a label (VoiceOver announces the trait separately)

### Grouping Related Elements

```swift
// Group label + value as single VoiceOver element
VStack {
    Text("Battery")
    Text("82%")
}
.accessibilityElement(children: .combine)
// VoiceOver reads: "Battery, 82%"
```

### Custom Actions (reduce swipe count)

```swift
// Instead of requiring swipe to buttons, provide custom actions
ListRowView(item: item)
    .accessibilityActions {
        Button("Edit") { edit(item) }
        Button("Delete") { delete(item) }
        Button("Share") { share(item) }
    }
```

---

## Dynamic Type

All text must scale with user's preferred text size. This is non-optional for App Store submission.

### Size Scale

| Name | Scale factor | Usage |
|---|---|---|
| xSmall | 0.75× | Small labels shrink |
| Small | 0.88× | |
| Medium | 0.94× | |
| Large (default) | 1.0× | System default |
| xLarge | 1.12× | |
| xxLarge | 1.25× | |
| xxxLarge | 1.375× | |
| AX1 | 1.5× | Accessibility sizes |
| AX2 | 1.75× | |
| AX3 | 2.0× | |
| AX4 | 2.375× | |
| AX5 | 2.75× | Maximum |

### Implementation

```swift
// ✅ Always use text styles
Text("Hello")
    .font(.body)    // scales automatically

// ❌ Never hardcode sizes
Text("Hello")
    .font(.system(size: 17)) // doesn't scale

// Custom font that scales
Text("Hello")
    .font(.custom("MyFont", size: 17, relativeTo: .body)) // scales relative to .body
```

### Layout for Large Type

At AX3+ sizes, layouts must reflow (not clip or overlap):

```swift
// Adapt layout for accessibility sizes
@Environment(\.dynamicTypeSize) var typeSize

HStack {
    if typeSize >= .xxxLarge {
        VStack { label; value }  // stack vertically at large sizes
    } else {
        HStack { label; Spacer(); value }  // side-by-side at normal sizes
    }
}
```

Rules:
- Never truncate body text at any size: `.lineLimit(nil)` for important content
- Allow scrolling when content overflows
- Test at AX1, AX3, AX5 minimum — not just default

---

## Tap Target Size

### iOS Rule

Minimum: **44×44pt**. Non-negotiable.

Common violations:
- Small icons without expanded hit area
- Custom checkboxes sized to visual element only
- Close buttons on modals that are 20×20pt visually

### Fix: Expand Hit Target Without Changing Visual Size

```swift
// Option 1: contentShape
Image(systemName: "xmark")
    .frame(width: 20, height: 20)           // visual size
    .contentShape(Rectangle().size(44, 44)) // hit area
    .onTapGesture { dismiss() }

// Option 2: frame
Button(action: dismiss) {
    Image(systemName: "xmark")
}
.frame(minWidth: 44, minHeight: 44)

// Option 3: padding
Button(action: action) {
    Image(systemName: "star")
}
.padding(12) // adds 12pt padding around visual = 44×44 total if icon is 20×20
```

### macOS Rule

Minimum: **28×28pt** (pointer-based, more precise than touch).
Still increase if the element is frequently targeted.

### visionOS Rule

Same as iOS: **44×44pt** minimum. Spatial targeting (look + pinch) has lower precision than touch.

---

## Color Contrast

### Requirements

| Content | AA | AAA |
|---|---|---|
| Normal text (< 18pt, not bold) | 4.5:1 | 7:1 |
| Large text (≥ 18pt or ≥ 14pt bold) | 3:1 | 4.5:1 |
| UI components (icons, borders, focus rings) | 3:1 | — |

### On Liquid Glass Backgrounds

Glass backgrounds change based on what's behind them — always test contrast in both conditions:

1. Light content behind glass (light dashboard, white background)
2. Dark content behind glass (dark photo, dark app background)

```swift
// Provide high-contrast fallback
@Environment(\.colorSchemeContrast) var contrast

Text("Important")
    .foregroundStyle(contrast == .increased
        ? Color(.label)          // solid color for high contrast
        : .secondary)            // secondary (translucent) for normal
```

### Never Use Color Alone

Always pair color with a second indicator (icon, pattern, text):

```swift
// ❌ Color alone
Circle().fill(isOnline ? .green : .red)

// ✅ Color + icon
HStack {
    Circle().fill(isOnline ? .green : .red)
    Image(systemName: isOnline ? "checkmark" : "xmark")
}
.accessibilityLabel(isOnline ? "Online" : "Offline")
```

---

## Keyboard Navigation (iPadOS + macOS)

Every action accessible via touch must also be accessible via keyboard.

```swift
// Focus management
@FocusState private var isFocused: Bool

TextField("Search", text: $query)
    .focused($isFocused)
    .onAppear { isFocused = true } // auto-focus on appear

// Custom keyboard shortcuts
Button("Submit") { submit() }
    .keyboardShortcut(.return)

Button("Cancel") { cancel() }
    .keyboardShortcut(.escape)
```

### Tab Order

VoiceOver and keyboard navigation follow the visual order (top-left → bottom-right for LTR). If your layout order differs from visual order, override it:

```swift
VStack {
    secondaryContent
    primaryContent  // visually on top but second in DOM
}
.accessibilitySortPriority(1)  // on primaryContent to make it first
```

---

## Testing Checklist

### VoiceOver Testing

- [ ] Every interactive element has a label
- [ ] Actions have hints
- [ ] Decorative images are hidden
- [ ] Reading order matches visual order
- [ ] All custom controls announce their value and state

### Dynamic Type Testing

Test at: **xSmall**, **Large (default)**, **AX1**, **AX3**, **AX5**

- [ ] No text truncates at AX5
- [ ] No layouts clip or overlap at AX5
- [ ] Scroll is available if content overflows
- [ ] Custom fonts scale correctly

### Tap Target Testing

- [ ] All interactive elements ≥ 44×44pt (run `xcrun simctl launch` with Accessibility Inspector)

### Contrast Testing

- [ ] All text passes 4.5:1 in both light and dark mode
- [ ] All glass surfaces tested in light AND dark environments
- [ ] High Contrast mode enabled — verify no information is lost

### Reduce Motion

- [ ] `.accessibilityReduceMotion` respected throughout
- [ ] No content is hidden/revealed exclusively through animation
