# Canonical Skill Template

This document defines the exact section ordering skills must follow for prompt-cache optimization.

## Shared rules

- One skill file = one H1.
- Keep `description` action-oriented and router-friendly.
- Preserve prompt blocks verbatim.
- Do not add duplicate H1s.
- For derived trigger text, prefer user-problem phrases over skill names.

## Skill type: `promptkit`

### Canonical order

1. Frontmatter with `name`, `title`, `description`, `type: "promptkit"`, `label: "Prompt Kit"`, `project`
2. Single H1
3. Short intro paragraph
4. `## How to use this kit`
5. `---`
6. Repeated prompt blocks in order

### Required shape

```md
---
name: {slug}
title: "{original title value, unchanged}"
description: "Use this when: {comma-separated action/problem phrases derived from title and intro — at least 5 phrases}"
type: "promptkit"
label: "Prompt Kit"
project: "{original project value, unchanged}"
---

# {Single H1 — pick the most descriptive one if there are duplicates, remove the other}

{Original 1-3 line summary paragraph}

## When to use

{2-5 bullet points summarizing the trigger scenarios — derived from the existing intro text. This section FRONT-LOADS the routing triggers for the LLM.}

## How to use this kit

{Original "How to use" content verbatim — if present. If not present (organize-project-files), this section is OMITTED entirely.}

---

## Prompt 1: {Name}
[... rest of prompts in order, byte-identical content ...]
```

### Worked example

Use `agent-product-analytics` as the model: title and project stay unchanged, the intro stays short, `## How to use this kit` comes before the first prompt, then prompt blocks continue in source order.

## Skill type: `guide`

### Canonical order

1. Frontmatter with `name`, `title`, `description`, `type: "guide"`, `label: "Guide"`, `project`
2. Single H1
3. Short summary paragraph
4. `## When to use`
5. `## The Pain Map`
6. `## The Primitive Model`
7. Tool sections in original order

### Required shape

```md
---
name: {slug}
title: "{original title}"
description: "Use this when: {phrases}"
type: "guide"
label: "Guide"
project: "{original project}"
---

# {Single H1}

{1-3 line summary}

## When to use

{Bullets summarizing trigger scenarios}

{Original guide sections in original order: "The Pain Map", "The Primitive Model", then each tool section with its ## Job, ## Use When, ## Safe To Use Checklist subsections}
```

### Worked example

Use `ai-office-files-guide` as the model: one H1, then `## The Pain Map`, then `## The Primitive Model`, then the workbook/deck prompt kit sections in order.

## Skill type: `token-burn`

### Canonical order

1. Frontmatter with `name` and `description` only
2. Single H1
3. Brief intro line
4. `## Workflow`
5. `## Source Rules`
6. `## Done Means`

### Required shape

```md
---
name: token-burn-all-sources
description: Build a token-burn dashboard that tracks Codex, Claude Code, Claude chat, and ChatGPT on the same axes, with exact and estimated usage kept visibly separate.
---

# Token Burn Dashboard For All Sources

Use this skill when the user wants one dashboard across Codex, Claude, and ChatGPT.

## Workflow

...
```

### Worked example

Use `token-burn-all-sources` as-is: its frontmatter is already minimal, and the body already follows the optimal section order.

## Derived description text for the 7 skills

| Skill | Type | Description |
|---|---|---|
| agent-product-analytics | promptkit | Use this when: instrument agent analytics, my agent has no event tracking, generate agent instrumentation code, turn agent corrections into eval cases, read completion vs acceptance numbers, agent product analytics blind spots, four-quadrant framework for agent workflows, wire agent_run_id tracking |
| ai-office-files-guide | guide | Use this when: stop asking AI to make a deck, AI-generated Office files can't be trusted, Excel formula risk, PowerPoint evidence gaps, workbook doctor, deck architecture review, Excel-to-deck evidence mapping, pretty-but-wrong AI output, verify AI-created spreadsheet, trust layer for AI documents |
| ai-office-files-promptkit | promptkit | Use this when: build source packet for AI Office work, inspect Excel before AI uses it, turn analysis into slide story, tie slide claims to workbook evidence, pre-share verification for deck, AI PowerPoint workflow, Office file truth setup, workbook repair prompts |
| organize-project-files | promptkit | Use this when: organize project files before writing, build a project room, source inventory from folder, grounded draft instead of guessed draft, messy folder of project materials, duplicate files audit, missing context list, project room refresh |
| public-ai-work-apprenticeship | promptkit | Use this when: make invisible AI work visible, share AI work with my team, public AI channel post, format AI session transcript, sensitivity boundary for AI sharing, senior leader AI modeling, apprenticeship from AI work, private vs public AI work |
| opus-benchmark-routing | promptkit | Use this when: route task to right model, Opus 4.8 vs Codex vs GPT-5, build real eval set, verification plan for agentic work, map AI spend to accepted outputs, model selection not leaderboard, task router for model choice, benchmark-based routing |
| token-burn-all-sources | token-burn | Build a token-burn dashboard that tracks Codex, Claude Code, Claude chat, and ChatGPT on the same axes, with exact and estimated usage kept visibly separate. |

## Notes

- Keep prompt blocks byte-identical when converting source skills.
- Do not invent extra trigger phrases.
- Do not change `type`, `label`, or `project` values in the examples.
