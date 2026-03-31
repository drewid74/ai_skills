---
name: web-performance-a11y
description: "Use this skill whenever the user wants to optimize web performance, improve page load times, audit accessibility, or ensure compliance with WCAG standards. Triggers include: any mention of 'performance', 'page speed', 'Lighthouse', 'Core Web Vitals', 'LCP', 'FID', 'INP', 'CLS', 'TTFB', 'Time to First Byte', 'First Contentful Paint', 'FCP', 'bundle size', 'lazy loading', 'code splitting', 'tree shaking', 'minification', 'compression', 'caching', 'CDN', 'image optimization', 'WebP', 'AVIF', 'accessibility', 'a11y', 'WCAG', 'screen reader', 'ARIA', 'alt text', 'keyboard navigation', 'focus management', 'color contrast', 'semantic HTML', 'skip link', 'tab order', 'JAWS', 'NVDA', 'VoiceOver', 'axe', 'pa11y', 'wave', 'SEO', 'meta tags', 'structured data', 'Open Graph', or any request to make a website faster, more accessible, or more SEO-friendly. Also use when the user asks 'why is my site slow?', 'how do I pass Lighthouse?', or 'make this accessible'. If someone shares a web page or component and mentions performance or accessibility concerns, use this skill."
---

## Overview

Performance and accessibility are not separate concerns—they affect the same fundamental goal: making your site usable for everyone. This skill covers measuring and improving Core Web Vitals, optimizing assets and delivery, and ensuring WCAG 2.1/2.2 AA compliance.

## Core Web Vitals

### LCP (Largest Contentful Paint)
- **What**: Time until the largest visible content element renders (hero image, heading, paragraph)
- **Target**: ≤ 2.5 seconds
- **Why it matters**: Users judge site speed in the first few seconds; slow LCP drives bounce rates
- **Common causes**: Large unoptimized images, render-blocking CSS/JS, slow server response (high TTFB), client-side rendering without SSR
- **Fixes**:
  - Optimize hero image: responsive sizes, modern format (WebP/AVIF), remove bloat
  - Preload critical resources: `<link rel="preload" href="hero.webp" as="image">`
  - Use SSR/SSG to deliver HTML with content already in it
  - Reduce TTFB with CDN, caching, and server optimization

### INP (Interaction to Next Paint) — replaces FID
- **What**: Responsiveness to user interactions (click, tap, keypress); time until next visual update
- **Target**: ≤ 200ms
- **Why it matters**: Slow interactivity frustrates users and makes sites feel broken
- **Common causes**: Long JavaScript tasks blocking main thread (>50ms), expensive event handlers, layout thrashing
- **Fixes**:
  - Break long tasks with `requestIdleCallback()`, `setTimeout(0)`, or scheduler API
  - Debounce and throttle handlers (resize, scroll events)
  - Avoid forced synchronous layout: read DOM properties after writes, batch updates
  - Move expensive computation to Web Workers (crypto, image processing)

### CLS (Cumulative Layout Shift)
- **What**: Unexpected visual instability—how much content shifts without user input
- **Target**: ≤ 0.1 (0.01 for ads)
- **Why it matters**: Users misclick moving buttons and lose their place; increases anxiety
- **Common causes**: Images/ads without dimensions, dynamic content insertion above fold, web fonts causing text reflow
- **Fixes**:
  - Set explicit width/height on all images and video (or use `aspect-ratio` CSS)
  - Reserve space for dynamic content: `min-height` for ads, dropdowns, lazy-loaded content
  - Preload fonts or use `font-display: swap` to prevent text reflow
  - Avoid inserting content above the fold after page load

### TTFB (Time to First Byte)
- **What**: Server response time—how long until the browser receives the first byte
- **Target**: ≤ 800ms
- **Fixes**:
  - Use a CDN to serve from edge locations near users
  - Enable edge caching on dynamic requests (short TTL)
  - Server-side caching for database queries and expensive computations
  - Optimize database queries (indexes, N+1 prevention)
  - Reduce middleware overhead

## Asset Optimization

### Images
- **Format selection**: AVIF (30-50% smaller than JPEG) > WebP (25-35% smaller) > JPEG/PNG
- **Responsive images**: Use `<img srcset="image-400w.webp 400w, image-800w.webp 800w" sizes="(max-width: 600px) 400px, 800px">` to serve appropriately-sized variants
- **Lazy loading**: Add `loading="lazy"` to below-fold images (native browser support; automatically deferred)
- **Dimensions**: Always set width and height attributes (prevents CLS when image loads)
- **Tools**: sharp (Node.js), Squoosh (CLI), ImageMagick for batch processing
- **SVG**: Use for icons, logos, and simple graphics (vector, infinitely scalable, tiny file size)

