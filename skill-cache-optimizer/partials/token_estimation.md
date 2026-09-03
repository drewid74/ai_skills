# Token Estimation Conventions

## Method

```
estTokens = ceil(charCount × 0.25)
```

This is a rough English-leaning approximation. It is NOT a substitute for
tokenizer telemetry.

## Labels (mandatory)

Every numeric token claim MUST be labelled:

| Label | Meaning |
|---|---|
| **estimated** | Computed via chars × 0.25 |
| **modeled** | Derived from a heuristic formula (e.g., CES sub-scores) |
| **projected** | Predicted post-refactor delta |
| **measured** | ONLY when telemetry (e.g., actual model API counts) is provided by the user |

## What counts

- Markdown files (`.md`, `.markdown`)
- Plain text (`.txt`)
- JSON / YAML referenced as prompt content (`.json`, `.yml`, `.yaml`)

## What does NOT count

- Files matching `backup_*`, `*.bak`, `*.tmp`, `*.swp`, `*~`
- `node_modules/`, `.git/`
- Binary files
- Files in `examples/` that are explicitly excluded from the prompt at runtime

## Multi-file aggregation

When a skill spans multiple files, the analyzer sums byte counts across
all included files. The CES reflects the COMBINED prompt as a single
cacheable unit, since most skill loaders concatenate or reference them
in a stable order.

## Caveats

- Code-heavy sections (JS/Python) tokenize differently than prose; chars×0.25 may under-count by 10–20%
- CJK content tokenizes very differently; if detected, flag in `ambiguities[]`
- This estimator does NOT account for model-specific BPE quirks

Report any deviation in `verificationTrail.ambiguities`.
