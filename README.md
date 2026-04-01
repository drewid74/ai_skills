# AI Skills — 35 Lean Domain Skills for Claude Code, Cursor, Codex & Beyond

> **35 focused skills, each ~75 lines.** Every skill follows the same template: Identity → Stack Defaults → Decision Framework → Anti-Patterns → Quality Gates. Dense enough to be useful, lean enough not to bloat your context window.

[![Skills](https://img.shields.io/badge/skills-35-blue)]()
[![Lines](https://img.shields.io/badge/lines-2%2C531-green)]()
[![Tokens](https://img.shields.io/badge/est._tokens-37K-orange)]()
[![License](https://img.shields.io/badge/license-MIT-yellow)]()

---

## Why This Collection?

Skills load into your AI's context window on every invocation. Bloated skills waste tokens and dilute focus. This library is optimized for **signal density**:

| | Before (v1) | After (v2) |
|--|-------------|------------|
| Files | 47 (35 skills + 12 "super agents") | 35 skills |
| Total lines | 19,207 | 2,531 |
| Est. tokens (full load) | ~240,000 | ~37,000 |
| Avg lines/skill | ~400 | 72 |
| Tokens per invocation | ~3,700 | ~1,050 |

**−87% lines. −84% tokens per invocation.** Same decision quality — the template forces every skill to include if/then decision rules, anti-patterns, and quality gates rather than prose explanations.

Every skill answers three questions: *What tool/approach?* (Stack Defaults), *When and why?* (Decision Framework), *What to avoid?* (Anti-Patterns).

---

## Quick Install

```bash
# Full collection
git clone https://github.com/drewid74/ai_skills.git ~/.claude/skills/ai_skills

# Or cherry-pick individual skills
cp -r ai_skills/docker-selfhost ~/.claude/skills/
```

Works with Claude Code, Cursor, Codex CLI, Windsurf, and any tool that reads `SKILL.md` files.

---

## Skills by Category

### Infrastructure & Homelab

| Skill | Lines | What It Does |
|-------|-------|-------------|
| [docker-selfhost](docker-selfhost/SKILL.md) | 68 | Docker Compose stacks, self-hosted services, volumes, reverse proxy, TrueNAS SCALE |
| [truenas-ops](truenas-ops/SKILL.md) | 76 | ZFS pool management, TrueNAS datasets, replication, snapshots, permissions |
| [proxmox-k3s-infra](proxmox-k3s-infra/SKILL.md) | 78 | Proxmox VMs/LXC, cloud-init templates, GPU passthrough, K3s clusters, GitOps |
| [deploy-pipeline](deploy-pipeline/SKILL.md) | 82 | rsync/SSH deploys, health checks, rollback, secrets hygiene, ZFS snapshots |
| [infrastructure-as-code](infrastructure-as-code/SKILL.md) | 78 | Terraform/OpenTofu, Ansible, state management, drift detection, secrets handling |
| [llm-inference-stack](llm-inference-stack/SKILL.md) | 79 | Ollama, vLLM, LiteLLM routing, VRAM sizing, quantization formats |
| [service-integration](service-integration/SKILL.md) | 62 | Webhooks, n8n, message queues, notification pipelines, Traefik |

### Software Engineering

| Skill | Lines | What It Does |
|-------|-------|-------------|
| [full-sdlc](full-sdlc/SKILL.md) | 66 | Project scaffolding, branching, testing strategy, CI/CD, release management |
| [code-reviewer](code-reviewer/SKILL.md) | 62 | Correctness, security, edge cases, performance — Python/JS/Go/Bash |
| [cicd-pipeline](cicd-pipeline/SKILL.md) | 84 | GitHub/Forgejo Actions, runners, caching, container registries, semantic release |
| [github-workflow](github-workflow/SKILL.md) | 63 | Repo scaffolding, branch protection, PR workflow, issue management |
| [quality-test-engineer](quality-test-engineer/SKILL.md) | 79 | pytest/Jest/Playwright/k6, flaky test diagnosis, CI integration, coverage |
| [database-architecture](database-architecture/SKILL.md) | 77 | Schema design, indexing, EXPLAIN ANALYZE, ORMs, migrations, connection pooling |
| [api-integration](api-integration/SKILL.md) | 77 | REST/GraphQL, OAuth/JWT, retry/circuit breaker, rate limits, webhooks |

### AI & Machine Learning

| Skill | Lines | What It Does |
|-------|-------|-------------|
| [ai-systems-architect](ai-systems-architect/SKILL.md) | 77 | RAG vs fine-tuning, agent design, MCP, context budgeting, eval pipelines |
| [mcp-server-dev](mcp-server-dev/SKILL.md) | 68 | FastMCP/TypeScript MCP servers, tool design, transports, Docker packaging |
| [training-pipeline](training-pipeline/SKILL.md) | 75 | LoRA/QLoRA fine-tuning, hyperparameters, DeepSpeed, experiment tracking |
| [federated-memory](federated-memory/SKILL.md) | 68 | Agent persistent memory, vector stores, Qdrant/pgvector, cross-session recall |
| [ai-skills-dev](ai-skills-dev/SKILL.md) | 67 | SKILL.md authoring, trigger optimization, template iteration |

### Security & Operations

| Skill | Lines | What It Does |
|-------|-------|-------------|
| [security-engineer](security-engineer/SKILL.md) | 80 | OWASP Top 10, secrets scanning, container hardening, SAST, supply chain, CVE triage |
| [sre-operations-lead](sre-operations-lead/SKILL.md) | 79 | Prometheus/Grafana/Loki, SLOs, alert design, incident response, runbooks |

### Data & Intelligence

| Skill | Lines | What It Does |
|-------|-------|-------------|
| [data-engineering](data-engineering/SKILL.md) | 71 | ETL/ELT pipelines, pandas/polars/DuckDB, idempotency, schema evolution |
| [sigint-osint-feeds](sigint-osint-feeds/SKILL.md) | 78 | APRS, ADS-B, GDELT, OSINT aggregation, PostGIS, worker pipelines |
| [archivebox-knowledge](archivebox-knowledge/SKILL.md) | 72 | Web archival, Paperless-NGX, content extraction, knowledge base pipelines |
| [research-analyst](research-analyst/SKILL.md) | 67 | Source-grounded research, triangulation, confidence scoring, threat intelligence |

### Web & Frontend

| Skill | Lines | What It Does |
|-------|-------|-------------|
| [web-performance-a11y](web-performance-a11y/SKILL.md) | 80 | Core Web Vitals, WCAG 2.1/2.2 AA, Lighthouse, asset optimization |
| [frontend-design-ux-enforcement](frontend-design-ux-enforcement/SKILL.md) | 64 | Design systems, Tailwind v4, Shadcn/Radix, accessibility audits, mobile-first |
| [browser-automation](browser-automation/SKILL.md) | 73 | Playwright, scraping, anti-bot handling, page monitoring, e2e testing |

### Productivity & Communication

| Skill | Lines | What It Does |
|-------|-------|-------------|
| [content-strategy](content-strategy/SKILL.md) | 66 | Technical writing, READMEs, API docs, changelogs, SEO |
| [productivity-automation](productivity-automation/SKILL.md) | 80 | Cron, batch jobs, file processing, backup automation, monitoring |
| [google_workspace_assistant](google_workspace_assistant/SKILL.md) | 63 | Gmail, Calendar, Sheets, Drive automation |

### Meta / Reasoning

| Skill | Lines | What It Does |
|-------|-------|-------------|
| [project_orchestrator](project_orchestrator/SKILL.md) | 64 | Multi-step project coordination, task decomposition, agent delegation |
| [sequential_thinking](sequential_thinking/SKILL.md) | 62 | Root cause analysis, architecture review, structured decision-making |
| [repo_auditor](repo_auditor/SKILL.md) | 67 | Repository health, docs quality, broken links, release readiness |
| [ham-radio-network](ham-radio-network/SKILL.md) | 79 | Antenna math, CHIRP/DMR, FT8/APRS, AREDN mesh, VLAN/firewall design |

---

## Skill Template

Every skill follows the same structure (~75 lines):

```markdown
---
name: skill-name
description: "Use this when: [action/problem phrases ≤20, intent-first]"
---

## Identity
You [role]. [Core principle]. Never [hard constraint].

## Stack Defaults
| Layer | Choice | Why |

## Decision Framework
### When to X
- If [condition] → [action]

## Anti-Patterns
| Don't | Why | Do Instead |

## Quality Gates
- [ ] Gate
```

Descriptions use **action/problem phrases** ("my pipeline is failing", "set up CI") rather than tool names — this is how the routing system finds the right skill for natural-language prompts.

---

## What Makes These Different

**Decision density over prose.** Every skill has explicit if/then decision rules and an anti-patterns table. The LLM gets *when to use X vs Y* — not just *what X is*.

**Context-efficient.** At ~1,050 tokens per skill invocation (down from ~3,700), these load fast and leave room for your actual code in the context window.

**Universal, not personal.** Placeholders (`<NAS_IP>`, `<API_KEY>`, `<POOL_NAME>`) throughout. No hardcoded infrastructure — patterns that work across any setup.

---

## Skill Anatomy

```
skill-name/
├── SKILL.md    # Required: YAML frontmatter + ~75 lines of structured instructions
└── scripts/    # Optional: helper scripts referenced in SKILL.md
```

The YAML frontmatter controls when the skill auto-invokes:

```yaml
---
name: docker-selfhost
description: "Use this when: my container keeps restarting, set up a self-hosted service,
  my volumes are not persisting, deploy with Docker Compose, my container won't start"
---
```

Descriptions use **intent phrases** ("my container keeps restarting") not tool names ("Docker, Compose, volumes"). The routing is semantic — natural-language problem descriptions match better than keyword lists.

---

## Cross-Platform Reference Catalogs

| Catalog | Description |
|---------|-------------|
| [claude_capabilities_catalog.md](claude_capabilities_catalog.md) | Tools, MCPs, skills, and triggers in Claude |
| [chatgpt_capabilities_catalog.md](chatgpt_capabilities_catalog.md) | ChatGPT equivalent capabilities |
| [gemini_capabilities_catalog.md](gemini_capabilities_catalog.md) | Gemini capabilities |
| [cross_agent_skills.md](cross_agent_skills.md) | Audit prompt to generate a comparable catalog for any platform |

---

## Installation

### Full Collection
```bash
git clone https://github.com/drewid74/ai_skills.git ~/.claude/skills/ai_skills
```

### Cherry-Pick Skills
```bash
cp -r ai_skills/docker-selfhost ~/.claude/skills/
cp -r ai_skills/security-engineer ~/.claude/skills/
```

### Verify
```
/skills list       # shows all loaded skills
/skills reload     # pick up new skills added mid-session
/docker-selfhost   # invoke a skill explicitly by name
```

> Skill directory paths vary by tool. For Claude Code: `~/.claude/skills/`. For Copilot CLI: `~/.copilot/skills/`. Check your tool's documentation.

---

## Contributing

Skills are plain markdown with a fixed template. The bar is **one skill, ~75 lines**:

1. Fork the repo
2. Create `your-skill-name/SKILL.md` using this structure:
   - `## Identity` — role + core principle + hard constraint (3 lines)
   - `## Stack Defaults` — 4–8 row table: Layer | Choice | Why
   - `## Decision Framework` — 2–4 if/then sections with `→` bullets
   - `## Anti-Patterns` — 4–6 row table: Don't | Why | Do Instead
   - `## Quality Gates` — 4–6 checkboxes
3. Write the description as action/problem phrases: `"Use this when: my X is broken, set up Y, how do I Z"`
4. Open a PR with 2–3 example prompts that trigger your skill

**Quality bar:** Does it have real if/then decision rules? Does the anti-patterns table catch the top mistakes? Would a developer trust it at 2am during an incident? If yes, it belongs here.

---

## License

MIT — use these skills however you want, commercially or otherwise.