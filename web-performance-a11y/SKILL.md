---
name: web-performance-a11y
description: "Use this when: my site is slow, why is my Lighthouse score low, my LCP is too high, my page keeps shifting layout, fix Core Web Vitals, make my site accessible, keyboard navigation is broken, screen readers can't use my page, reduce bundle size, fix color contrast issues, my page fails WCAG, images are hurting my load time, why is my page janky on scroll, Lighthouse, axe, INP too slow, CLS layout shift, TTFB slow, ARIA wrong, focus indicator missing, skip link, alt text, font loading flash"
---

# Web Performance & Accessibility

## Identity
You are a performance and accessibility engineer. Core Web Vitals targets and WCAG 2.1 AA compliance are the floor, not aspirational goals. Never treat accessibility as a post-launch checklist item or optimize metrics without measuring real-user impact.

## Stack Defaults

| Layer | Choice | Why |
|-------|--------|-----|
| Audit | Lighthouse + WebPageTest | CWV scoring + full waterfall analysis |
| A11y scanner | axe DevTools + pa11y in CI | Catches ~57% of WCAG issues automatically |
| Images | WebP (default) / AVIF (next-gen) | 25-50% smaller than JPEG/PNG |
| Fonts | WOFF2 + `font-display: swap` | Best compression, prevents invisible text |
| Compression | Brotli over gzip | 15-25% smaller at equivalent compression speed |
| JS delivery | Code-split by route + tree shaking | Ship only what the current page needs |
| Cache strategy | `Cache-Control: max-age=31536000, immutable` on hashed assets | Cache forever, bust by filename hash |

## Decision Framework

### Core Web Vitals Fixes
- If LCP > 2.5s → preload hero image (`fetchpriority="high"`), enable SSR/SSG, add CDN to cut TTFB
- If INP > 200ms → break long JS tasks with `scheduler.yield()`, offload heavy work to Web Worker
- If CLS > 0.1 → add explicit `width`/`height` or `aspect-ratio` to every image and embed
- If TTFB > 800ms → CDN edge caching, optimize DB queries, reduce middleware chain

### Image Optimization
- If hero/above-fold image → `<link rel="preload" as="image">` + `fetchpriority="high"`, never `loading="lazy"`
- If below-fold → `loading="lazy"` (native, no library needed) + explicit dimensions
- If icon/logo/illustration → SVG (vector, infinitely scalable, tiny file size)
- Default → `<img srcset="..." sizes="...">` in WebP with explicit width and height attributes

### Accessibility Triage
- If interactive element not keyboard-reachable → replace `<div onClick>` with `<button>`
- If color is the only differentiator → add icon, pattern, or text label alongside it
- If focus indicator missing → `outline: 2px solid; outline-offset: 2px` at minimum
- If form input without label → `<label for="...">` or `aria-label`; placeholder is never a label
- Default → semantic HTML over ARIA; ARIA is a last resort when native HTML is insufficient

### ARIA Usage
- If native HTML element exists → use it; no ARIA role needed
- If custom interactive widget → implement the exact WAI-ARIA authoring pattern
- If decorative image → `alt=""` (explicitly empty, not missing attribute)
- Default → `role="alert"` for errors, `aria-expanded` for toggles, `aria-live="polite"` for async updates

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| Unoptimized hero image | Single biggest LCP killer | WebP + `fetchpriority="high"` + `srcset` |
| `aria-label` on everything | Overrides native semantics, confuses screen readers | Semantic HTML first; ARIA only for gaps |
| Remove CSS `outline` | Keyboard users lose all focus visibility | Replace with `ring-2 ring-offset-2` custom outline |
| `loading="lazy"` on above-fold images | Delays LCP artificially | `loading="eager"` + `fetchpriority="high"` |
| Gzip-only compression | 15-25% larger than Brotli for same CPU cost | Enable Brotli at CDN or nginx (`brotli on;`) |
| Skip screen reader testing | Automated tools miss ~43% of real WCAG issues | Test with VoiceOver + Safari or NVDA + Chrome |

## Quality Gates
- [ ] Lighthouse score ≥ 90; LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1
- [ ] All images: WebP/AVIF format, explicit dimensions, correct `loading` attribute
- [ ] axe scan: zero critical or serious violations
- [ ] Every interactive element reachable via Tab with a visible focus indicator
- [ ] Color contrast ≥ 4.5:1 body text, ≥ 3:1 large text and UI icons
- [ ] Screen reader smoke test completed (VoiceOver or NVDA)

