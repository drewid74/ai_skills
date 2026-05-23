---
name: harness-engineering
description: "Use this when: design an agent harness, what goes in AGENTS.md, my agent keeps doing the wrong things, workspace isolation for agents, agent ignores my rules, structure agent instructions, prevent agent drift, agent keeps breaking things, CI for agent PRs, my agent breaks production, multi-agent coordination, AGENTS.md structure, agent hooks, PreToolUse hook, PostToolUse hook, agent entropy, blast radius control, agent loop termination, agent state persistence, checkpoint resume, generator evaluator pattern, eval harness CI gate, authority tier model, Symphony harness, WORKFLOW.md design, harness vs agent loop, minimum viable harness, production harness, agent guardrails, agent permission model, tool registry, execution context, harness engineering checklist, context window engineering, mechanical enforcement linters hooks, agent observability tracing, cost controls circuit breaker, human in the loop escalation"
---

# Harness Engineering


## Core Insight

**An agent harness is everything that surrounds the model.** The model generates text. The harness decides:
- What the model sees (context management)
- What it can do (tool registry + permission model)
- When it must stop (termination controls)
- What is enforced regardless of what the model decides (hooks, linters)
- What happens when things go wrong (state recovery, escalation, kill switch)

The critical distinction: **AGENTS.md rules are advice the model can reason away. Hooks are constraints that always fire.** A PreToolUse hook blocking `.env` edits cannot be overridden by the model's reasoning. A CLAUDE.md rule saying "don't edit .env" can be.

---

## Four-Layer Architecture

*Source: WOWCharlotte/harness-skills community spec, validated across 10 production sources.*

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Multi-Agent System                                  │
│ Agent Spawn / State Handoff / Collaboration Patterns        │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Plugin & Hooks                                      │
│ PreToolUse Hook / PostToolUse Hook / Plugin Lifecycle       │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Tool System                                         │
│ Tool Registry / Permission Model / Execution Context         │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Harness Core                                        │
│ Agent Loop / Session Management / Config & Permissions      │
└─────────────────────────────────────────────────────────────┘
         ↕                                      ↕
  LLM API (Claude/LiteLLM)          External Tools
  (Filesystem, Bash, Web, MCP, etc.)
