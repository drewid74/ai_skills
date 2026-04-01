# GitHub Copilot — Skill Building Capabilities Catalog

> Generated: 2026-03-31 | Purpose: Reference for building custom instructions and agent skills for GitHub Copilot

---

## 0. Platform Overview

GitHub Copilot supports custom instructions across multiple surfaces: VS Code, JetBrains, GitHub.com, Copilot CLI, and the Copilot coding agent. The instruction system uses three file types with hierarchical precedence, plus the newer Agent Skills standard for portable, reusable capabilities.

**Plans that support custom instructions:** Copilot Individual, Copilot Business, Copilot Enterprise

---

## 1. Instruction File Types

### Repository-Wide Instructions (`copilot-instructions.md`)

| Property | Detail |
|----------|--------|
| **Location** | `.github/copilot-instructions.md` |
| **Format** | Plain Markdown (no frontmatter required) |
| **Scope** | All files in the repository |
| **Applied to** | Chat, code completions, code review, Copilot CLI |
| **Priority** | Below personal instructions, above organization instructions |

**What to put here:** Project-wide coding standards, preferred frameworks, naming conventions, testing requirements, architectural patterns. Think of it as the project's "house style" document.

**Example:**
```markdown
## Code Standards
- Use TypeScript strict mode for all new files
- Prefer functional components with hooks over class components
- All API endpoints must include OpenAPI JSDoc annotations
- Use pnpm as the package manager, never npm or yarn
- Error responses follow RFC 7807 Problem Details format

## Testing
- Every PR must include tests; use Vitest for unit tests
- Integration tests use Testcontainers for database dependencies
- Minimum 80% branch coverage for new code
```

### Path-Specific Instructions (`.instructions.md`)

| Property | Detail |
|----------|--------|
| **Location** | `.github/instructions/*.instructions.md` (or anywhere in repo) |
| **Format** | Markdown with YAML frontmatter |
| **Scope** | Files matching the `applyTo` glob pattern |
| **Applied to** | Chat and code completions when matching files are in context |

**Frontmatter fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `applyTo` | Yes | Glob pattern (e.g., `"**/*.test.ts"`, `"src/api/**"`) |

**Example:**
```markdown
---
applyTo: "src/components/**/*.tsx"
---
Use Tailwind CSS utility classes exclusively — no CSS modules or styled-components.
All components must accept a `className` prop for composition.
Use `forwardRef` for any component that wraps a native HTML element.
Prefer `clsx` for conditional class names.
```

### Organization Instructions

| Property | Detail |
|----------|--------|
| **Configuration** | Admin settings in github.com organization |
| **Format** | Plain text entered in the UI |
| **Scope** | All repositories in the organization |
| **Priority** | Lowest (personal > repo > org) |

---

## 2. Agent Skills (Open Standard)

Agent Skills are the portable, reusable capability format — the same open standard used by VS Code Copilot, Codex CLI, Gemini CLI, and Claude Code.

### SKILL.md Format

| Field | Required | Constraint | Description |
|-------|----------|------------|-------------|
| `name` | Yes | Max 64 chars, lowercase with hyphens, must match directory name | Unique skill identifier |
| `description` | Yes | Max 1,024 chars | What the skill does AND when to use it |
| `argument-hint` | No | — | Hint text shown in chat when invoked as slash command |
| `user-invocable` | No | Default: `true` | Whether skill appears in "/" menu |
| `disable-model-invocation` | No | Default: `false` | If `true`, requires manual invocation only |

### Directory Structure

```
skill-name/
├── SKILL.md              # Required — YAML frontmatter + markdown instructions
├── scripts/              # Optional — executable code
├── references/           # Optional — documentation loaded as needed
└── assets/               # Optional — templates, examples, resources
```

### Storage Locations

| Scope | Location | Use Case |
|-------|----------|----------|
| **Project** | `.github/skills/` | Repo-specific skills, version-controlled |
| **Project (aliases)** | `.claude/skills/`, `.agents/skills/` | Cross-platform compatibility |
| **Personal** | `~/.copilot/skills/` | Your skills, all projects |
| **Personal (aliases)** | `~/.claude/skills/`, `~/.agents/skills/` | Cross-platform compatibility |
| **Custom** | Configurable via `chat.skillsLocations` setting in VS Code | Additional skill directories |

