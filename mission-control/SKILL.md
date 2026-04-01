---
name: Mission Control
description: Meta-agent orchestrator consolidating project orchestration, sequential reasoning, and RF calculations. Routes complex tasks to specialized agents, decomposes work via DAG, resolves conflicts with evidence-based arbitration, and provides real-time progress tracking.
triggers:
  - "delegate this across agents"
  - "I need to orchestrate multiple tasks"
  - "break this down into parallel work"
  - "coordinate these systems"
  - "RF calculation needed" OR "antenna design" OR "ham radio"
  - "decide between X and Y technologies"
  - "resolve disagreement from parallel agents"
  - "show progress on my complex project"
tags: ["orchestration", "multi-agent", "reasoning", "RF-calculations", "ham-radio"]
author: Claude Code
---

# Mission Control: Meta-Agent Orchestrator & RF Reference

Mission Control is the executive layer above isolated agents. It handles **task decomposition into DAGs, cost-aware delegation, conflict resolution, reasoning audits, and RF calculations**. The WHY: complex problems need parallel work + centralized conflict resolution + audit trails for debugging.

## Core Pattern 1: Multi-Agent Router

**WHY**: Not all tasks fit one agent. Router analyzes intent and keyword patterns to delegate to the right specialist (orchestrator, reasoner, RF-calculator, database-advisor, etc.).

```python
# Pseudo-code for intent analysis routing
ROUTER_KEYWORDS = {
    "orchestrator": ["delegate", "coordinate", "parallel", "DAG", "state", "checkpoint"],
    "reasoner": ["why", "decision", "root cause", "trade-off", "analysis", "matrix"],
    "rf_calculator": ["antenna", "RF", "coax", "SWR", "link budget", "repeater", "CHIRP", "DMR"],
    "tech_advisor": ["database", "framework", "hosting", "architecture", "choose between"],
    "conflict_resolver": ["contradiction", "disagree", "conflicting", "merge results"]
}

def route_task(user_prompt):
    """Analyze intent and route to appropriate agent(s)."""
    matched_agents = []
    for agent, keywords in ROUTER_KEYWORDS.items():
        if any(kw in user_prompt.lower() for kw in keywords):
            matched_agents.append(agent)

    # Execute matched agents in parallel if independent
    # Otherwise sequence by dependencies
    return execute_agents(matched_agents, user_prompt)
```

**Example workflow**: "Coordinate antenna setup and link budget calculations for a repeater" → routes to both orchestrator (coordinate) + RF calculator (antenna, link budget).

## Core Pattern 2: DAG Task Decomposition

**WHY**: Sequential thinking is slow. DAG (directed acyclic graph) identifies parallelizable tasks and eliminates artificial dependencies.

```
Task: "Deploy new architecture with RF link"
│
├─ [PARALLEL] Analyze RF requirements → Calculate antenna placement → Design AREDN mesh
│              └─ Feeds into: Link budget validation
├─ [PARALLEL] Compare database options → Select framework → Design VLANs
│              └─ Feeds into: Integration test plan
├─ [SEQUENTIAL AFTER ABOVE] Create conflict resolution matrix (parallel results might contradict)
└─ [SEQUENTIAL LAST] Execute with fallback strategy
```

Task decomposition uses **4-step deconstruction**:
1. **Identify subtasks**: Parse user request for implicit parallel work
2. **Map dependencies**: Which tasks block others? Which are independent?
3. **Assign agents**: Route each subtask to the appropriate specialist
4. **Aggregate results**: Merge outputs, detect conflicts (see Pattern 3)

### Task Registry
Each task in the DAG is formally tracked with: **state** (In-Progress, Blocked, Completed), **assigned agent**, **dependencies** (blocking tasks), and **completion criteria** (acceptance tests). Registry enables cross-agent handoff auditing and prevents task loss in complex workflows.

## Core Pattern 3: Cost-Aware Delegation

**WHY**: API calls are expensive. Use local tools/skills when confidence > threshold; reserve expensive APIs for disambiguation.

