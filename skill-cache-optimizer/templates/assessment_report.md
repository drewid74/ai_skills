# Skill Cache Assessment — `<SKILL_NAME>`

**Target:** `<ABSOLUTE_PATH>`
**Generated:** `<ISO8601>`
**Method:** modeled (heuristic) — token counts are estimated (chars × 0.25)

---

## 1) Scorecard

| Metric | Score | Band |
|---|---|---|
| **Cache Efficiency Score (CES)** | `<CES>/100` | `<BAND>` |

### Sub-scores

| Dimension | Value | Direction |
|---|---|---|
| Cacheable prefix % | `<n>%` | higher is better |
| Dynamic contamination % | `<n>%` | lower is better |
| Modularization score | `<n>/100` | higher is better |
| Inline payload risk | `<n>/100` | lower is better |
| Determinism score | `<n>/100` | higher is better |
| Repetition % | `<n>%` | lower is better |
| `EXECUTION IS INVALID` gates detected | `<n>` | positive signal |

---

## 2) Volume

| | Value |
|---|---|
| Total files analyzed | `<n>` |
| Total bytes | `<n>` |
| Estimated total tokens | `<n>` |
| Files skipped (backup/tmp/hidden) | `<n>` |

### Per-file inventory

| File | Bytes | Est. tokens |
|---|---|---|
| `<path>` | `<n>` | `<n>` |

---

## 3) Findings

Sorted: Critical → High → Medium → Low.

| ID | Severity | Category | File:Line | Finding | Fix |
|---|---|---|---|---|---|
| `<ID>` | `<sev>` | `<cat>` | `<file>:<line>` | `<message>` | `<fix>` |

If no findings: `✅ No structural cache anti-patterns detected.`

---

## 4) Modularization opportunities

| File | Section | Bytes | Est. tokens freed | Proposed target |
|---|---|---|---|---|
| `<file>` | `<heading>` | `<n>` | `<n>` | `<folder>/<file>.md` |

**Total potential token reduction if all externalized:** `<sum>` (estimated)

---

## 5) Refactor plan (prioritized)

| Priority | Action | Addresses | Projected savings (est. tokens) | Risk | Preservation note |
|---|---|---|---|---|---|
| `<p>` | `<action>` | `<finding ID>` | `<n>` | `<risk>` | `<what must stay identical>` |

**Implementation order:** Critical → High → Modularization → Medium → Low.

---

## 6) Risks & preservation notes

- All recommendations preserve correctness, evidence integrity, retrieval completeness, validation rigor, and explicit uncertainty labels.
- No recommendation removes a validation gate, reconciliation step, or `EXECUTION IS INVALID` clause.
- Any tradeoff is flagged explicitly with `TRADEOFF:` prefix.

---

## 7) Verification trail

| | |
|---|---|
| Files analyzed | `<n>` |
| Files skipped | `<n>` |
| Rules applied | `dynamic-contamination, inline-payload-risk, repetition, modularization, determinism, retrieval-completeness, context-mode-usage, word-copilot-block, preservation-gates` |
| Ambiguities | `<list or "none">` |
| Errors | `<list or "none">` |

---

## (Optional) 8) Comparison

Present only when `compareAgainst` was provided:

| | This skill | Comparison skill | Δ |
|---|---|---|---|
| CES | `<n>` | `<n>` | `<±n>` |
| Est. tokens | `<n>` | `<n>` | `<±n>` |
