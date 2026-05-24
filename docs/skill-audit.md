# Skill Audit Report

**Date:** 2026-05-24  
**Scope:** All skills in `C:\Users\afair\dev\ai_skills`  
**Files audited:** 65 of 66 (`arbitrage-audit/SKILL.md` missing)  
**Auditor:** Claude Sonnet 4.6 (opencode session)

---

## Executive Summary

The collection is in good shape overall. The core ~35 skills follow a consistent, lean template (~75 lines) with strong decision density. The Android reference skills are intentionally longer and code-heavy — appropriate for their purpose. The Karpathy trio and a few strategic/business skills use a different interview-style format, which is intentional but inconsistently documented.

**Key findings:**

- **1 missing file** (`arbitrage-audit`) — listed in README, no SKILL.md on disk
- **2 routing conflicts** — `deep-research-pro` vs `research-analyst`; `sre-operations-lead` vs `grafana-prometheus-monitoring`
- **1 hardcoded personal path** — `ai-innovation-radar` references `C:\users\afair\dev\dev_island\...`
- **3 skills with weak/missing trigger phrases** — `android-agp-upgrade`, `android-cli`, `android-compose-migration`
- **1 skill with stale date-specific content** — `strategic-timing-decision-matrix` hardcodes 2026 IPO dates that will age out
- **README count mismatch** — README says 43 skills; actual count is 65+ (README is stale)

**Overall ratings:**
- ✅ Good: 48 skills
- ⚠️ Needs work: 16 skills
- ❌ Critical issues: 1 skill (missing file)

---

## Per-Skill Table

| Skill | Rating | Primary Issue |
|-------|--------|---------------|
| agentic-economy-readiness-test | ✅ | — |
| ai-innovation-radar | ⚠️ | Hardcoded personal path |
| ai-skills-dev | ✅ | — |
| ai-systems-architect | ✅ | — |
| android-agp-upgrade | ⚠️ | Weak trigger phrases |
| android-auto | ✅ | — |
| android-ble-hardware | ⚠️ | BLE overlap with android-bluetooth |
| android-bluetooth | ✅ | Has explicit routing guards |
| android-camera1-to-camerax | ✅ | — |
| android-cli | ⚠️ | Vague description, broad triggers |
| android-compose-migration | ⚠️ | Weak trigger phrases |
| android-compose-realtime | ✅ | — |
| android-foreground-service | ✅ | — |
| android-navigation-3 | ✅ | — |
| android-obd | ✅ | Has explicit routing guards |
| android-on-device-ml | ✅ | — |
| android-play-billing-upgrade | ✅ | — |
| android-r8-analyzer | ✅ | — |
| android-security | ✅ | — |
| android-telemetry-pipeline | ✅ | — |
| android-video-capture | ✅ | Apache-2.0 lineage noted |
| api-integration | ✅ | — |
| arbitrage-audit | ❌ | SKILL.md file missing |
| archivebox-knowledge | ✅ | — |
| browser-automation | ✅ | — |
| career-gap-map | ✅ | — |
| cicd-pipeline | ✅ | — |
| code-reviewer | ✅ | — |
| content-strategy | ✅ | — |
| data-engineering | ✅ | — |
| database-architecture | ✅ | — |
| deep-research-pro | ⚠️ | Routing conflict with research-analyst |
| deploy-pipeline | ✅ | — |
| docker-selfhost | ✅ | — |
| federated-memory | ✅ | — |
| five-verticals-positioning-audit | ✅ | — |
| frontend-design-pro | ✅ | — |
| full-sdlc | ✅ | — |
| github-workflow | ✅ | — |
| grafana-prometheus-monitoring | ✅ | Long but intentionally comprehensive |
| gws-assistant-pro | ✅ | — |
| ham-radio-network | ✅ | — |
| harness-engineering | ✅ | Most complete skill in repo |
| infrastructure-as-code | ✅ | — |
| ios-developer | ⚠️ | Boilerplate structure; references possibly missing resource file |
| karpathy-metric-pre | ⚠️ | Non-standard format (intentional but undocumented) |
| karpathy-trace-infrastructure | ⚠️ | Non-standard format (intentional but undocumented) |
| karpathy-triplet-diag | ⚠️ | Non-standard format (intentional but undocumented) |
| life-engine | ✅ | — |
| live-retrieval | ✅ | — |
| llm-inference-stack | ✅ | — |
| mcp-server-dev | ✅ | — |
| org-level-model-dependency | ✅ | — |
| outcome-based-system-prompt | ✅ | — |
| play-billing-library-version-upgrade | ✅ | — |
| productivity-automation | ✅ | — |
| project-orchestrator-pro | ✅ | — |
| proxmox-k3s-infra | ✅ | — |
| quality-test-engineer | ✅ | — |
| repo-auditor-pro | ✅ | — |
| research-analyst | ⚠️ | Routing conflict with deep-research-pro |
| security-engineer | ✅ | — |
| sequential-thinking-pro | ✅ | — |
| service-integration | ✅ | — |
| sigint-osint-feeds | ✅ | — |
| sre-operations-lead | ⚠️ | Routing overlap with grafana-prometheus-monitoring |
| strategic-timing-decision-matrix | ⚠️ | Hardcoded 2026 IPO dates; will age out |
| training-pipeline | ✅ | — |
| truenas-ops | ✅ | — |
| web-performance-a11y | ✅ | — |
| weekly-signal-diff | ✅ | — |

