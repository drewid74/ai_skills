# AI Skills — Functional Skill Framework

A collection of reusable Claude Code skills covering common technical workflows. Each skill is a self-contained instruction set that teaches Claude how to perform a specific domain of tasks reliably and consistently.

## What Is a Skill?

A skill is a directory containing a `SKILL.md` file with YAML frontmatter and markdown instructions. Claude reads the frontmatter description to decide when to invoke the skill, and the body to determine how to execute it. Skills can include optional scripts, reference docs, templates, and assets.

```
skill-name/
├── SKILL.md          # Required: trigger description + instructions
├── scripts/          # Optional: helper scripts
├── references/       # Optional: supplemental docs
└── assets/           # Optional: templates, configs
```

---

## References in This Repo

### [claude_capabilities_catalog](claude_capabilities_catalog.md)
**Reference for all available tools, MCPs, skills, and triggers currently in Claude.**

### [ChatGPT_Capabilities_Catalog](chatgpt_capabilities_catalog.md)
**ChatGPT Capabilities Catalog with available tools, MCPs, skills, and triggers.**

### [gemini_capabilities_catalog](gemini_capabilities_catalog.md)
**Gemini capabilities catalog with available tools, MCPs, skills, and triggers.**

### [cross_agent_skills](cross_agent_skills.md)
**Cross-Agent Skills & Capabilities Audit Prompt to generate a comparable capabilities catalog.**


## Skills in This Repo

### [ai-skills-dev](ai-skills-dev/SKILL.md)
**Design, build, and test AI skills and agent workflows.**

Covers the full lifecycle of skill development: writing effective trigger descriptions, prompt engineering principles, agent architecture patterns (single agent, orchestrator/worker, pipeline, evaluator loop), cross-platform portability, and publishing skills as `.skill` files or GitHub repos. Includes testing methodology from quick vibe checks to formal eval pipelines.

**Triggers on:** skill development, prompt engineering, agent design, MCP development, LLM fine-tuning, RAG, embeddings, AI workflow design.

---

### [docker-selfhost](docker-selfhost/SKILL.md)
**Generate and manage Docker Compose stacks for self-hosted services.**

Produces complete, production-ready `docker-compose.yml` and `.env.example` files for self-hosted deployments. Covers TrueNAS Scale-specific constraints, reverse proxy integration (Traefik, nginx proxy manager, Cloudflare tunnels), network isolation patterns, volume/permission management, common service stacks (media, productivity, home automation, dev tools), migration from cloud to self-hosted, and backup strategy.

**Triggers on:** docker, docker-compose, TrueNAS, self-hosted, homelab, reverse proxy, container troubleshooting, any commonly self-hosted service name (Jellyfin, Nextcloud, Gitea, etc.).

---

### [github-workflow](github-workflow/SKILL.md)
**Automate GitHub repository management and CI/CD workflows.**

Provides structured workflows for repository scaffolding (README, .gitignore, issue templates, PR templates), branch strategy selection (trunk-based, GitHub Flow, Git Flow), PR creation and review using GitHub MCP tools, issue triage and labeling, and GitHub Actions CI/CD pipeline generation. Covers Docker build/push pipelines, release automation, and compound operations like search-fix-PR.

**Triggers on:** GitHub, git, pull requests, issues, CI/CD, GitHub Actions, branch management, repo setup, code review.

---

### [ham-radio-network](ham-radio-network/SKILL.md)
**Amateur radio calculations, programming, and home network infrastructure.**

Handles antenna design math (dipole, vertical, Yagi, coax loss, SWR/return loss), link budget calculations, repeater offset standards, CHIRP CSV generation for radio programming, DMR codeplug basics, digital mode setup (FT8/WSJT-X, APRS, Winlink), AREDN mesh networking, and home network design (VLAN layout, firewall rules, DNS architecture, subnet planning).

**Triggers on:** ham radio, amateur radio, HF/VHF/UHF, antenna, repeater, APRS, DMR, FT8, SDR, CHIRP, AREDN, mesh network, VLAN design, home network infrastructure.

---

### [productivity-automation](productivity-automation/SKILL.md)
**Build scheduled tasks, batch file workflows, and personal automation pipelines.**

Covers cron expression reference and scheduled task creation, self-contained task prompt writing, batch file rename/convert/organize operations, data transformation pipelines (CSV, JSON, logs), monitoring and alerting patterns (service health, disk space, SSL expiry, container status), backup automation with the 3-2-1 rule, and recurring workflow templates (daily summary, weekly cleanup, file watch pattern).

**Triggers on:** automate, schedule, recurring, batch files, organize, backup, monitor, cron, daily/weekly tasks, file processing, data transformation.

---

