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