```

### Layer 1: Harness Core

**Agent Loop** — the loop itself (`while (!done) { LLM → tools → loop }`) is not the harness. The harness controls the loop:
- `max_turns` hard limit (not optional)
- Timeout enforcement (wall-clock, not just turns)
- Loop detection: same action repeated without progress → terminate
- Forced termination paths with state preservation

**Session Manager**
```
Session {
  id:         UUID
  messages:   Message[]        # immutable, appended only
  metadata:   Map<str, any>
  workspace:  IsolatedDir      # per-session working directory
  created_at: DateTime
  updated_at: DateTime
}
```
- Sessions serialize to disk and are resumable
- Each session has isolated working directory, env vars, and tool cache
- Message history: ToolResult appended after each tool execution

**Config & Permissions**
- Three tiers: `ReadOnly` / `WorkspaceWrite` / `DangerFullAccess`
- Least-privilege default: start minimal, elevate only with confirmation gate
- All config version-controlled alongside code

**Layer 1 Engineering Checklist**
- [ ] Agent loop has explicit termination conditions, cannot loop infinitely
- [ ] Session message history is serializable and resumable
- [ ] Permission model covers all tools with no gaps
- [ ] LLM call failures have retry with exponential backoff
- [ ] Tool execution timeouts can be forcibly terminated

---

### Layer 2: Tool System

**Tool Registry**
```
ToolSpec {
  name:                 string
  description:          string        # LLM sees this — be precise
  input_schema:         JSON Schema   # LLM sees this — be complete
  required_permission:  PermissionMode
  execute:              fn(input: Value) → Result<Value>
}
```
- Declarative registration: tools declare metadata, discovered at runtime
- Schema-driven validation: LLM sees `input_schema`, never implementation code
- Three categories: built-in (filesystem/bash/network), MCP (external services), user-defined

**Tool Executor**
```
trait ToolExecutor {
  async fn execute(
    spec:  &ToolSpec,
    input: Value,
    ctx:   &ExecutionContext
  ) → Result<Value>
}
```
- Executor is pluggable: same ToolSpec can have different backends (local vs. container)
- Dangerous tools execute in subprocess/container for isolation
- Tool results are cacheable by input for idempotency

**Execution Context** — per-invocation context containing:
- Working directory (workspace-scoped)
- Env vars (explicit allowlist only — never parent `os.environ`)
- Tool call audit log
- Session-level permission grants

**Layer 2 Engineering Checklist**
- [ ] Tool description gives LLM enough context to choose correctly
- [ ] `input_schema` includes required field validation — invalid input → structured error, not crash
- [ ] Bash tool has timeout limit — broken commands cannot freeze the system
- [ ] Dangerous tools execute in subprocess/container
- [ ] Registered-only tools — no dynamic tool discovery in production

---

### Layer 3: Plugins & Hooks

**The enforcement layer.** Intercepts every tool call at two points regardless of what the model decided.

**PreToolUse Hook** (blocking)
```
PreToolUseHook {
  tool_name: string
  input:     Value
  → Block(reason: string) | Allow | Modify(new_input: Value)
}
```
Minimum production requirements:
- Block writes to secrets files (`.env`, `*.pem`, `*.key`, `id_*`)
- Block destructive patterns (`rm -rf /`, `DROP TABLE`, production DB writes)
- Validate parameter schemas — schema mismatch → structured error
- Detect prompt injection in tool inputs
- Rate limiting per tool per session

**PostToolUse Hook**
```
PostToolUseHook {
  tool_name: string
  input:     Value
  output:    Value
  → Log | InjectContext(str) | Raise(error: Value)
}
```
Responsibilities:
- Validate output schema
- Detect silent failures (3-15% of tool calls fail without raising)
- Inject additional context into model's next message
- Write structured audit log entry

**Additional lifecycle hooks:**
- `SessionStart` — inject context, initialize telemetry, load progress files
- `SessionEnd` — persist state, clean up workspace, write summary
- `AfterCompaction` — re-inject critical rules that summarization may have lost
- `OnEscalation` — human handoff with state preservation

**Plugin Lifecycle:**
```
Plugin {
  name:     string
  version:  string
  hooks:    HookSpec[]
  init:     fn(config: PluginConfig) → Result<()>
  shutdown: fn() → Result<()>
}
```

**Layer 3 Engineering Checklist**
- [ ] PreToolUse hook covers all destructive operations
- [ ] Secrets files are on a blocklist — not just documented in AGENTS.md
- [ ] Every tool call produces a structured audit log entry
- [ ] Silent failure detection in PostToolUse (output validation)
- [ ] SessionEnd hook persists state — crash-safe recovery

---

### Layer 4: Multi-Agent System

**Topology patterns:**

**Planner / Executor / Evaluator (most common)**
```
Planner   → breaks goal into atomic tasks, never executes
Executor  → executes one task, never plans, never self-evaluates
Evaluator → grades executor output against predetermined criteria
           never generates the artifact it's evaluating
```
Critical: Evaluator must be a separate agent from the one that generated the output. Self-evaluation produces systematically optimistic results.

**Coordinator / Worker**
```
Coordinator → tracks state, assigns tasks, never executes tools directly
Worker      → executes a specific scoped task, reports result to coordinator
```
Coordinator maintains the plan; workers own atomic units of work.

**Authority Tier Model (Stackbilt pattern)**
```
auto_safe  → merge without human review (doc updates, test additions,
             minor refactors with full test pass)
