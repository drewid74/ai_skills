---
name: frontend-design-pro
description: "Use this skill for UI/UX development, frontend refactoring, design system enforcement, and accessibility audits. Triggers: 'CSS', 'Tailwind', 'React', 'component', 'styling', 'UI', 'UX', 'responsive', 'mobile-first', 'accessibility', 'ARIA', 'v0', 'Shadcn', 'Framer Motion', 'animation', 'layout', 'grid', 'flexbox', or requests to 'make it look better', 'fix the alignment', or 'build a landing page'."
---

# Frontend Design & UX Playbook

## Overview
Transform functional requirements into high-fidelity, high-utility interfaces using modern web standards. This skill enforces the "No-Average" rule to ensure professional, unique aesthetics.

## Available Design Tools
- **Frameworks**: Next.js 15+, Tailwind v4 (CSS variables engine)
- **Component Libraries**: Shadcn/UI, Radix Primitives, Magic UI
- **Logic**: Framer Motion for micro-interactions, Lucide for iconography

## Design Philosophy: The "No-Average" Rule
1. **Typography**: Avoid system defaults. Use high-contrast scale ($1.250$ ratio).
2. **Color**: Use functional palettes (Success/Warning/Error) + 1 unique brand accent.
3. **Hierarchy**: Use whitespace (8px grid) over borders to separate concerns.

## Standard Component Workflow
1. **Scaffolding**: Generate clean, semantic HTML5/JSX.
2. **Logic Check**: Ensure client/server component separation in Next.js.
3. **Styling**: Apply Tailwind classes; use `@theme` blocks for reusable tokens.
4. **Accessibility (A11y)**: Add ARIA labels, ensure 4.5:1 contrast, and keyboard navigability.

## Compound Operations
- **Design Audit**: Review an existing file and provide a "Consistency Report" before refactoring.
- **Theme Injection**: Automatically update `globals.css` with a new color variable set.
- **Mobile-First Refactor**: Restructure a desktop-only component into a responsive, touch-friendly version.

## Output Format
- Provide code in clean blocks.
- List specific UI improvements made (e.g., "Increased tracking for better readability").
- Include a "Preview Description" of how the UI should behave.