```
Cost matrix:
  Local reasoning tree (high-confidence): Cost = 0, latency = instant
  Local RF calculator (formula-based): Cost = 0, latency = instant
  Expert API call (GPT-4, domain model): Cost = $0.03, latency = 2-5s

Decision rule:
  IF task = "antenna design" AND confidence(local_formula) > 0.90
    THEN use local dipole/yagi calculator
  ELSE IF task = "choose database" AND confidence < 0.70
    THEN escalate to expert decision framework API
```

**Example**: "Should I use PostgreSQL or MongoDB for this real-time RF data?" → First check local decision matrix (90% of cases covered). If ambiguous, escalate with cost awareness.

## Core Pattern 4: Conflict Resolver

**WHY**: Parallel agents can produce contradictory outputs. Evidence-based arbitration prevents confusion.

```
Input:
  Agent A: "Use Postgres (ACID, structured data)"
  Agent B: "Use Redis (fast, real-time)"

Conflict Analysis:
  - Do they conflict on same decision? YES (database choice)
  - Priority: Data durability vs. speed?
  - User context: "RF monitoring system with 100ms latency requirement"

Evidence Scoring:
  Agent A (Postgres): +0.6 durability, +0.3 latency → Total 0.9
  Agent B (Redis): +0.9 latency, -0.5 durability → Total 0.4

Resolution: Suggest hybrid (Redis cache + Postgres persistence)
```

### No-Loops Anti-Pattern (Operational Rule)
If agents pass a task back-and-forth more than twice (A→B→A→B), HALT immediately and escalate to human. This breaks infinite delegation cycles where neither agent claims ownership. Flag blockers, show task history, and request human decision on next steps.

### Root Cause Analysis (RCA) Formal Steps
When debugging failures: **(1) Observation** — what is the error/failure?; **(2) History** — what changed recently (code, config, environment)?; **(3) Hypothesis** — list 3 potential causes ranked by probability; **(4) Isolation** — design specific test to prove/disprove each hypothesis. Prevents guesswork and speeds resolution.

## Core Pattern 5: Reasoning Audit Trail

**WHY**: Debugging complex multi-agent workflows requires full chain-of-thought. Black-box outputs aren't acceptable.

Explicit reasoning steps strengthen audit quality: **(1) Branching** — explore Path A (optimal/complex) vs Path B (fast/simple) with trade-off analysis; **(2) Validation** — test logic against edge cases and corner scenarios; **(3) Uncertainties/Assumptions** — formally track unknowns and constraints in output for transparency.

Log structure:
```yaml
audit_log:
  task_id: "deploy-rf-system-2024"
  timestamp: "2024-03-15T14:32:00Z"

  decomposition:
    - subtask: "antenna_design"
      agent: "rf_calculator"
      status: "complete"
      reasoning: "Used dipole formula for 2m band"
      result: "53.5cm antenna, 50-ohm match"

  delegation:
    - agent: "orchestrator"
      cost: 0
      confidence: 0.95
      reason: "Task matches exact orchestration pattern"

  conflicts:
    - contradiction: "Frequency offset disagreement"
      resolution: "Evidence scoring favored FM standard +5.0 MHz"

  checkpoints:
    - "antenna design validated against SWR model"
    - "AREDN mesh topology verified for reachability"
    - "all subtasks complete, ready for hardware"
```

## Core Pattern 6: Decision Framework Library

**WHY**: Recurring tech choices (database, framework, hosting) deserve pre-built decision matrices to cut analysis time.

### Decision Matrix: Database Selection
```
Criteria: Data structure, latency, durability, scaling, cost

PostgreSQL:  struct(1.0), latency(0.6), durability(1.0), scale(0.8), cost(0.7) → 0.82
MongoDB:     struct(0.4), latency(0.8), durability(0.6), scale(0.9), cost(0.6) → 0.66
Redis:       struct(0.2), latency(1.0), durability(0.3), scale(0.9), cost(0.8) → 0.66
TimescaleDB: struct(0.9), latency(0.9), durability(0.9), scale(0.8), cost(0.7) → 0.84 ← Best for RF monitoring
```