proposed   → open PR, wait for human approval before merge
blocked    → reject immediately, surface to human, do not attempt
```
Authority tier is determined **deterministically from task metadata** (labels, issue fields) — never from LLM classification of its own work.

**State Handoff Contract**
Spawning agent MUST pass to sub-agent:
- Current working directory and branch
- Progress file path (or inline progress summary)
- List of files already modified
- Test run results
- Explicit scope (files/modules this sub-agent may touch)
- Files/modules out of scope (MUST NOT)

**Layer 4 Engineering Checklist**
- [ ] Evaluator is distinct from generator — same agent cannot grade its own output
- [ ] Authority tier determined from task metadata, not LLM self-assessment
- [ ] State handoff contract explicitly lists in-scope and out-of-scope files
- [ ] Orphaned workspaces are garbage-collected on session end
- [ ] Sub-agent spawn includes explicit max_turns budget

---

## Minimum Viable Harness

**All six required. Missing any one = not production-safe.**

```
1. AGENTS.md / CLAUDE.md (instructions contract)
   — What the agent knows about its environment, constraints, prohibited actions.
   — ~100 lines max. Entry point for progressive disclosure — depth lives in docs/.
   — Version-controlled alongside code. Stale docs are worse than no docs.
   — One per scope (repo root + per-subcomponent as needed).
   — Structure: system of record pointer → prohibited actions → tool guidance → escalation path

2. PreToolUse hook (blocking, bypass-proof)
   — Minimum: block secrets files, block destructive patterns, validate schemas.
   — AGENTS.md rules can be reasoned away. Hooks cannot.
   — Implement before first production task. Not optional.

3. Explicit loop termination
   — max_turns hard limit + wall-clock timeout + loop detection.
   — An agent without a step budget is a billing incident.
   — Log which termination condition fired for every completed session.

4. State persistence mechanism
   — Progress file (agent writes task state after each significant action).
   — git log (work history survives context resets).
   — On recovery: agent reads progress file before any action.
   — Without this, every context boundary = full restart from zero.

5. Output validation before commitment
   — Run tests before committing code.
   — Validate schema before writing to external systems.
   — Check required invariants before closing the issue/task.
   — 3–15% of tool calls fail silently. Validation catches what errors miss.

6. Structured audit log
   — Every tool call: tool name, input, output, duration, hook decisions.
   — Every model decision: reasoning trace (even if abbreviated).
   — Every block: what was blocked, which hook, why.
   — Mandatory for debugging. Required for any compliance posture.
```

---

## AGENTS.md / Knowledge Base Structure

*Source: OpenAI harness engineering blog — field-tested on 1M-line codebase.*

**Do not write a monolith.** A single large AGENTS.md fails in three ways:
1. Context is scarce — it crowds out task, code, and relevant docs
2. When everything is "important," nothing is — agents pattern-match locally instead of navigating
3. It rots instantly — agents can't distinguish stale rules; humans stop maintaining it

**Correct structure:**
```
AGENTS.md  (~100 lines)           ← table of contents only
  - Where to find deeper docs
  - Prohibited actions (hard rules)
  - Tool guidance (which tool for which task)
  - Escalation path (when to stop and ask)

docs/                             ← system of record
  architecture/
    overview.md
    layer-definitions.md
    dependency-rules.md
  conventions/
    code-style.md
    error-handling.md
    testing-strategy.md
  operations/
    deployment.md
    runbook.md
    on-call.md
  decisions/
    YYYY-MM-DD-decision-title.md  ← ADRs
```

**Progressive disclosure**: agents start with the small entry point (AGENTS.md) and navigate to deeper docs as needed. The harness teaches agents *where to look*, not *everything they need to know upfront*.

**Mechanical enforcement**: CI jobs validate that docs/ is up-to-date, cross-linked, and structured correctly. A recurring "doc-gardening" agent scans for stale docs that don't reflect real code behavior and opens fix-up PRs.

---

## Entropy Management (Garbage Collection)

*Source: OpenAI harness engineering, field result: eliminated "AI slop Friday" (20% of eng week).*

Agents replicate patterns that exist in the repo — including uneven or suboptimal ones. Without active management, drift compounds.

**Golden Principles** — opinionated, mechanical rules that keep the codebase legible for future agent runs:
- Prefer shared utility packages over hand-rolled helpers (keeps invariants centralized)
- Parse at the boundary — validate data shapes on entry; never probe "YOLO-style"
- One canonical pattern per problem (if two patterns exist, one should be removed)

**Recurring cleanup process:**
```
Background task runs on schedule:
  1. Scan for deviations from golden principles
  2. Update quality grade (per-module or per-file metric)
  3. Open targeted refactoring PRs (small, reviewable in <1 minute)
  4. Automerge when tests pass + grade improves

