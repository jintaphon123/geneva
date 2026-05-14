---
name: ux-designer
argument-hint: "[mode] — persona / journey / usability / synthesis / tokens / components / handoff"
description: >
  UX research and design system covering user personas, journey maps, usability testing,
  research synthesis, design tokens, component documentation, and developer handoff.

  Auto-invoke when Bond asks: user persona, persona generation, journey map, user journey,
  usability test, user testing plan, user research synthesis, synthesize findings,
  design tokens, token system, from brand color, component documentation, design system,
  atomic design, developer handoff, design-dev handoff, export tokens, Figma tokens,
  WCAG accessibility, color contrast, 8pt grid.
---

# UX Designer

Seven modes covering the full UX research and design system workflow.

---

## Mode Detection

| Input | Mode |
|---|---|
| "user persona", "persona generation", "create persona" | **Persona** |
| "journey map", "user journey", "map the experience" | **Journey Map** |
| "usability test", "user testing plan", "moderated test" | **Usability Test** |
| "research synthesis", "synthesize findings", "cluster insights" | **Synthesis** |
| "design tokens", "token system", "from brand color", "color scale" | **Design Tokens** |
| "component docs", "design system components", "atomic design", "component library" | **Components** |
| "dev handoff", "design-dev handoff", "export tokens", "Figma sync" | **Dev Handoff** |

---

## Mode 1 — Persona

Generate research-backed user personas from interview or analytics data.

### Persona Format

```markdown
# [Persona Name] — [Archetype Label]

**Age:** [range] | **Role:** [job title / context] | **Tech comfort:** Low / Medium / High

## Quote
"[A direct quote or composite that captures their worldview]"

## Goals
- [Primary goal — what success looks like for them]
- [Secondary goal]

## Frustrations
- [Top pain point with current solutions]
- [Secondary frustration]

## Behaviors
- [How they work — frequency, tools, environment]
- [Key habit relevant to the product]

## Design Implications
- [What this persona needs from the UI/UX — actionable for design]
- [What to avoid for this persona]
```

### Four Archetypes

| Archetype | Profile | Frequency of use | Feature depth |
|---|---|---|---|
| **Power User** | Expert, daily use, seeks control | Daily | 10+ features |
| **Casual User** | Occasional, task-focused | Weekly | 3–5 features |
| **Business User** | Team context, output-oriented | Daily | Work-specific subset |
| **Mobile-First** | Primary on mobile, on-the-go | Daily | Streamlined core only |

### Research-to-Persona Process

1. Collect: interview transcripts, survey data, analytics (behavior clusters)
2. Code: tag each data point by theme (goal, frustration, behavior, quote)
3. Cluster: group similar tags — each cluster = a candidate persona
4. Validate: % of real users each persona represents (prioritize by volume)
5. Name + write: give persona a name, photo description, fill the format above

Full methodology → `references/research-methods.md`

---

## Mode 2 — Journey Map

Map the end-to-end user experience across a scenario.

### Journey Map Format

| Stage | [Stage 1] | [Stage 2] | [Stage 3] | [Stage 4] | [Stage 5] |
|---|---|---|---|---|---|
| **Actions** | What they do | | | | |
| **Touchpoints** | Where they interact | | | | |
| **Emotions** (1–5) | 😟1 | 😐3 | 😊4 | | |
| **Pain Points** | What's hard | | | | |
| **Opportunities** | How to improve | | | | |

### Stage Definition Rules

- Stages = major phases in the user's goal-completion journey (not app screens)
- Typical stages: Awareness → Consider → Onboard → Use → Expand → Refer / Renew
- Map from the user's perspective, not the product's feature list

### Navigation Map (inbound/outbound)

For each stage, note:
- **Entry points:** How users get to this stage (link, email, search, referral)
- **Exit points:** Where they go next — or where they drop off

### Pain Point + Opportunity Pairing

Every pain point → one opportunity hypothesis:
- Pain: "I don't know where to start after signing up"
- Opportunity: "Add a guided first-action prompt on the empty state"

Full guide → `references/research-methods.md`

---

## Mode 3 — Usability Test

Design a usability test plan from scratch.

### Method Selection

| Method | Users | Duration | When to use |
|---|---|---|---|
| **Moderated Remote** | 5–8 | 45–60 min | Deep insight, explore unknown problems |
| **Unmoderated Remote** | 10–20 | 15–20 min | Validate specific hypotheses at scale |
| **Guerrilla** | 3–5 | 5–10 min | Fast directional signal, limited resources |

