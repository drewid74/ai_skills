---
name: mission-control-pro
description: >-
  Meta-agent orchestrator for complex multi-step projects. Routes tasks to
  specialized agents via DAG decomposition, resolves conflicting agent outputs
  with evidence-based arbitration, provides cost-aware delegation, and includes
  RF/ham radio calculation reference (antenna, link budget, coax, SWR, AREDN).
triggers:
  - "delegate this across agents"
  - "orchestrate multiple tasks"
  - "break this down into parallel work"
  - "coordinate these systems"
  - "RF calculation needed"
  - "antenna design"
  - "ham radio link budget"
  - "resolve disagreement from parallel agents"
  - "show progress on complex project"
tags: [orchestration, multi-agent, reasoning, RF, ham-radio, dag, conflict-resolution]
author: next-gen
---

# Mission Control: Meta-Agent Orchestrator & RF Reference

## Identity

Executive layer above isolated agents. Decompose complex tasks into DAGs, route to specialists, resolve conflicts with evidence scoring, maintain audit trails. For RF/ham radio: prefer local formula over API call (cost = $0, instant).

## Stack Defaults

| Domain | Default | Notes |
|--------|---------|-------|
| Task decomposition | DAG | Identify parallel vs. sequential subtasks |
| Conflict resolution | Evidence scoring | Weighted criteria, not majority vote |
| Cost awareness | Local-first | Formulas/local logic before external APIs |
| State tracking | Task registry | state + agent + deps + acceptance criteria |
| RF calculator | Built-in formulas | Dipole, vertical, Yagi, coax, SWR, link budget |

## Decision Framework

```
IF task involves multiple parallel workstreams:
  → Decompose to DAG: identify independent subtasks → assign agents → aggregate
  → Track each subtask: state(In-Progress/Blocked/Completed), agent, deps

IF parallel agents produce conflicting outputs:
  → Evidence scoring: weight criteria against user context
  → Score each option: sum weighted criteria
  → Recommend highest scorer; explain trade-offs
  → If agents loop A→B→A→B twice: HALT, escalate to human

IF choosing between tools/databases:
  → Check local decision matrix first (cost $0, instant)
  → Only escalate to expensive API if local confidence < 0.70

IF RF/antenna calculation needed:
  → Use built-in formulas (see RF Reference below)
  → Always show: formula, inputs, result, operational meaning

IF debugging multi-agent failure:
  → RCA: Observation → History → Hypothesis(×3) → Isolation test
```

## Anti-Patterns

| Anti-Pattern | Use Instead |
|--------------|-------------|
| Sequential execution when parallel is possible | DAG decomposition |
| Accepting first agent output without conflict check | Evidence-based arbitration |
| Calling expensive API for deterministic calculation | Local formula/decision matrix |
| A→B→A→B delegation loop | HALT at 2 cycles, escalate to human |
| Black-box recommendations | Show scoring + evidence always |
| No audit trail | Structured audit log per task |

## Quality Gates

- [ ] DAG identifies all parallelizable subtasks before starting
- [ ] Every task has acceptance criteria and assigned agent
- [ ] Conflicts scored with explicit weighted criteria
- [ ] Audit log: decomposition, delegation, conflicts, checkpoints
- [ ] Cost matrix consulted before API calls
- [ ] No delegation loops > 2 cycles

---

## Multi-Agent Router

```python
ROUTER_KEYWORDS = {
    "orchestrator":    ["delegate", "coordinate", "parallel", "DAG", "checkpoint"],
    "reasoner":        ["why", "decision", "root cause", "trade-off", "analysis"],
    "rf_calculator":   ["antenna", "RF", "coax", "SWR", "link budget", "repeater", "DMR"],
    "tech_advisor":    ["database", "framework", "architecture", "choose between"],
    "conflict_resolver": ["contradiction", "disagree", "conflicting", "merge results"]
}

def route_task(prompt: str) -> list[str]:
    matched = [agent for agent, kws in ROUTER_KEYWORDS.items()
               if any(kw.lower() in prompt.lower() for kw in kws)]
    return matched or ["orchestrator"]
```

## DAG Task Decomposition

```
4-step process:
1. Identify subtasks — parse implicit parallel work
2. Map dependencies — which tasks block others?
3. Assign agents — route each to specialist
4. Aggregate — merge outputs, detect conflicts

Example — "Deploy RF system with AREDN mesh":
  ├── [PARALLEL] RF analysis → antenna design → AREDN topology
  │               └─ Feeds: link budget validation
  ├── [PARALLEL] Database selection → VLAN design
  │               └─ Feeds: integration test plan
  ├── [SEQUENTIAL] Conflict resolution
  └── [SEQUENTIAL LAST] Execute with fallback
```

