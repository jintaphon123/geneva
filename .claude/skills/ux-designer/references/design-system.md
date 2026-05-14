# Design System Reference

## Token Categories

### 1. Color Tokens

#### Scale Generation (from brand color)

10-step scale (50–900):
- 50: 95% lightness — subtle backgrounds, hover fills
- 100: 90% lightness — light fills
- 200: 80% lightness — borders, dividers
- 300: 65% lightness — disabled text, placeholder
- 400: 50% lightness — secondary elements
- 500: base brand color — primary actions
- 600: 15% darker — hover state
- 700: 25% darker — pressed state
- 800: 35% darker — dark text on light bg
- 900: 50% darker — headings, max contrast

#### Semantic Color Tokens

```css
/* Primary */
--color-primary-default: var(--brand-500);
--color-primary-hover: var(--brand-600);
--color-primary-pressed: var(--brand-700);
--color-primary-subtle: var(--brand-50);
--color-primary-on: #FFFFFF; /* text on primary bg */

/* Status */
--color-error: #DC2626;
--color-error-subtle: #FEE2E2;
--color-warning: #D97706;
--color-warning-subtle: #FEF3C7;
--color-success: #16A34A;
--color-success-subtle: #DCFCE7;
--color-info: #2563EB;
--color-info-subtle: #DBEAFE;

/* Surface */
--color-surface-default: #FFFFFF;
--color-surface-subtle: var(--neutral-50);
--color-surface-raised: #FFFFFF; /* cards on subtle bg */
--color-surface-overlay: rgba(0,0,0,0.5); /* modal backdrops */

/* Text */
--color-text-primary: var(--neutral-900);
--color-text-secondary: var(--neutral-600);
--color-text-tertiary: var(--neutral-400);
--color-text-disabled: var(--neutral-300);
--color-text-inverse: #FFFFFF;
--color-text-link: var(--brand-600);

/* Border */
--color-border-default: var(--neutral-200);
--color-border-strong: var(--neutral-400);
--color-border-focus: var(--brand-500);
```

### 2. Typography Tokens

```css
/* Font family */
--font-sans: 'Inter', system-ui, -apple-system, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* Font size (1.25x modular scale) */
--text-xs:   0.625rem;  /* 10px */
--text-sm:   0.75rem;   /* 12px */
--text-base: 1rem;      /* 16px */
--text-lg:   1.25rem;   /* 20px */
--text-xl:   1.563rem;  /* 25px */
--text-2xl:  1.953rem;  /* 31px */
--text-3xl:  2.441rem;  /* 39px */
--text-4xl:  3.052rem;  /* 49px */
--text-5xl:  3.815rem;  /* 61px */

/* Font weight */
--font-regular:   400;
--font-medium:    500;
--font-semibold:  600;
--font-bold:      700;

/* Line height */
--leading-tight:  1.2;   /* headings */
--leading-snug:   1.375; /* large body */
--leading-normal: 1.5;   /* default body */
--leading-relaxed: 1.625; /* long-form reading */

/* Letter spacing */
--tracking-tight:  -0.025em; /* headings */
--tracking-normal: 0;
--tracking-wide:   0.025em;  /* all-caps labels */
```

### 3. Spacing (8pt Grid)

```css
--space-0:  0;
--space-1:  0.25rem;  /* 4px */
--space-2:  0.5rem;   /* 8px */
--space-3:  0.75rem;  /* 12px */
--space-4:  1rem;     /* 16px */
--space-5:  1.25rem;  /* 20px */
--space-6:  1.5rem;   /* 24px */
--space-8:  2rem;     /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
--space-20: 5rem;     /* 80px */
--space-24: 6rem;     /* 96px */
```

### 4. Border Radius

```css
--radius-none: 0;
--radius-sm:   0.25rem;   /* 4px — inputs, tags */
--radius-md:   0.5rem;    /* 8px — cards, buttons */
--radius-lg:   0.75rem;   /* 12px — modals, large cards */
--radius-xl:   1rem;      /* 16px — panels */
--radius-2xl:  1.5rem;    /* 24px — large surfaces */
--radius-full: 9999px;    /* pills, avatars */
```

### 5. Shadows (Elevation)

