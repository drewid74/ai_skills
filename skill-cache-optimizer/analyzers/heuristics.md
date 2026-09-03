# Analyzer Heuristics

The rule set applied by `scripts/analyze.js`. Each rule emits zero or more
findings with an ID prefix.

---

## DYN — Dynamic Contamination (severity: high/medium)

Detects runtime values embedded in the static cacheable prefix.

| Pattern | Severity | Rationale |
|---|---|---|
| Hard-coded ISO date (`\d{4}-\d{2}-\d{2}`) | high | Changes per run; breaks prefix cache |
| Template variable `{{...}}` | medium | Indicates unfinished templating |
| `current_datetime`, `now()`, `today`, `yesterday`, `right now` | high | Runtime time reference baked into prompt |
| `Generated: <digit>` | high | Generation-stamp leaked into prompt |

**Fix:** Move all runtime values into a labelled `# DYNAMIC PAYLOAD` section appended after the static prefix, or pass via a separate message.

---

## PAY — Inline Payload Risk (severity: critical/high)

Detects oversized code/JSON fences embedded in the prompt.

| Trigger | Severity |
|---|---|
| ` ``` ` fence ≥200 lines | critical |
| ` ``` ` fence ≥100 lines | high |
| ` ```json ` fence ≥20 lines | high |

**Fix:** Externalize to `examples/`, `schemas/`, or `partials/` and reference by path.

---

## REP — Repetition (severity: medium/high)

Hashes normalized paragraphs (≥80 chars, lowercased, whitespace-collapsed). Reports any paragraph appearing ≥2 times across the skill folder.

| Trigger | Severity |
|---|---|
| 2–3 occurrences | medium |
| ≥4 occurrences | high |

**Fix:** Extract to `partials/<name>.md` and reference once.

---

## MOD — Modularization Opportunities

Identifies sections >2KB whose headings match externalizable patterns.

| Heading match | Target folder |
|---|---|
| REGISTRY / SERVICE LIST | `registries/` |
| SCHEMA / SCHEMAS | `schemas/` |
| WORD COPILOT / FORMATTING BLOCK | `templates/` |
| TEMPLATE / OUTPUT STRUCTURE | `templates/` |
| EXAMPLE / WORKED EXAMPLE | `examples/` |

Emitted as `modularization[]` entries rather than `findings[]`.

---

## DET — Determinism (severity: low)

Walks H1–H6 headings; flags any depth jump >1 (e.g., H2 → H4).

**Fix:** Normalize heading hierarchy so each section is at most one level deeper than its parent.

---

## RET — Retrieval Completeness (severity: high/medium)

Triggered when a file mentions search/query/fetch/retrieve operations against incidents/records/pages/results. Checks for presence of:

- pagination (`pagination`, `nextPageToken`, `@odata.count`, `nextCursor`)
- deduplication (`dedup`, `deduplicate`, `unique`, `distinct`)
- reconciliation (`reconcil`, `cross-check`, `secondary pass`, `completeness`)

Severity is **high** if pagination is missing, otherwise **medium**.

---

## CTX — Context-Mode Usage (severity: high)

Triggered when a file references large data ops (transcript, bridge, payload, JSON dump, Kusto, telemetry, ">10KB") but does NOT mention `ctx_execute`, `ctx_execute_file`, `ctx_fetch_and_index`, or `ctx_index`.

**Fix:** Add a `CONTEXT-MODE REQUIRED` section and route large payload handling through sandbox execution.

---

## WCB — Word Copilot Block (severity: low)

Detects an inline `=== INSTRUCTIONS FOR WORD COPILOT ===` block when no `word_copilot*` file exists in the skill folder.

**Fix:** Move to `templates/word_copilot_block.md`.

---

## PRES — Preservation Gate Detection (informational)

Counts occurrences of `EXECUTION IS INVALID` clauses across the skill.
This is a **positive signal** (presence of hard failure modes) — reported
in the scorecard, never penalized.

---

## File scope

- Walks the target folder recursively
- Skips: `backup_*`, `*.bak`, `*.tmp`, `*.swp`, `*~`, `node_modules/`, `.git/`
- Reads only: `*.md`, `*.markdown`, `*.txt`, `*.json`, `*.yml`, `*.yaml`

---

## Severity → CES weight

The Cache Efficiency Score weights are defined in `scripts/analyze.js#scoreSkill`. Sub-scores roll up as:

```
CES = 0.30 * cacheable_prefix_pct
    + 0.20 * (100 - dynamic_contamination_pct)
    + 0.15 * modularization_score
    + 0.15 * (100 - inline_payload_risk)
    + 0.10 * determinism_score
    + 0.10 * (100 - repetition_pct)
```
