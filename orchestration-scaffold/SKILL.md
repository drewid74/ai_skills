# Orchestration Scaffold

## Description

Use this when: scaffold a local AI orchestration stack, set up LangGraph supervisor, connect Ollama to OpenCode, configure MCP servers for agent tools, wire OpenCode as the developer interface for a multi-agent system, set up A2A protocol between LangGraph and OpenCode, configure VS Code for agent development, orchestration stack on TrueNAS / Docker Compose homelab, choose between AG2 and CrewAI sub-frameworks, set up agent harness with PreToolUse hooks, define SLIs for an AI orchestration stack, design generator-evaluator pattern for agent output, local inference routing with Qwen3 or Mistral Small.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Developer Interface                                            │
│  OpenCode TUI + VS Code (opencode.ai)                          │
│    ├── MCP Tools → Docker MCP servers                          │
│    │     ├── mcp-filesystem  :8811  (read/write workspace)     │
│    │     └── mcp-custom      :8812  (domain-specific tools)    │
│    └── A2A Protocol → LangGraph Supervisor  :8123              │
│              └── Sub-framework (choose one — see below)        │
│                        ↓                                       │
│               Ollama  :11434                                   │
│               Qwen3:32b (coding) | Mistral-Small-3.1 (fast)   │
└─────────────────────────────────────────────────────────────────┘

Flowise  :3000  — visual prototyping ONLY, not production data path
```

**Model split:**
- Architect / planner agent → cloud model (Claude Sonnet via LiteLLM gateway)
- Coder / executor agent → local Qwen3:32b (data locality, zero cost per call)
- Fast routing / classification → Mistral Small 3.1

---

## Sub-Framework Decision

**Choose one.** Do not use both — three orchestration layers (LangGraph → CrewAI → AG2) is over-abstracted.

| Criterion | Use LangGraph + AG2 | Use LangGraph + CrewAI |
|-----------|---------------------|------------------------|
| Primary workload | Code generation, tool-calling loops, iterative refinement | Role-based delegation (researcher, writer, reviewer) |
| Team mental model | State machine / graph | Crew of specialists |
| Best for | Dev agent, CI runner, code review bot | Document pipeline, research assistant, content workflows |
| Complexity | Lower (AG2 is thin) | Higher (CrewAI adds role scaffolding) |
| Default | **✅ Recommended for dev tooling** | When role semantics add real clarity |

---

## Required: Harness Engineering Checklist

*These are non-negotiable before any production task. Missing any one = not production-safe.*

### 1. PreToolUse Hooks (bypass-proof)

Define in `opencode.json` or a hook plugin. Minimum blocklist:

```python
# hooks/pre_tool_use.py
BLOCKED_PATTERNS = [
    r"\.env$", r"\.pem$", r"\.key$", r"id_rsa", r"id_ed25519",
    r"rm\s+-rf\s+/", r"DROP\s+TABLE", r"DELETE\s+FROM.*WHERE\s+1",
]
BLOCKED_PATHS = ["/etc/passwd", "/etc/shadow", "~/.ssh/"]

def pre_tool_use(tool_name: str, input: dict) -> PreToolResult:
    # Block secrets and destructive patterns regardless of model reasoning
    ...
```

Hooks enforce constraints. AGENTS.md rules are advice the model can reason around. They are not equivalent.

### 2. Loop Termination (all three required)

```yaml
# docker-compose.yml — langgraph-supervisor service
environment:
  MAX_TURNS: "25"           # hard turn limit per task
  TASK_TIMEOUT_SEC: "300"   # wall-clock timeout
  LOOP_DETECT_WINDOW: "3"   # same action N times → terminate
```

An agent without a step budget is a billing incident. Log which termination condition fired for every completed session.

### 3. Generator-Evaluator Separation

Never let an agent grade its own output.

```
Generator:   produces the artifact (code, PR, response)
Evaluator:   grades against predetermined criteria
             — separate agent, separate context
             — criteria defined before generation started
             — does NOT receive the generator's reasoning trace