For RF monitoring systems specifically, **TimescaleDB** outperforms: handles time-series RF data, maintains schema integrity, and achieves low-latency queries on large datasets.

## Module 7: RF Calculations & Ham Radio Reference

**WHY**: RF engineering requires precise formulas. Mission Control includes a calculator for antenna design, link budgets, coax loss, and repeater coordination. ALL formulas preserved for operators.

### Dipole Antenna (Half-Wave)
```
Length (meters) = 142.65 / frequency_MHz
  Example: 2m band (146 MHz) → 142.65 / 146 = 0.977m ≈ 97.7cm (matched pair)
  WHY: Half-wavelength resonance produces ~50 ohm impedance with ~6 dBi gain
```

### Vertical Antenna (Quarter-Wave)
```
Length (meters) = 71.33 / frequency_MHz
  Example: 2m band (146 MHz) → 71.33 / 146 = 0.489m ≈ 49cm
  WHY: Quarter-wave uses ground plane for image, omni-directional pattern, lower angle of radiation
```

### Yagi Antenna Gain
```
Approximate gain (dBi) = 10 + 8.5 * log10(f_MHz)
  2m band (146 MHz): 10 + 8.5 * log10(146) ≈ 32.6 dBi
  70cm band (446 MHz): 10 + 8.5 * log10(446) ≈ 37.1 dBi
  WHY: More elements, closer spacing = higher directivity and gain, but narrower beam
```

### Coax Cable Loss
```
Loss (dB) = (length_ft / 100) * loss_per_100ft
  RG-58 @ 146 MHz: 4.6 dB/100ft
  RG-8X @ 146 MHz: 2.7 dB/100ft
  LMR-400 @ 146 MHz: 1.4 dB/100ft

Example: 50ft RG-8X at 146 MHz → (50/100) * 2.7 = 1.35 dB loss
  WHY: Thicker cable (larger diameter conductor) = lower resistance, less loss
```

### SWR & Return Loss
```
SWR = (1 + ρ) / (1 - ρ)  where ρ = reflection coefficient
Return Loss (dB) = -20 * log10(ρ)

SWR 1.5:1 → ρ = 0.2 → Return Loss = 13.98 dB (GOOD)
SWR 2.0:1 → ρ = 0.33 → Return Loss = 9.54 dB (ACCEPTABLE)
SWR 3.0:1 → ρ = 0.5 → Return Loss = 6.02 dB (MARGINAL, tune antenna)

WHY: SWR measures mismatch between antenna impedance and transmission line. Mismatch reflects power.
```

### Link Budget & Path Loss
```
Path Loss (dB) = 32.45 + 20*log10(f_MHz) + 20*log10(distance_km)
  VHF (146 MHz), 10km: 32.45 + 20*log10(146) + 20*log10(10) = 106.2 dB

Link Budget = Tx Power (dBm) + Tx Gain (dBi) - Path Loss (dB) - Cable Loss (dB) - Rx Noise Figure (dB) - Required SNR (dB)
  50W TX (47 dBm) + 6 dBi Tx antenna - 106.2 dB path - 2 dB cable - 6 dB RX NF - 10 dB SNR
  = 47 + 6 - 106.2 - 2 - 6 - 10 = -71.2 dB (FAIL: budget negative)
  → Add Yagi (+8 dBi) → -71.2 + 8 = -63.2 dB (still marginal)

WHY: Link budget ensures receiver has enough SNR. Negative budget = no signal, redesign needed.
```