---

## Detailed Findings — ⚠️ and ❌ Skills

### ❌ arbitrage-audit — MISSING FILE

`arbitrage-audit/SKILL.md` does not exist on disk. The skill is registered in the opencode skill list and referenced in the README. Any invocation will silently fail or fall back to a generic response.

**Fix:** Create the file or remove the skill registration.

---

### ⚠️ ai-innovation-radar — Hardcoded Personal Path

The skill body references a hardcoded Windows path: `C:\users\afair\dev\dev_island\...`. This makes the skill non-portable and will break for any other user who installs the collection.

**Fix:** Replace with a placeholder (e.g., `<PROJECT_ROOT>`) or make the path configurable via a variable at the top of the skill.

---

### ⚠️ android-agp-upgrade — Weak Trigger Phrases

The description is: *"Upgrades, or migrates, an Android project to use Android Gradle Plugin (AGP) version 9."* This is a capability statement, not a trigger phrase. A developer typing "my AGP upgrade is failing" or "migrate to AGP 9" may not match this description reliably.

**Fix:** Rewrite description as action/problem phrases: `"Use this when: upgrade AGP, migrate to AGP 9, Android Gradle Plugin version 9, AGP migration, gradle plugin upgrade, build.gradle AGP version, com.android.application plugin upgrade"`

---

### ⚠️ android-ble-hardware — BLE Overlap with android-bluetooth

Both skills cover BLE scanning, GATT, and Android 12+ permissions. `android-bluetooth` has explicit routing guards ("Do not use for non-Android Bluetooth firmware... use android-obd for ELM327"). `android-ble-hardware` does not have equivalent guards pointing away from `android-bluetooth`.

**Fix:** Add a routing guard to `android-ble-hardware` clarifying it is for Nordic BLE library / hardware peripheral integration, and that generic BLE/GATT questions should use `android-bluetooth`.

---

### ⚠️ android-cli — Vague Description

The description lists a broad mix of unrelated triggers: project creation, SDK management, emulator management, ADB commands, screenshots, layout inspection. This is a catch-all that will over-trigger on many Android questions.

**Fix:** Narrow the description to the specific CLI tool this skill covers, or split into more focused skills. If it's a wrapper for a specific `android` CLI binary, name that binary explicitly.

---

### ⚠️ android-compose-migration — Weak Trigger Phrases

The description is a capability statement ("Provides a structured workflow for migrating an Android XML View to Jetpack Compose") rather than action/problem phrases. Developers asking "how do I migrate my XML layout to Compose" may not match.

**Fix:** Rewrite as: `"Use this when: migrate XML to Compose, XML View to Jetpack Compose, convert layout XML to Compose, migrate Fragment to Compose, interop XML Compose, ComposeView in XML, AndroidView in Compose, migrate RecyclerView to LazyColumn"`

---

### ⚠️ deep-research-pro vs research-analyst — Routing Conflict

Both skills share nearly identical trigger phrases: "research", "find sources", "fact-check", "citations", "verify information", "competitive analysis". A router cannot reliably distinguish between them.

**Differentiation analysis:**
- `deep-research-pro`: Emphasizes live web search, Perplexity-style retrieval, current news/docs
- `research-analyst`: Emphasizes structured analysis, triangulation, confidence scoring, threat intelligence

**Fix:** Sharpen the descriptions to make the distinction explicit. `deep-research-pro` should own "search the web", "latest news", "find current docs". `research-analyst` should own "structured analysis", "threat intelligence", "triangulate findings", "confidence scoring", "source evaluation".

---

### ⚠️ ios-developer — Boilerplate Structure

This skill uses a generic community template format with boilerplate sections ("Use this skill when...", "Do not use this skill when...") rather than the lean Identity/Stack Defaults/Decision Framework/Anti-Patterns/Quality Gates template used by the rest of the collection. It also references `resources/implementation-playbook.md` — a file that may not exist in the installed location.

**Fix:** Rewrite to match the standard template. Verify `resources/implementation-playbook.md` exists or remove the reference.

---

### ⚠️ karpathy-metric-pre / karpathy-trace-infrastructure / karpathy-triplet-diag — Non-Standard Format