```

Minimum eval suite per harness run:
- `task_completion_rate`: % tasks completed without escalation
- `error_rate`: % runs ending in unhandled exception
- `cost_per_task`: mean + p95 token cost
- `escalation_rate`: % tasks hitting human-in-loop gate

### 4. State Handoff Contract

When LangGraph supervisor spawns an OpenCode task via A2A, it MUST pass:

```json
{
  "session_id": "<uuid>",
  "branch": "agent/<issue-id>",
  "workspace_dir": "/tmp/workspace-<issue-id>",
  "progress_file": "/tmp/workspace-<issue-id>/progress.md",
  "files_modified": [],
  "in_scope": ["src/", "tests/"],
  "out_of_scope": [".env", "infra/", "*.pem"],
  "max_turns": 20
}
```

### 5. AGENTS.md (≤ 100 lines, table-of-contents only)

```markdown
# AGENTS.md

## System of Record
→ docs/architecture/overview.md
→ docs/conventions/code-style.md
→ docs/operations/runbook.md

## Prohibited Actions (enforced by hook — listed here for visibility)
- Do not write to .env, *.pem, *.key, id_*
- Do not run destructive patterns outside workspace
- Do not modify files in out_of_scope list

## Escalate When
- Three consecutive failed attempts on same task
- Any write to production systems
- Unsure of scope — ask, don't guess
```

Depth lives in `docs/`. Progressive disclosure: agents navigate to deeper docs as needed.

---

## OpenCode Configuration

### `opencode.json`

```json
{
  "model": "claude-sonnet-4-5",
  "mcp": {
    "filesystem": {
      "type": "local",
      "command": "docker",
      "args": ["run", "--rm", "-v", "${workspace}:/workspace",
               "mcp-filesystem:latest"],
      "env": { "WORKSPACE_DIR": "${workspace}" }
    },
    "custom-tools": {
      "type": "http",
      "url": "http://localhost:8812/mcp"
    },
    "langgraph": {
      "type": "http",
      "url": "http://localhost:8123/mcp"
    }
  },
  "agents": {
    "default": ".opencode/agents/orchestrator.md"
  }
}
```

### `.opencode/agents/orchestrator.md`

```markdown
---
mode: primary
model: claude-sonnet-4-5
description: Orchestration coordinator — plans tasks, delegates to LangGraph, validates results
tools:
  - mcp:filesystem
  - mcp:custom-tools
  - mcp:langgraph
---

You are the orchestration coordinator. You plan tasks and delegate execution to the LangGraph supervisor.

Rules:
- Never execute code directly — delegate to LangGraph via the `langgraph` MCP tool
- Validate all outputs from sub-agents before reporting completion
- Follow the state handoff contract when spawning tasks
- Read progress.md before taking any action on a resumed task
```

### `.opencode/agents/coder.md`

```markdown
---
mode: subagent
model: ollama/qwen3:32b
description: Code executor — implements code changes, runs tests, reports results
tools:
  - mcp:filesystem
  - bash
---

You are the code executor. You implement exactly what the orchestrator specifies.

