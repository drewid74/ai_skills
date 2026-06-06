---
name: full-sdlc
description: >-
  Guide complete software development lifecycle from requirements through
  production. Tech stack selection, ADR templates, branching strategy, testing
  pyramid, CI/CD, release management, observability setup, and architectural
  onboarding for new codebases.
triggers:
  - "design a new system"
  - "help me architect this project"
  - "start a new codebase"
  - "what's the right stack for"
  - "set up branching strategy"
  - "document architecture decision"
  - "plan release process"
  - "onboard to this codebase"
tags: [sdlc, architecture, adr, testing, release, ci-cd, onboarding]
author: merged
---

# Full SDLC

## Identity

Guide every phase of software development without skipping steps. Always document decisions as ADRs. Default to trunk-based development and the test pyramid. Prefer boring technology unless there's a specific reason not to.

## Stack Defaults

| Phase | Default | Notes |
|-------|---------|-------|
| Language | Python / TypeScript | Match team's existing skills |
| Database | PostgreSQL | Unless time-series → TimescaleDB |
| API framework | FastAPI / Express | Matches language default |
| Auth | JWT + refresh tokens | Or managed: Clerk, Auth0 |
| Branching | Trunk-based | Feature branches ≤ 3 days |
| CI | GitHub Actions | Or GitLab CI |
| IaC | Terraform + Ansible | Terraform for infra, Ansible for config |
| Observability | Prometheus + Grafana + Loki | → See grafana-prometheus-monitoring |

## Decision Framework

```
IF choosing tech stack:
  1. List non-negotiables (language, compliance, team skills)
  2. Evaluate 3 options against: performance, scalability, maintainability, cost
  3. Document as ADR before writing code
  4. Prefer what the team already knows unless gap is critical

IF structuring project:
  → apps/ | packages/ | tooling/ for monorepos
  → src/ | tests/ | docs/ | config/ per service

IF writing tests:
  → 70% unit (fast, isolated)
  → 20% integration (real dependencies, transaction rollback)
  → 10% E2E (critical user flows only)
  → Never skip tests for "speed" — they pay back immediately

IF deploying:
  → semver tags: MAJOR.MINOR.PATCH
  → staging always before production
  → blue-green or canary for zero-downtime
  → automated rollback if error rate > 2% post-deploy

IF something is slow/broken in production:
  → Logs (what happened) → Metrics (how often) → Traces (why slow)
```

## Anti-Patterns

| Anti-Pattern | Use Instead |
|--------------|-------------|
| No ADR for major decisions | ADR in `docs/adr/` before coding |
| Long-lived feature branches | Trunk-based, feature flags for incomplete features |
| "We'll add tests later" | Test pyramid from day one |
| Manual deployments | CI/CD pipeline with required checks |
| No monitoring until it breaks | Observability before first production deploy |
| Monolith vs microservices by default | Monolith first, split when clear boundary emerges |

## Quality Gates

- [ ] ADR written for each significant tech choice
- [ ] Test coverage ≥ 80% for business logic
- [ ] CI passes before merge (lint + test + security scan)
- [ ] Staging environment matches production config
- [ ] Rollback procedure documented and tested
- [ ] On-call runbook exists for production service

→ See `cicd-pipeline` for GitHub Actions / GitLab CI patterns  
→ See `code-reviewer` for review checklist  
→ See `grafana-prometheus-monitoring` for observability stack  
→ See `github-workflow` for branch/PR strategy details

---

## Phase 1: Requirements & Scoping

### MoSCoW Prioritization

```
Must Have (M):  Non-negotiable. Project fails without these.
Should Have (S): Important but deferrable under timeline pressure.
Could Have (C):  Nice-to-have. Implement if time allows.
Won't Have (W):  Explicitly out of scope this release.

Example — User Auth feature:
  M: Email/password login, email verification
  S: Social login (GitHub, Google)
  C: Profile picture upload
  W: Video onboarding tutorial (defer to v2)

M+S = 3 weeks | M+S+C = 5 weeks → cut C if shipping at 3 weeks
```

### User Story Format

```
As a <user> I want <capability> so that <business value>

Acceptance Criteria:
  Given <precondition>
  When <action>
  Then <outcome>

Edge cases:
  - Empty/null input behavior
  - Concurrent operation behavior
  - Permission boundary behavior
```

---

## Phase 2: Architecture Decision Records

### ADR Template

```markdown
# ADR-NNN: <Decision Title>

## Status: [Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

## Context
- What is the problem?
- What constraints apply? (team size, SLA, compliance)

## Decision
We will use <X> because <Y>.

## Consequences
- Benefits: ...
- Risks: ...
- Mitigation: ...

## Alternatives Considered
- Option B: <why rejected>
- Option C: <why rejected>
```