### [deep_research](deep_research/SKILL.md)
**Web research, fact-grounding, and sourced technical analysis.**

Eliminates hallucinations by grounding every claim in real-world data. Enforces a structured research protocol: query expansion into 3-5 sub-queries, source diversity across at least 3 domains, recency filtering (18 months for tech), and triangulation requiring two independent sources before marking a fact "Confirmed." Supports market analysis, spec verification, literature reviews, and OSINT fusion. Outputs include a confidence score, hyperlinked source list, and TL;DR synthesis.

**Triggers on:** research, search, find, check, latest news, documentation, specs, comparison, who is, what is the best, current trends, citations, links.

---

### [sequential_thinking](sequential_thinking/SKILL.md)
**Structured reasoning framework for complex architecture, debugging, and decisions.**

Forces exploration of a reasoning tree before answering — deconstructing requirements into atomic constraints, branching into optimal vs. fast paths, validating against edge cases, and synthesizing a justified recommendation. Includes a root cause analysis workflow for debugging (observation → history → hypothesis → isolation). Supports architectural review, decision matrices, and dependency mapping.

**Triggers on:** why, how should I approach, debug, architecture, logic, plan, strategy, complex, broken, root cause, analyze, tasks with more than 5 dependencies.

---

### [google_workspace_assistant](google_workspace_assistant/SKILL.md)
**Automate Gmail, Calendar, Google Sheets, and Drive via Google Workspace MCP tools.**

Bridges raw data and professional communication across the GWS ecosystem. Enforces a drafting-first workflow (never sends without explicit confirmation), context retrieval from prior email threads before composing, and scheduling rules (15-minute transition buffers, purpose/agenda required on all invites). Supports inbox triage, report-to-Sheets sync, and daily briefing generation from Calendar and Gmail.

**Triggers on:** email, Gmail, draft, inbox, calendar, meeting, schedule, appointment, spreadsheet, Sheets, Google Docs, Drive, sync data, send report, check availability, organize my day.

---

### [frontend_design_ux_enforcement.md](frontend_design_ux_enforcement.md/SKILL.md)
**UI/UX development, design system enforcement, and accessibility audits.**

Enforces a "No-Average" design philosophy: high-contrast typography scales, functional color palettes with a brand accent, and whitespace-first hierarchy on an 8px grid. Generates semantic HTML5/JSX with proper Next.js client/server separation, Tailwind v4 styling with `@theme` tokens, and full A11y compliance (ARIA labels, 4.5:1 contrast, keyboard navigation). Supports design audits, theme injection into `globals.css`, and mobile-first refactors.

**Triggers on:** CSS, Tailwind, React, component, styling, UI, UX, responsive, mobile-first, accessibility, ARIA, Shadcn, Framer Motion, animation, layout, grid, flexbox, make it look better, fix the alignment, build a landing page.

---

### [project_orchestrator](project_orchestrator/SKILL.md)
**Multi-agent project orchestration — decompose, delegate, and coordinate across skills.**

Acts as the central "Brain" for complex missions. Breaks high-level goals into a directed acyclic graph (DAG) of tasks, identifies dependencies, delegates to specialized skills with minimal context passing, checkpoints state after each completion, and synthesizes final delivery. Enforces a no-loop rule (halts after two agent hand-offs without progress) and tracks cost awareness by preferring local tools over expensive research calls.

**Triggers on:** manage project, orchestrate, coordinate, start new build, full stack plan, integrate skills, workflow design, agent hand-off, multi-step mission.

---

### [repo_auditor](repo_auditor/SKILL.md)
**Repository health audit — structure, documentation, links, and AI-readiness.**

Evaluates a local or remote repository across four layers: structural integrity (README, LICENSE, .gitignore, llms.txt, CI/CD scaffolding), content quality (stale docs, clarity, naming consistency), link and dependency integrity (external URL 404 checks, internal path validation, version pinning), and AI-readiness (SKILL.md frontmatter validation, entrypoint documentation). Outputs an executive summary, categorized findings, and a prioritized action plan of quick vs. strategic fixes.

**Triggers on:** audit repo, check repository, is this repo clean, review structure, missing files, broken links, repo best practices, check README, prepare for release.

---

## Installation

Copy any skill directory into your Claude Code skills folder:

```bash
# Typically:
~/.claude/skills/skill-name/
```

Or install the full collection:

```bash
git clone https://github.com/drewid74/ai_skills.git ~/.claude/skills/ai_skills
```

> Check your Claude Code version's skill discovery path — it may vary.

## Contributing

Skills are plain markdown. To add or improve one:
1. Fork the repo
2. Edit or add a `SKILL.md` following the structure in [ai-skills-dev](ai-skills-dev/SKILL.md)
3. Open a PR with example prompts that validate the trigger description
