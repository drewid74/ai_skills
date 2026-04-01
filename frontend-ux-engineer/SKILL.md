---
title: Frontend UX Engineer
description: "Super-agent consolidating UI/UX development, design system enforcement, technical content strategy, and workspace automation. Triggers: 'fix UX', 'audit design', 'write docs', 'brand voice', 'schedule meeting', 'component library', 'landing page'"
domains:
  - frontend
  - ux
  - design-systems
  - content-strategy
  - automation
tags:
  - tailwind
  - react
  - accessibility
  - design-tokens
  - documentation
  - email-automation
  - brand-consistency
---

# Frontend UX Engineer

A universal super-agent that combines UI/UX development, design system enforcement, technical content strategy, and workspace automation. This skill handles everything from pixel-perfect component implementation to brand-voice consistency across all outputs.

## Why This Consolidation?

Modern product development requires seamless integration between frontend engineering, user experience design, technical documentation, and team coordination. This skill unifies these domains because:

1. **Design & Code are Inseparable** — UX decisions manifest directly in React components and Tailwind configurations
2. **Documentation is UX** — Users interact with your product through code examples, API docs, and READMEs
3. **Consistency Matters** — Brand voice, design tokens, and communication style must align across all touchpoints
4. **Automation Amplifies Quality** — Systematic processes for audits, content, and scheduling prevent drift

---

## Section 1: Frontend Design & UX Enforcement

### The No-Average Rule

**Why:** Average UI feels dated within months. Great UI ages beautifully because it prioritizes clarity, hierarchy, and intentionality over trends.

Every component should answer: *Does this serve a user need, or does it exist because it looked good in a design tool?*

```jsx
// BAD - Decorative without purpose
const Button = () => (
  <button className="px-4 py-2 rounded-lg shadow-lg hover:shadow-xl transition-all">
    Click me
  </button>
);

// GOOD - Purposeful hierarchy, accessible, intentional spacing
const Button = ({ variant = "primary", disabled = false, children }) => {
  const variants = {
    primary: "bg-blue-600 text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-300",
    secondary: "bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-2 focus:ring-gray-400",
    ghost: "text-gray-700 hover:bg-gray-50 focus:ring-2 focus:ring-gray-200"
  };
  
  return (
    <button
      disabled={disabled}
      className={`
        px-4 py-2 rounded-md font-medium text-sm
        transition-colors duration-200
        disabled:opacity-50 disabled:cursor-not-allowed
        ${variants[variant]}
      `}
      aria-label={children}
    >
      {children}
    </button>
  );
};
```