Rules:
- Stay in scope (in_scope list from handoff contract)
- Write progress.md after each significant action
- Run tests before reporting completion
- If tests fail 3 times, escalate — do not continue guessing
```

---

## Docker Compose

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes:
      - ollama_models:/root/.ollama
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  langgraph-supervisor:
    build: ./langgraph
    ports: ["8123:8123"]
    environment:
      OLLAMA_URL: http://ollama:11434
      LITELLM_URL: http://litellm:4000         # cloud model gateway
      MAX_TURNS: "25"
      TASK_TIMEOUT_SEC: "300"
      LOOP_DETECT_WINDOW: "3"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8123/health"]
      interval: 15s
      timeout: 5s
      retries: 3
    depends_on:
      ollama:
        condition: service_healthy

  mcp-filesystem:
    image: mcp/filesystem:latest
    ports: ["8811:8811"]
    volumes:
      - workspace:/workspace:rw
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8811/health"]
      interval: 15s

  mcp-custom-tools:
    build: ./mcp-tools
    ports: ["8812:8812"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8812/health"]
      interval: 15s

  flowise:
    image: flowiseai/flowise:latest
    ports: ["3000:3000"]
    volumes:
      - flowise_data:/root/.flowise
    profiles: ["dev"]          # dev profile only — not started in production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/v1/ping"]
      interval: 30s

  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports: ["3001:3000"]
    volumes:
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
      - grafana_data:/var/lib/grafana

  loki:
    image: grafana/loki:latest
    ports: ["3100:3100"]
    volumes:
      - ./monitoring/loki-config.yml:/etc/loki/local-config.yaml:ro
      - loki_data:/loki

volumes:
  ollama_models:
  workspace:
  flowise_data:
  prometheus_data:
  grafana_data:
  loki_data:
```

---

## SRE: SLIs, Alerts, Runbooks

### SLIs (define before going live)

```promql
# Task completion rate
rate(orchestration_tasks_total{status="complete"}[5m])
/ rate(orchestration_tasks_total[5m])

# LangGraph supervisor p99 latency
histogram_quantile(0.99,
  rate(langgraph_task_duration_seconds_bucket[5m])
)

# Ollama inference error rate
rate(ollama_requests_total{status=~"5.."}[5m])
/ rate(ollama_requests_total[5m])

# Agent loop termination rate (should stay low)
rate(agent_loop_terminations_total{reason="max_turns"}[1h])
```

### Alerts

```yaml
# monitoring/alerts.yml
groups:
  - name: orchestration
    rules:
      - alert: TaskCompletionRateLow
        expr: |
          rate(orchestration_tasks_total{status="complete"}[10m])
          / rate(orchestration_tasks_total[10m]) < 0.80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Task completion below 80%"
          runbook: "docs/operations/runbook.md#task-completion-low"

      - alert: OllamaHighErrorRate
        expr: |
          rate(ollama_requests_total{status=~"5.."}[5m])
          / rate(ollama_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Ollama error rate above 5%"
          runbook: "docs/operations/runbook.md#ollama-errors"

      - alert: AgentLoopRunaway
        expr: rate(agent_loop_terminations_total{reason="max_turns"}[1h]) > 0.1
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "More than 10% of agents hitting max_turns limit"
          runbook: "docs/operations/runbook.md#loop-runaway"
```

**Rules:**
- Alert only on user-facing impact — not CPU/memory thresholds
- Every alert needs `for:`, `severity:`, and `runbook:` annotation
- Tail-sample traces: 100% errors, 1% success
- Dashboards provisioned from git — never manual Grafana UI

### Runbook Template

```markdown
# Runbook: <Alert Name>

## Symptom
<What the user sees>

## Immediate Mitigation
```bash
# Copy-paste commands
docker compose restart langgraph-supervisor
```

## Investigation
```bash
# Logs
docker compose logs langgraph-supervisor --tail=100
```

## Root Cause Categories
- [ ] Ollama OOM → check `docker stats ollama`
- [ ] Model not loaded → `curl localhost:11434/api/tags`
- [ ] Loop runaway → check `agent_loop_terminations_total` metric

## Escalate If
<Condition under which to wake someone up>
```

---

## A2A Integration (LangGraph → OpenCode)

```python
# langgraph/nodes/opencode_node.py
import httpx
from typing import TypedDict

class AgentTask(TypedDict):
    session_id: str
    branch: str
    workspace_dir: str
    progress_file: str
    files_modified: list[str]
    in_scope: list[str]
    out_of_scope: list[str]
    max_turns: int
    instruction: str

async def call_opencode(task: AgentTask) -> dict:
    """Delegate a task to OpenCode via A2A protocol."""
    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(
            "http://localhost:28482/a2a/tasks/send",  # a2a-opencode adapter
            json={
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": task["instruction"]}],
                },
                "metadata": {k: v for k, v in task.items() if k != "instruction"},
            }
        )
        response.raise_for_status()
        return response.json()
```

