# Platform-Specific Design Conventions

## iOS

### Navigation Paradigms

**Tab Bar (UITabBarController / TabView)**

- 2–5 top-level destinations only
- Each tab is a peer destination (not a sub-view or action)
- Tab icons: SF Symbols, filled = active, outlined = inactive
- Tab labels: always visible, 1–2 words max
- Never hide the tab bar mid-session (except full-screen media playback)

```swift
TabView(selection: $selectedTab) {
    HomeView().tabItem {
        Label("Home", systemImage: "house")
    }.tag(0)
    
    SearchView().tabItem {
        Label("Search", systemImage: "magnifyingglass")
    }.tag(1)
    
    ProfileView().tabItem {
        Label("Profile", systemImage: "person")
    }.tag(2)
}
.tint(.accentColor)
```

**Navigation Stack (drill-down hierarchy)**

```swift
NavigationStack {
    List(items) { item in
        NavigationLink(item.title, destination: ItemDetailView(item: item))
    }
    .navigationTitle("Items")
    .navigationBarTitleDisplayMode(.large) // or .inline
}
```

Large title: list/root views. Inline title: detail views.
Never add a custom "Back" button — always use the system back button.

**Sheets (focused tasks)**

```swift
.sheet(isPresented: $showingForm) {
    NavigationStack {  // sheets need their own NavigationStack
        FormView()
            .navigationTitle("New Item")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { showingForm = false }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { save(); showingForm = false }
                }
            }
    }
}
```

Modal (`.fullScreenCover`): only when the task requires full-screen or involves a camera/media picker.

**Safe Areas**

Always respect safe area insets — never draw content behind the home indicator or status bar.
```swift
.ignoresSafeArea(.container, edges: .top)  // extend background ONLY
// Content must still be inside safe area
```

### iOS Interaction Patterns

**Long press → Context menu (not separate UI):**
```swift
.contextMenu {
    Button("Edit", systemImage: "pencil") { }
    Button("Delete", systemImage: "trash", role: .destructive) { }
}
```

**Swipe actions on list rows:**
```swift
.swipeActions(edge: .trailing) {
    Button("Delete", role: .destructive) { delete(item) }
}
.swipeActions(edge: .leading) {
    Button("Pin") { pin(item) }.tint(.yellow)
}
```

**Pull-to-refresh:**
```swift
.refreshable {
    await loadData()
}
```

---

## macOS

### Navigation Paradigms

**Sidebar + Split View (default for most apps)**

```swift
NavigationSplitView {
    // Sidebar
    List(selection: $selectedItem) {
        Section("Library") {
            Label("All Items", systemImage: "tray.full")
                .tag(SidebarItem.allItems)
        }
    }
    .navigationSplitViewColumnWidth(min: 200, ideal: 240)
} detail: {
    // Detail view
    if let item = selectedItem {
        ItemDetailView(item: item)
    } else {
        ContentUnavailableView("Select an item", systemImage: "tray")
    }
}
```

**Toolbar (actions on current document/selection)**

```swift
.toolbar {
    ToolbarItemGroup(placement: .automatic) {
        Button("New", systemImage: "plus") { createNew() }
        Button("Delete", systemImage: "trash") { delete() }
            .disabled(selectedItem == nil)
    }
}
```

Never put global navigation in the toolbar — that's the sidebar's job.

**Menu Bar**

Standard menu structure: App Menu > File > Edit > View > [Feature-specific] > Window > Help

Always implement:
- Edit: Undo, Redo, Cut, Copy, Paste, Select All
- View: Enter Full Screen
- Window: Minimize, Zoom, Bring All to Front

**Keyboard Shortcuts**

Every frequent action must have a keyboard shortcut. Use system-standard shortcuts for standard actions:
- ⌘N: New
- ⌘O: Open
- ⌘S: Save
- ⌘W: Close window
- ⌘Q: Quit
- ⌘Z/⇧⌘Z: Undo/Redo

### macOS-Specific Behaviors

- Right-click → context menu (same content as long-press context menu on iOS)
- Drag and drop: support where iOS has share sheet
- Cursor hover: show tooltip for icon-only buttons (`.help("Tooltip text")`)
- Window resizing: all panels must reflow gracefully at any window size
- Inspect panel: right-side inspector panel for object properties (common in creative apps)

---

## visionOS

### Spatial Design Concepts

**Windows:** Flat 2D surfaces in space. Users can position and resize them anywhere. Designed like iPad apps but aware of their spatial context.

**Volumes:** 3D bounded space for 3D content (ModelEntity, RealityView). Fixed dimensions. Content can be interacted with from any angle.

**Immersive Spaces:** Full-environment experiences. User sees only virtual content (or mixed with reality in portal mode).

### Navigation in visionOS

**Ornaments:** Controls that float adjacent to a window. Use for contextual actions that don't belong in the main window chrome.

```swift
.ornament(attachmentAnchor: .scene(.leading)) {
    // Side panel controls — floats beside the main window
    VStack {
        Button("Tools", systemImage: "wrench") { }
        Button("Layers", systemImage: "square.3.layers.3d") { }
    }
    .padding()
    .glassBackgroundEffect()
}
```

**Window Anchoring:** Windows open in front of the user by default. Don't force window position — users choose where they want it.

### Spatial Interaction

- **Look + pinch:** equivalent to tap on iOS
- **Direct touch:** for elements within arm's reach
- **Drag:** pinch + move hand
- Minimum tappable size in spatial: 44×44pt (same as iOS)

### Glass on visionOS

Glass is even more critical on visionOS — you never know what's in the user's environment. Always:
- Use `.glassBackgroundEffect()` for floating panels
- Validate contrast on bright AND dark environments
- Never use opaque white backgrounds (they appear as solid walls in the user's space)

---

## iPad Considerations (Bridge between iOS and macOS)

### Stage Manager (iPadOS 16+)

Apps may run in a floating window, not full-screen. Design layouts that reflow gracefully at any window size.

### Pointer and Keyboard Support

On iPad with external keyboard and trackpad:
- All list items must have hover states
- All interactive elements respond to pointer hover
- Full keyboard navigation must work (same as macOS)
- Keyboard shortcuts should work (at minimum: ⌘N, ⌘S, ⌘W)

### iPad-First vs iPhone-First

iPad layout: use `NavigationSplitView` (sidebar + detail).
iPhone layout: use `NavigationStack` (single column).

```swift
#if os(iOS)
if UIDevice.current.userInterfaceIdiom == .pad {
    NavigationSplitView { SidebarView() } detail: { DetailView() }
} else {
    NavigationStack { ListView() }
}
#endif
```

Or use `horizontalSizeClass` for adaptive layout without device detection.