### Test Plan Template

```markdown
# Usability Test Plan — [Feature / Flow]

**Research question:** [What single question are we trying to answer?]
**Method:** Moderated / Unmoderated / Guerrilla
**Participants:** [N] users — [screener criteria]
**Duration:** [X] minutes per session
**Moderator:** [Name] | **Observer:** [Name]

---

## Tasks

### Task 1: [Core task name]
"Please [action in second person, present tense — no hints]"
Success criteria: [observable behavior = task complete]
Failure criteria: [user gives up / asks for help / makes critical error]

### Task 2: [Task name]
[Same format]

---

## Metrics
- Task completion rate (%)
- Time on task (seconds)
- Error rate per task
- Satisfaction rating (post-task, 1–5)
- System Usability Scale (SUS) — post-session

---

## Discussion Questions (post-tasks)
1. "What was the most confusing part of that experience?"
2. "Was there anything you expected to find but couldn't?"
3. "How does this compare to [competitor / current solution]?"
```

### Task Writing Rules

- Use second person, present tense: "Go to your account settings and..."
- No hints: don't say "click the blue button" or use product jargon
- Give a realistic scenario: "Imagine you just received a client brief and need to..."
- One action per task — don't combine multiple goals

Full frameworks → `references/research-methods.md`

---

## Mode 4 — Synthesis

Synthesize qualitative research into actionable insights.

### 4-Step Synthesis Process

**Step 1 — Code**
Tag every data point with a theme label. One tag per observation.
Codes: goal, frustration, behavior, workaround, mental model, quote, delight.

**Step 2 — Cluster**
Group similar codes together. Each cluster = a potential insight.
Rule: don't force — if a code doesn't fit a cluster, create a new one.

**Step 3 — Quantify**
Count how many participants or data points support each cluster.
→ prioritize clusters with support from 3+ sources.

**Step 4 — Insight Statement**
Convert cluster → insight → opportunity:
```
Observation: [what users said or did]
Insight: [why this happens — underlying need or mental model]
Opportunity: [product implication — what we could do]
```

### Insight Quality Check

- [ ] Grounded: supported by 3+ data points (not a single anecdote)
- [ ] Non-obvious: not something engineering could have guessed
- [ ] Actionable: leads to a specific design or product decision
- [ ] Framed as need: "users need X" not "users want a button that..."

Full guide → `references/research-methods.md`

---

## Mode 5 — Design Tokens

Generate a complete design token system from a brand color.

### Token Generation Process

**Input:** Brand primary color (hex, e.g. `#0066CC`)

**Step 1 — Color Scale (10-step)**

Generate a 10-step scale from the brand color:
- 50: near-white tint (backgrounds, subtle fills)
- 100–400: light tones (hover states, secondary backgrounds)
- 500: base brand color (primary buttons, links)
- 600–800: dark tones (pressed states, text on light bg)
- 900: near-black shade (headings, high-contrast text)

Also generate: secondary color (complementary or analogous), neutral/gray scale, semantic colors.

**Step 2 — Semantic Colors**

```
--color-primary: [500 value]
--color-primary-hover: [600 value]
--color-primary-pressed: [700 value]
--color-primary-subtle: [50 value]
--color-error: #E53E3E (or brand-adjusted red)
--color-warning: #F6AD55 (or brand-adjusted amber)
--color-success: #38A169 (or brand-adjusted green)
--color-surface-default: #FFFFFF
--color-surface-subtle: [neutral-50]
--color-text-primary: [neutral-900]
--color-text-secondary: [neutral-600]
--color-text-disabled: [neutral-400]
```

**Step 3 — Typography Scale (1.25× ratio)**

| Token | Size | Use |
|---|---|---|
| text-xs | 10px | Labels, captions |
| text-sm | 12px | Secondary text |
| text-base | 16px | Body (default) |
| text-lg | 20px | Lead paragraphs |
| text-xl | 25px | Section headings |
| text-2xl | 31px | Page headings |
| text-3xl | 39px | Display headings |

Font weights: 400 (regular), 500 (medium), 600 (semibold), 700 (bold)
Line heights: 1.5 (body), 1.2 (headings)

**Step 4 — Spacing (8pt grid)**

