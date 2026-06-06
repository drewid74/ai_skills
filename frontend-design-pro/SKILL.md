---
name: frontend-design-pro
description: "Use this when: my UI looks amateurish, make this look better, fix the layout alignment, my design feels inconsistent, add dark mode, my buttons aren't keyboard accessible, build a landing page, my mobile layout is broken, enforce a design system, my animations are too aggressive, clean up my component styles, my UI has no visual hierarchy, add proper focus indicators, Tailwind, Shadcn, React, Next.js, accessibility audit, design tokens, WCAG, responsive, component architecture, Storybook"
---

# Frontend Design & UX Enforcement

## Identity

Transform functional-but-average UIs into polished, consistent, accessible interfaces. Every design decision is intentional. Never ship hardcoded hex values, broken keyboard navigation, or animations that ignore `prefers-reduced-motion`. Design audits produce quantified findings ("14 pages use non-standard colors"), not qualitative feedback.

## Stack Defaults

| Layer | Choice | Notes |
|-------|--------|-------|
| Framework | Next.js 15 + App Router | Server Components by default |
| Styling | Tailwind v4 | `@theme` CSS-variable engine |
| Components | Shadcn/UI + Radix Primitives | Accessible base, fully ownable |
| Animation | Framer Motion | State-change clarification only |
| Icons | Lucide React | Consistent stroke, tree-shakeable |
| Typography | 1.250 modular scale | Clear hierarchy, no arbitrary overrides |
| Spacing | 8px grid (Tailwind steps 2/4/6/8) | Visual rhythm |
| Docs | Storybook | 3+ stories per component |

## Decision Framework

```
IF two elements compete for attention:
  → Increase size/weight contrast, not add borders

IF whitespace feels off:
  → Verify 8px grid alignment before touching other properties

IF new component needed:
  → semantic HTML → ARIA → design tokens → keyboard test → Storybook → ship

IF existing component needs polish:
  → Run "Consistency Report" (audit values) before editing classes

IF layout broken on mobile:
  → flex-col base, md:flex-row override, 44px touch targets

IF new color needed:
  → CSS variable in globals.css @theme, NEVER inline hex

IF dark mode:
  → [data-theme="dark"] variable overrides, not scattered dark: utilities

IF adding animation:
  → Only if communicating state change, loading, or guiding attention
  → Always wrap in @media (prefers-reduced-motion: no-preference)

IF Next.js component:
  → Default: Server Component (no 'use client')
  → 'use client' only for: useState, useEffect, event listeners
  → Never put data fetching in client components
```

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| Hardcode `#hex` inline | Theming breaks, audit fails | Tailwind token → CSS variable |
| `<div onClick>` | Keyboard-inaccessible | `<button>` with explicit role |
| Remove focus `outline` | Keyboard users lose navigation | `ring-2 ring-offset-2 ring-brand-primary` |
| Arbitrary `[margin:13px]` | Breaks 8px grid | Nearest Tailwind step (`m-3` = 12px) |
| Animation without motion guard | Vestibular/seizure risk | Wrap in `prefers-reduced-motion` media query |
| `data fetching in 'use client'` | Forces client bundle | Move fetch to Server Component |
| "Colors seem inconsistent" | Qualitative only | Audit with count: "14 pages, 6 non-token colors" |

## Quality Gates

- [ ] No raw hex values — all colors reference design tokens
- [ ] All interactive elements keyboard-reachable, visible focus ring
- [ ] Contrast ≥ 4.5:1 text, ≥ 3:1 large text and UI icons
- [ ] Mobile layout verified at 375px and 768px viewports
- [ ] `prefers-reduced-motion` respected in every animation
- [ ] Audit produces metrics (N violations) before any refactor begins
- [ ] Every component has Storybook stories (3+ minimum)

→ See `web-performance-a11y` for Core Web Vitals and CI accessibility testing

---

## Design Tokens (globals.css)

```css
/* globals.css */
@theme {
  --color-brand:       #4f46e5;
  --color-brand-hover: #4338ca;
  --color-brand-fg:    #ffffff;
  --color-surface-1:   #ffffff;
  --color-surface-2:   #f9fafb;
  --color-surface-3:   #f3f4f6;
  --color-text:        #111827;
  --color-text-muted:  #6b7280;
  --color-border:      #e5e7eb;
  --color-error:       #ef4444;
  --color-error-hover: #dc2626;
  --color-success:     #22c55e;
  --color-warning:     #f59e0b;
}

[data-theme="dark"] {
  --color-surface-1:   #111827;
  --color-surface-2:   #1f2937;
  --color-surface-3:   #374151;
  --color-text:        #f9fafb;
  --color-text-muted:  #9ca3af;
  --color-border:      #374151;
}
```