**Why this is better:**
- Variants create predictable hierarchy
- Focus states ensure accessibility
- Disabled state is handled systematically
- Transition durations are consistent (no arbitrary 300ms)
- Token-based colors (blue-600, not #2563eb directly)

### Tailwind v4 Design Tokens Strategy

**Why:** Hardcoded hex values scatter across your codebase like weeds. CSS variables enforce consistency and enable runtime theme switching.

```css
/* tailwind.config.js - Define your design system in one place */
export default {
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "rgb(var(--color-primary) / <alpha-value>)",
          secondary: "rgb(var(--color-secondary) / <alpha-value>)",
          success: "rgb(var(--color-success) / <alpha-value>)",
          error: "rgb(var(--color-error) / <alpha-value>)",
        },
      },
      spacing: {
        xs: "var(--spacing-xs, 0.25rem)",
        sm: "var(--spacing-sm, 0.5rem)",
        md: "var(--spacing-md, 1rem)",
        lg: "var(--spacing-lg, 1.5rem)",
      },
      borderRadius: {
        sm: "var(--radius-sm, 0.25rem)",
        md: "var(--radius-md, 0.375rem)",
        lg: "var(--radius-lg, 0.5rem)",
      },
    },
  },
};
```

```css
/* globals.css - Root token definitions */
:root {
  --color-primary: 59 130 246; /* blue-500 */
  --color-secondary: 107 114 128; /* gray-500 */
  --color-success: 34 197 94; /* green-500 */
  --color-error: 239 68 68; /* red-500 */
  
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
}

[data-theme="dark"] {
  --color-primary: 96 165 250; /* blue-400 for dark mode */
  --color-secondary: 156 163 175; /* gray-400 */
}
```

**Why this pattern:**
- Single source of truth for brand colors
- Theme switching requires no component changes
- Accessibility team can audit colors in one file
- Design tokens scale across mobile and desktop

### Tailwind v4 @theme Blocks

**Why:** Tailwind v4 introduces CSS `@theme` blocks for defining design tokens directly in CSS, replacing JS config in some cases. This enables CSS-first token management with full Tailwind integration.

```css
/* styles.css - Tailwind v4 @theme syntax */
@theme {
  --color-primary: #2563eb;
  --color-secondary: #6b7280;
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --radius-md: 0.375rem;
}
```

Use `@theme` for simple token systems; stick with `tailwind.config.js` for complex scaling rules or plugin dependencies. Both approaches coexist seamlessly.

### Shadcn/UI & Radix Workflow

**Why:** These libraries provide accessible primitives (unstyled components built on WAI-ARIA). You layer Tailwind on top, maintaining full control while eliminating 90% of a11y bugs.

```jsx
// Example: Accessible dropdown using Radix primitives
import * as SelectPrimitive from "@radix-ui/react-select";
import { ChevronDown } from "lucide-react";

const Select = ({ options, value, onChange, label }) => (
  <SelectPrimitive.Root value={value} onValueChange={onChange}>
    <label className="block text-sm font-medium text-gray-700 mb-2">
      {label}
    </label>
    <SelectPrimitive.Trigger className="
      flex items-center justify-between
      w-full px-3 py-2 rounded-md
      border border-gray-300
      bg-white text-left
      hover:border-gray-400
      focus:outline-none focus:ring-2 focus:ring-blue-500
      data-[state=open]:border-blue-500
    ">
      <SelectPrimitive.Value placeholder="Select option" />
      <SelectPrimitive.Icon asChild>
        <ChevronDown className="w-4 h-4 text-gray-600" />
      </SelectPrimitive.Icon>
    </SelectPrimitive.Trigger>

    <SelectPrimitive.Content className="
      z-50 min-w-48 rounded-md border border-gray-200
      bg-white shadow-lg p-1
    ">
      <SelectPrimitive.Viewport>
        {options.map((opt) => (
          <SelectPrimitive.Item
            key={opt.value}
            value={opt.value}
            className="
              flex items-center px-3 py-2 rounded-md
              cursor-pointer outline-none
              hover:bg-gray-100
              focus:bg-blue-50
              data-[state=checked]:bg-blue-50 data-[state=checked]:font-semibold
            "
          >
            <SelectPrimitive.ItemText>{opt.label}</SelectPrimitive.ItemText>
          </SelectPrimitive.Item>
        ))}
      </SelectPrimitive.Viewport>
    </SelectPrimitive.Content>
  </SelectPrimitive.Root>
);

export default Select;
```

**Why Radix + Tailwind:**
- Radix handles keyboard navigation, ARIA attributes, focus management
- Tailwind handles visual styling
- You never build a broken accessible component

### Component Library Options: Shadcn/UI, Magic UI, Radix

**Shadcn/UI** — Copy-paste component library built on Radix + Tailwind. Full control, minimal dependencies. Best for startups and design-heavy projects.

**Magic UI** — Animated component library with pre-built Tailwind components featuring smooth transitions and micro-interactions. Best when animations are part of brand identity (SaaS dashboards, motion-forward apps).

**Radix** — Headless primitives for building custom components. Most control, steepest learning curve. Best for design systems where consistency is non-negotiable.

Choose based on your animation philosophy: Shadcn (minimal motion) → Magic UI (purposeful animation) → Radix (full customization).

### Framer Motion: Purposeful Animation

**Why:** Motion should clarify, not distract. Every animation answers: "Does this help the user understand state change?"

```jsx
import { motion, AnimatePresence } from "framer-motion";

// BAD - Animations for decoration
const DecorativeBox = () => (
  <motion.div
    animate={{ rotate: 360 }}
    transition={{ duration: 2, repeat: Infinity }}
    className="w-10 h-10 bg-blue-500 rounded"
  />
);

// GOOD - Animation clarifies state change
const NotificationStack = ({ notifications }) => (
  <div className="fixed top-4 right-4 space-y-2">
    <AnimatePresence mode="popLayout">
      {notifications.map((notif) => (
        <motion.div
          key={notif.id}
          initial={{ opacity: 0, y: -20, x: 400 }}
          animate={{ opacity: 1, y: 0, x: 0 }}
          exit={{ opacity: 0, y: -20, x: 400 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="bg-green-100 border border-green-400 rounded-md p-4"
        >
          {notif.message}
        </motion.div>
      ))}
    </AnimatePresence>
  </div>
);
```

**Why this motion pattern:**
- Entrance animation shows item appeared (y: -20 → 0)
- Exit animation explains item left (same direction)
- Spring physics feel responsive, not mechanical
- No decoration: every frame serves user understanding

### Next.js Client & Server Component Separation

**Why:** Next.js 13+ defaults to Server Components for data fetching and security. Use `'use client'` sparingly for interactive elements. This pattern speeds initial load and reduces JavaScript shipped to browsers.

```jsx
// app/dashboard/page.js - Server Component (default)
import { fetchUserStats } from "@/lib/api";
import StatCard from "./stat-card"; // Client component

export default async function Dashboard() {
  const stats = await fetchUserStats(); // Runs on server only

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <StatCard title="Users" value={stats.totalUsers} />
      <StatCard title="Revenue" value={stats.revenue} />
    </div>
  );
}

// app/dashboard/stat-card.js - Client Component (interactive)
'use client';
import { useState } from "react";

export default function StatCard({ title, value }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div onClick={() => setExpanded(!expanded)} className="cursor-pointer p-4 border rounded">
      <h3>{title}</h3>
      <p>{value}</p>
    </div>
  );
}
```

**Why this matters:** Server components eliminate hydration mismatches, reduce bundle size, and let you access databases directly. Use `'use client'` only for hooks (useState, useEffect) and event listeners.

### Mobile-First Architecture

**Why:** Mobile constraints force clarity. Designing for 375px screens creates better 1440px experiences.

```jsx
// Mobile-first responsive grid
const ProductGrid = () => (
  <div className="
    grid gap-4
    grid-cols-1         /* Mobile: 1 column */
    sm:grid-cols-2      /* Tablet: 2 columns */
    lg:grid-cols-3      /* Desktop: 3 columns */
    xl:grid-cols-4      /* Wide: 4 columns */
    p-4 sm:p-6 lg:p-8   /* Scaling padding */
  ">
    {/* Products */}
  </div>
);

// Semantic HTML: Structure first, styling second
const Card = ({ title, description, image }) => (
  <article className="rounded-lg border border-gray-200 overflow-hidden">
    <img
      src={image}
      alt={`${title} preview`}
      className="w-full h-48 object-cover"
    />
    <div className="p-4">
      <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
      <p className="text-sm text-gray-600 mt-2">{description}</p>
    </div>
  </article>
);
```

### Accessibility Audit Checklist

Run this before shipping any component:

1. **Keyboard Navigation**: Tab through entire interface. All interactive elements reachable?
2. **Color Contrast**: Text passes WCAG AA (4.5:1 normal, 3:1 large). Use WebAIM contrast checker.
3. **ARIA Labels**: Form inputs have `<label>`, icons have `aria-label`, buttons have descriptive text.
4. **Focus Indicators**: `focus:ring-2` visible on all interactive elements.
5. **Semantic HTML**: Use `<button>` not `<div onclick>`. Use `<nav>`, `<main>`, `<aside>`.
6. **Screen Reader Test**: Enable VoiceOver (Mac) or NVDA (Windows). Headings make sense? Order logical?
7. **Motion**: No auto-playing animations. Respect `prefers-reduced-motion`.

```jsx
// Accessibility-first template
const AccessibleForm = () => {
  const [email, setEmail] = React.useState("");
  
  return (
    <form onSubmit={(e) => e.preventDefault()} className="space-y-4">
      <div>
        <label htmlFor="email" className="block text-sm font-medium">
          Email Address
        </label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          aria-describedby="email-hint"
          className="
            mt-1 w-full px-3 py-2 border border-gray-300 rounded-md
            focus:outline-none focus:ring-2 focus:ring-blue-500
          "
          required
        />
        <p id="email-hint" className="text-xs text-gray-500 mt-1">
          We'll never share your email.
        </p>
      </div>
      <button
        type="submit"
        className="
          w-full px-4 py-2 bg-blue-600 text-white rounded-md
          hover:bg-blue-700 focus:ring-2 focus:ring-blue-300
          disabled:opacity-50 disabled:cursor-not-allowed
        "
      >
        Subscribe
      </button>
    </form>
  );
};
```

---

## Section 2: Technical Content Strategy

### Why Documentation is a Product Feature

**Why:** If users can't understand how to use your product, it doesn't matter how well-built it is. Documentation is where technical excellence becomes user success.

### The Documentation Pyramid

Every project needs:

1. **Getting Started (5 min)** — One working example, zero prerequisites
2. **Core Concepts (15 min)** — What problems does this solve? When should I use it?
3. **API Reference** — Exhaustive, searchable, with examples
4. **Troubleshooting** — Common errors with solutions

```markdown
# Authentication Module

## Getting Started (5 minutes)

```bash
npm install @company/auth
```

```jsx
import { useAuth } from "@company/auth";

export default function Profile() {
  const { user, logout } = useAuth();
  
  return (
    <div>
      <h1>Welcome, {user.name}</h1>
      <button onClick={logout}>Sign Out</button>
    </div>
  );
}
```

That's it. You now have user authentication.

## Core Concepts

**User Sessions** — When `useAuth()` initializes, it checks if a valid token exists in localStorage. If yes, user is auto-logged in.

**JWT Expiration** — Tokens expire after 24 hours. The hook automatically refreshes them silently (zero user friction).

**Logout Behavior** — Clears localStorage, invalidates token server-side, redirects to `/login`.

## API Reference

...detailed props, return values, etc.

## Troubleshooting

**Q: User stays logged in after logging out?**
A: Check that your logout handler calls both `removeToken()` and redirects. [Example code].
```

**Why this structure:**
- Impatient developers get working code in 5 minutes
- Curious developers understand the "why"
- Reference section is there when they need details
- Troubleshooting prevents frustration

### Technical SEO Foundations

**Why:** Search engines crawl code as much as content. Canonical URLs, robots.txt, structured data, and sitemaps determine visibility.

**Canonical URLs** — Set `<link rel="canonical" href="https://example.com/article">` on every page to prevent duplicate content penalties. Required for multi-domain setups.

**robots.txt** — Control what bots crawl. Disallow private pages: `Disallow: /admin/`. Allow search indexing: `Allow: /`.

**sitemap.xml** — List all pages for faster discovery. Auto-generate with tools (Next.js plugins, static site generators). Submit to Google Search Console.

**Structured Data (JSON-LD)** — Markup pages with schema.org vocabulary. Helps Google understand your content type (article, product, recipe, etc.). Example: `<script type="application/ld+json">{"@type": "Article", "headline": "..."}</script>` appears in rich results (snippets, carousels).

### SEO-Optimized Technical Writing

**Why:** Good documentation ranks on Google, bringing organic users. Every page should target a specific search intent.

```markdown
# How to Handle File Uploads in React (Best Practices 2025)

## Search Intent: "How do I upload files in React?"

Users want: Working code + common pitfalls + best practices

## The Problem (Why File Uploads Are Hard)

- Browser file APIs are low-level
- Validation logic scatters across components
- Server integration varies by backend
- Error states are often forgotten

## The Solution (4-Step Pattern)

**Step 1: Validate on Client**
**Step 2: Upload with Progress Feedback**
**Step 3: Handle Errors Gracefully**
**Step 4: Integrate with Backend**

[Each step: problem → code → explanation]

## Common Mistakes (Addresses "Why does my upload keep failing?")

1. Sending FormData with wrong headers ← Most common
2. Forgetting CORS configuration
3. No timeout handling for large files
4. Silent failures (no error UI)

## Performance Tips (Retention: readers stay longer = Google ranks higher)

- Chunk large files (avoid timeouts)
- Show upload progress (psychological relief)
- Cancel uploads in-flight (user experience)
```

**Why this format:**
- Targets actual Google searches ("how to...")
- Answers user's implicit questions (why is this hard?)
- Common mistakes prevent support tickets
- Performance tips reduce bounce rate

### Email & Documentation Automation

**Why:** Repetitive writing (weekly digests, templated responses, status updates) should be systematic, not manual.

```markdown
# Email Template: Weekly Status Digest

Template variables: {week_start}, {week_end}, {milestone_status}, {blockers}, {upcoming}

Subject: Weekly Update — {week_start} to {week_end}

Hi {recipient_name},

This week we shipped:
- {achievement_1}
- {achievement_2}
- {achievement_3}

Milestones on track: {milestone_status}

Current blockers:
{blockers}

Next week's focus:
{upcoming}

Reply if you have questions.
Best,
{sender_name}

---

WHY THIS WORKS:
- Variables ensure consistent info
- Emoji-free, professional tone
- Scannable (bullets, headers)
- Brief (no one reads walls of text)
```

### README Best Practices

Every project README should answer:

```markdown
# Project Name

[One-sentence problem statement]

## What It Does

[Three bullet points: main capabilities]

## Installation

```bash
npm install package
```

## Quick Example

```javascript
// Simplest possible working code
const result = library.solve(problem);
```

## Documentation

[Link to full docs]

## Contributing

[Link to contribution guide]

## License

MIT
```

**Why this template:**
- Answers "Should I use this?" in seconds
- No jargon, no theory
- Installation is copy-paste
- Example works immediately
- Links prevent docs duplication

### Runbooks & Playbooks

**Why:** Operational procedures should be structured, repeatable documents—not tribal knowledge. Runbooks prevent firefighting chaos during incidents.

**Structure**: Title → Prerequisites → Step-by-step procedure → Expected outcomes → Rollback steps. Example: "Database Backup Runbook" includes prechecks (disk space available?), backup command, verification, and rollback (restore from snapshot if corruption detected).

**Playbooks** extend runbooks with decision trees for common scenarios ("Customer reports slow dashboard" → Check query logs → Index missing? → Run index script → Verify improvement).

Store in version control alongside code. Link to runbooks in monitoring alerts.

### Architecture Decision Records (ADRs)

**Why:** Architectural choices should be documented with reasoning. Future maintainers understand *why* you chose React over Vue or PostgreSQL over MongoDB.

**Format**: Status (Proposed/Accepted/Superseded) → Context (problem statement) → Decision (what we chose and why) → Consequences (tradeoffs, maintenance burden).

**Example**: "ADR-001: Use Supabase for Authentication. Context: We needed fast auth setup. Decision: Supabase's JWT + RLS reduced custom auth code by 80%. Consequences: Vendor lock-in (mitigated by open-source Postgrest)."

Store ADRs in `docs/adr/` with numbered filenames. Link to related ADRs. Update status if superseded.

### Changelog Management

**Why:** Users need to understand what changed, not just see version bumps. Keep a Changelog format standardizes this.

**Format**: For each release, document Added (new features), Changed (behavior changes), Deprecated (sunset warnings), Removed (breaking changes), Fixed (bugs), Security (vulnerability patches).

```markdown
## [2.1.0] — 2025-04-01

### Added
- New `useOptimisticUpdate` hook for instant UI feedback

### Changed
- `Button` component now requires `aria-label` prop

### Deprecated
- `useAuth()` hook (use `useUser()` instead)

### Fixed
- Memory leak in notification stack

### Security
- Updated dependencies to patch CVE-2025-xxxx
```

Pair with **Conventional Commits** for automation: `feat: new hook`, `fix: memory leak`, `BREAKING CHANGE: removed hook` automatically generate changelog entries.

### Content Documentation Platforms

**Why:** Markdown documentation needs a home. Modern platforms render beautifully, support versioning, and integrate with your workflow.

**MkDocs** — Python-based, Material theme included, lightweight, excellent for API docs and user guides. Best if your team knows Python.

**Docusaurus** — React-based, search included, sidebar auto-generation, versioning built-in. Best for larger projects needing advanced features.

**Astro Starlight** — Modern static site builder, Markdown-first, great DX. Best for design-forward documentation sites.

**GitBook** — SaaS solution, no build step required, collaborative editing, publishing to custom domains. Best for non-technical writers.

**Style Enforcement**: Use **Vale** (linter for writing style) and **markdownlint** (Markdown syntax) to prevent typos and inconsistent formatting in CI/CD.

### Google Workspace MCP Integration

**Why:** Automate communication workflows directly from code. Gmail, Calendar, and Sheets MCPs enable draft-before-sending email chains, schedule conflict detection, and data-driven documentation.

**Gmail Tools**: `list_messages`, `get_thread`, `create_draft`, `send_message`, `search_emails` — Pull context from email history, maintain tone, generate drafts for review before sending.

**Calendar Tools**: `list_events`, `create_event`, `check_availability` — Detect scheduling conflicts, enforce 15-minute buffer blocks between meetings, suggest optimal times for team standups.

**Sheets Tools**: `read_spreadsheet`, `update_values`, `append_row` — Populate docs from live data, generate reports, sync product roadmaps to shared sheets.

**Communication Workflow**: Context Retrieval (pull user's email history + tone patterns) → Tone Matching (adapt draft voice to user's actual writing) → Drafting (generate message) → Draft-Before-Sending (require review, never auto-send). Buffer rules: enforce 15-minute transition blocks between back-to-back meetings to prevent meeting fatigue.

---

## Section 3: Design System Enforcer

### Token Validation Pipeline

**Why:** Color values, spacing, fonts should come from a finite set. Arbitrary values create visual chaos.

```javascript
// design-tokens.js - Single source of truth
export const TOKENS = {
  colors: {
    brand: "#2563EB",
    success: "#10B981",
    error: "#EF4444",
    warning: "#F59E0B",
    neutral: {
      50: "#F9FAFB",
      100: "#F3F4F6",
      500: "#6B7280",
      900: "#111827",
    },
  },
  spacing: [4, 8, 12, 16, 24, 32, 48, 64],
  typography: {
    fontFamily: "Inter, system-ui, sans-serif",
    sizes: [12, 14, 16, 18, 20, 24, 32],
    weights: [400, 500, 600, 700],
  },
  borderRadius: [4, 6, 8, 12],
};

// validate-tokens.js - Audit components
export function validateTokenUsage(cssString) {
  const invalidPatterns = [
    /bg-\[#[0-9A-F]{6}\]/, // Arbitrary colors
    /px-\[\d+px\]/, // Arbitrary spacing
    /text-\[\d+px\]/, // Arbitrary font sizes
  ];
  
  const violations = [];
  invalidPatterns.forEach((pattern) => {
    const matches = cssString.match(pattern);
    if (matches) {
      violations.push({
        pattern: matches[0],
        fix: "Use design token instead (see TOKENS.js)",
      });
    }
  });
  
  return violations.length === 0
    ? { valid: true }
    : { valid: false, violations };
}
```

**Why validation matters:**
- Catches arbitrary colors before they ship
- Forces design decisions through design team
- Makes brand refresh trivial (update one file)
- Accessibility audit becomes easier (finite color palette)

### Design Audit Workflow

**Why:** Audits evaluate existing UIs against design system standards, identifying gaps and inconsistencies before they compound.

**Process**: (1) Screenshot existing pages. (2) Compare against design tokens (colors, spacing, typography match?). (3) Document violations with before/after mockups. (4) Create tickets for remediation. (5) Report impact: "14 pages use non-standard colors" (quantify the problem). (6) Track fixes and re-audit quarterly.

Tools: Figma plugins (design token comparators), screenshot overlays, automated contrast checkers. Report format: executive summary (metrics) + detailed findings (by component) + remediation roadmap (phases).

### Component Consistency Checklist

Before marking a component "done":

```markdown
# Component Review Checklist

## Visual Consistency
- [ ] Colors from TOKENS only (no hex values)
- [ ] Spacing uses margin/padding scale (4, 8, 12, 16...)
- [ ] Typography uses defined sizes (12, 14, 16, 18...)
- [ ] Border radius consistent (4, 6, 8, 12 only)
- [ ] Shadows match design system (sm, md, lg)

## Interaction States
- [ ] Hover state (background/text change, not just opacity)
- [ ] Active state (clear, different from hover)
- [ ] Disabled state (opacity + cursor-not-allowed)
- [ ] Focus state (ring-2 with correct color)

## Accessibility
- [ ] All interactive elements keyboard-accessible
- [ ] Color contrast passes WCAG AA (4.5:1)
- [ ] ARIA labels where needed
- [ ] Semantic HTML (button vs div, etc.)

## Responsive
- [ ] Mobile layout correct (1 column, full width)
- [ ] Tablet layout correct (2 columns)
- [ ] Desktop layout correct (3+ columns)
- [ ] Touch targets ≥ 44px (mobile)

## Code Quality
- [ ] Props documented with JSDoc
- [ ] No console.logs
- [ ] No hardcoded values (use tokens)
- [ ] Storybook story included
```

---

## Section 4: Brand Voice Engine

### Style Guide Enforcement

**Why:** "We sound professional but approachable" is too vague. Document actual patterns so writers can replicate voice.

```markdown
# Brand Voice Guide

## Our Voice: Clear. Confident. Human.

### Tone Hierarchy

**Confident** (Features, solutions) — "React Native lets you build iOS and Android apps with one codebase."

**Reassuring** (Troubleshooting, help) — "Don't worry, this error usually means... Here's how to fix it."

**Conversational** (Blog, examples) — "We kept asking ourselves: why is this so hard?"

### Writing Patterns

**Avoid**
- "Utilize" (use instead)
- "Please note that" (just state fact)
- "The system will automatically" (be specific: "We refresh your token every 24 hours")
- Passive voice ("errors are handled" → "We catch errors for you")

**Use**
- "You" — address reader directly
- "We" — show we're behind the product
- Specific examples — "This takes ~500ms" beats "This is performant"
- Short sentences — Break complex ideas into steps

### Email Template

Subject: [Action Required] vs [Update] vs [Reminder] — Be specific

Body:
1. One-sentence summary (reader decides if they read further)
2. Context (why this matters)
3. What to do (step 1, step 2, step 3)
4. Expected outcome
5. Link to help article

❌ "Please be aware that we have made updates to our system that may affect your workflow."

✅ "Your API keys now expire after 90 days. Here's how to rotate them (2-minute process)."
```

### Tone Consistency Across Channels

| Channel | Tone | Example |
|---------|------|---------|
| **Error Message** | Helpful, specific | "Missing API key. [Add key](#docs/api-keys)" |
| **Loading State** | Reassuring | "Generating report..." (avoid generic spinners) |
| **Success** | Celebratory, brief | "Launched! View live." |
| **Blog** | Conversational | "We shipped X because Y. Here's what we learned." |
| **Documentation** | Clear, instructional | "Run npm install, then check your API key." |

**Why consistency matters:**
- Users trust brands that sound like themselves
- Consistent voice = recognizable = professional
- New writers follow patterns, not guesses

---

## Section 5: Landing Page Generator

### Conversion-Optimized Patterns

**Why:** Not all landing pages convert. High-conversion pages follow psychological patterns: clarity, social proof, urgency, risk reversal.

```jsx
// Conversion-optimized landing page structure
const LandingPage = () => (
  <div className="bg-white">
    {/* HERO: Big Promise + CTA */}
    <section className="px-4 py-20 sm:py-32 text-center">
      <h1 className="text-4xl sm:text-6xl font-bold text-gray-900 max-w-3xl mx-auto">
        Ship 10x Faster with Automated Testing
      </h1>
      <p className="text-xl text-gray-600 mt-6 max-w-2xl mx-auto">
        Stop manual QA. Our AI catches bugs before users see them.
      </p>
      <button className="mt-8 px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
        Start Free Trial (No Credit Card)
      </button>
    </section>

    {/* SOCIAL PROOF: Numbers + Logos */}
    <section className="bg-gray-50 px-4 py-12">
      <div className="grid grid-cols-3 gap-8 max-w-4xl mx-auto text-center">
        <div>
          <div className="text-3xl font-bold text-blue-600">50K+</div>
          <p className="text-gray-600">Engineers trust us</p>
        </div>
        <div>
          <div className="text-3xl font-bold text-blue-600">99.9%</div>
          <p className="text-gray-600">Bug catch rate</p>
        </div>
        <div>
          <div className="text-3xl font-bold text-blue-600">$2M</div>
          <p className="text-gray-600">Saved in QA costs</p>
        </div>
      </div>
      <div className="flex justify-center gap-4 mt-8 flex-wrap">
        <img src="stripe-logo.svg" alt="Stripe" className="h-6" />
        <img src="figma-logo.svg" alt="Figma" className="h-6" />
        {/* Include 3-4 recognizable logos */}
      </div>
    </section>

    {/* FEATURES: Problem + Solution */}
    <section className="px-4 py-20 max-w-4xl mx-auto">
      <h2 className="text-3xl font-bold text-center mb-12">Three Problems We Solve</h2>
      {[
        {
          problem: "Your QA team is overwhelmed",
          solution: "We handle 90% of test cases automatically",
          cta: "See how →",
        },
        {
          problem: "Bugs slip through to production",
          solution: "AI-powered testing catches edge cases humans miss",
          cta: "Learn more →",
        },
        {
          problem: "Testing slows down shipping",
          solution: "Tests run in parallel. Deploy 10x faster",
          cta: "Benchmark →",
        },
      ].map((item, idx) => (
        <div key={idx} className="border-l-4 border-blue-600 pl-6 mb-8">
          <h3 className="font-semibold text-lg text-gray-900">{item.problem}</h3>
          <p className="text-gray-600 mt-2">{item.solution}</p>
          <a href="#" className="text-blue-600 hover:underline text-sm">
            {item.cta}
          </a>
        </div>
      ))}
    </section>

    {/* CTA + Risk Reversal */}
    <section className="bg-blue-600 text-white px-4 py-16 text-center">
      <h2 className="text-3xl font-bold">Ready to 10x Your Testing?</h2>
      <button className="mt-6 px-8 py-3 bg-white text-blue-600 rounded-lg hover:bg-gray-100 font-semibold">
        Start Free Trial
      </button>
      <p className="text-blue-100 text-sm mt-4">
        14-day free trial. No credit card. No commitment.
      </p>
    </section>
  </div>
);
```

**Why this pattern converts:**
- **Hero**: Makes product promise unmissable
- **Numbers**: "50K engineers" beats "trusted by many"
- **Logos**: Social proof from recognizable brands
- **Problem-Solution**: Frames benefit, not feature
- **CTA placement**: End of value prop, not intro
- **Risk reversal**: "No credit card" removes friction

### Landing Page Audit Questions

Before publishing, ask:

1. **Above the fold** — Can visitor understand value in 3 seconds without scrolling?
2. **CTA clarity** — What happens when I click the button? (Clear: "Start Free Trial" vs Vague: "Get Started")
3. **Friction points** — How many clicks to convert? (Optimal: 2-3, not 10)
4. **Mobile experience** — Is it usable on mobile? (60% of visitors are mobile)
5. **Objection handling** — Do you address "It's too expensive" or "Does it work for my use case?"
6. **Proof** — Are numbers real? Do logos include actual users?

---

## Section 6: Component Library Manager (Storybook)

### Story Documentation Pattern

**Why:** Storybook is where developers learn how to use your components. Bad stories = developers either avoid components or use them wrong.

```jsx
// Button.stories.jsx
import Button from "./Button";

export default {
  title: "Components/Button",
  component: Button,
  parameters: {
    docs: {
      description: {
        component:
          "Accessible button component supporting multiple variants and sizes. Uses Radix primitives for keyboard navigation and ARIA attributes.",
      },
    },
  },
  argTypes: {
    variant: {
      description: "Visual style of the button",
      control: { type: "select" },
      options: ["primary", "secondary", "ghost", "danger"],
    },
    size: {
      description: "Button size: sm (28px), md (36px), lg (44px)",
      control: { type: "select" },
      options: ["sm", "md", "lg"],
    },
    disabled: {
      description: "Disables interaction and visual feedback",
      control: { type: "boolean" },
    },
    onClick: {
      description: "Fired when button is clicked",
      action: "clicked",
    },
  },
};

// PRIMARY STORY - How most developers use this
export const Primary = {
  args: {
    variant: "primary",
    size: "md",
    children: "Save Changes",
  },
};

// SECONDARY STORY - Alternative style
export const Secondary = {
  args: {
    variant: "secondary",
    children: "Cancel",
  },
};

// EDGE CASE STORIES - Common mistakes
export const Disabled = {
  args: {
    variant: "primary",
    disabled: true,
    children: "Processing...",
  },
};

export const LongLabel = {
  args: {
    variant: "primary",
    children: "This is a very long button label to test text wrapping",
  },
};

// USAGE STORY - Shows real-world context
export const InForm = {
  render: () => (
    <form className="space-y-4">
      <input type="text" placeholder="Email" className="w-full px-3 py-2 border rounded" />
      <Button variant="primary">Subscribe</Button>
    </form>
  ),
};
```

**Why this structure:**
- Primary story shows the happy path
- Variants show all options
- Edge cases prevent "Why doesn't this work?" issues
- Usage story shows real context
- argTypes enable interactive documentation

---

## Usage Checklist

When starting any frontend project:

- [ ] **Design System**: All tokens in one file (colors, spacing, typography)
- [ ] **Component Library**: Core components built to checklist (a11y, responsive, variants)
- [ ] **Storybook**: Every component has 3+ stories
- [ ] **Documentation**: README answers "what" + "why", not just "how"
- [ ] **Brand Voice**: Style guide documented with real examples
- [ ] **Accessibility**: Audit checklist passed before merge
- [ ] **Mobile First**: Tested on 375px viewport
- [ ] **Email Templates**: Standardized for consistency

---

## Why This Matters

Frontend development isn't just code. It's also:
- User understanding (documentation)
- Team alignment (design tokens, brand voice)
- User trust (accessibility, consistency)
- Maintainability (patterns, not exceptions)

This consolidated skill ensures every layer—from pixels to prose—reflects intentional, user-centered design thinking.
