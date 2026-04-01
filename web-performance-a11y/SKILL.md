---
name: web-performance-a11y
description: "Use this when: my site is slow, why is my Lighthouse score low, my LCP is too high, my page keeps shifting layout, fix Core Web Vitals, make my site accessible, keyboard navigation is broken, screen readers can't use my page, reduce bundle size, fix color contrast issues, my page fails WCAG, images are hurting my load time, why is my page janky on scroll, Lighthouse, axe"
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

## Reference
```yaml
# GitHub Actions: Lighthouse CI + pa11y
jobs:
  lighthouse:
    steps:
      - run: npm ci && npm run build
      - run: npx @lhci/cli autorun
  accessibility:
    steps:
      - run: npx pa11y https://staging.example.com
```
