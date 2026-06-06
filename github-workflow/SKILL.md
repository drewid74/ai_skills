---
name: github-workflow
description: >-
  Expert GitHub workflow automation. Branch strategy, PR lifecycle, protected
  branches, Actions CI/CD, GitHub MCP tool orchestration, compound operations
  (PR creation → review → merge), and repository management patterns.
triggers:
  - "create PR and request review"
  - "set up branch protection"
  - "automate GitHub workflow"
  - "PR lifecycle management"
  - "manage issues and milestones"
  - "compound GitHub operations"
  - "GitHub Actions pipeline"
  - "fork and PR workflow"
tags: [github, git, pr, actions, ci-cd, branch-strategy, mcp]
author: merged
---

# GitHub Workflow

## Identity

Execute complete GitHub workflows — branch, commit, PR, review, merge — without stopping to ask for clarification. Default to trunk-based development. Never leave a PR open without review requested. Always set base branch explicitly.

## Stack Defaults

| Operation | Default | Notes |
|-----------|---------|-------|
| Branch model | Trunk-based | Feature branches ≤ 3 days |
| PR size | ≤ 400 lines changed | Split larger PRs |
| Merge strategy | Squash merge | Clean linear history |
| Branch protection | Require 1 review + CI | On `main` always |
| Commit style | Conventional commits | `feat:`, `fix:`, `chore:` |
| Issue tracking | Labels + milestones | `bug`, `feature`, `tech-debt` |

## Decision Framework

```
IF starting new feature:
  → create_branch from main: feature/short-description
  → commits follow conventional commit format
  → PR when: tests pass, description has Why + What
ELIF reviewing PR:
  → check: tests added?, breaking change?, security impact?
  → request changes on: missing tests, hardcoded secrets, N+1 queries
  → approve on: correct logic, tested, matches ticket
ELIF merging:
  → squash merge preferred (clean history)
  → delete branch after merge
  → close linked issues with "Closes #NNN"
IF hotfix needed:
  → branch from main: hotfix/description
  → PR with [HOTFIX] prefix
  → merge → tag immediately
IF compound operation (create PR + review + merge):
  → create_branch → push_files → create_pull_request
  → add_issue_comment (review notes) → merge_pull_request
```

## Anti-Patterns

| Anti-Pattern | Use Instead |
|--------------|-------------|
| Long-lived feature branches (>3 days) | Trunk-based with feature flags |
| Force-push to main | Branch protection + squash merge |
| PR with no description | Template: Why / What / Testing / Breaking |
| Merging without CI passing | Require status checks in branch protection |
| Secrets in commit history | GitHub Secrets + `git filter-repo` to purge |
| 1000-line PRs | Split into logical atomic PRs |

## Quality Gates

- [ ] Branch protection on `main`: require reviews + status checks
- [ ] PR template exists (`.github/pull_request_template.md`)
- [ ] Issue labels defined: `bug`, `feature`, `tech-debt`, `blocked`
- [ ] CI runs on every PR (at minimum: lint + test)
- [ ] No secrets in repository history
- [ ] `CODEOWNERS` defined for critical paths

→ See `cicd-pipeline` for GitHub Actions workflow patterns  
→ See `security-engineer` for supply chain hardening (branch protection, signed commits)

---

## GitHub MCP Tool Reference

When the GitHub MCP is connected, these tools are available for compound operations:

| Tool | Purpose |
|------|---------|
| `create_branch` | Create new branch from base |
| `push_files` | Push one or more files in single commit |
| `create_pull_request` | Open PR with title, body, base, head |
| `get_pull_request` | Fetch PR details, status, reviews |
| `merge_pull_request` | Merge with squash/merge/rebase strategy |
| `create_pull_request_review` | Submit review (APPROVE/REQUEST_CHANGES/COMMENT) |
| `get_pull_request_files` | List changed files in PR |
| `create_issue` | Open issue with labels, assignees |
| `update_issue` | Edit issue state, labels, assignees |
| `add_issue_comment` | Comment on issue or PR |
| `list_commits` | List recent commits on branch |
| `get_file_contents` | Read file at ref/branch |
| `search_code` | Full-text search across repos |
| `fork_repository` | Fork for external contribution |

## Compound Operation: Full PR Lifecycle

```python
# Step 1: Create branch
create_branch(repo="owner/repo", branch="feature/add-auth", from_branch="main")

# Step 2: Push changes
push_files(
    repo="owner/repo",
    branch="feature/add-auth",
    files=[{"path": "src/auth.py", "content": "..."}],
    message="feat: add JWT authentication middleware"
)

# Step 3: Open PR
pr = create_pull_request(
    repo="owner/repo",
    title="feat: add JWT authentication middleware",
    body="""## Why
Unauthenticated endpoints are accessible. Closes #42.

## What
- JWT middleware validates tokens on protected routes
- 401 on missing/invalid tokens
- Tests cover valid, expired, and malformed tokens

## Breaking Changes
None — all existing unprotected routes unchanged.""",
    head="feature/add-auth",
    base="main",
    draft=False
)

# Step 4: Request review
add_issue_comment(
    repo="owner/repo",
    issue_number=pr["number"],
    body="@teammate please review auth middleware logic in `src/auth.py`"
)
```

## Branch Protection Configuration

```yaml
# Via GitHub API or UI: Settings → Branches → Add rule
branch: main
rules:
  require_pull_request_reviews:
    required_approving_review_count: 1
    dismiss_stale_reviews: true
  require_status_checks:
    strict: true                  # Branch must be up to date
    contexts:
      - "ci/test"
      - "ci/lint"
  require_conversation_resolution: true
  restrict_force_pushes: true
  restrict_deletions: true
```

## PR Template (`.github/pull_request_template.md`)

```markdown
## Why
<!-- What problem does this solve? Link to issue: Closes #NNN -->

## What changed
<!-- Summary of changes -->

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing steps: 

## Breaking changes
<!-- List any breaking changes, or "None" -->

## Checklist
- [ ] No secrets or credentials committed
- [ ] Documentation updated (if applicable)
- [ ] `CHANGELOG.md` updated (for library releases)
```

## GitHub Actions: Branch Trigger Patterns

```yaml
# .github/workflows/pr-checks.yml
name: PR Checks

on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip
      - run: pip install -r requirements.txt
      - run: pytest --tb=short -q

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install ruff
      - run: ruff check .
```

## Conventional Commits Reference

```
feat:     New feature (minor version bump)
fix:      Bug fix (patch version bump)
chore:    Maintenance (no version bump)
docs:     Documentation only
refactor: Code change without feature/fix
test:     Test additions/changes
perf:     Performance improvement
ci:       CI/CD changes
build:    Build system changes
BREAKING CHANGE: footer note → major version bump

Examples:
  feat: add OAuth2 PKCE flow for mobile clients
  fix: resolve race condition in worker pool shutdown
  chore(deps): bump httpx from 0.27.0 to 0.28.1
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| PR blocked by stale review | Review dismissed by new commit | Re-request review; enable "dismiss stale reviews" |
| CI passes locally, fails on PR | Environment diff (secrets, OS) | Use `act` locally to simulate GH Actions runner |
| Merge conflict on PR | Long-lived branch diverged | `git fetch && git rebase origin/main` |
| Branch protection bypass needed | Emergency hotfix | Temporarily disable rule as admin; re-enable immediately |
| Secrets found in commit | Hardcoded credentials | `git filter-repo --path-regex`; rotate credentials immediately |
| PR auto-merge not triggering | Required checks not reporting | Verify workflow name matches branch protection context string |
