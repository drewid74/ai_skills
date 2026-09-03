---
name: skill-cache-optimizer
description: "Use this when: analyze a skill, optimize a skill, audit skill cache, reduce token usage in a skill, refactor a skill, modularize a skill, improve skill cache hit rate, find token waste, skill prompt audit, skill architecture review, score a skill, before/after skill optimization, skill efficiency report"
model: claude-sonnet-4.6
context-mode: required
---

# Skill Cache Optimizer

Analyze ANY skill folder (or single SKILL.md file) and produce:

1. **Quantitative scorecard** — token volume, cacheable %, repetition, modularization score
2. **Findings list** — concrete cache-blocking patterns with file:line citations
3. **Refactor plan** — prioritized changes with projected token savings
4. **Optional refactored markdown** — if explicitly requested

Optimization MUST preserve correctness, validation rigor, evidence integrity, and operational semantics.

---

# WHEN TO USE

Trigger this skill whenever the user asks to:
- analyze / optimize / audit / score a skill
- reduce token usage or improve cache hits for a prompt or skill
- modularize, refactor, or restructure a skill
- assess a skill's prompt architecture before/after changes
- compare two skills for efficiency

---

# INPUT CONTRACT

Accept ONE of:

| Input form | Example |
|---|---|
| Absolute folder path | `C:\Users\drewfairaizl\dev\ai_skills\hls-morning-brief` |
| Absolute file path to a SKILL.md | `C:\...\hls-morning-brief\SKILL.md` |
| Glob across the repo (multi-skill compare) | `C:\Users\drewfairaizl\dev\ai_skills\*` |

If the user names a skill without a path, resolve it against `~/dev/ai_skills/<name>/`.

---

# EXECUTION MODEL (TWO PHASES — DO NOT VIOLATE)

## PHASE A — DYNAMIC ANALYSIS (sandbox only)

ALL file reads, parsing, regex matching, repetition detection, and token
counting MUST execute inside `ctx_execute` against `scripts/analyze.js`.

This phase MUST return only:
- normalized JSON `AnalysisResult` (see `schemas/analysis_result.md`)
- compact markdown summary

NEVER return:
- raw SKILL.md contents
- raw payload excerpts longer than 200 chars
- file content dumps

## PHASE B — STATIC REPORT RENDERING

Consume the JSON from Phase A and render the assessment using the
deterministic template at `templates/assessment_report.md`.

No additional tool calls. No re-reading of source files. No new analysis.

---

# HOW TO INVOKE (REQUIRED PATTERN)

```javascript
// 1. Run the analyzer (Phase A)
ctx_execute(language: "javascript", code: `
  const { analyzeSkill } = require('C:/Users/drewfairaizl/dev/ai_skills/skill-cache-optimizer/scripts/analyze.js');
  const result = analyzeSkill({
    target: "<ABSOLUTE_PATH>",
    compareAgainst: null,           // optional: another skill path for delta
    includeRefactoredMarkdown: false // set true only when user asks
  });
  console.log(JSON.stringify(result, null, 2));
`)

// 2. Render the report (Phase B) using templates/assessment_report.md
```

The analyzer is fully self-contained — no npm dependencies, Node built-ins only, runs on Node and Bun.

---

# WHAT THE ANALYZER MEASURES

| Dimension | Metric | Cache impact |
|---|---|---|
| Volume | Total chars, est. tokens (chars/4), file count | Baseline |
| Cacheable prefix stability | % of body matching stable patterns | High |
| Dynamic contamination | Timestamps, `{{var}}` in body, run-specific text | Critical |
| Repetition | Duplicate paragraphs (normalized hash) | High |
| Inline payload risk | Code fences >100 lines, JSON blobs >20 lines, embedded registries | Critical |
| Modularization score | Sections >2KB matching externalizable patterns | High |
| Determinism | Numbered section order, table consistency, heading depth | Medium |
| Retrieval completeness | Pagination, dedup, reconciliation mentions for query patterns | Medium |
| Context-mode usage | Mentions of `ctx_execute` / `ctx_execute_file` vs large data ops | High |
| Word Copilot block | Externalized vs inline | Low |