Human taste is captured once. Enforced continuously on every line.
```

**Technical debt cadence**: pay continuously in small increments — never let it compound into a painful burst. Quality grade documents give the GC agent a signal; without measurement, GC has no target.

---

## Context Window Engineering

**The harness decides what the model sees at every step.**

**Token budget slots:**
```
System prompt:    ~2,000 tokens   (stable, rarely changes)
Task context:     ~4,000 tokens   (current issue, plan, constraints)
Relevant code:    ~8,000 tokens   (files being worked on)
Tool history:     ~6,000 tokens   (recent tool calls + results)
Docs (retrieved): ~4,000 tokens   (on-demand, progressive disclosure)
Working memory:   remaining       (progress notes, hypotheses)
```

**Compaction triggers** (not ad-hoc — threshold-based):
- Tool history exceeds budget → summarize oldest N entries
- Session exceeds X turns → summarize early session context
- AfterCompaction hook → re-inject: prohibited actions, current branch, progress file path

**Curation rules:**
- Stale tool results pruned from mid-session history
- Docs injected on demand (agent navigates to them), not front-loaded
- AGENTS.md always in system prompt — never pruned
- Progress file re-injected at SessionStart and AfterCompaction

---

## Workspace Isolation

**Per-task workspace required for any concurrent or multi-session harness.**

**Pattern: git worktree per issue**
```bash
# Harness creates isolated workspace for each task
git worktree add ../workspace-${ISSUE_ID} -b agent/${ISSUE_ID}
# Agent works in isolated directory
# Workspace torn down after PR is merged or task is closed
```

**What is isolated per workspace:**
- Git branch (no cross-task contamination)
- Working directory (filesystem changes don't bleed)
- Environment variables (only task-relevant vars passed)
- Log/metric stack (ephemeral; torn down on task complete)
- Running application instance (one per worktree for UI/API validation)

**What is NOT isolated** (shared infrastructure):
- LLM API (shared gateway — cost tracking, not isolation)
- Test databases (use fixtures or test-scoped schemas)
- Package caches (read-only from shared cache — write to workspace copy)

---

## Production vs. Prototype

| Dimension | Prototype | Production Harness |
|---|---|---|
| **Loop control** | `max_turns` only | Budget + timeout + loop detection + circuit breaker |
| **Constraint enforcement** | AGENTS.md rules (LLM-parsed) | Mechanical hooks (always fire, bypass-proof) |
| **State** | In-memory, lost on crash | Checkpoint-resume, cross-session progress files |
| **Tool errors** | Thrown exceptions | Structured error objects; model receives actionable signal |
| **Evaluation** | Self-evaluation | Generator-Evaluator separation; CI-gated eval harness |
| **Observability** | Console logs | Structured traces per step, metric dashboards, regression alerts |
| **Cost** | No controls | Per-request + per-session + daily budgets; 80% alert mandatory |
| **Authority model** | Binary (allowed/not) | Tiered (auto_safe/proposed/blocked), deterministic mapping |
| **Architectural consistency** | Doc-based conventions | Mechanical linters + structural tests + GC agents |
| **Security** | Prompt instructions | Schema validation, input screening, branch isolation, secret detection |
| **Human escalation** | Manual interruption | Defined triggers, escalation paths, kill switch with state preservation |

---

## Evaluation Harness

*The single highest-impact pattern in harness engineering (harness-engineering.ai).*

**Generator-Evaluator Separation:**
```
Generator:  produces the artifact (code, PR, response)
Evaluator:  grades against predetermined criteria
            — MUST be distinct from Generator
            — MUST use criteria defined before generation started
            — MUST NOT be given the generator's reasoning
