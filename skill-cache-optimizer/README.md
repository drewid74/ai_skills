# skill-cache-optimizer

Analyze any skill in `~/dev/ai_skills/` for prompt cache efficiency and
produce an actionable refactor plan.

## What it does

Runs a self-contained Node analyzer against a skill folder and emits:

- **Cache Efficiency Score (CES)** — 0–100 composite metric
- **Findings** with file:line citations (Critical → Low)
- **Modularization opportunities** — sections that should be externalized
- **Refactor plan** — prioritized changes with projected token savings
- **Optional comparison** between two skills

## How to invoke

Trigger phrases (frontmatter routes the agent here automatically):

- "analyze hls-morning-brief"
- "optimize skill X"
- "audit cache for skill Y"
- "score the skill at <path>"
- "compare skill A vs skill B for efficiency"

The agent will:
1. Run `scripts/analyze.js` inside `ctx_execute` (Phase A)
2. Render the report from `templates/assessment_report.md` (Phase B)

## Files

| Path | Purpose |
|---|---|
| `SKILL.md` | Operational runbook (this is the entry point) |
| `scripts/analyze.js` | Pure Node.js analyzer (no deps; Node 18+ / Bun) |
| `analyzers/heuristics.md` | Rule set, severity, and CES weights |
| `schemas/analysis_result.md` | JSON contract returned by the analyzer |
| `templates/assessment_report.md` | Phase B output template |
| `templates/refactor_plan.md` | Refactor item template |
| `templates/word_copilot_block.md` | Reusable Word formatting tail |
| `partials/token_estimation.md` | Token math conventions |
| `examples/example_usage.md` | Worked example against hls-morning-brief |

## Preservation contract (hard)

The optimizer NEVER recommends:
- removing validation gates
- dropping reconciliation steps
- hiding uncertainty labels
- shortening `EXECUTION IS INVALID` clauses

If a recommendation cannot satisfy the contract, it is marked
`SKIPPED — VIOLATES PRESERVATION`.

## Token estimation

All token counts are **estimated** (chars × 0.25). The analyzer never
claims measured telemetry. See `partials/token_estimation.md`.