## Conflict Resolver (Evidence Scoring)

```
User context: "RF monitoring system, 100ms latency requirement"

Agent A: "Use Postgres (ACID, structured)"
Agent B: "Use Redis (fast, real-time)"

Criteria        Weight  Postgres  Redis
Durability       0.4    1.0→0.40  0.3→0.12
Latency          0.4    0.6→0.24  0.9→0.36
Schema           0.2    1.0→0.20  0.2→0.04
                        Total: 0.84   0.52

Resolution: Postgres. Consider Redis cache if p95 > 100ms under load.
```

## Decision Matrix: Database

| DB | Score | Best For |
|----|-------|----------|
| TimescaleDB | 0.84 | RF/IoT time-series |
| PostgreSQL | 0.82 | Structured, relational |
| Redis | 0.66 | Cache layer, ephemeral |
| MongoDB | 0.66 | Flexible schema |

## Audit Log Format

```yaml
audit_log:
  task_id: deploy-rf-system
  decomposition:
    - subtask: antenna_design
      agent: rf_calculator
      status: complete
      result: "97.7cm dipole, 50Ω"
  conflicts:
    - contradiction: frequency offset
      resolution: "Evidence scoring: +600kHz (FM standard)"
  checkpoints:
    - "Antenna validated against SWR model"
    - "All subtasks complete"
```

---

## RF Calculations Reference

### Dipole (Half-Wave)
```
Length (m) = 142.65 / f_MHz
146 MHz → 0.977m (97.7cm)    WHY: Half-λ resonance ≈ 50Ω, 2.15 dBi
```

### Vertical (Quarter-Wave)
```
Length (m) = 71.33 / f_MHz
146 MHz → 0.489m (48.9cm)    WHY: Ground plane as image, omni pattern
```

### Yagi Gain
```
Gain (dBi) ≈ 10 + 8.5 × log10(f_MHz)
146 MHz → 28.4 dBi   446 MHz → 32.5 dBi
```

### Coax Loss per 100ft

| Cable | 146 MHz | 446 MHz |
|-------|---------|---------|
| RG-58 | 4.6 dB | 8.9 dB |
| RG-8X | 2.7 dB | 5.3 dB |
| LMR-400 | 1.4 dB | 2.7 dB |

```
50ft RG-8X @ 146 MHz: (50/100) × 2.7 = 1.35 dB
```

### SWR & Return Loss
```
SWR 1.5:1 → 14 dB return loss   ← GOOD
SWR 2.0:1 → 9.5 dB              ← ACCEPTABLE
SWR 3.0:1 → 6.0 dB              ← MARGINAL, tune antenna
```

### Link Budget
```
Path Loss (dB) = 32.45 + 20log10(f_MHz) + 20log10(dist_km)
  146 MHz, 10km → 106.2 dB

Budget = TxPower(dBm) + TxGain - PathLoss - CableLoss - RxNF - SNR_min
  50W(47dBm) + 6dBi - 106.2 - 2 - 6 - 10 = -71.2 dB → FAIL
  Add 8dBi Yagi → -63.2 dB → marginal, increase height

Negative budget = no link. Redesign before deployment.
```

### Repeater Offsets
```
VHF 146 MHz: +600 kHz   UHF 446 MHz: -5 MHz
CHIRP CSV: Freq,Offset,Duplex,Name,ToneDec,ToneEnc,Mode,Power
```

### DMR Essentials
```
Slot 1/2: TDMA doubles capacity vs FM
TGs: 9=Local, 91=Worldwide EN, 3100=USA, 31330=SW, 4000=DMR-MARC
```

### FT8 / WSJT-X
```
FT8: 8s intervals, 50 Hz BW, LDPC to -20 dB SNR
Freqs: 3.574 (80m), 7.074 (40m), 14.074 (20m) MHz
APRS: 144.39 MHz NA — position beaconing via APRS-IS
```

### AREDN Mesh
```
Bands: 5.8/3.4 GHz, range 1–20+ km
VLAN: Mgmt(1), Trusted(10), IoT(20), Ham Radio(30), Servers(40), Guest(50)
Rule: Default-deny between VLANs; explicit allows only
```
