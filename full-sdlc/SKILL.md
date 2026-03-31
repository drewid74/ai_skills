---
name: full-sdlc
description: "Use this skill whenever the user wants to plan, scaffold, build, test, or ship a software project end-to-end. Triggers include: any mention of 'new project', 'start a project', 'scaffold', 'boilerplate', 'project setup', 'SDLC', 'software development lifecycle', 'architecture', 'tech stack', 'project structure', 'monorepo', 'microservices', 'testing strategy', 'CI/CD pipeline', 'release process', 'versioning', 'semantic versioning', 'changelog', 'documentation', 'code quality', 'linting', 'formatting', 'pre-commit hooks', 'project management', 'sprint planning', 'technical debt', 'refactoring', 'migration', 'upgrade path', or requests to help plan, organize, or execute a software project from idea to production. Also use when the user asks 'how should I structure this?', 'what's the best stack for X?', 'help me plan this feature', or wants guidance on development workflow, branching strategies, or release management. If someone has an idea and wants to turn it into working software, use this skill."
---

## Overview

Guide projects from idea through production. Cover requirements gathering, architecture decisions, project scaffolding, development workflow, testing, CI/CD, release management, and maintenance. Match technical decisions to constraints, not trends. Start simple—complexity costs more than people predict.

## Phase 1: Requirements & Planning

### Gathering Requirements
Ask before coding: Who uses this? What problem does it solve? Budget? Timeline? Hardware? Document as user stories: "As a [role], I want [capability] so that [benefit]."

Use MoSCoW: Must-have vs Should-have vs Could-have vs Won't-do. This filters scope creep early.

Identify constraints: hosting, languages, team skills, existing infrastructure. These drive tech decisions.

### Architecture Decision Records (ADRs)

Document every significant choice in `docs/decisions/ADR-001-database-choice.md`. Format:

```
Title: Choose PostgreSQL over MongoDB
Status: Accepted
Context: Need relational schema, complex joins, strong consistency
Decision: Use PostgreSQL with Prisma ORM
Consequences: SQL learning curve; excellent for our schema; scales well
```

Why? Future-you (or your team) will forget WHY you chose PostgreSQL.

### Tech Stack Selection

Match to constraints, not hype. Default picks:

- **Backend**: FastAPI (Python), Express (Node), Axum (Rust)—pick based on team expertise
- **Database**: PostgreSQL first (relational), MongoDB only if truly schema-less, Redis for caching
- **Frontend**: React/Vue/Svelte—choose based on project scale and team comfort
- **Hosting**: Docker → container registry → orchestration (start with Fly.io, Railway, or self-hosted)

Monolith vs microservices? Start monolith unless you have a specific deployment reason for splitting.

## Phase 2: Project Scaffolding

### Directory Structure

**Python (FastAPI):**
```
project/
├── src/api/          # Route handlers
├── src/core/         # Business logic
├── src/models/       # Data models
├── src/services/     # External integrations
├── tests/            # unit/, integration/
├── docs/decisions/   # ADRs
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── README.md
```

**TypeScript (Next.js/Express):**
```
project/
├── src/app/          # Pages/routes
├── src/lib/          # Business logic
├── src/services/     # API clients
├── src/types/        # Type definitions
├── tests/
├── docker-compose.yml
├── package.json
├── tsconfig.json
├── .env.example
└── README.md
```

### Essential Files

- **README.md**: What it does, how to run, how to contribute
- **.gitignore**: Language-appropriate + IDE files + .env
- **.env.example**: Every environment variable with placeholders (committed)
- **LICENSE**: MIT for open source, proprietary for private
- **Dockerfile + docker-compose.yml**: Containerize day one
- **CONTRIBUTING.md**: If anyone else touches the code

### Configuration Management

Use environment variables (12-factor app). Parse at startup into a typed config object, validate required fields immediately, fail fast if missing. Store `.env` in gitignore, `.env.example` in git.

## Phase 3: Development Workflow

### Branching Strategy

**Trunk-based** (recommended for small teams): develop on main, short-lived feature branches, merge daily. Requires CI discipline but eliminates merge hell.

**GitHub Flow**: main is always deployable, feature branches for changes, PRs for review. Simpler than Git Flow.

