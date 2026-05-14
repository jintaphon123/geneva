---
name: web-animator
description: >
  Cinematic 2.5D interactive websites using scroll storytelling, parallax depth, text animations,
  and 45+ premium scroll techniques — no WebGL required. Pure CSS + JavaScript.

  Auto-invoke when Bond asks: web animation, scroll animation, parallax, scrollytelling, immersive website,
  landing page animation, Apple-style animation, sections that overlap, hero animation, scroll-driven effects,
  text animation, clip-path reveal, product floating between sections, sticky section, scroll effect,
  "make it feel alive", "cinematic", "premium feel", "feels like Apple", aurora background,
  blur on scroll, fade in on scroll, pin section, horizontal scroll. Covers landing pages, product sites,
  hero sections, any web design needing motion, depth, or cinematic quality.
---

# Web Animator

Cinematic 2.5D websites using CSS + JavaScript scroll techniques. No WebGL, no 3D modeling required.

Three modes: **Build** (from scratch), **Enhance** (add effects to existing), **Debug** (fix perf/animation issues).

Reference files:
- `references/animation-techniques.md` — 45+ techniques across 8 categories with code patterns

---

## Before Starting (ALWAYS run first)

**Check for context:**
- Read `project-context.md` or `product-context.md` if they exist
- Ask Bond (if no context file): brief + key assets + target feel (3 questions max)

**Asset inspection:**
```bash
find . -name "*.png" -o -name "*.jpg" -o -name "*.webp" -o -name "*.svg" | head -20
# Inspect: dimensions, transparency, subject (person/product/abstract?)
# Plan: which assets get depth layers, which are static
```

---

## Mode Detection

| Input | Mode |
|---|---|
| New landing page, "build from scratch", has assets ready | **Build** |
| Existing page + "add animations", "make it more alive" | **Enhance** |
| "Lagging", "janky", "animation not working", performance | **Debug** |

---

## Mode 1 — Build from Scratch

Read `references/animation-techniques.md` fully before executing.

**Workflow (in order — do not skip steps):**

**Step 1: Brief + Assets**
- Extract: what is the product/brand, who is the audience, what emotion should it evoke?
- Inspect all assets: dimensions, subject, transparency, usability as depth layers

**Step 2: Layer Architecture**
Assign depth layers before writing code:
```
Layer 5 (back):   background gradient or sky
Layer 4:          far parallax (mountains, abstract shapes)
Layer 3:          mid ground (product environment)
Layer 2:          main subject (product or hero image)
Layer 1 (front):  text, UI elements
```

**Step 3: Section Map**
Plan all sections before coding:
- What enters/exits each section?
- Is any section sticky (pin on scroll)?
- What transitions between sections?

**Step 4: Code**
- HTML structure first (semantic, accessible)
- CSS layers + base styles
- JavaScript scroll logic (IntersectionObserver or GSAP ScrollTrigger)
- Reduced motion: wrap all animations in `@media (prefers-reduced-motion: no-preference)`

**Step 5: Performance Check**
- Only animate: `transform`, `opacity` (GPU-accelerated)
- Never animate: `width`, `height`, `top`, `left`, `margin` (causes reflow)
- Add `will-change: transform` only where needed (not globally)

---

## Mode 2 — Enhance Existing

Read `references/animation-techniques.md` fully before executing.

**Workflow:**
1. Read current HTML/CSS structure
2. Identify: which sections have most visual weight? (prioritize these)
3. Propose 3-5 specific animations with rationale (don't implement without approval)
4. Apply one technique at a time, test each
5. Final pass: GPU rules, reduced-motion, mobile check

---

## Mode 3 — Debug

```
Performance: Open DevTools → Performance tab → record scroll
Look for:  Layout thrashing (alternating purple+green), long frames (red)
Fix: Move reads before writes; batch DOM operations

Jank: Check if animating non-GPU properties → move to transform/opacity
Fix: transform: translateY() instead of top:; opacity instead of visibility:

Not smooth: Check if will-change is missing or overused
Fix: Add will-change: transform to elements being animated; remove from static elements
```

---

## Global Rules

- Every page must feel like a cinematic experience — flat/static is a failure state
- Never hardcode pixel heights for sticky sections — use `100vh` or `min-content`
- Performance rule: 60fps on a mid-range laptop is the bar (not just high-end machines)
- Accessibility: `prefers-reduced-motion` must disable all animations (not just slow them)
- Mobile: test at 375px width; parallax depth is fine, but ensure content is readable