### Repeater Offset & Duplexing
```
VHF Repeater (146 MHz band):
  Input: 146.52 MHz, Output: 147.12 MHz (offset +600 kHz)
  WHY: Duplexer isolates RX and TX antennas; Rx on lower freq, Tx on higher

70cm Repeater (446 MHz band):
  Input: 447.00 MHz, Output: 442.00 MHz (offset -5 MHz)
  WHY: Positive offset (VHF) vs negative offset (UHF) convention

CHIRP CSV format for programming (supports ICOM, Yaesu, Kenwood, Baofeng):
  Freq, Offset, Duplex, Name, ToneDec, ToneEnc, Mode, Power, Skip, Comment
  146520000, 600000, +, "W5XYZ Rpt", 141.3, 141.3, FM, High, , "Local repeater"

Radio Manufacturer Programming: CHIRP is the universal programmer for ICOM handhelds (IC-2300H, ID-51A), Yaesu (FT-7900, FT-891), Kenwood (TM-D710), and Baofeng (UV-5R). Download .csv codeplugs, edit, and upload to radio.
```

### DMR Codeplug Essentials
```
Slot 1: Control & voice (1-30s)  [TDMA divides time into 2 slots]
Slot 2: Voice (simultaneous with Slot 1)

Talkgroup (TG):
  9: Local
  3100: Germany
  3120: Europe
  4000: DMR-MARC
  91: Worldwide English

Zone: Group of channels (e.g., "Local", "Regional", "DMR-MARC")
Contact: TG definition (name, ID, type)
RX Group List: Which TGs to monitor on a channel

WHY: DMR TDMA doubles capacity vs analog FM. Codeplug defines frequency, TG, zone, encryption.
```

### AREDN Mesh Networking (RF over IP)
```
AREDN = Amateur Radio Emergency Data Network
  Uses 5.8/3.4 GHz ISM bands (regulation-dependent)
  Point-to-point links 1-20+ km
  Mesh topology = self-healing, multi-hop redundancy

VLAN Planning Table (Structured Design):
  VLAN 1:  Management (switches, controllers)       | Default-deny outbound
  VLAN 10: Trusted (operator workstations)          | Full internal access
  VLAN 20: IoT (sensors, logging devices)           | No outbound to LAN
  VLAN 30: Ham Radio (transceivers, modems)         | Explicit routing only
  VLAN 40: Servers (data, repeater controller)      | DMZ protection
  VLAN 50: Guest (temporary, sandboxed)             | No internal access
  VLAN 60: DMZ (external links, firewall rules)     | Strict ingress/egress

Firewall Rules Principles:
  (1) Default-deny between all VLANs (no cross-VLAN traffic unless explicitly allowed)
  (2) IoT VLAN (20) has no outbound access to LAN (except DNS + time)
  (3) Explicit allow rules for cross-VLAN services (e.g., 30→40 for radio logs to server)
  (4) Management VLAN (1) isolated: no inbound from other VLANs

Firewall design for ham shack VLAN:
  WAN Interface: Isolated from mesh
  Mesh VLAN: 10.0.0.0/8 (AREDN standard)
  Shack Devices: 192.168.1.0/24 (separate from mesh)
  Rules: Mesh subnet <-> Shack via explicit routes only

WHY: Isolation prevents mesh traffic from flooding local networks. Explicit routing = operator control.

VLAN tagging example (Ubiquiti):
  Port 1: Trunk (carries mesh + shack VLANs)
  Port 2-4: Shack devices (access VLAN 2)
  VLAN 1: Mesh (tagged)
  VLAN 2: Shack (untagged on local ports)

DNS Architecture (Local + Cloud):
  Pi-hole / AdGuard Home: Local DNS + ad-blocking at network edge
  Unbound: Recursive resolver (authoritative + caching layer)
  Split-horizon DNS: Different responses for internal vs external queries
  DoH/DoT forwarding: DNS-over-HTTPS/TLS to upstream providers (privacy-first)
  Failover: Multiple DNS servers, automatic switchover on provider outage
```