All three use an XML `<role>`/`<instructions>` format with a phased interview structure. This is intentionally different from the standard template and works well for their use case. However, there is no documentation explaining why these three differ from the rest of the collection.

**Fix (low priority):** Add a comment at the top of each file noting the intentional format difference, e.g., `<!-- Interview-style skill: uses phased Q&A rather than standard template -->`. This prevents future contributors from "fixing" the format unnecessarily.

---

### ⚠️ sre-operations-lead vs grafana-prometheus-monitoring — Routing Overlap

Both skills trigger on: "set up monitoring", "alerts", "Prometheus", "Grafana", "SLOs", "observability". A developer asking "my Prometheus alerts are too noisy" could match either.

**Differentiation analysis:**
- `sre-operations-lead`: Incident response, runbooks, on-call, SLO definition, postmortems — the *operations* layer
- `grafana-prometheus-monitoring`: Dashboard provisioning, scrape config, recording rules, cardinality — the *tooling* layer

**Fix:** Add explicit routing guards. `sre-operations-lead` should note "for dashboard/scrape configuration, use grafana-prometheus-monitoring". `grafana-prometheus-monitoring` should note "for incident response and runbooks, use sre-operations-lead".

---

### ⚠️ strategic-timing-decision-matrix — Stale Date-Specific Content

The skill body hardcodes specific 2026 IPO dates, valuations, and capital dynamics (SpaceX June–July 2026, OpenAI Q3 2026, Anthropic Q4 2026, Nasdaq-100 rule effective May 1 2026). This content will become factually incorrect as events unfold or timelines shift.

**Fix:** Either (a) add a prominent `<!-- Last verified: 2026-05-24 — review quarterly -->` header, or (b) restructure the skill to use a parameterized timeline that the user provides rather than hardcoded dates.

---

## Cross-Cutting Issues

### 1. README Count Mismatch

The README states "43 skills" and "35 skills" in various places. The actual count is 65+ skills. The README tables are also incomplete — they list ~35 skills but the repo contains significantly more (Karpathy trio, strategic/business skills, life-engine, weekly-signal-diff, etc.).

**Fix:** Update README skill count and tables to reflect the actual collection.

### 2. Inconsistent Format Across Skill Categories

Three distinct formats exist in the collection:
- **Standard template** (~75 lines): Identity → Stack Defaults → Decision Framework → Anti-Patterns → Quality Gates
- **Android reference** (longer, code-heavy): Full implementation guides with Kotlin examples
- **Interview/advisory** (Karpathy trio, strategic skills): XML role tags, phased Q&A, output format specs

This is fine architecturally, but the README only documents the standard template. New contributors may not know which format to use for which type of skill.

**Fix:** Add a "Skill Types" section to the README documenting all three formats and when to use each.

### 3. Missing Routing Guards in Several Skills

`android-bluetooth` and `android-obd` are exemplary — they explicitly name sibling skills and when to route to them. Most other skills with potential overlaps (e.g., `deep-research-pro`, `sre-operations-lead`, `android-ble-hardware`) lack these guards.

**Fix:** Add "Do not use for X — use [skill-name] instead" lines to all skills with known routing conflicts.

### 4. No Explicit Version Pinning in Stack Defaults

Several skills reference tools without version constraints (e.g., "Tailwind v4" in `frontend-design-pro` is good; most others just say "Playwright", "pytest", etc.). When major breaking versions exist, pinning helps the LLM give accurate advice.

**Fix (low priority):** Add version notes to Stack Defaults tables where major version differences matter (e.g., Playwright v1.x, pytest 7+, Terraform 1.x vs OpenTofu).

---

## Top-10 Fix List (Prioritized)

| Priority | Skill | Fix |
|----------|-------|-----|
| 1 | `arbitrage-audit` | Create SKILL.md or remove registration — currently broken |
| 2 | `ai-innovation-radar` | Remove hardcoded personal path `C:\users\afair\dev\dev_island\...` |
| 3 | `deep-research-pro` + `research-analyst` | Sharpen descriptions to eliminate routing ambiguity |
| 4 | `sre-operations-lead` + `grafana-prometheus-monitoring` | Add cross-skill routing guards |
| 5 | `android-agp-upgrade` | Rewrite description as action/problem trigger phrases |
| 6 | `android-compose-migration` | Rewrite description as action/problem trigger phrases |
| 7 | `android-ble-hardware` | Add routing guard pointing to `android-bluetooth` for generic BLE |
| 8 | `ios-developer` | Rewrite to standard template; verify/remove `resources/implementation-playbook.md` reference |
| 9 | `strategic-timing-decision-matrix` | Add last-verified date header; plan for content refresh |
| 10 | README | Update skill count (43 → 65+) and add missing skills to tables |