```css
--shadow-sm:  0 1px 2px rgba(0,0,0,0.05);
--shadow-md:  0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1);
--shadow-lg:  0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1);
--shadow-xl:  0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1);
--shadow-2xl: 0 25px 50px -12px rgba(0,0,0,0.25);
```

### 6. Animation Tokens

```css
/* Duration */
--duration-instant: 0ms;
--duration-fast:    100ms;
--duration-normal:  200ms;
--duration-slow:    300ms;
--duration-slower:  500ms;

/* Easing */
--ease-linear:    linear;
--ease-in:        cubic-bezier(0.4, 0, 1, 1);
--ease-out:       cubic-bezier(0, 0, 0.2, 1);
--ease-in-out:    cubic-bezier(0.4, 0, 0.2, 1);
--ease-spring:    cubic-bezier(0.34, 1.56, 0.64, 1); /* bouncy */
--ease-decelerate: cubic-bezier(0, 0, 0, 1);          /* elements entering */
--ease-accelerate: cubic-bezier(0.3, 0, 1, 1);         /* elements leaving */
```

### 7. Breakpoints

```css
--breakpoint-sm:  480px;   /* Large phone landscape */
--breakpoint-md:  640px;   /* Small tablet */
--breakpoint-lg:  768px;   /* Tablet */
--breakpoint-xl:  1024px;  /* Laptop */
--breakpoint-2xl: 1280px;  /* Desktop */
--breakpoint-3xl: 1536px;  /* Large desktop */
```

---

## Atomic Design Hierarchy

### Atoms (single-purpose, no composition)

| Component | Description |
|---|---|
| Button | Primary / Secondary / Ghost / Destructive + sizes |
| Input | Text, email, password, number + states |
| Checkbox / Toggle / Radio | Selection controls |
| Badge | Status labels, counts |
| Avatar | User image with fallback initials |
| Icon | SF Symbols or custom icon set wrapper |
| Spinner | Loading state indicator |
| Divider | Horizontal / vertical separator |
| Label | Form field label (not standalone text) |

### Molecules (2–5 atoms composed)

| Component | Atoms it contains |
|---|---|
| SearchBar | Input + Icon + (optional Button) |
| FormField | Label + Input + Error message |
| Card | Surface + Heading + Content + (optional CTA) |
| AlertBanner | Icon + Text + (optional Button) |
| Toast | Icon + Text + (optional Action) + Close |
| MenuItem | Icon + Label + (optional Badge / Chevron) |
| Stat | Label + Value + Trend indicator |

### Organisms (multiple molecules)

| Component | Description |
|---|---|
| Header | Logo + Nav links + CTA + Avatar menu |
| Sidebar | Logo + MenuItem list + User section |
| DataTable | Header row + Data rows + Pagination |
| Form | Multiple FormFields + Submit button |
| Modal | Overlay + Dialog + Header + Content + Footer |
| EmptyState | Illustration + Heading + Description + CTA |
| Notification panel | List of Toast items |

### Variant Pattern

Document ALL variants before writing code:

```
Button variants:
  Style: primary | secondary | ghost | destructive
  Size: sm (32px) | md (40px) | lg (48px)
  State: default | hover | active | focus | disabled | loading

Total variants: 4 styles × 3 sizes × 6 states = 72 states to design
Ship: default + hover + focus + disabled (minimum)
```

---

## WCAG Contrast Reference

### Requirements

| Text type | AA | AAA |
|---|---|---|
| Normal text (< 18px, not bold) | 4.5:1 | 7:1 |
| Large text (≥ 18px or ≥ 14px bold) | 3:1 | 4.5:1 |
| UI components, icons, borders | 3:1 | — |
| Focus indicators | 3:1 | — |

### Testing Tools

- Browser: axe DevTools extension (free, most comprehensive)
- Design: Figma plugin "Contrast" or "A11y - Color Contrast Checker"
- Code: Storybook accessibility addon
- CLI: `npx axe-cli https://yoursite.com`

### Automated vs Manual Testing

Automated tools find: missing alt text, contrast failures, missing ARIA labels, heading hierarchy errors.
Manual testing catches: logical reading order, keyboard trap bugs, screen reader announcement quality, dynamic content updates.

Run both. Automated ≠ accessible.