See `analyzers/heuristics.md` for the full rule set and thresholds.

---

# SCORING

A composite **Cache Efficiency Score (CES)** from 0–100:

```text
CES = 0.30 * cacheable_prefix_pct
    + 0.20 * (100 - dynamic_contamination_pct)
    + 0.15 * modularization_score
    + 0.15 * (100 - inline_payload_risk)
    + 0.10 * determinism_score
    + 0.10 * (100 - repetition_pct)
```

Bands:
- **90–100** Excellent — production-ready
- **75–89** Good — minor refactor
- **60–74** Fair — meaningful rework recommended
- **<60** Poor — structural redesign needed

---

# OUTPUT STRUCTURE (FIXED)

Render in this exact order — see `templates/assessment_report.md`:

1. Scorecard (CES + sub-scores)
2. Volume & token estimate
3. Findings (sorted Critical → High → Medium → Low) with file:line
4. Modularization opportunities (proposed folder moves)
5. Refactor plan (prioritized, with projected token deltas)
6. Risks & preservation notes
7. Verification trail (files analyzed, rules applied, ambiguities)

---

# REFACTOR PLAN RULES

Each refactor item MUST include:
- **What** — concrete change (move section X to file Y, replace inline Z with reference)
- **Why** — finding ID it addresses
- **Projected savings** — token delta (estimate), with method labeled
- **Risk** — what could break (low / med / high)
- **Preservation** — what MUST remain identical (validation, output structure)

NEVER recommend a change that:
- removes a validation gate
- drops a reconciliation step
- hides uncertainty labels
- weakens a completeness guarantee
- shortens an `EXECUTION IS INVALID` clause

If a finding requires a tradeoff, flag it explicitly: `TRADEOFF: <accuracy> vs <tokens>`.

---

# TOKEN ESTIMATION CONVENTION

- Estimation: `chars / 4` (English-leaning approximation)
- Label all numbers as **estimated**, **modeled**, or **projected**
- NEVER claim measured telemetry unless the user provides it
- For multi-file skills, sum across files in the skill folder (excluding `backup_*`, `.bak`, `.tmp`, hidden files)

See `partials/token_estimation.md`.

---

# CONTEXT-MODE REQUIREMENTS

This skill is `context-mode: required`. Phase A MUST run in `ctx_execute`.
If a user invokes this skill without context-mode available, refuse with:

```text
This skill requires context-mode (ctx_execute) to avoid loading skill source into the conversation. Please enable context-mode or invoke the analyzer manually.
```

---

# PRESERVATION CONTRACT (HARD)

Every recommendation MUST preserve:
- correctness of business logic
- evidence integrity (no inferred data shortcuts)
- retrieval completeness guarantees (pagination, dedup, reconciliation)
- validation rigor (no gate removal)
- output structure that downstream consumers depend on
- explicit uncertainty labels

If a recommendation cannot satisfy the preservation contract, mark it
`SKIPPED — VIOLATES PRESERVATION` and explain.

---

# STYLE

- Concise engineering language
- Deterministic wording
- Implementation-focused — every finding has a fix
- No fluffy prose
- All metrics labeled (estimated / modeled / projected)

---

# FINAL RULE

If the assessment report includes raw SKILL.md content excerpts longer
than 200 chars, makes unlabeled token claims, or recommends removing a
validation/reconciliation step:

```text
EXECUTION IS INVALID
```

---

# REFERENCES

- `scripts/analyze.js` — Phase A analyzer (Node, no deps)
- `analyzers/heuristics.md` — rule set and thresholds
- `schemas/analysis_result.md` — JSON contract returned by the analyzer
- `templates/assessment_report.md` — Phase B output template
- `templates/refactor_plan.md` — refactor item template
- `templates/word_copilot_block.md` — reusable formatting tail
- `partials/token_estimation.md` — token math conventions
- `examples/example_usage.md` — end-to-end worked example
