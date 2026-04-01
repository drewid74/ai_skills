# AI Skills — 35 Domain Skills + 12 Super Agents for Claude Code, Cursor, Codex & Beyond

> **Not 1,000 shallow templates. 35 focused skills + 12 domain-owning super agents that actually teach your AI how to think.** Each skill is 200-500 lines of battle-tested patterns, real code examples, decision frameworks, and troubleshooting guides. Super agents consolidate multiple skills into 700-1,200 line domain specialists that handle entire workflows end-to-end. (AKA - I've learned from my mistakes and repetition)

[![Skills](https://img.shields.io/badge/skills-35-blue)]()
[![Super Agents](https://img.shields.io/badge/super_agents-12-purple)]()
[![Lines of Knowledge](https://img.shields.io/badge/lines-19%2C207-green)]()
[![License](https://img.shields.io/badge/license-MIT-yellow)]()

---

## Why This Collection?

Most skill repos give you a paragraph per topic. This one gives you an **engineering reference** per topic. The difference:

| Approach | Depth | Result |
|----------|-------|--------|
| Typical skill repo | "Use Docker. Pin image tags. Set restart policies." | LLM knows keywords but not tradeoffs |
| **This repo** | Full Docker Compose templates, TrueNAS-specific patterns, GPU passthrough, reverse proxy integration, migration workflows, troubleshooting tables | LLM generates production-ready stacks and debugs real problems |

Every skill explains **why**, not just what. The LLM reads these and understands the reasoning behind decisions — so it can adapt to your specific situation instead of parroting templates.

---

## Quick Install

```bash
# Full collection
git clone https://github.com/drewid74/ai_skills.git ~/.claude/skills/ai_skills

# Or cherry-pick individual skills
cp -r ai_skills/docker-selfhost ~/.claude/skills/
```

Works with Claude Code, Cursor, Codex CLI, Windsurf, and any tool that reads `SKILL.md` files.

> **Super agents vs. individual skills:** Super agents are self-contained — they don't depend on the skills they absorb. Install just the super agents you want, just the individual skills, or both. They live side-by-side with no conflicts.

---

## Skills by Category

### Infrastructure & Homelab

| Skill | Lines | What It Does |
|-------|-------|-------------|
| [docker-selfhost](docker-selfhost/SKILL.md) | 134 | Docker Compose generation, TrueNAS SCALE, reverse proxy, self-hosted service stacks |
| [truenas-ops](truenas-ops/SKILL.md) | 355 | ZFS, TrueNAS API scripting, dataset management, migration, replication, backup/restore |
| [proxmox-k3s-infra](proxmox-k3s-infra/SKILL.md) | 194 | Proxmox VE, VMs, LXC, GPU passthrough, K3s clusters, Helm, GitOps with FluxCD/ArgoCD |
| [deploy-pipeline](deploy-pipeline/SKILL.md) | 423 | SSH/rsync deploy scripts (bash + PowerShell), secrets management, Dockge, rollback strategies |
| [infrastructure-as-code](infrastructure-as-code/SKILL.md) | 265 | Terraform/OpenTofu, Ansible, state management, modules, roles, Terraform+Ansible handoff |
| [llm-inference-stack](llm-inference-stack/SKILL.md) | 234 | Ollama, vLLM, NVIDIA NIM, LiteLLM routing, VRAM sizing, quantization, multi-node topology |
| [service-integration](service-integration/SKILL.md) | 360 | n8n, Node-RED, message queues, notification pipelines, Traefik, Uptime Kuma, cron patterns |

### Software Engineering

| Skill | Lines | What It Does |
|-------|-------|-------------|
| [full-sdlc](full-sdlc/SKILL.md) | 242 | Requirements through production — scaffolding, branching, testing, CI/CD, release management |
| [code-reviewer](code-reviewer/SKILL.md) | 205 | Systematic review: correctness, security, edge cases, performance, Python/JS/Go/Bash patterns |
| [cicd-pipeline](cicd-pipeline/SKILL.md) | 344 | GitHub/Forgejo Actions, self-hosted runners, build caching, container registries, release automation |
| [github-workflow](github-workflow/SKILL.md) | 144 | Repo scaffolding, branch strategies, PR management, GitHub Actions, release workflows |
| [testing-framework](testing-framework/SKILL.md) | 374 | pytest, Jest/Vitest, Playwright, k6 load testing, mocking, fixtures, CI integration, debugging flaky tests |
| [database-architecture](database-architecture/SKILL.md) | 202 | Schema design, indexing, EXPLAIN ANALYZE, ORMs, migrations, connection pooling, replication, PostgreSQL ops |
| [api-integration](api-integration/SKILL.md) | 502 | REST/GraphQL/WebSocket design, OAuth/JWT, resilience patterns (retry, circuit breaker), webhooks |

### AI & Machine Learning

| Skill | Lines | What It Does |
|-------|-------|-------------|
| [agentic-architecture](agentic-architecture/SKILL.md) | 279 | Agent design patterns (ReAct, multi-agent), RAG pipelines, tool use, guardrails, evaluation |
| [mcp-server-dev](mcp-server-dev/SKILL.md) | 345 | Build MCP servers (FastMCP + TypeScript), tool design, transports, Docker packaging, federation |
| [training-pipeline](training-pipeline/SKILL.md) | 237 | LoRA/QLoRA fine-tuning, data prep, hyperparameters, DeepSpeed, autonomous training loops, MLflow |
| [federated-memory](federated-memory/SKILL.md) | 212 | Agent memory (working/recall/archival), vector stores, federation model, sync, graph knowledge |
| [ai-skills-dev](ai-skills-dev/SKILL.md) | 175 | Skill development lifecycle, prompt engineering, agent architecture, cross-platform portability |

### Security & Operations

| Skill | Lines | What It Does |
|-------|-------|-------------|
| [security-reviewer](security-reviewer/SKILL.md) | 314 | OWASP Top 10, container hardening, SSH/firewall, TLS, secrets management, scanning pipelines |
| [observability-sre](observability-sre/SKILL.md) | 478 | Prometheus, Grafana, Loki, OpenTelemetry, alerting philosophy, SLI/SLO, incident response, runbooks |

### Data & Intelligence

| Skill | Lines | What It Does |
|-------|-------|-------------|
| [data-engineering](data-engineering/SKILL.md) | 282 | ETL/ELT pipelines, pandas/polars/DuckDB, data validation, file formats, cleaning, orchestration |
| [sigint-osint-feeds](sigint-osint-feeds/SKILL.md) | 280 | APRS, ADS-B, USGS, NOAA, GDELT, RSS aggregation, satellite tracking, PostGIS, worker patterns |
| [archivebox-knowledge](archivebox-knowledge/SKILL.md) | 172 | Web archival, Paperless-NGX, content extraction, summarization pipelines, knowledge base integration |
| [deep_research](deep_research/SKILL.md) | 29 | Source-grounded web research with triangulation, confidence scoring, and citation |

### Web & Frontend

| Skill | Lines | What It Does |
|-------|-------|-------------|
| [web-performance-a11y](web-performance-a11y/SKILL.md) | 193 | Core Web Vitals, asset optimization, WCAG 2.1/2.2 AA compliance, Lighthouse, SEO |
| [frontend_design_ux_enforcement.md](frontend_design_ux_enforcement.md/SKILL.md) | 34 | Design systems, Tailwind v4, semantic HTML, accessibility audits, mobile-first patterns |
| [browser-automation](browser-automation/SKILL.md) | 273 | Playwright, scraping patterns, anti-bot handling, e2e testing, page monitoring |

### Productivity & Communication

| Skill | Lines | What It Does |
|-------|-------|-------------|
| [content-strategy](content-strategy/SKILL.md) | 193 | Technical writing, READMEs, blog posts, API docs, SEO, email, documentation systems |
| [productivity-automation](productivity-automation/SKILL.md) | 156 | Cron, batch workflows, data transformation, monitoring, backup automation, templates |
| [google_workspace_assistant](google_workspace_assistant/SKILL.md) | 32 | Gmail, Calendar, Sheets, Drive automation with drafting-first workflow |

### Meta / Reasoning

| Skill | Lines | What It Does |
|-------|-------|-------------|
| [project_orchestrator](project_orchestrator/SKILL.md) | 46 | Multi-agent orchestration — DAG task decomposition, delegation, checkpointing |
| [sequential_thinking](sequential_thinking/SKILL.md) | 33 | Structured reasoning trees, root cause analysis, architecture review, decision matrices |
| [repo_auditor](repo_auditor/SKILL.md) | 47 | Repository health audit — structure, docs, links, dependencies, AI-readiness |
| [ham-radio-network](ham-radio-network/SKILL.md) | 140 | Antenna math, CHIRP CSV, DMR codeplug, FT8/APRS, AREDN mesh, VLAN/firewall design |

---

## Super Agents — Domain-Owning Specialists

Super agents consolidate multiple narrow skills into broad domain experts that handle entire workflows end-to-end. They absorb all knowledge from their constituent skills, add new capabilities, and explain the WHY behind every pattern. **The original 35 skills remain untouched** — use super agents when you want one specialist to own a whole domain, or individual skills when you want focused depth on a single topic.

### Infrastructure & Platform

| Super Agent | Lines | Absorbs | What It Does |
|-------------|-------|---------|-------------|
| [homelab-commander](homelab-commander/SKILL.md) | 1,154 | docker-selfhost, truenas-ops, proxmox-k3s-infra, deploy-pipeline | Full homelab infrastructure: Docker Compose stacks, TrueNAS storage, Proxmox VMs, K3s clusters, cross-platform migration, disaster recovery, network topology visualization, DNS management, blue-green deployments, FluxCD GitOps, VLAN configuration |
| [sre-operations-lead](sre-operations-lead/SKILL.md) | 1,038 | observability-sre, productivity-automation | System reliability ownership: Prometheus/Grafana/Loki/OpenTelemetry observability, runbook generation, incident command, SLI/SLO error budgets, alert tuning, capacity planning, automated remediation, on-call rotation design, backup automation (rsync, restic, 3-2-1 rule), ELK/EFK stack alternatives, APM |

### Software & DevOps

| Super Agent | Lines | Absorbs | What It Does |
|-------------|-------|---------|-------------|
| [devops-engineer](devops-engineer/SKILL.md) | 1,236 | cicd-pipeline, github-workflow, infrastructure-as-code | Complete delivery pipeline: CI/CD (GitHub Actions, Forgejo, self-hosted runners), release management (semantic versioning, changelogs), IaC (Terraform/OpenTofu, Ansible), secrets lifecycle (Vault, rotation, leak detection), dependency auditing, PR review, git worktree management |
| [software-architect](software-architect/SKILL.md) | 997 | full-sdlc, code-reviewer, database-architecture, repo_auditor | Full-stack architecture: requirements through production, code quality gates, schema design and optimization (PostgreSQL, pgvector, VACUUM), migration planning, ADR management, tech debt tracking, monorepo navigation, codebase onboarding |
| [quality-test-engineer](quality-test-engineer/SKILL.md) | 1,060 | testing-framework, web-performance-a11y | Comprehensive QA: test architecture (unit/integration/E2E/load with pytest, Jest, Playwright, k6), contract testing (Pact), property-based and mutation testing, Core Web Vitals optimization, WCAG accessibility compliance, visual regression, chaos engineering, HTTP/2-3, Brotli, Testcontainers |

### AI & Machine Learning

| Super Agent | Lines | Absorbs | What It Does |
|-------------|-------|---------|-------------|
| [ai-systems-architect](ai-systems-architect/SKILL.md) | 913 | agentic-architecture, mcp-server-dev, federated-memory, ai-skills-dev | End-to-end AI systems: agent workflow design (ReAct, Plan-and-Execute, multi-agent), MCP server scaffolding and Docker packaging, RAG pipeline architecture, federated memory, skill development lifecycle, eval harness building, cost/latency optimization |
| [ml-engineer](ml-engineer/SKILL.md) | 819 | training-pipeline, llm-inference-stack | Complete ML pipelines: fine-tuning (LoRA/QLoRA/full with PEFT/bitsandbytes), DPO/RLHF alignment, distributed training (DeepSpeed stages 1-3, FSDP), inference deployment (vLLM, Ollama, SGLang, TGI), quantization advising, VRAM calculators, embedding models for RAG, dataset curation, experiment comparison |

### Integration & Security

| Super Agent | Lines | Absorbs | What It Does |
|-------------|-------|---------|-------------|
| [api-integration-engineer](api-integration-engineer/SKILL.md) | 879 | api-integration, service-integration, browser-automation | Unified integrations: REST/GraphQL/WebSocket/gRPC API design, OAuth2/PKCE/JWT auth, resilience patterns (retry, circuit breaker, bulkhead), service orchestration (n8n, Node-RED), notification services (Ntfy, Gotify, Apprise), reverse proxy (Traefik, Cloudflare Tunnels), Playwright browser automation, ethical scraping |
| [security-compliance-officer](security-compliance-officer/SKILL.md) | 839 | security-reviewer | Security audit framework: OWASP Top 10 (injection, XSS, CSRF, SSRF), container image hardening, SSH/firewall configuration, secrets management (Vault, SOPS), SSL/cert lifecycle, CIS benchmarks, SAST/DAST tools (CodeQL, Semgrep, ZAP), supply chain security (SBOM, Sigstore, SLSA), incident forensics, dependency CVE scanning |

### Intelligence & Frontend

| Super Agent | Lines | Absorbs | What It Does |
|-------------|-------|---------|-------------|
| [intelligence-analyst](intelligence-analyst/SKILL.md) | 844 | sigint-osint-feeds, archivebox-knowledge, deep_research | Intelligence platform: multi-source OSINT fusion (APRS, ADS-B, AIS vessel tracking, GDELT, USGS, NOAA), threat correlation with STIX/TAXII/OpenCTI, knowledge graph construction, web archival (ArchiveBox, FlareSolverr), source credibility scoring, automated briefing generation, satellite tracking (SGP4), RF signal decoding |
| [frontend-ux-engineer](frontend-ux-engineer/SKILL.md) | 1,098 | frontend_design_ux_enforcement, content-strategy, google_workspace_assistant | UI/UX ownership: design system enforcement (Tailwind v4, Shadcn/Radix, Magic UI), "No-Average Rule" aesthetics, accessibility audits, technical content strategy (READMEs, ADRs, changelogs, SEO), brand voice engine, Google Workspace MCP integration (Gmail, Calendar, Sheets), documentation platforms (MkDocs, Docusaurus) |

### Meta / Orchestration

| Super Agent | Lines | Absorbs | What It Does |
|-------------|-------|---------|-------------|
| [mission-control](mission-control/SKILL.md) | 402 | project_orchestrator, sequential_thinking, ham-radio-network | Executive orchestration layer: multi-agent routing with cost-aware delegation, DAG task decomposition, conflict resolution with evidence-based arbitration, reasoning audit trails (branching, validation, RCA), task registry tracking, ham radio calculator (antenna math, CHIRP CSV, DMR codeplug, FT8/APRS, AREDN mesh, VLAN/firewall/DNS design) |

---

## What Makes These Different

**Depth over breadth.** Each skill is a focused engineering reference, not a feature list. Here's what you get inside a typical skill:

- Decision frameworks ("when to use X vs Y, and why")
- Practical code examples (Python, TypeScript, bash, YAML) you can use immediately
- Architecture patterns with tradeoff analysis
- Configuration templates with explanations
- Troubleshooting tables mapping symptoms to fixes
- Tool comparisons with honest assessments

**Universal, not personal.** Every skill uses placeholders (`<NAS_IP>`, `<API_KEY>`, `<POOL_NAME>`) and explains patterns that work across any setup. No hardcoded infrastructure.

**Principles over procedures.** Instead of "here's how to configure Stripe," you get "here's how to build resilient API integrations" — so the LLM can apply the pattern to any service.

---

## Skill Anatomy

```
skill-name/
├── SKILL.md          # Required: YAML frontmatter + markdown instructions
├── scripts/          # Optional: helper scripts for deterministic tasks
├── references/       # Optional: supplemental documentation
└── assets/           # Optional: templates, configs, icons
```

The YAML frontmatter controls when the skill activates:

```yaml
---
name: docker-selfhost
description: "Use this skill whenever the user wants to work with Docker,
  Docker Compose, containers, TrueNAS Scale, self-hosted services..."
---
```

The markdown body is the knowledge the LLM reads when the skill triggers. Write it like you're briefing a smart colleague who needs context, not step-by-step hand-holding.

---

## Cross-Platform Reference Catalogs

Bonus: capabilities catalogs for comparing what each AI platform can do.

| Catalog | Description |
|---------|-------------|
| [claude_capabilities_catalog.md](claude_capabilities_catalog.md) | All available tools, MCPs, skills, and triggers in Claude |
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
# Copy just the skills you want
cp -r ai_skills/docker-selfhost ~/.claude/skills/
cp -r ai_skills/security-reviewer ~/.claude/skills/
```

### Verify
Skills appear automatically once they're in your skills directory. The LLM reads the frontmatter `description` field to decide when to invoke each skill.

> Skill directory paths vary by tool. For Claude Code, the default is `~/.claude/skills/`. Check your tool's documentation for the correct location.

---

## Contributing

Skills are plain markdown. The barrier to entry is low:

1. Fork the repo
2. Create a directory with a `SKILL.md` file (use [ai-skills-dev](ai-skills-dev/SKILL.md) for the template)
3. Write 200-500 lines of domain knowledge with code examples and troubleshooting
4. Open a PR with 2-3 example prompts that validate your trigger description

Quality bar: if a developer with 5 years of experience would learn something from your skill, it belongs here. If it's just paraphrasing documentation, it doesn't.

---

## License

MIT — use these skills however you want, commercially or otherwise.