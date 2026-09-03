# AnalysisResult — JSON contract returned by `scripts/analyze.js`

```jsonc
{
  "target": "<absolute path to analyzed skill>",
  "compareAgainst": "<absolute path|null>",
  "generatedAt": "<ISO8601>",

  "inventory": [
    {
      "path": "relative/path/to/file.md",
      "bytes": 12345,
      "estTokens": 3086,
      "isSkillFile": true
    }
  ],

  "volume": {
    "totalFiles": 7,
    "totalBytes": 45678,
    "estTotalTokens": 11420,
    "method": "estimated (chars/4)"
  },

  "findings": [
    {
      "id": "DYN-1",
      "severity": "critical|high|medium|low",
      "category": "dynamic-contamination|inline-payload|repetition|determinism|retrieval-completeness|context-mode-usage|modularization",
      "file": "SKILL.md",
      "line": 42,
      "excerpt": "<=120 char snippet",
      "message": "Human-readable finding",
      "fix": "Actionable recommendation",
      "locations": ["file#blockN", "..."]  // only for repetition findings
    }
  ],

  "modularization": [
    {
      "file": "SKILL.md",
      "heading": "HLS Service Registry",
      "bytes": 2770,
      "estTokensFreed": 693,
      "proposedTarget": "registries/hls-service-registry.md",
      "label": "service registry"
    }
  ],

  "refactorPlan": [
    {
      "priority": "critical|high|medium|low",
      "action": "Concrete change description",
      "addresses": "<finding ID or category>",
      "projectedTokenSavings": 693,
      "method": "estimated",
      "risk": "low|medium|high",
      "preservation": "What must remain identical"
    }
  ],

  "scorecard": {
    "ces": 78,
    "band": "Excellent|Good|Fair|Poor",
    "subScores": {
      "cacheablePrefixPct": 88.5,
      "dynamicContaminationPct": 3.2,
      "modularizationScore": 92.0,
      "inlinePayloadRisk": 5.5,
      "determinismScore": 98.0,
      "repetitionPct": 1.4
    },
    "method": "modeled (heuristic weights)",
    "executionGatesDetected": 3
  },

  "comparison": {                                // present only if compareAgainst was provided
    "self":  { "ces": 78, "estTokens": 11420 },
    "other": { "target": "<path>", "ces": 65, "estTokens": 14210 },
    "deltaCES": 13,
    "deltaTokens": -2790
  },

  "risks": [],

  "errors": [
    { "where": "<phase>", "message": "<error>", "stack": "<optional>" }
  ],

  "verificationTrail": {
    "filesAnalyzed": 7,
    "filesSkipped": 2,
    "rulesApplied": [
      "dynamic-contamination",
      "inline-payload-risk",
      "repetition",
      "modularization",
      "determinism",
      "retrieval-completeness",
      "context-mode-usage",
      "word-copilot-block",
      "preservation-gates"
    ],
    "ambiguities": []
  }
}
```

## Field semantics

- **`estTokens` / `estTotalTokens`** — char count × 0.25. Always estimated.
- **`severity`** levels: `critical` (must fix), `high` (should fix), `medium` (worth fixing), `low` (nice to have).
- **`projectedTokenSavings`** — character savings × 0.25, only for modularization-driven refactors where the section will be referenced rather than inlined.
- **`executionGatesDetected`** — count of `EXECUTION IS INVALID` clauses; positive signal, never penalized.
- **`errors[]`** — non-fatal; analyzer never throws. Missing file reads, parse errors, etc. land here so Phase B can surface them.