## Accessible Button Component

```tsx
// components/ui/action-button.tsx
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cn } from "@/lib/utils"

interface ActionButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger"
  asChild?: boolean
}

export const ActionButton = React.forwardRef<HTMLButtonElement, ActionButtonProps>(
  ({ variant = "primary", asChild = false, className, children, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        ref={ref}
        className={cn(
          // Base: 8px grid, 44px min touch target, visible focus ring
          "inline-flex items-center justify-center min-h-[44px] px-4 py-2 rounded-md",
          "text-sm font-medium transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
          "disabled:pointer-events-none disabled:opacity-50",
          // Tokens only — no arbitrary hex
          variant === "primary" &&
            "bg-[var(--color-brand)] text-[var(--color-brand-fg)] hover:bg-[var(--color-brand-hover)] focus-visible:ring-[var(--color-brand)]",
          variant === "secondary" &&
            "bg-[var(--color-surface-2)] text-[var(--color-text)] hover:bg-[var(--color-surface-3)] focus-visible:ring-[var(--color-border)]",
          variant === "danger" &&
            "bg-[var(--color-error)] text-white hover:bg-[var(--color-error-hover)] focus-visible:ring-[var(--color-error)]",
          className
        )}
        {...props}
      >
        {children}
      </Comp>
    )
  }
)
ActionButton.displayName = "ActionButton"
```

## Motion-Safe Animation

```tsx
// Framer Motion with reduced-motion guard
import { motion, useReducedMotion } from "framer-motion"

function FadeIn({ children }: { children: React.ReactNode }) {
  const prefersReduced = useReducedMotion()
  return (
    <motion.div
      initial={{ opacity: prefersReduced ? 1 : 0, y: prefersReduced ? 0 : 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: prefersReduced ? 0 : 0.2 }}
    >
      {children}
    </motion.div>
  )
}

// CSS: always guard animations
@media (prefers-reduced-motion: no-preference) {
  .animated-element {
    transition: transform 200ms ease;
  }
}
```

## Design Audit Output Format

```
## Design Audit — /dashboard (2026-06-06)

WCAG AA Violations: 7 found

CRITICAL (block merge):
  [A11Y-01] 3 <div onClick> elements — replace with <button>
  [A11Y-02] Contrast ratio 2.8:1 on muted text (#6b7280 on #f9fafb) — min 4.5:1

HIGH:
  [A11Y-03] 5 icon buttons missing aria-label
  [A11Y-04] Form input #email has no associated <label>

MEDIUM:
  [A11Y-05] Focus indicator missing on nav links (no ring class)

Token Violations: 4 found
  Line 42: color: #3b82f6 → use var(--color-brand)
  Line 67: padding: 13px → use p-3 (12px) or p-4 (16px)
  Line 89: font-size: 11px → use text-xs (12px)
  Line 104: border-radius: 3px → use rounded-sm
```

## Storybook Story Template

```tsx
// components/ui/action-button.stories.tsx
import type { Meta, StoryObj } from "@storybook/react"
import { ActionButton } from "./action-button"

const meta: Meta<typeof ActionButton> = {
  title: "UI/ActionButton",
  component: ActionButton,
  argTypes: {
    variant: { control: "select", options: ["primary", "secondary", "danger"] },
    disabled: { control: "boolean" },
  },
}
export default meta
type Story = StoryObj<typeof ActionButton>

export const Primary: Story = {
  args: { children: "Save Changes", variant: "primary" },
}
export const Danger: Story = {
  args: { children: "Delete Account", variant: "danger" },
}
export const Disabled: Story = {
  args: { children: "Submit", variant: "primary", disabled: true },
}
export const LongLabel: Story = {
  args: { children: "Submit form with very long label text to test overflow", variant: "primary" },
}
```

## Typography Scale

```css
/* 1.250 modular scale */
.text-xs    { font-size: 0.64rem; }   /* 10.24px */
.text-sm    { font-size: 0.8rem; }    /* 12.8px  */
.text-base  { font-size: 1rem; }      /* 16px    */
.text-lg    { font-size: 1.25rem; }   /* 20px    */
.text-xl    { font-size: 1.563rem; }  /* 25px    */
.text-2xl   { font-size: 1.953rem; }  /* 31px    */
.text-4xl   { font-size: 3.052rem; }  /* 49px    */
```