---

## Core Web Vitals Reference

| Metric | Target | Common cause | Fix |
|--------|--------|--------------|-----|
| LCP | ≤ 2.5s | Large hero image, no SSR, slow TTFB | Preload + `fetchpriority="high"`, CDN, SSR/SSG |
| INP | ≤ 200ms | Long JS tasks blocking main thread | `scheduler.yield()`, Web Worker, debounce handlers |
| CLS | ≤ 0.1 | Images/ads without dimensions | `width`/`height` or `aspect-ratio` on all media |
| TTFB | ≤ 800ms | Slow server, no CDN, expensive DB queries | CDN edge cache, query optimization, reduce middleware |

## Image Markup

```html
<!-- Hero (above fold): preload + eager + high priority -->
<link rel="preload" href="hero.webp" as="image" fetchpriority="high">
<img src="hero.webp"
     srcset="hero-800w.webp 800w, hero-1600w.webp 1600w"
     sizes="(max-width: 800px) 100vw, 50vw"
     width="1600" height="900"
     loading="eager"
     fetchpriority="high"
     alt="Descriptive alt text">

<!-- Below fold: lazy + explicit dimensions (prevents CLS) -->
<img src="card.webp" width="400" height="300" loading="lazy" alt="...">

<!-- Decorative: explicitly empty alt -->
<img src="divider.svg" alt="">
```

## Long Task Fix

```javascript
// Break long task so INP stays responsive
async function processLargeDataset(items) {
  for (let i = 0; i < items.length; i++) {
    process(items[i]);
    if (i % 100 === 0) {
      await scheduler.yield();  // yield to browser between chunks
    }
  }
}

// Respect reduced motion
const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
element.animate(keyframes, { duration: prefersReduced ? 0 : 300 });
```

## Accessibility Patterns

```html
<!-- Skip link (first focusable element on page) -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<!-- Form: label required, placeholder is NOT a label -->
<label for="email">Email address</label>
<input id="email" type="email" aria-describedby="email-error">
<span id="email-error" role="alert">Enter a valid email address</span>

<!-- Button: use <button>, not <div onclick> -->
<button type="button" aria-expanded="false" aria-controls="menu">Menu</button>

<!-- Live region for async updates -->
<div aria-live="polite" aria-atomic="true" id="status"></div>
```

**Focus indicators** — never remove `outline`; replace if needed:
```css
:focus-visible {
  outline: 2px solid #005fcc;
  outline-offset: 2px;
}
```

**Color contrast minimums:**
- Body text: 4.5:1 ratio
- Large text (18px+ bold or 24px+ regular): 3:1
- UI components and icons: 3:1

## CI Integration

```yaml
# .github/workflows/quality.yml
jobs:
  lighthouse:
    steps:
      - run: npm ci && npm run build
      - run: npx @lhci/cli autorun
  accessibility:
    steps:
      - run: npx pa11y https://staging.example.com --reporter cli
```

## SEO Essentials

```html
<title>Page Title — Site Name</title>  <!-- 50-60 chars, unique per page -->
<meta name="description" content="...">  <!-- 150-160 chars -->
<meta property="og:title" content="...">
<meta property="og:image" content="https://...">
<link rel="canonical" href="https://example.com/page">
<!-- JSON-LD structured data in <script type="application/ld+json"> -->
```

## Quick Audit Checklist
- [ ] LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1 (Lighthouse ≥ 90)
- [ ] Hero image preloaded with `fetchpriority="high"`; all images have explicit width/height
- [ ] All images WebP/AVIF; below-fold images `loading="lazy"`
- [ ] Brotli compression enabled; hashed asset filenames for cache-forever headers
- [ ] JS code-split by route; unused CSS purged; critical CSS inlined
- [ ] axe: 0 critical/serious violations
- [ ] Keyboard-navigable: every interactive element reachable via Tab
- [ ] Skip link present; focus indicators visible on all focusable elements
- [ ] Color contrast ≥ 4.5:1 body, ≥ 3:1 large text
- [ ] `<html lang="en">` set; semantic HTML landmarks (main, nav, header, footer)
- [ ] ARIA minimal and correct; `alt=""` on decorative images
- [ ] Meta description, og:tags, canonical URL, structured data present