### JavaScript
- **Code splitting**: Load only code for the current route/feature. Each route gets its own bundle.
- **Tree shaking**: Remove unused exports (ES modules + bundler required)
- **Dynamic imports**: Use `import('feature')` for non-critical features loaded on demand
- **Bundle analysis**: webpack-bundle-analyzer, source-map-explorer, vite-bundle-visualizer to visualize bloat
- **Third-party audits**: Remove unused libraries, defer non-essential scripts, self-host critical analytics

### CSS
- **Critical CSS**: Inline above-fold styles in `<style>` tag, load the rest async with `<link media="print" onload="this.media='all'">`
- **Remove unused CSS**: PurgeCSS (legacy) or Tailwind's built-in purge; check Sass files too
- **Minification**: cssnano, LightningCSS, or built-in bundler minification
- **Avoid @import chains**: Each import creates an HTTP request; use bundler instead
- **Modern CSS**: Container queries, cascade layers, and `:has()` reduce JavaScript needs

### Fonts
- **font-display: swap**: Show fallback font immediately, swap to custom font when loaded (prevents invisible text)
- **Preload critical fonts**: `<link rel="preload" href="inter-bold.woff2" as="font" type="font/woff2" crossorigin>`
- **Subset fonts**: Include only character sets needed (Latin vs full Unicode reduces size 50-70%)
- **Format**: WOFF2 only (best compression, supported everywhere); drop WOFF/TTF
- **Limit variations**: Each weight/style is a separate file; fewer = faster (e.g., 2 weights, 2 styles = 4 files)

## Delivery Optimization

### Caching
- **Browser caching**: Set `Cache-Control: max-age=31536000, immutable` on hashed assets (cache forever if content never changes)
- **Service workers**: Cache static assets for repeat visitors, enable offline experience, background sync
- **Conditional requests**: ETag or Last-Modified headers for dynamic content (304 Not Modified saves bandwidth)
- **Cache busting**: Content hash in filenames (`app.a1b2c3d4.js`); change content = change filename = instant cache invalidation

### Compression
- **Brotli** preferred over gzip (15-25% smaller at same compression speed)
- **Enable at CDN/reverse proxy**: nginx (`brotli on;`), Cloudflare (automatic), AWS CloudFront (enable in settings)
- **Pre-compress at build time**: Generate `.br` and `.gz` versions of static assets for fastest delivery
- **What to compress**: HTML, CSS, JS, SVG, JSON, XML (not images/video—already compressed)

### CDN
- **Serve static assets** from CDN edge nodes (closest geographic location to user)
- **API caching**: Short TTL on dynamic endpoints, or edge compute (Cloudflare Workers) for transformations
- **Cache invalidation**: Use versioned URLs (hash in filename) to avoid manual purges

### HTTP/2 and HTTP/3
- **HTTP/2**: Multiplexing (multiple requests per connection), header compression, server push (deprecated)
- **HTTP/3 (QUIC)**: UDP-based, faster connection establishment, better on lossy/high-latency networks
- **Enable**: Usually just a config toggle at reverse proxy or CDN level

## Accessibility (WCAG 2.1/2.2 AA)

### Perceivable
- **Alt text**: Every `<img>` must have alt text. Decorative images: `alt=""`. Informative images: describe content meaningfully (not "image of"; answer "what does this communicate?")
- **Color contrast**: Minimum 4.5:1 for normal text, 3:1 for large text (18px+ bold or 24px+ regular). Check with WebAIM contrast checker or DevTools accessibility panel
- **Text resize**: Content must remain usable at 200% zoom. Use relative units (rem, em) for text sizes, not fixed px
- **Captions**: Video requires captions; audio requires transcript or captions
- **No information by color alone**: Colorblind users cannot distinguish red/green. Use icons, patterns, underlines, or text in addition to color

