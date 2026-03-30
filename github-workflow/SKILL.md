---
name: github-workflow
description: "Use this skill whenever the user wants to manage GitHub repositories, automate Git workflows, create or review pull requests, manage issues, set up CI/CD pipelines, or work with GitHub Actions. Triggers include: any mention of 'GitHub', 'git', 'repo', 'repository', 'pull request', 'PR', 'issue', 'branch', 'merge', 'CI/CD', 'GitHub Actions', 'workflow', '.github', 'release', 'deploy', or requests to review code, manage branches, automate builds, or set up project structure. Also use when the user wants to create README files, LICENSE files, .gitignore, branch protection rules, or any repository scaffolding. If the user mentions wanting to organize a project on GitHub, track bugs with issues, or automate any part of their development workflow, use this skill."
---

# GitHub Workflow Automation Skill

## Overview

Streamline GitHub repository management, PR workflows, issue tracking, CI/CD setup, and project organization using the GitHub MCP tools.

## Available GitHub MCP Tools

This skill leverages the full GitHub MCP toolset:

**Repos**: create_repository, fork_repository, search_repositories, get_file_contents, create_or_update_file, push_files, create_branch, list_commits
**Issues**: create_issue, get_issue, list_issues, update_issue, add_issue_comment, search_issues
**PRs**: create_pull_request, get_pull_request, list_pull_requests, get_pull_request_files, get_pull_request_comments, get_pull_request_reviews, get_pull_request_status, create_pull_request_review, merge_pull_request, update_pull_request_branch
**Search**: search_code, search_issues, search_repositories, search_users

## Repository Setup Workflow

When creating a new repository:

1. **Create the repo** with `create_repository` (private by default, ask user)
2. **Push initial structure** with `push_files` in a single commit:
   - README.md with project description, setup instructions, usage
   - .gitignore appropriate for the language/framework
   - LICENSE (ask user: MIT, Apache 2.0, GPL, etc.)
   - .github/ISSUE_TEMPLATE/ with bug report and feature request templates
   - .github/PULL_REQUEST_TEMPLATE.md
3. **Set up branches**: Create `develop` branch if the user wants a Git Flow model

### .gitignore Generation

Ask what language/framework and generate comprehensive .gitignore. Common patterns:

- **Node.js**: node_modules/, dist/, .env, *.log
- **Python**: __pycache__/, *.pyc, venv/, .env, dist/, *.egg-info/
- **Docker**: .env, docker-compose.override.yml
- **General**: .DS_Store, .vscode/, .idea/, *.swp

### GitHub Actions CI/CD

When the user wants automated builds/tests/deploys, generate `.github/workflows/` files:

**Basic CI template** (adapt per language):
```yaml
name: CI
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up environment
        # Language-specific setup
      - name: Install dependencies
        # Package manager install
      - name: Run tests
        # Test runner command
      - name: Build
        # Build command
```

**Docker build + push workflow**: Build image, push to GHCR or Docker Hub, with caching.

**Release workflow**: Auto-create releases on tag push with changelog generation.

## PR Management Workflow

### Creating PRs
When the user wants to create a PR:
1. Check current branch state with `list_commits`
2. Create PR with `create_pull_request` including clear title and body
3. Body format: Summary bullets, test plan, any breaking changes

### Reviewing PRs
When asked to review a PR:
1. `get_pull_request` for overview (title, description, base/head)
2. `get_pull_request_files` to see what changed
3. `get_pull_request_status` to check CI status
4. Read the actual diff to provide substantive review
5. `create_pull_request_review` with specific comments on files/lines

### PR Hygiene
- Always check CI status before suggesting merge
- Prefer squash merge for feature branches (cleaner history)
- Use rebase merge for small fixes (preserves commit messages)
- Regular merge for long-lived branches with meaningful history

## Issue Management

### Creating Issues
Structure issues clearly:
- **Bug reports**: Steps to reproduce, expected vs actual behavior, environment details
- **Feature requests**: User story format, acceptance criteria, priority suggestion
- **Tasks**: Clear definition of done, checklist of sub-tasks in the body

### Issue Triage
When managing a backlog:
1. `list_issues` with filters (state, labels, sort)
2. Suggest labeling scheme: bug, enhancement, documentation, good-first-issue, priority-high/medium/low
3. Use milestones for release planning

## Branch Strategy Recommendations

**For solo/small projects**: Trunk-based development
- Work on `main`, use short-lived feature branches
- Merge via PR for code review habit even if solo

**For team projects**: GitHub Flow
- `main` is always deployable
- Feature branches from `main`, PR back to `main`
- Deploy on merge

**For release-based projects**: Git Flow
- `main` for production, `develop` for integration
- `feature/*` from develop, `release/*` for release prep
- `hotfix/*` from main for emergency fixes

## Useful Compound Operations

**Find and fix**: Search code for a pattern, create a branch, push the fix, open a PR:
1. `search_code` to find instances
2. `create_branch` for the fix
3. `create_or_update_file` with the changes
4. `create_pull_request` with description of what was fixed

**Bulk issue creation**: When the user has a list of tasks, create multiple issues with consistent labeling and milestone assignment.

**PR status dashboard**: List open PRs with their CI status, review status, and staleness.

## Output Format

When performing GitHub operations, always report back:
- What was created/modified (with links where possible)
- Any follow-up actions needed
- Relevant URLs (repo, PR, issue links)