Example populated:

```markdown
# ADR-001: PostgreSQL + TypeScript + Turborepo

## Status: Accepted

## Context
- 5 services sharing domain logic
- Team experienced in Node.js
- Complex data relationships

## Decision
PostgreSQL (ACID, JSON, extensions) + TypeScript (type safety) + Turborepo (caching, pipelining)

## Consequences
- Benefits: Type safety across API boundary, strong consistency
- Risks: TypeScript compile overhead, Postgres ops required
- Mitigation: Invest in tooling, runbook docs

## Alternatives Considered
- MySQL: Weaker consistency historically
- MongoDB: Horizontal scaling easier but eventual consistency
```

---

## Phase 3: Project Structure

```
# Monorepo (Turborepo)
.
├── apps/
│   ├── web/          (Next.js)
│   ├── api/          (Node.js/FastAPI)
│   └── worker/       (background jobs)
├── packages/
│   ├── shared/       (domain types, utilities)
│   ├── ui/           (reusable components)
│   └── database/     (schema, migrations)
├── turbo.json
└── pnpm-workspace.yaml

# Single service
src/
├── api/          (routes, handlers)
├── services/     (business logic, no I/O)
├── db/           (queries, migrations)
├── workers/      (async jobs)
└── utils/        (pure utilities)
tests/
├── unit/
├── integration/
└── e2e/
docs/
└── adr/          (ADR-001.md, ADR-002.md, ...)
```

---

## Phase 4: Testing Pyramid

```
         /E2E\       10% — Full user flow, real browser (Playwright)
        /------\
       /Integr  \    20% — Real DB + API (TestClient, testcontainers)
      /----------\
     / Unit       \  70% — Pure logic, mocked I/O (pytest, Vitest)
    /--------------\
```

### Test naming convention

`test_<what>_<condition>_<expected_outcome>`

```python
# Good:
def test_process_payment_with_expired_card_returns_402(): ...
def test_create_user_duplicate_email_raises_conflict(): ...

# Bad:
def test_payment(): ...
def test_user_2(): ...
```

### Coverage targets

```
Business logic:   90%
API handlers:     80%
UI components:    60%
DB queries:       100% (integration tests)
Infrastructure:   80%
```

---

## Phase 5: CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run test:ci
      - run: npm run lint

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run build
      - name: Blue-green deploy
        run: |
          NEW_ID=$(npm run deploy:new-version)
          npm run smoke-test -- $NEW_ID
          npm run cutover -- $NEW_ID
```

---

## Phase 6: Release Management

### Semantic Versioning

```
MAJOR.MINOR.PATCH
  Breaking features  Fixes

Process:
  1. git tag v1.2.3
  2. generate changelog: git log v1.2.2..v1.2.3 --oneline
  3. write release notes (include migration guide for MAJOR)
  4. deploy staging → verify → deploy production
  5. monitor error rate for 30 min
  6. automated rollback if error rate > 2%
```

---

## Phase 7: Maintenance & Observability

### Observability Triad

```
Logs (what happened):
  ERROR: Payment failed for order #123: Stripe timeout
  Context: user_id=456, amount=$99.99, retry_count=2

Metrics (how much / how often):
  payment_duration_ms{quantile="0.95"} 450
  payment_failures_total{reason="stripe_timeout"} 15

Traces (why slow):
  Request → ValidateOrder(5ms) → ChargeCard(450ms) → UpdateInventory(20ms)
  Slow span: ChargeCard (network + retries)

Alert thresholds:
  error_rate > 1%: page on-call
  p99_latency > 2s: investigate
  failed_deploy: rollback automatically
```

---

## Codebase Onboarding Checklist

When inheriting or auditing an existing project:

```
STRUCTURE
□ Clear folder organization (src/, tests/, docs/, config/)
□ Entry points documented
□ Appropriate .gitignore (no secrets, no build artifacts)

CONTENT QUALITY
□ README with setup + usage
□ CONTRIBUTING.md exists
□ LICENSE file present
□ ADRs in docs/adr/ or equivalent
□ No dead code / unused imports

DEPENDENCY HEALTH
□ Lock file committed (package-lock.json, uv.lock, go.sum)
□ npm audit / pip-audit / trivy clean
□ No major version outdated without reason

AI-READINESS
□ Architecture document (ARCHITECTURE.md or ADRs)
□ Key flows documented (auth, payment, data ingestion)
□ API contracts (OpenAPI or GraphQL schema)
□ Error patterns documented
```
