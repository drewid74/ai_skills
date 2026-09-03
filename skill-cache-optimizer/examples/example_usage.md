# Example: Analyzing `hls-morning-brief`

End-to-end walk-through of how the agent runs this skill.

---

## User request

> "Analyze hls-morning-brief for cache efficiency"

## Phase A — Run the analyzer

```javascript
ctx_execute(language: "javascript", code: `
  const { analyzeSkill } = require('C:/Users/drewfairaizl/dev/ai_skills/skill-cache-optimizer/scripts/analyze.js');
  const result = analyzeSkill({
    target: 'C:/Users/drewfairaizl/dev/ai_skills/hls-morning-brief'
  });
  console.log(JSON.stringify(result, null, 2));
`)
```

Returns an `AnalysisResult` JSON object (see `schemas/analysis_result.md`).

## Phase B — Render the report

Using `templates/assessment_report.md`, populate the placeholders from
the JSON. No additional file reads, no new tool calls.

Example output excerpt:

---

# Skill Cache Assessment — `hls-morning-brief`

**Target:** `C:\Users\drewfairaizl\dev\ai_skills\hls-morning-brief`
**Generated:** `2026-06-02T15:45:00Z`
**Method:** modeled (heuristic) — token counts are estimated

## 1) Scorecard

| Metric | Score | Band |
|---|---|---|
| **CES** | 72/100 | Fair |

### Sub-scores

| Dimension | Value |
|---|---|
| Cacheable prefix % | 84.0% |
| Dynamic contamination % | 6.0% |
| Modularization score | 65.0/100 |
| Inline payload risk | 22.0/100 |
| Determinism score | 100/100 |
| Repetition % | 4.2% |
| `EXECUTION IS INVALID` gates | 2 |

## 3) Findings (excerpt)

| ID | Sev | Category | File:Line | Finding | Fix |
|---|---|---|---|---|---|
| PAY-1 | high | inline-payload | SKILL.md:218 | Large inline regex code block (118 lines) | Move to `partials/preprod-regex.md` and reference |
| MOD-1 | — | modularization | SKILL.md:160 | "SERVICE REGISTRY" section is 2770 bytes | Already externalized to `registries/hls_service_registry.md` ✅ |
| REP-1 | medium | repetition | — | "EXECUTION IS INVALID" paragraph appears 3x | Acceptable — these are intentional preservation gates |

## 5) Refactor plan (excerpt)

| Priority | Action | Projected savings | Risk |
|---|---|---|---|
| High | Externalize PROD-only enforcement regex block to `partials/preprod-regex.md` | ~470 tokens | Low |
| Medium | Consolidate the three preservation-gate paragraphs into a single referenced partial | ~120 tokens | Low |

---

## Optional: Compare two skills

```javascript
analyzeSkill({
  target: 'C:/Users/drewfairaizl/dev/ai_skills/hls-morning-brief',
  compareAgainst: 'C:/Users/drewfairaizl/dev/ai_skills/hls-monthly-review'
});
```

The result includes a `comparison` block:

```json
{
  "comparison": {
    "self":  { "ces": 72, "estTokens": 4820 },
    "other": { "target": "...hls-monthly-review", "ces": 81, "estTokens": 3210 },
    "deltaCES": -9,
    "deltaTokens": 1610
  }
}
```
