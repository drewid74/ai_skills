# AI Skills Repo — Optimization Report
Generated: 2026-05-23

## Summary

**66 skills, 7,727 lines, avg 117 lines/skill (target: 60–90)**
**Estimated recoverable token waste: ~14,600 tokens per session that loads multiple skills**

---

## Priority 1: Fix Critically Thin Descriptions (High ROI — routing failures)

These 6 skills have descriptions too short or prose-only to trigger reliably. Skills that don't trigger on the right query waste a full tool call on the wrong skill.

| Skill | Problem | Fix |
|---|---|---|
| `ios-developer` | Single sentence, no action phrases | Add 10+ comma-separated trigger phrases |
| `android-cli` | Prose description | Convert to comma-separated triggers |
| `r8-analyzer` | Prose, not phrases | Convert to comma-separated triggers |
| `play-billing-library-version-upgrade` | Single trigger phrase | Add upgrade/migrate/version-specific triggers |
| `navigation-3` | Prose description | Convert to comma-separated triggers |
| `camera1-to-camerax` | Single trigger phrase | Add migration/deprecated/Camera2 triggers |

**Good reference:** `harness-engineering` (40+ triggers), `grafana-prometheus-monitoring` (40+ triggers)

---

## Priority 2: Eliminate Duplicate Boilerplate (~2,700 tokens recoverable)

### 24-line "Automated Testing" block duplicated in 9 skills

Exact duplicate across: `android-agp-upgrade`, `android-bluetooth`, `android-camera1-to-camerax`,
`android-cli`, `android-compose-migration`, `android-navigation-3`, `android-obd`,
`android-play-billing-upgrade`, `android-r8-analyzer`

**Fix:** Create `references/android-testing-baseline.md` with the canonical block.
Replace 24-line block in each skill with:
```
See: references/android-testing-baseline.md
```

### 4-line "Lineage" preamble in 8 skills (~400 tokens)

Present in: `android-auto`, `android-ble-hardware`, `android-compose-realtime`,
`android-foreground-service`, `android-on-device-ml`, `android-security`,
`android-telemetry-pipeline`, `android-video-capture`

**Fix:** Move to YAML `source:` field or delete entirely — it adds no value at inference time.

---

## Priority 3: Refactor Bloated Skills to Use references/ (~11,000 tokens recoverable)

The `references/` pattern exists in the spec but is used by **zero** skills today. These are the worst offenders:

| Skill | Lines | Fix |
|---|---|---|
| `grafana-prometheus-monitoring` | 832 | Move stack-specific configs (Alertmanager, Mimir, Loki, DCGM) to separate references/ files. Core skill stays <100 lines |
| `harness-engineering` | 466 | Move the AGENTS.md template and full checklist to references/harness-checklist.md |
| `android-bluetooth` | 279 | Move BluetoothSocket code patterns to references/android-bt-patterns.md |
| `android-security` | 279 | Move KeyStore code examples to references/android-keystore-examples.md |
| `android-on-device-ml` | 277 | Move TFLite delegate setup to references/android-tflite-setup.md |
| `android-telemetry-pipeline` | 271 | Move Room schema patterns to references/android-telemetry-schema.md |
| `android-video-capture` | 267 | Move CameraX boilerplate to references/android-camerax-boilerplate.md |
| `android-auto` | 255 | Move template code to references/android-auto-templates.md |
| `android-compose-realtime` | 242 | Move Canvas/derivedStateOf patterns to references/android-compose-realtime-patterns.md |
| `android-obd` | 241 | Move AT command sequences to references/elm327-at-commands.md |
| `android-ble-hardware` | 219 | Move GATT profile code to references/android-ble-gatt-profiles.md |

**Rule of thumb:** Skill body = triggers + workflow decision tree + common pitfalls (≤90 lines).
Code examples, templates, reference tables → `references/`.

---

## Priority 4: Fix Routing Conflicts (Indirect token waste — wrong skill loads)

### Android Bluetooth 3-way overlap
`android-bluetooth`, `android-ble-hardware`, `android-obd` all overlap on BLE/Bluetooth triggers.

**Fix:** Add explicit `DO NOT USE FOR` boundaries to each:
- `android-bluetooth` → "DO NOT USE FOR: BLE GATT profiles (use android-ble-hardware), ELM327/OBD (use android-obd)"
- `android-ble-hardware` → "DO NOT USE FOR: Classic Bluetooth/SPP (use android-bluetooth), OBD protocol (use android-obd)"
- `android-obd` → Already has good boundaries — keep

### AI skills 2-way overlap
`ai-systems-architect` and `ai-skills-dev` overlap on "system prompt" and "pipeline" triggers.

**Fix:**
- `ai-systems-architect` → Add "DO NOT USE FOR: writing skill descriptions or SKILL.md files (use ai-skills-dev)"
- `ai-skills-dev` → Add "DO NOT USE FOR: system architecture, LLM selection, RAG design (use ai-systems-architect)"

### Grafana/SRE overlap
`grafana-prometheus-monitoring` and `sre-operations-lead` overlap on monitoring/alerting/dashboards.

**Fix:**
- `grafana-prometheus-monitoring` → "For tool configuration and provisioning"
- `sre-operations-lead` → "For operational decisions, SLOs, and incident response"

---

## Priority 5: Add Cross-References for Sequential Skills

The Karpathy trilogy has no cross-references. Users hitting one should be pointed to the others.

Add to each skill's description:
- `karpathy-triplet-diag` → "Run first. Then use karpathy-trace-infrastructure and karpathy-metric-pre."
- `karpathy-trace-infrastructure` → "Part 2 of 3. See also: karpathy-triplet-diag, karpathy-metric-pre."
- `karpathy-metric-pre` → "Part 3 of 3. See also: karpathy-triplet-diag, karpathy-trace-infrastructure."

---

## Minor Inconsistencies

- **Section naming**: 10 skills use "Common Pitfalls", others use "Anti-Patterns" — standardize to one
- **IF/THEN trees missing**: 4 skills use prose instead of structured IF/THEN routing blocks:
  `ai-innovation-radar`, `agentic-economy-readiness-test`, `android-compose-migration`, `android-navigation-3`
- **Reference Files section**: Only `android-bluetooth` has it — pattern is valid, should be added to any skill with code examples

---

## Token Waste Summary

| Category | Est. Tokens Wasted | Effort |
|---|---|---|
| Automated Testing duplication (9 skills) | ~2,700 | Low — create 1 file, 9 edits |
| Lineage boilerplate (8 skills) | ~400 | Low — delete 4 lines x8 |
| Bloated bodies >200 lines (11 skills) | ~11,000 | Medium — content audit per skill |
| Prose vs IF/THEN (4 skills) | ~500 | Low — restructure |
| Thin descriptions mis-routing (6 skills) | Indirect | Low — rewrite descriptions |
| **TOTAL RECOVERABLE** | **~14,600 tokens** | |

---

## Recommended Execution Order

1. **Fix the 6 thin descriptions** — 30 min, immediate routing improvement
2. **Create `references/android-testing-baseline.md`** and redirect 9 skills — 20 min, ~2,700 tokens saved
3. **Delete Lineage preambles** from 8 skills — 10 min, ~400 tokens saved
4. **Add `DO NOT USE FOR` boundaries** to BT trio and AI skills — 20 min, routing quality
5. **Refactor `grafana-prometheus-monitoring`** into core + references/ — 45 min, biggest single win
6. **Refactor `harness-engineering`** into core + references/ — 30 min
7. **Standardize section naming** and add IF/THEN trees to 4 prose skills — 60 min
8. **Add Karpathy cross-references** — 10 min