| Token | Value | Use |
|---|---|---|
| space-1 | 4px | Tight gaps (icon + label) |
| space-2 | 8px | Default component padding |
| space-3 | 12px | Section internal spacing |
| space-4 | 16px | Component margins |
| space-6 | 24px | Section gaps |
| space-8 | 32px | Layout sections |
| space-12 | 48px | Page sections |
| space-16 | 64px | Major layout divisions |

**Step 5 — Other Token Categories**

```
Border radius: none(0) / sm(4px) / md(8px) / lg(12px) / xl(16px) / full(9999px)
Box shadow: sm / md / lg / xl (elevation levels)
Duration: instant(0ms) / fast(100ms) / normal(200ms) / slow(300ms) / slower(500ms)
Easing: ease-in / ease-out / ease-in-out / spring (cubic-bezier(0.34,1.56,0.64,1))
Breakpoints: sm(480) / md(640) / lg(768) / xl(1024) / 2xl(1280) / 3xl(1536)
```

Full token system → `references/design-system.md`

---

## Mode 6 — Components

Document and structure a component library using atomic design.

### Atomic Design Hierarchy

```
Atoms         → Button, Input, Icon, Badge, Avatar, Checkbox, Toggle
Molecules     → SearchBar (Input + Button), FormField (Label + Input + Error), Card
Organisms     → Header (Nav + Logo + CTA), DataTable, Form, Sidebar
Templates     → DashboardLayout, AuthLayout, LandingLayout
```

### Component Documentation Format

```markdown
# [ComponentName]

## Overview
[1-2 sentences: what it is and when to use it]

## Variants
| Variant | Description | When to use |
|---|---|---|
| primary | [description] | Primary action |
| secondary | [description] | Secondary action |
| ghost | [description] | Tertiary / destructive |

## Props
| Prop | Type | Default | Description |
|---|---|---|---|
| variant | 'primary' \| 'secondary' \| 'ghost' | 'primary' | Visual style |
| size | 'sm' \| 'md' \| 'lg' | 'md' | Component size |
| disabled | boolean | false | Disables interaction |

## States
- Default, Hover, Active (pressed), Focus, Disabled, Loading

## Accessibility
- ARIA role: button
- Keyboard: Enter + Space to activate
- Focus ring: visible, 2px offset
- Disabled: aria-disabled="true", not focusable

## Do / Don't
✅ Do: Use primary for the single most important action per view
❌ Don't: Use more than one primary button per section
```

Full patterns → `references/design-system.md`

---

## Mode 7 — Dev Handoff

Prepare design assets for engineering consumption.

### Export Formats

**CSS Custom Properties:**
```css
:root {
  --color-primary-500: #0066CC;
  --color-primary-600: #0052A3;
  --font-size-base: 16px;
  --space-4: 16px;
  --radius-md: 8px;
}
```

**Tailwind Config:**
```js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#E6F0FF',
          500: '#0066CC',
          900: '#002952',
        }
      },
      spacing: {
        '4': '16px',
        '8': '32px',
      }
    }
  }
}
```

**JSON (for design tools / multi-platform):**
```json
{
  "color": {
    "primary": {
      "500": { "value": "#0066CC", "type": "color" }
    }
  },
  "spacing": {
    "4": { "value": "16px", "type": "spacing" }
  }
}
```

### Handoff Checklist

- [ ] All token values exported in agreed format (CSS / Tailwind / JSON)
- [ ] Component specs include: spacing, typography, color tokens (not hardcoded values)
- [ ] States documented for all interactive components
- [ ] Responsive behavior specified (mobile-first breakpoints)
- [ ] WCAG contrast ratios verified for all text/background combinations
- [ ] Motion specs included (duration, easing) for animated components
- [ ] Figma file organized: Frames labeled, components in library, auto-layout used

Full guide → `references/handoff-guide.md`

---

## WCAG Quick Reference

| Check | AA requirement | AAA requirement |
|---|---|---|
| Normal text contrast | 4.5:1 | 7:1 |
| Large text (18px+ or 14px bold) | 3:1 | 4.5:1 |
| UI components (icons, borders) | 3:1 | — |
| Focus indicator | Visible, 3:1 | — |

---

## References

- `references/research-methods.md` — Persona methodology, journey mapping, usability test structures, synthesis coding, validation checklists
- `references/design-system.md` — Token categories, atomic design hierarchy, variant pattern conventions, WCAG contrast
- `references/handoff-guide.md` — CSS/Tailwind/JSON export formats, Figma sync setup, framework integration, handoff checklist