```

**Eval harness as CI gate:**
- Run on: every model change, every prompt change, every tool schema change, every AGENTS.md change
- Block deployment on regression
- Track eval score over time — catch gradual drift before it compounds
- Eval suite must be owned by humans — agents cannot be the source of truth for their own eval criteria

**Minimum eval suite per harness:**
```
task_completion_rate:    % tasks completed without human escalation
error_rate:              % runs ending in unhandled exception
cost_per_task:           mean + p95 token cost
escalation_rate:         % tasks hitting human-in-loop gate
loop_detection_rate:     % runs terminated by loop detector (should be low)
```

---


## Dev-Island Specific Patterns + Symphony Security

See `./references/dev-island-patterns.md` for: LiteLLM gateway setup, Forgejo two-token model, aiohttp `AF_INET` HTTPS quirk, Redis episode stream schema, LGTM port assignments (Prom 29220, Loki 29221, Tempo 29222, Grafana 29223), workspace isolation pattern, and the Symphony Blast Radius security checklist.

---

## Anti-Patterns

| Pitfall | Symptom | Fix |
|---|---|---|
| AGENTS.md monolith | Agent misses constraints; file rots | ~100 lines max; depth in docs/ |
| Rules as AGENTS.md text | Model reasons around "prohibited" actions | Move to PreToolUse hook |
| No loop termination | Billing incident; agent spins | max_turns + timeout + loop detection — all three |
| Self-evaluation | Agent always reports success | Separate Evaluator agent, never same as Generator |
| Inherited env vars | Secret leaks into agent subprocess | Explicit env dict; MUST NOT list in MUST DO |
| Single Forgejo token | Blast radius = full repo access | Poller token + push token, minimum scope each |
| No progress file | Every context reset = full restart | Agent writes `progress.md` after each significant action |
| Silent tool failures | Bugs appear from nowhere | PostToolUse output validation; 3–15% of calls fail silently |
| Agent generates eval criteria | Agents pass their own tests | Eval criteria defined by humans before generation |
| Tool errors thrown as exceptions | Model receives no actionable signal | Structured error objects returned, not raised |

---

## Reference Sources

| # | Source | Date | Key Contribution |
|---|---|---|---|
| 1 | OpenAI / Ryan Lopopolo — "Harness Engineering" | Feb 2026 | AGENTS.md as ToC, entropy/GC, workspace isolation, progressive disclosure, throughput → merge philosophy |
| 2 | WOWCharlotte/harness-skills community spec | Apr 2026 | 4-layer architecture, engineering checklists, ToolSpec/ExecutionContext schemas |
| 3 | ddhigh.com / Lei Xia | Mar 2026 | 5-layer model, Prompt Engineering vs. Harness Engineering comparison |
| 4 | harness-engineering.ai / Dr. Sarah Chen | Mar 2026 | 6-component framework, failure modes per missing component, Generator-Evaluator as highest-impact pattern |
| 5 | Zylos Research — "Agent Harness Design Patterns" | Mar 2026 | LangChain benchmark: harness change alone lifted task completion 52.8% → 66.5%; Generator-Evaluator from Anthropic |
| 6 | vitthalmirji.com — "Build the Harness, Not the Code" | Feb 2026 | Staff/principal engineer translation; hooks as enforcement vs. CLAUDE.md as suggestions |
| 7 | Gothar Engineering — "Agentic AI in Production" | Mar 2026 | Structural guardrails vs. prompt guardrails; eval harness as CI gate |
| 8 | Stackbilt — "How Do You Trust an AI Agent" | Mar 2026 | Branch-per-task isolation; authority tiers (auto_safe/proposed/blocked) |
| 9 | Anthropic Claude Code Docs — Hooks, AGENTS.md | 2026 | 15 lifecycle events, PreToolUse/PostToolUse intercept model, CLAUDE.md/rules/ layered memory |
| 10 | Fordel Studios — "Production Patterns from the Field" | Apr 2026 | State machine pattern, orchestrator-executor separation, tool wrapper contracts |
