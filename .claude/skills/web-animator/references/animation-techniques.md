# Animation Techniques Reference

## GPU Rules (CRITICAL — always check before animating)

```css
/* ✅ GPU-accelerated — smooth at 60fps */
transform: translateX() translateY() scale() rotate()
opacity: 0 → 1

/* ❌ Causes reflow — avoid for animation */
width, height, top, left, right, bottom, margin, padding

/* will-change: only where needed */
.animated-element { will-change: transform; }
/* Remove after animation completes: element.style.willChange = 'auto'; */
```

## Category 1 — Parallax Depth

### Basic Parallax (CSS Custom Properties)
```css
.parallax-section {
    --scroll: 0;
    transform: translateY(calc(var(--scroll) * 0.4px));
}
```
```javascript
// Update on scroll
let ticking = false;
window.addEventListener('scroll', () => {
    if (!ticking) {
        requestAnimationFrame(() => {
            const scrollY = window.scrollY;
            document.querySelectorAll('[data-parallax]').forEach(el => {
                const speed = parseFloat(el.dataset.parallax) || 0.3;
                el.style.transform = `translateY(${scrollY * speed}px)`;
            });
            ticking = false;
        });
        ticking = true;
    }
});
```

### 2.5D Layer Stack
```css
.scene {
    position: relative;
    overflow: hidden;
    height: 100vh;
}
.layer-bg    { transform: translateY(calc(var(--scroll) * 0.1px)); }  /* slowest */
.layer-mid   { transform: translateY(calc(var(--scroll) * 0.3px)); }
.layer-fg    { transform: translateY(calc(var(--scroll) * 0.6px)); }  /* fastest */
.layer-text  { transform: translateY(calc(var(--scroll) * 0px)); }    /* no parallax — text stays */
```

## Category 2 — Sticky & Pin Sections

### Sticky Section (element pins while content scrolls past)
```css
.sticky-container {
    position: relative;
    height: 300vh;   /* how long it stays sticky */
}
.sticky-content {
    position: sticky;
    top: 0;
    height: 100vh;
    overflow: hidden;
}
```

### Progress-Based Animation (progress 0→1 as section scrolls)
```javascript
function getScrollProgress(el) {
    const rect = el.getBoundingClientRect();
    const windowH = window.innerHeight;
    return Math.max(0, Math.min(1, (windowH - rect.top) / (windowH + rect.height)));
}

// Animate based on progress
const sticky = document.querySelector('.sticky-container');
window.addEventListener('scroll', () => {
    const progress = getScrollProgress(sticky);
    // Use progress: 0 = entering, 0.5 = midway, 1 = leaving
    hero.style.scale = 1 + progress * 0.3;
    text.style.opacity = 1 - progress * 2;
});
```

## Category 3 — Text Animations

### Words Light Up on Scroll (word-by-word reveal)
```css
.animated-text .word {
    opacity: 0.2;
    transition: opacity 0.3s ease;
}
.animated-text .word.visible {
    opacity: 1;
}
```
```javascript
function splitIntoWords(el) {
    el.innerHTML = el.textContent.split(' ')
        .map(w => `<span class="word">${w} </span>`).join('');
}

const observer = new IntersectionObserver(entries => {
    entries.forEach(({ target, intersectionRatio }) => {
        if (intersectionRatio > 0.3) target.classList.add('visible');
    });
}, { threshold: 0.3 });

document.querySelectorAll('.animated-text .word').forEach(w => observer.observe(w));
```

### Text Fly In (slide + fade)
```css
@keyframes flyIn {
    from { opacity: 0; transform: translateY(40px); }
    to   { opacity: 1; transform: translateY(0); }
}

.fly-in {
    opacity: 0;
    animation: flyIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

/* Stagger children */
.fly-in:nth-child(1) { animation-delay: 0ms; }
.fly-in:nth-child(2) { animation-delay: 100ms; }
.fly-in:nth-child(3) { animation-delay: 200ms; }
```

### Bleed Typography (text larger than viewport — cinematic)
```css
.bleed-text {
    font-size: clamp(4rem, 15vw, 12rem);
    font-weight: 900;
    letter-spacing: -0.04em;
    line-height: 0.9;
    overflow: hidden;    /* clips if needed */
}
```

## Category 4 — Clip-Path Reveals

### Curtain Drop
```css
.curtain-reveal {
    clip-path: inset(0 0 100% 0);   /* hidden */
    transition: clip-path 0.8s cubic-bezier(0.76, 0, 0.24, 1);
}
.curtain-reveal.visible {
    clip-path: inset(0 0 0% 0);     /* revealed */
}
```

### Iris Open
```css
.iris-reveal {
    clip-path: circle(0% at 50% 50%);
    transition: clip-path 1s cubic-bezier(0.76, 0, 0.24, 1);
}
.iris-reveal.visible {
    clip-path: circle(150% at 50% 50%);
}
```