### Operable
- **Keyboard navigation**: Every interactive element reachable via Tab, operable via Enter/Space. No keyboard traps.
- **Skip link**: First focusable element should link to main content (`<a href="#main-content">Skip to main</a>`; place before nav)
- **Focus indicators**: Visible focus outline on all buttons, links, inputs. Never remove `outline` without providing a visible replacement (e.g., `outline: 2px solid blue`)
- **Tab order**: Logical reading order matches visual order. Let DOM order dictate tab order; don't use CSS to rearrange interactive elements
- **No time limits**: Or provide controls to pause/extend. Especially critical for forms, quizzes, checkout
- **Reduced motion**: Respect `prefers-reduced-motion: reduce` media query. Disable animations and transitions for users who set this

### Understandable
- **Language**: Set `<html lang="en">` (or appropriate language code). Screen readers need this for pronunciation.
- **Form labels**: Every `<input>` has an associated `<label>` using `for` attribute or wrapping. Placeholder is NOT a label.
- **Error messages**: Clearly state what's wrong and how to fix it. Associate errors with their field via `aria-describedby`
- **Consistent navigation**: Nav structure, menu order, and link names should be consistent across all pages
- **Predictable behavior**: No unexpected context changes when focus moves or input is submitted

### Robust
- **Semantic HTML**: Use `<button>` for buttons (not `<div onclick>`), `<nav>` for navigation, `<main>` for main content, `<header>`, `<footer>`, `<article>`, `<aside>`. Valid HTML is prerequisite for accessibility.
- **ARIA**: Use only when semantic HTML is insufficient. Prefer native HTML. Common uses: `role="alert"`, `aria-expanded="true"`, `aria-live="polite"`, `aria-hidden="true"` on decorative elements
- **Landmarks**: `<main>`, `<nav>`, `<header>`, `<footer>`, `<aside>` help screen reader users jump directly to sections
- **Headings**: Hierarchical structure (h1 → h2 → h3), no skipped levels. One `<h1>` per page.

## Testing & Tools

### Performance
- **Lighthouse**: Chrome DevTools > Lighthouse tab. CI integration with `lhci` for automated checks
- **WebPageTest**: Detailed waterfall analysis, test from multiple geographic locations and devices
- **Chrome DevTools Performance tab**: Flame chart, long tasks, layout shifts, main thread blocking
- **Bundle analyzers**: webpack-bundle-analyzer, source-map-explorer, vite-bundle-visualizer to visualize bloat

### Accessibility
- **axe DevTools**: Browser extension, scans rendered DOM for WCAG violations
- **pa11y**: CLI and CI tool for automated accessibility testing (`pa11y https://example.com`)
- **WAVE**: Visual overlay showing issues and regions
- **Screen readers**: VoiceOver (macOS/iOS, free), NVDA (Windows, free), JAWS (Windows, paid). Test with at least NVDA + Chrome or VoiceOver + Safari
- **Keyboard testing**: Unplug mouse and navigate entire site with keyboard. Can you reach and operate every interactive element?

### CI Integration Example
```yaml
name: Performance & Accessibility
on: [pull_request]
jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm ci && npm run build
      - run: npx @lhci/cli@0.9.x autorun
  pa11y:
    runs-on: ubuntu-latest
    steps:
      - run: npx pa11y https://staging.example.com
```

## SEO Essentials
- **Title tag**: Unique per page, 50-60 characters, include primary keyword
- **Meta description**: Unique per page, 150-160 characters, compelling call-to-action
- **Structured data**: JSON-LD in `<script>` tags helps search engines understand content (Product, Article, Organization, etc.)
- **Open Graph tags**: Control social media previews (`og:title`, `og:image`, `og:description`, `og:type`)
- **Sitemap.xml** and **robots.txt**
- **Canonical URL**: `<link rel="canonical" href="https://example.com/page">` prevents duplicate content issues
- **Mobile-friendly**: Responsive design, no horizontal scroll, tap targets ≥ 48px, viewport meta tag

## Quick Audit Checklist
- [ ] Lighthouse performance score ≥ 90
- [ ] LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1
- [ ] All images have alt text, width, height attributes
- [ ] Color contrast ≥ 4.5:1 for body text
- [ ] Site fully keyboard-navigable; every button/link reachable via Tab
- [ ] Skip link present and functional
- [ ] Semantic HTML (buttons, forms, landmarks); minimal `<div>` soup
- [ ] ARIA attributes correct and minimal (prefer native HTML)
- [ ] axe scan: 0 critical/serious violations
- [ ] Assets compressed (Brotli), images in WebP/AVIF format
- [ ] Critical CSS inlined, JS code-split by route, unused code removed
- [ ] Meta description, title, og:tags, structured data in place