Reference: `github.com/shashikanth-gs/a2a-opencode`

---

## VS Code Integration

### Recommended Extensions
- `ms-vscode.remote-containers` — run OpenCode sessions inside devcontainer
- `ms-vscode.docker` — inspect running stack containers
- `grafana.vscode-jsonnet` — edit dashboard JSON/Jsonnet provisioning files
- `redhat.vscode-yaml` — docker-compose and prometheus config validation

### `.vscode/tasks.json`

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start orchestration stack",
      "type": "shell",
      "command": "docker compose up -d ollama langgraph-supervisor mcp-filesystem mcp-custom-tools prometheus grafana loki",
      "group": "build"
    },
    {
      "label": "Start with Flowise (dev)",
      "type": "shell",
      "command": "docker compose --profile dev up -d",
      "group": "build"
    },
    {
      "label": "Tail agent logs",
      "type": "shell",
      "command": "docker compose logs -f langgraph-supervisor mcp-custom-tools",
      "isBackground": true
    },
    {
      "label": "Open Grafana",
      "type": "shell",
      "command": "start http://localhost:3001",
      "group": "test"
    }
  ]
}
```

### `.vscode/launch.json` (attach to LangGraph)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Attach to LangGraph Supervisor",
      "type": "python",
      "request": "attach",
      "connect": { "host": "localhost", "port": 5678 },
      "pathMappings": [
        { "localRoot": "${workspaceFolder}/langgraph", "remoteRoot": "/app" }
      ]
    }
  ]
}
```

---

## Security Checklist

- [ ] PreToolUse hook blocks secrets files and destructive patterns
- [ ] MCP servers with write operations require API key (`hmac.compare_digest`)
- [ ] Agent subprocess env is explicit allowlist — never `inherit=True`
- [ ] `out_of_scope` list in every handoff contract includes `.env`, `*.pem`, `*.key`
- [ ] Flowise behind authentication when `dev` profile is active
- [ ] LiteLLM virtual key per agent — budget-capped, not shared master key
- [ ] Secret detection in PostToolUse hook before logging tool outputs

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Three orchestration layers (LangGraph + CrewAI + AG2) | Debugging impossible; latency compounds | Choose one sub-framework |
| Flowise in production data path | Non-reproducible behavior, hard to test | Flowise is dev/prototyping only (`profiles: ["dev"]`) |
| No `max_turns` on LangGraph nodes | Runaway agent burns tokens until timeout | Set `MAX_TURNS` env var; log termination reason |
| Single MCP server for all tools | One restart takes down all tools | One MCP server per domain |
| AGENTS.md as the only constraint layer | Model reasons around "prohibited" rules | PreToolUse hooks for anything critical |
| Self-evaluation | Agent always reports success | Separate Evaluator agent |
| Progress file not written | Context reset = full restart from zero | Coder agent writes `progress.md` after each action |
| Dashboards created in Grafana UI | Lost on container rebuild | Provision from `monitoring/grafana/dashboards/*.json` in git |

---

## References

- OpenCode docs: https://opencode.ai/docs
- OpenCode agents: https://opencode.ai/docs/agents
- OpenCode MCP: https://opencode.ai/docs/mcp-servers
- A2A adapter: https://github.com/shashikanth-gs/a2a-opencode
- LangGraph: https://langchain-ai.github.io/langgraph/
- AG2 (AutoGen successor): https://ag2.ai/docs
- CrewAI: https://docs.crewai.com
- Ollama: https://ollama.com/library
- FastMCP: https://github.com/jlowin/fastmcp