### Wipe Left to Right
```css
.wipe-reveal {
    clip-path: inset(0 100% 0 0);
    transition: clip-path 0.9s cubic-bezier(0.76, 0, 0.24, 1);
}
.wipe-reveal.visible {
    clip-path: inset(0 0% 0 0);
}
```

## Category 5 — Section Transitions

### Section Overlap (next section slides over current)
```css
section {
    position: sticky;
    top: 0;
    height: 100vh;
    z-index: var(--section-index, 1);
    border-radius: 24px 24px 0 0;   /* rounded top when overlapping */
}
section:nth-child(1) { --section-index: 1; }
section:nth-child(2) { --section-index: 2; }
section:nth-child(3) { --section-index: 3; }
```

### Scale-Up Transition (section zooms in as you scroll)
```javascript
window.addEventListener('scroll', () => {
    sections.forEach((section, i) => {
        const rect = section.getBoundingClientRect();
        const progress = Math.max(0, -rect.top / window.innerHeight);
        const scale = 1 - progress * 0.1;
        section.style.transform = `scale(${scale})`;
        section.style.borderRadius = `${progress * 24}px`;
    });
});
```

## Category 6 — Product Floating Between Sections

### Product Rise Effect (image appears to float up between sections)
```css
.product-float {
    position: sticky;
    top: 50%;
    transform: translateY(-50%);
    z-index: 10;
    transition: transform 0.1s linear;
}
```
```javascript
// Track two sections — product moves between them
const section1 = document.querySelector('.section-1');
const section2 = document.querySelector('.section-2');
const product = document.querySelector('.product-float');

window.addEventListener('scroll', () => {
    const s1Rect = section1.getBoundingClientRect();
    const progress = Math.max(0, Math.min(1, -s1Rect.bottom / window.innerHeight));
    const yOffset = progress * -100;  // move up 100px as section1 exits
    const scale = 1 + progress * 0.15;
    product.style.transform = `translateY(calc(-50% + ${yOffset}px)) scale(${scale})`;
});
```

## Category 7 — Backgrounds

### Aurora Blob (animated gradient blobs)
```css
@keyframes blob-move {
    0%, 100% { border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
    50%       { border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; }
}

.aurora-blob {
    position: absolute;
    width: 600px;
    height: 600px;
    border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%;
    filter: blur(80px);
    opacity: 0.6;
    animation: blob-move 8s ease-in-out infinite;
    pointer-events: none;
}

.blob-1 { background: #7C3AED; animation-delay: 0s; }
.blob-2 { background: #2563EB; animation-delay: -3s; }
.blob-3 { background: #7C3AED40; animation-delay: -6s; }
```

### Gradient Background with Scroll-Driven Color Shift
```javascript
const colors = [
    ['#0f0f1a', '#1a0f2e'],   // dark purple (section 1)
    ['#0f1a0f', '#0f2e0f'],   // dark green (section 2)
    ['#1a0f0f', '#2e0f0f'],   // dark red (section 3)
];

window.addEventListener('scroll', () => {
    const totalH = document.body.scrollHeight - window.innerHeight;
    const progress = window.scrollY / totalH;
    const idx = Math.floor(progress * (colors.length - 1));
    const t = (progress * (colors.length - 1)) % 1;
    // Lerp between colors[idx] and colors[idx+1]
    document.body.style.background = lerpGradient(colors[idx], colors[Math.min(idx+1, colors.length-1)], t);
});
```

## Category 8 — Scroll-Driven CSS (Modern)

### Native CSS Scroll Animation (Chrome 115+)
```css
@keyframes fade-up {
    from { opacity: 0; transform: translateY(30px); }
    to   { opacity: 1; transform: translateY(0); }
}

.card {
    animation: fade-up linear both;
    animation-timeline: view();
    animation-range: entry 0% cover 30%;
}

/* Horizontal scroll progress bar */
.progress-bar {
    position: fixed;
    top: 0;
    left: 0;
    height: 3px;
    background: #7C3AED;
    transform-origin: left;
    animation: progress-grow linear;
    animation-timeline: scroll(root);
}
@keyframes progress-grow {
    from { transform: scaleX(0); }
    to   { transform: scaleX(1); }
}
```

## IntersectionObserver — Standard Trigger Pattern

```javascript
// Reusable trigger for fade-in/slide-in animations
const animObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            // Optional: unobserve after first trigger
            // animObserver.unobserve(entry.target);
        }
    });
}, {
    threshold: 0.15,           // trigger when 15% visible
    rootMargin: '0px 0px -50px 0px',  // trigger slightly before fully visible
});

document.querySelectorAll('[data-animate]').forEach(el => animObserver.observe(el));
```

## Reduced Motion (REQUIRED)

```css
@media (prefers-reduced-motion: reduce) {
    *,
    ::before,
    ::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
    
    /* Ensure content is still visible without animation */
    [data-animate],
    .fly-in,
    .curtain-reveal,
    .iris-reveal {
        opacity: 1 !important;
        transform: none !important;
        clip-path: none !important;
    }
}
```
