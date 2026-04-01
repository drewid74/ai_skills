# Cursor IDE — Skill Building Capabilities Catalog

> Generated: 2026-03-31 | Purpose: Reference for building custom rules and instructions for Cursor IDE

---

## 0. Platform Overview

Cursor uses a layered rules system to give its AI assistant (powered by various LLM backends) persistent context about your coding preferences, project conventions, and domain knowledge. Rules are defined as `.mdc` or `.md` files with YAML frontmatter that controls when and how they activate.

**Plans:** Free, Pro ($20/mo), Business ($40/user/mo), Enterprise (custom)

---

## 1. Rule Types

### User Rules (Global)

| Property | Detail |
|----------|--------|
| **Configuration** | Cursor Settings > General > Rules for AI |
| **Format** | Plain text in settings UI |
| **Scope** | All projects, all sessions |
| **Version controlled** | No (stored locally) |

**Use for:** Personal coding style, language preferences, formatting opinions that follow you everywhere.

**Example:**
```
Always use TypeScript strict mode.
Prefer functional programming patterns.
When writing Python, use type hints on all function signatures.
Use 2-space indentation for YAML and JSON files.
```

### Project Rules (`.cursor/rules/`)

| Property | Detail |
|----------|--------|
| **Location** | `.cursor/rules/*.mdc` or `.cursor/rules/*.md` |
| **Format** | Markdown with YAML frontmatter |
| **Scope** | Current project only |
| **Version controlled** | Yes — commit to repo |

This is the primary mechanism for project-specific AI customization.

### Team Rules (Organization)

| Property | Detail |
|----------|--------|
| **Configuration** | Cursor dashboard (Business/Enterprise plans) |
| **Scope** | All projects for team members |
| **Priority** | Highest — overrides project and user rules |

---

## 2. .mdc File Format

### Frontmatter Fields

| Field | Required | Values | Description |
|-------|----------|--------|-------------|
| `description` | Recommended | Free text | Explains rule purpose; used by "Apply Intelligently" mode to decide relevance |
| `alwaysApply` | No | `true` / `false` | If `true`, included in every session regardless |
| `globs` | No | Glob pattern(s) | File patterns that trigger the rule (e.g., `["*.tsx", "src/api/**"]`) |

### Activation Modes

| Mode | Frontmatter | Behavior |
|------|-------------|----------|
| **Always Apply** | `alwaysApply: true` | Included in every conversation |
| **Apply Intelligently** | `alwaysApply: false`, `description` set, no `globs` | Cursor decides based on description match to current task |
| **Apply to Specific Files** | `globs` set | Activates when matching files are in context |
| **Apply Manually** | No `alwaysApply`, no `globs`, no `description` | Only activates when user types `@rule-name` |

### Examples

**Always-on project conventions:**
```markdown
---
description: "Core project conventions for the API service"
alwaysApply: true
---
This is a FastAPI project using SQLAlchemy 2.0 async with PostgreSQL.
All endpoints return Pydantic v2 models.
Use dependency injection for database sessions.
Alembic manages all schema migrations — never write raw DDL.
```

**File-scoped rule:**
```markdown
---
description: "React component patterns"
globs: ["src/components/**/*.tsx"]
---
Use functional components with hooks exclusively.
All components must be wrapped in `React.memo` unless they accept children.
Use `clsx` for conditional classNames.
Extract custom hooks into `src/hooks/` when reused across 2+ components.
```

**Agent-decided (intelligent matching):**
```markdown
---
description: "Database migration and schema change guidance. Use when creating or modifying database tables, writing Alembic migrations, or changing SQLAlchemy models."
---
Always create a new Alembic migration for schema changes:
  alembic revision --autogenerate -m "description"

Never modify existing migrations that have been applied.
Test migrations with: alembic upgrade head && alembic downgrade -1 && alembic upgrade head
Include both upgrade() and downgrade() in every migration.
```

---

## 3. AGENTS.md Support

| Property | Detail |
|----------|--------|
| **Location** | Project root or any subdirectory |
| **Format** | Plain Markdown (no frontmatter) |
| **Scope** | Always included in agent mode sessions |
| **Nesting** | Subdirectory AGENTS.md files combine with parents; more specific files take precedence |

AGENTS.md is a simpler alternative to `.mdc` rules when you don't need activation modes or glob scoping. It's always active and requires no configuration.

---

## 4. Directory Structure

```
your-project/
├── .cursor/
│   └── rules/
│       ├── project-conventions.mdc      # Always-on project standards
│       ├── react-components.mdc         # Glob-scoped to *.tsx
│       ├── api-endpoints.mdc            # Glob-scoped to src/api/**
│       ├── database.mdc                 # Intelligently applied
│       └── deployment.mdc               # Manual — @deployment to activate
├── AGENTS.md                            # Optional always-on alternative
└── src/
    └── AGENTS.md                        # Optional nested instructions
```

---

## 5. Priority and Precedence

When multiple rule sources exist (highest priority first):

1. **Team Rules** (Business/Enterprise admin dashboard)
2. **Project Rules** (`.cursor/rules/`)
3. **User Rules** (Cursor Settings)
4. **AGENTS.md** (always active in agent sessions)

Within project rules, more specific globs take precedence over broader ones.

---

## 6. Key Constraints

| Constraint | Limit |
|------------|-------|
| **Individual rule length** | 500 lines recommended maximum |
| **File extensions** | `.mdc` or `.md` |
| **Rule application scope** | Chat and Composer only |
| **Not applied to** | Inline Edit (Cmd/Ctrl+K), Cursor Tab autocomplete |
| **YAML frontmatter** | Must be valid YAML with correct indentation |

### Best Practices

- Write short, direct, instructive rules — no fluff
- Split large guidance into multiple composable rules
- Use `description` field for intelligent matching — be specific about when the rule applies
- Prefer `globs` for file-type-specific rules over relying on intelligent matching
- Keep `alwaysApply: true` rules minimal — they consume context in every session

---

## 7. Porting ai_skills to Cursor

Skills from this repo need minor adaptation for Cursor's `.mdc` format:

```bash
# Create the rules directory
mkdir -p .cursor/rules

# For each skill, convert SKILL.md to .mdc
# The content is the same — just change the frontmatter keys
```

**Conversion example:**

Original SKILL.md frontmatter:
```yaml
---
name: deploy-pipeline
description: Deployment pipeline automation for SSH/rsync, Docker, and Dockge stacks
---
```

Converted to `.mdc`:
```yaml
---
description: "Deployment pipeline automation for SSH/rsync, Docker, and Dockge stacks. Use when writing deploy scripts, configuring CI/CD pipelines, setting up Docker deployments, or managing Dockge stacks."
alwaysApply: false
---
```

The markdown body transfers directly — no content changes needed. The main differences are: drop `name` (Cursor uses the filename), rename to `.mdc` extension, and optionally add `globs` or `alwaysApply` for activation control.

---

## Sources

- [Cursor Docs: Rules](https://cursor.com/docs/context/rules)
- [Awesome Cursor Rules MDC](https://github.com/sanjeed5/awesome-cursor-rules-mdc)
- [Cursor Rules Reference](https://github.com/sanjeed5/awesome-cursor-rules-mdc/blob/main/cursor-rules-reference.md)
- [Cursor Rules Complete Guide (2026)](https://www.vibecodingacademy.ai/blog/cursor-rules-complete-guide)
