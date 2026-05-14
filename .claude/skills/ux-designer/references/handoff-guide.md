# Developer Handoff Guide

## Export Formats

### CSS Custom Properties

Best for: web apps, any framework, maximum compatibility.

```css
/* tokens.css */
:root {
  /* Colors */
  --color-primary-50:  #E6F0FF;
  --color-primary-500: #0066CC;
  --color-primary-600: #0052A3;
  --color-primary-900: #002952;

  --color-text-primary:   #111827;
  --color-text-secondary: #4B5563;
  --color-surface-default: #FFFFFF;
  --color-surface-subtle: #F9FAFB;

  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --text-sm:   0.75rem;
  --text-base: 1rem;
  --text-lg:   1.25rem;
  --text-xl:   1.563rem;
  --font-medium:   500;
  --font-semibold: 600;
  --leading-normal: 1.5;
  --leading-tight:  1.2;

  /* Spacing */
  --space-2: 0.5rem;
  --space-4: 1rem;
  --space-8: 2rem;

  /* Borders */
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1);

  /* Animation */
  --duration-normal: 200ms;
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  :root {
    --color-text-primary:    #F9FAFB;
    --color-surface-default: #111827;
    --color-surface-subtle:  #1F2937;
  }
}
```

### Tailwind Config Extension

Best for: projects already using Tailwind CSS.

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50:  '#E6F0FF',
          100: '#CCE0FF',
          500: '#0066CC',
          600: '#0052A3',
          700: '#003D7A',
          900: '#002952',
        },
        surface: {
          default: '#FFFFFF',
          subtle:  '#F9FAFB',
          raised:  '#FFFFFF',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        xs:   ['0.625rem', { lineHeight: '1rem' }],
        sm:   ['0.75rem',  { lineHeight: '1rem' }],
        base: ['1rem',     { lineHeight: '1.5rem' }],
        lg:   ['1.25rem',  { lineHeight: '1.75rem' }],
        xl:   ['1.563rem', { lineHeight: '2rem' }],
        '2xl':['1.953rem', { lineHeight: '2.25rem' }],
      },
      spacing: {
        '1': '0.25rem',
        '2': '0.5rem',
        '3': '0.75rem',
        '4': '1rem',
        '6': '1.5rem',
        '8': '2rem',
        '12': '3rem',
        '16': '4rem',
      },
      borderRadius: {
        sm:   '0.25rem',
        md:   '0.5rem',
        lg:   '0.75rem',
        xl:   '1rem',
        full: '9999px',
      },
      transitionDuration: {
        fast:   '100ms',
        normal: '200ms',
        slow:   '300ms',
      },
    },
  },
}
```

### JSON (Design Tool Sync)

Best for: multi-platform (iOS + Android + Web), Figma Token Studio, Style Dictionary.

```json
{
  "color": {
    "primary": {
      "50":  { "value": "#E6F0FF", "type": "color" },
      "500": { "value": "#0066CC", "type": "color" },
      "600": { "value": "#0052A3", "type": "color" },
      "900": { "value": "#002952", "type": "color" }
    },
    "text": {
      "primary":   { "value": "{neutral.900}", "type": "color" },
      "secondary": { "value": "{neutral.600}", "type": "color" },
      "disabled":  { "value": "{neutral.300}", "type": "color" }
    }
  },
  "spacing": {
    "2": { "value": "8",  "type": "spacing" },
    "4": { "value": "16", "type": "spacing" },
    "8": { "value": "32", "type": "spacing" }
  },
  "borderRadius": {
    "md": { "value": "8",  "type": "borderRadius" },
    "lg": { "value": "12", "type": "borderRadius" }
  },
  "fontSizes": {
    "base": { "value": "16", "type": "fontSizes" },
    "lg":   { "value": "20", "type": "fontSizes" }
  }
}
```

---

## Figma Organization for Handoff

### File Structure

```
[Project] Design System
├── 🎨 Foundations
│   ├── Colors (color styles)
│   ├── Typography (text styles)
│   ├── Spacing (spacing guide frame)
│   └── Shadows (effect styles)
├── 🧩 Components
│   ├── Atoms
│   ├── Molecules
│   └── Organisms
├── 📐 Templates
│   ├── Dashboard
│   ├── Auth
│   └── Landing
└── 📋 Handoff specs
    ├── Redline annotations
    └── Token mapping
```

### Component Library Rules

- All components use auto-layout (not fixed frames)
- All spacing uses the spacing variable/token (not hardcoded px)
- All colors use styles (not local fills)
- All text uses text styles
- Variants are defined via Component Properties (not separate components)
- All interactive states are in the variant set (Default, Hover, Active, Focus, Disabled)

### Annotation Checklist (per screen in handoff)

- [ ] All spacing annotated in token units (space-4, not "16px")
- [ ] All colors named by token (color-primary-500, not "#0066CC")
- [ ] All typography named by style (text-base/semibold, not "16px SemiBold")
- [ ] Responsive behavior noted: "stack vertically at < md breakpoint"
- [ ] Interaction notes: hover state, animation duration/easing
- [ ] Edge cases: empty state, loading state, error state

---

## Framework Integration Checklist

### React + CSS Variables

```tsx
// Apply tokens globally
import './tokens.css';

// Use in components
const Button = ({ children }) => (
  <button style={{
    backgroundColor: 'var(--color-primary-500)',
    padding: 'var(--space-2) var(--space-4)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--color-text-inverse)',
    transition: `background-color var(--duration-normal) var(--ease-out)`,
  }}>
    {children}
  </button>
);
```

### React + Tailwind (cn pattern)

```tsx
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const Button = ({ variant = 'primary', size = 'md', children }) => (
  <button className={cn(
    'font-medium rounded-md transition-colors duration-normal',
    variant === 'primary' && 'bg-primary-500 hover:bg-primary-600 text-white',
    variant === 'ghost'   && 'text-primary-600 hover:bg-primary-50',
    size === 'sm' && 'px-3 py-1.5 text-sm',
    size === 'md' && 'px-4 py-2 text-base',
    size === 'lg' && 'px-6 py-3 text-lg',
  )}>
    {children}
  </button>
);
```

### Figma Token Sync (via Style Dictionary or Tokens Studio)

```bash
# Install Style Dictionary
npm install -D style-dictionary

# style-dictionary.config.json
{
  "source": ["tokens.json"],
  "platforms": {
    "css": {
      "transformGroup": "css",
      "buildPath": "src/",
      "files": [{ "destination": "tokens.css", "format": "css/variables" }]
    },
    "js": {
      "transformGroup": "js",
      "buildPath": "src/",
      "files": [{ "destination": "tokens.js", "format": "javascript/es6" }]
    }
  }
}
```

---

## Handoff Acceptance Criteria (Definition of "Design Done")

A design is ready for engineering when:

- [ ] All screens cover: default state, loading state, empty state, error state
- [ ] Responsive behavior specified for all breakpoints that apply
- [ ] All interactive states designed: hover, active, focus, disabled
- [ ] Token references used (not hardcoded values) throughout
- [ ] Accessibility annotations present: alt text for images, ARIA labels for icons
- [ ] Motion specs documented: what animates, duration, easing, trigger
- [ ] Component names match the design system (not "Rectangle 4")
- [ ] Edge cases covered: long text, missing data, zero state, max items