### Invocation Methods

| Method | How | When |
|--------|-----|------|
| **Slash command** | Type `/` in chat, select skill | On-demand, user-initiated |
| **Auto-loading** | Copilot matches task to skill description | Automatic, context-driven |
| **Direct reference** | `/skill-name for login page` | On-demand with context |

### Invocation Control Matrix

| `user-invocable` | `disable-model-invocation` | Slash Command | Auto-Load |
|---|---|---|---|
| `true` (default) | `false` (default) | Yes | Yes |
| `false` | `false` | No | Yes |
| `true` | `true` | Yes | No |
| `false` | `true` | No | No |

---

## 3. Copilot CLI Instructions

| Property | Detail |
|----------|--------|
| **Location** | `~/.github/copilot-cli-instructions.md` |
| **Format** | Plain Markdown |
| **Scope** | All Copilot CLI interactions |

**Example:**
```markdown
Prefer POSIX-compatible commands over bash-specific syntax.
Use `fd` instead of `find` when available.
Always use `--dry-run` flags when available for destructive operations.
Default to interactive confirmation for file deletions.
```

---

## 4. Code Review Instructions

Custom instructions can specifically target Copilot's code review feature by including review-focused guidance in `copilot-instructions.md`:

```markdown
## Code Review Focus Areas
- Flag any use of `any` type in TypeScript
- Verify all database queries use parameterized statements
- Check that error boundaries exist around async operations
- Ensure new API endpoints have rate limiting
- Warn about missing input validation on public endpoints
```

---

## 5. AGENTS.md Support

| Property | Detail |
|----------|--------|
| **Location** | Repository root or any subdirectory |
| **Format** | Plain Markdown |
| **Scope** | Always included in agent mode sessions |
| **Nesting** | Subdirectory AGENTS.md files combine with parent |

AGENTS.md provides always-on instructions for Copilot's agent mode. Unlike `.instructions.md` files, it requires no frontmatter and no glob patterns — it's always active.

---

## 6. Priority and Precedence

When multiple instruction sources exist, Copilot merges them with this priority (highest first):

1. **Personal instructions** (user settings)
2. **Repository instructions** (`copilot-instructions.md`)
3. **Path-specific instructions** (`.instructions.md` with matching `applyTo`)
4. **Organization instructions** (admin-configured)
5. **Agent Skills** (loaded on-demand based on task)
6. **AGENTS.md** (always-on in agent mode)

---

## 7. Key Constraints

- Instructions are additive — they don't override each other, they combine
- Keep `copilot-instructions.md` concise; extremely long files may be truncated
- `.instructions.md` files only activate when files matching `applyTo` are in the conversation context
- Agent Skills use progressive disclosure — only metadata loads initially, full SKILL.md loads on activation
- Skill `name` must exactly match the parent directory name
- Skills work in VS Code, Copilot CLI, and the Copilot coding agent — not in github.com chat (yet)

---

## 8. Porting ai_skills to Copilot

To use skills from this repo with GitHub Copilot:

```bash
# Option 1: Symlink into personal skills directory
mkdir -p ~/.copilot/skills
ln -s /path/to/ai_skills/truenas-ops ~/.copilot/skills/truenas-ops

# Option 2: Copy into a repo's .github/skills/
cp -r /path/to/ai_skills/deploy-pipeline .github/skills/deploy-pipeline

# Option 3: Use .agents/skills/ for cross-platform compatibility
cp -r /path/to/ai_skills/deploy-pipeline .agents/skills/deploy-pipeline
```

No format conversion needed — the SKILL.md format is natively compatible.

---

## Sources

- [GitHub Docs: Configure Custom Instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions)
- [GitHub Docs: Adding Repository Custom Instructions](https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)
- [GitHub Docs: Creating Agent Skills](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-skills)
- [VS Code: Agent Skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
- [VS Code: Custom Instructions](https://code.visualstudio.com/docs/copilot/customization/custom-instructions)
- [GitHub Awesome Copilot](https://github.com/github/awesome-copilot)