### FT8 & WSJT-X Basics
```
FT8 = "Franke-Taylor design, 8-second intervals"
  Symbol rate: 6.25 baud (slow, robust)
  Bandwidth: 50 Hz (narrow, spectrum-efficient)
  Decoding: Uses LDPC error correction (can decode at -20 dB SNR)
  QSO cycle: Each side sends 8 seconds on, 8 seconds off

WSJT-X workflow:
  1. Tune RX to band frequency (e.g., 3574 kHz on 80m CW/FT8 section)
  2. Enable RX, watch waterfall for signals
  3. Click decode area to respond to a call
  4. Enter call sign, grid, power, name (MEPT)
  5. TX on next 8-second window

WHY: FT8 enables QSOs in poor propagation. LDPC codes decode below noise floor.

APRS = Automatic Packet Reporting System
  Beacon TX: Position, altitude, speed (via APRS-IS or radio)
  Digipeater: Receives beacon, re-transmits to extend range
  Typical: 144.39 MHz (North America)
  Format: !DDMM.SSN/DDDMM.SEN{Data (altitude, course, speed)

WHY: APRS creates real-time position map without cellular. Great for emergency comms.

Advanced Digital Modes:
  D-STAR: Digital voice + data, 5 kHz bandwidth, linked repeaters (Icom)
  Fusion (Yaesu): Digital voice codec, lower latency, easier QSY than D-STAR
  Winlink/VARA HF: Packet email via HF, tolerates poor propagation, emergency comms
  AllStar/Echolink: VoIP linking to internet repeaters, extends coverage globally
```

## Usage Examples

### Example 1: Orchestrate Multi-System RF Deployment
```
User: "I need to design a repeater system with RF link budget, AREDN mesh, and DMR codeplug setup."

Mission Control routing:
  1. Route to RF calculator: antenna design, link budget, cable loss
  2. Route to orchestrator: parallel RF design + AREDN topology + codeplug planning
  3. Aggregate: Check for conflicts (frequency coordination, power limits)
  4. Audit trail: Log each calculation step, link budget margin, mesh reachability

Output: Antenna specifications, link budget validation, AREDN topology diagram, DMR codeplug CSV template
```

### Example 2: Resolve Contradictory Agent Outputs
```
Agent A: "Use dipole for mobile antenna (omnidirectional, simple)"
Agent B: "Use Yagi for mobile antenna (higher gain, range +10km)"

Conflict resolver:
  Context: "Mobile truck deployment, 1-hour setup, range 50km minimum"
  Scoring: Dipole (simplicity +1, range -1 @ 50km = net 0)
           Yagi (setup complexity -1, range +2 = net +1)
  Resolution: "Recommend Yagi mounted on roof rack. +10km range critical for your 50km minimum. Setup is 30 min with quick-mount bracket."
  Audit: Evidence-based arbitration logged
```

### Example 3: Cost-Aware Decision
```
User: "Should I use Redis or PostgreSQL for RT RF data logging?"

Router detects: database selection → consult decision framework library

Local decision matrix (cost = $0, latency = instant):
  TimescaleDB: 0.84 (best, time-series optimized)
  PostgreSQL: 0.82 (good, structured)
  Redis: 0.66 (fast but ephemeral)

Recommendation: TimescaleDB. No need for expensive API call; local matrix covers this case.
Cost saved: $0.03 per query, instant response. Confidence: 0.95.
```

### Example 4: Daily Stand-up (Compound Operation)
Summarize progress of all active agents: list each task with status (In-Progress/Blocked/Completed), assigned agent, blockers, and next steps. Present status dashboard showing task counts by state, pending escalations, and RCA work. Identifies stalled work early and triggers human intervention on blocked tasks.

## Why This Pattern Works

1. **DAG decomposition** eliminates sequential bottlenecks; parallel agents finish faster
2. **Cost-aware routing** uses local tools first; escalates only when ambiguity is high
3. **Conflict resolution** with evidence prevents analysis paralysis
4. **Audit trails** make debugging transparent; operators understand every decision
5. **RF calculator** preserves domain expertise (formulas never change) with instant zero-cost lookups
6. **Decision frameworks** encode domain knowledge so recurring tech choices are fast

Mission Control is your **executive layer**: orchestrate parallel work, audit everything, reason transparently, and resolve conflicts with evidence.

---
**Last updated**: 2026-04-01 | **Status**: Production | **Next enhancement**: Add cost tracking dashboard widget