**Git Flow**: develop/main/feature/release/hotfix—only if you need explicit release management. Complexity = merge pain.

Rule: simpler is better.

### Commit Conventions

Use Conventional Commits: `type(scope): description`

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `perf`

Example: `feat(auth): add JWT refresh token rotation`

Why? Enables automatic changelog and semantic versioning. Use `commitlint` pre-commit hook to enforce.

### Code Quality

Set up early (retrofitting is painful):

- **Linting**: ESLint (JS), Ruff (Python), clippy (Rust)
- **Formatting**: Prettier (JS), Black (Python), rustfmt (Rust)
- **Pre-commit hooks**: Husky (JS) or pre-commit framework (Python)
- **Type checking**: TypeScript strict mode, mypy (Python)

Run these before commit, not after.

### Local Development

Use Docker Compose for all external services (database, Redis, message queue). Hot reload: nodemon (Node), uvicorn --reload (Python). Seed data scripts populate test database. Document setup so new developers clone → run → working in under 5 minutes.

## Phase 4: Testing Strategy

### The Testing Pyramid

- **Unit** (70%): test functions in isolation, mock external dependencies, fastest
- **Integration** (20%): test components together, use real database
- **E2E** (10%): test full user workflows, slowest but highest confidence

### Patterns

**Arrange-Act-Assert**: set up data → execute action → verify result.

**Fixtures**: reusable test data (pytest fixtures, Jest beforeEach).

**Mocking**: replace dependencies with controlled fakes.

**Test naming**: `test_login_with_invalid_password_returns_401` reads as documentation.

### When to Test

During development: run relevant tests in watch mode. Before merging: full suite in CI. Before release: full suite + manual smoke testing. Aim for 80% coverage—100% is diminishing returns.

## Phase 5: CI/CD Pipeline

### GitHub Actions Template

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Lint
      - name: Type check
      - name: Unit tests
      - name: Integration tests
      - name: Build

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
```

### Pipeline Stages

1. Lint & format check
2. Type check
3. Unit tests
4. Integration tests
5. Build artifact
6. Deploy (main branch only)

### Deployment Strategies

- **Direct**: push to main → deploy immediately (good for small teams with high confidence)
- **Staging → production**: deploy to staging, manual approve to production (safer)
- **Blue-green**: two production environments, switch traffic (zero downtime, rollback friendly)
- **Feature flags**: deploy code, toggle features independently (decouple deploy from release)

## Phase 6: Release Management

### Semantic Versioning

`MAJOR.MINOR.PATCH` (e.g., 1.4.2)

- MAJOR: breaking changes
- MINOR: new features (backward compatible)
- PATCH: bug fixes

Automate with `semantic-release`, `release-please`, or `standard-version`—they parse conventional commits and bump versions automatically.

### Changelog

Auto-generate from commits. Group by type (Features, Fixes, Breaking Changes). Ship with every release—users and contributors need it.

### Release Checklist

1. All tests passing on main
2. Changelog updated
3. Version bumped in `package.json` / `pyproject.toml`
4. Git tag created (`git tag v1.4.2`)
5. Release notes published (GitHub Releases)
6. Deploy to production
7. Monitor post-release

## Phase 7: Maintenance

### Technical Debt

Track issues tagged `tech-debt`. Dedicate 10-20% of each sprint to reducing it. Prioritize debt that slows daily development over debt that might cause problems someday.

### Dependencies

Automate updates with Dependabot or Renovate. Strategy: patch versions automatically, minor with review, major manually. Always commit lock files (`package-lock.json`, `poetry.lock`, `Cargo.lock`).

### Production Monitoring

- Health check endpoint: `/health` or `/healthz`
- Structured logging: JSON format for parsing
- Error tracking: Sentry or self-hosted
- Uptime monitoring: Uptime Kuma
- Key metrics: response time, error rate, resource usage

## Troubleshooting

- **"Works on my machine"**: containerize with Docker, pin dependency versions
- **Merge conflicts**: merge main into feature branches daily, keep PRs small
- **Flaky tests**: isolate dependencies, don't share test state, use deterministic data
- **Slow CI**: cache dependencies, run tests in parallel, skip unchanged modules
- **Scope creep**: refer back to requirements, defer nice-to-haves to backlog
