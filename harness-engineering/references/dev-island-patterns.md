# Dev-Island Specific Harness Patterns

Operational patterns specific to the dev-island infrastructure (LiteLLM, Forgejo, LGTM, Redis, ZFS workspaces).

---

## LiteLLM (<LITELLM_HOST>:4000)

```python
# Always use LiteLLM as the gateway — never direct API calls
client = openai.AsyncOpenAI(
    base_url="http://<LITELLM_HOST>:4000",
    api_key=settings.litellm_virtual_key,  # budget-capped per agent
)

# Per-agent virtual keys for cost tracking + blast radius
# Add MASTER_KEY to LiteLLM config; issue Symphony a budget-limited key
```

Enforce per-agent spending via LiteLLM virtual keys before Phase 1 smoke test.

---

## Forgejo Issue Adapter

```python
# Poller token: issue:read + label:write only (NOT repo write)
# Push token: branch write on configured repos only (NOT admin)
# Two tokens. Never one token with full access.

# Issue state machine:
#   open + label:symphony → picked up by harness
#   in-progress label → added by harness on task start
#   agent/ISSUE_ID branch → created on task start
#   PR → opened on task complete
#   closed + label:symphony-done → harness cleanup trigger
```

---

## aiohttp Requirement

```python
# Always use get_session() with AF_INET connector — bare ClientSession() fails
# on IPv6 Docker hostnames (CLAUDE.md constraint)
connector = aiohttp.TCPConnector(family=socket.AF_INET)
session = aiohttp.ClientSession(connector=connector)
```

---

## Redis Progress Stream

```python
# Harness writes progress events to dev_island:episodes stream
# Checkpoint format:
{
  "session_id":   str,
  "issue_id":     str,
  "turn":         int,
  "action":       str,   # tool_call | model_decision | checkpoint | complete | error
  "tool_name":    str | None,
  "result_code":  str,   # ok | blocked | error | escalated
  "timestamp":    float,
}
```

---

## LGTM Observability

```
Prometheus :29220 — scrape harness metrics
Loki       :29221 — structured log ingestion (JSON lines)
Tempo      :29222 — trace spans per tool call
Grafana    :29223 — harness dashboard

Minimum metrics to expose:
  harness_task_total{status="complete|error|escalated"}
  harness_task_duration_seconds (histogram)
  harness_tool_calls_total{tool,result}
  harness_cost_tokens_total{agent,model}
  harness_loop_terminations_total{reason}
```

---

## Workspace Isolation (Docker on ZFS)

```bash
# Per-issue git clone into /tmp/symphony-workspace-${ISSUE_ID}
# (ZFS ACL constraint: use tmpfs or /tmp, not bind-mounts into ZFS datasets)
# Git push via token URL embedding:
git remote set-url origin "http://${FORGEJO_PUSH_TOKEN}@192.168.7.205:29200/${repo}"
# WARNING: token in git remote URL — scrub from logs in PostToolUse hook
```

---

## Security Checklist (Symphony Blast Radius)

*From THREAT_MODEL_Symphony.md — must-fix items before Phase 1.*

- [ ] **Two Forgejo tokens** — poller token (read + label) separate from push token (branch write). Never one token.
- [ ] **Agent subprocess env isolation** — explicit env dict passed to subprocess. Never `inherit=True` or `os.environ`. Exact allowed vars: `LITELLM_URL`, `LITELLM_KEY`, `WORKSPACE_DIR`, `ISSUE_ID`. Nothing else.
- [ ] **SYMPHONY_ALLOWED_USERS** — whitelist of Forgejo users whose issues Symphony will process. Anyone who can file an issue controls the agent's prompt without this.
- [ ] **Forgejo token not embedded in `.git/config`** — any code running in workspace recovers the full write token from a clone URL. Use git credential helper or per-call auth header instead.
- [ ] **WORKFLOW.md hook allowlist** — restrict `pre_run`/`post_run` commands to a fixed allowlist (`pip install`, `uv sync`, `npm install`, `make install/clean`). Anything else → block + `symphony:config-error` label.
- [ ] **LiteLLM virtual key** — budget-capped key issued to Symphony. Add `MASTER_KEY` to LiteLLM config first.
- [ ] **Secret detection PostToolUse** — scan tool outputs for token patterns before logging or injecting into context.
