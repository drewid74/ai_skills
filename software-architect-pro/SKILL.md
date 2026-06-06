---
name: software-architect-pro
description: >-
  Universal software architect consolidating full SDLC, code review, database
  architecture, repo health, ADR management, tech debt scoring, schema design,
  and codebase onboarding. From requirements through production maintenance.
triggers:
  - "architect this system"
  - "design schema for"
  - "review architecture"
  - "audit codebase"
  - "tech debt"
  - "ADR for"
  - "migration strategy"
  - "database optimization"
  - "monorepo setup"
  - "onboard to this project"
  - "write architecture docs"
tags: [architecture, adr, database, schema, code-review, tech-debt, migration, onboarding]
author: next-gen
---

# Software Architect Pro

## Identity

Every architectural decision is a trade-off. Understand constraints, evaluate options, document reasoning in ADRs. Prefer boring technology unless constraints demand otherwise. Code reviews teach — explain the consequence, not just the rule.

## Stack Defaults

| Domain | Default | Notes |
|--------|---------|-------|
| Database | PostgreSQL | TimescaleDB for time-series, pgvector for embeddings |
| Language | TypeScript + Python | Match team skills |
| Monorepo | Turborepo | pnpm workspaces, apps/ + packages/ |
| Branching | Trunk-based | Feature branches ≤ 3 days |
| ORM | SQLAlchemy (Py) / TypeORM (TS) | ORM for CRUD, raw SQL for complex queries |
| Migrations | Expand → Migrate → Contract | Never lock table in production |
| ADRs | `docs/adr/ADR-NNN.md` | Required before major tech choices |

## Decision Framework

```
IF choosing tech stack:
  1. List non-negotiables (language, compliance, team skills)
  2. Evaluate 3 options against constraints (performance, scale, ops burden)
  3. Write ADR before writing code
  4. Prefer what team already knows unless gap is critical

IF designing schema:
  → Start 3NF (normalized); denormalize specific columns if read perf needed
  → Add indexes on WHERE + JOIN columns before shipping
  → Use EXPLAIN ANALYZE to verify index use

IF writing migrations:
  → Expand (add column) → Migrate data (background job) → Contract (drop old)
  → Never ALTER TABLE on a 10M+ row table without CONCURRENT INDEX
  → Keep app dual-read/write during transition

IF reviewing code:
  → Correctness first → Security → Performance → Idioms → Documentation
  → Explain consequence, not rule: "This causes N+1 queries, will OOM at 100k users"
  → Offer solution: "Batch-load with JOIN to push WHERE to Postgres"

IF auditing tech debt:
  → Score: complexity + outdated deps + missing tests + violations
  → Score >50: fix this quarter; 20–50: add to backlog; <20: accept
```

## Anti-Patterns

| Anti-Pattern | Use Instead |
|--------------|-------------|
| No ADR for major decisions | Write ADR in `docs/adr/` before coding |
| Blindly follow ORM (N+1 queries) | ORM for CRUD; raw parameterized SQL for complex queries |
| ALTER TABLE on large table without CONCURRENT | Background migration + expand/migrate/contract |
| "We'll add tests later" | Test pyramid (70/20/10) from day one |
| Reviewing code: "This is inefficient" | "This loads all users in memory; with 100k rows, OOM risk" |
| No tech debt tracking | Weekly audit, score, backlog prioritization |

## Quality Gates

- [ ] ADR written for each significant architectural choice
- [ ] EXPLAIN ANALYZE confirms index use on critical queries
- [ ] Migrations use expand/migrate/contract (no table locks)
- [ ] Test coverage ≥ 80% business logic, 100% DB queries (integration)
- [ ] No TODO/FIXME without linked issue
- [ ] Repository health audit passed (structure, deps, AI-readiness)

→ See `full-sdlc` for SDLC phase guidance and CI/CD patterns  
→ See `code-reviewer` for review checklist detail  
→ See `data-engineering` for pipeline architecture patterns  
→ See `grafana-prometheus-monitoring` for observability

---

## ADR Template

```markdown
# ADR-NNN: <Decision Title>

## Status: [Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

## Context
- Problem statement
- Constraints (team size, SLA, compliance, budget)

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

---

## Schema Design

### Normalization Trade-off

```sql
-- 3NF (fewer anomalies, requires JOIN)
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  total_amount DECIMAL(10,2),
  created_at TIMESTAMP
);
CREATE TABLE order_items (
  id UUID PRIMARY KEY,
  order_id UUID REFERENCES orders(id),
  product_id UUID REFERENCES products(id),
  quantity INT,
  unit_price DECIMAL(10,2)
);

-- Denormalized (faster reads, staleness risk)
ALTER TABLE orders ADD COLUMN item_count INT DEFAULT 0;
-- Needs trigger or app logic to keep in sync
```

### Index Strategy

```sql
-- Start with WHERE and JOIN columns
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);

-- Composite for multi-column filters
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at DESC);

-- Full-text search (PostgreSQL)
ALTER TABLE articles ADD COLUMN search_vec TSVECTOR;
CREATE INDEX idx_articles_fts ON articles USING GIN(search_vec);

-- Vector similarity (pgvector)
CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists=100);

-- Test: look for "Bitmap Index Scan" not "Seq Scan"
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id=$1 AND created_at > NOW()-'30d'::interval;
```

---

## Zero-Downtime Migration Pattern

```sql
-- Phase 1: Expand (non-blocking ADD)
ALTER TABLE users ADD COLUMN age_range VARCHAR(20);

-- Phase 2: Migrate data in batches (app continues serving)
UPDATE users SET age_range =
  CASE
    WHEN age < 18 THEN 'minor'
    WHEN age < 65 THEN 'adult'
    ELSE 'senior'
  END
WHERE age_range IS NULL LIMIT 1000;
-- Run in cron until all rows updated

-- Phase 3: Deploy app that uses age_range only

-- Phase 4: Contract (drop old column)
ALTER TABLE users DROP COLUMN age;

-- For indexes on large tables:
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
-- CONCURRENTLY = no table lock, takes longer
```

---

## ORM vs Raw SQL

```python
# ORM (CRUD — safe, prevents SQL injection)
def get_user(session: Session, user_id: str) -> User:
    return session.query(User).filter(User.id == user_id).first()

# Raw parameterized SQL (complex queries — explicit, fast)
def get_recent_orders(session: Session, start: datetime, end: datetime):
    return session.execute(
        """SELECT o.id, u.name, o.total_amount
           FROM orders o JOIN users u ON o.user_id = u.id
           WHERE o.created_at BETWEEN :start AND :end
           ORDER BY o.created_at DESC""",
        {"start": start, "end": end}
    )
# NEVER: f"WHERE created_at > {start}"  ← SQL injection
```

---

## pgvector (Embedding Search)

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE embeddings (
  id UUID PRIMARY KEY,
  content TEXT NOT NULL,
  embedding vector(1536)
);
CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists=100);

-- Similarity search
SELECT id, content, 1 - (embedding <=> $1::vector) AS similarity
FROM embeddings
ORDER BY embedding <=> $1::vector
LIMIT 5;
```

---

## Code Review Checklist

**Correctness:** logic matches requirements, edge cases handled (null/empty/boundary), no TODO without issue, tests exist  
**Security:** input validated, auth before sensitive ops, secrets not logged, rate limiting on public endpoints  
**Performance:** no N+1 queries, indexes on filter columns, no blocking ops in hot paths  
**Language idioms:**

```python
# Python
# BAD: bare except, mutable defaults
def f(items=[]):  ...   # mutable default — shared across calls
# GOOD:
def f(items=None):
    items = items or []

# TS/JS
# BAD: floating promise
async function work() { doSomething() }   # unhandled rejection
# GOOD:
async function work() { await doSomething() }

# Go
# BAD: ignored error
f, _ := os.Open(path)
# GOOD:
f, err := os.Open(path)
if err != nil { return err }
```

**Feedback format:**
> "This loads all users then filters in memory. With 100k users → OOM.  
> Recommend: `WHERE role = 'admin'` pushed to the SQL query."

---

## Tech Debt Scoring

```bash
# Find TODOs
git grep -i "TODO\|FIXME" -- '*.py' '*.ts' | wc -l

# Complexity (Python)
radon cc src/ --show-complexity

# Outdated deps
npm outdated   # or: pip-audit

# Coverage gap
coverage run -m pytest && coverage report --fail-under=80

# SAST
semgrep --config p/security-audit src/
```

| Symptom | Score | Action |
|---------|-------|--------|
| Cyclomatic complexity > 10 | +5 | Refactor |
| Outdated major version | +3/dep | Update |
| Coverage < 60% | +2/10% gap | Add tests |
| Security violation | +10 | Fix immediately |

Priority: >50 = this quarter; 20–50 = backlog; <20 = accept + document

---

## Repository Health Audit

```
STRUCTURE
□ Clear folders (src/, tests/, docs/, config/)
□ .gitignore: no secrets, no build artifacts
□ Entry points documented

CONTENT
□ README with setup + usage
□ CONTRIBUTING.md
□ LICENSE file
□ No dead code or unused imports

DEPENDENCY HEALTH
□ Lock file committed
□ npm audit / pip-audit / trivy clean
□ No unneeded deps

AI-READINESS (for LLMs to understand the codebase)
□ ADRs in docs/adr/
□ Key flows documented (auth, payment, etc.)
□ API contracts (OpenAPI / GraphQL schema)
□ Error patterns documented
```

---

## Codebase Onboarding Generator

Auto-generate in `docs/ARCHITECTURE.md`:

```markdown
# Architecture Overview

## Components
- **API Server** (src/server.ts): HTTP, input validation
- **Services** (src/services/): Domain logic, no I/O side effects
- **DB Layer** (src/db/): SQL queries, connection pooling
- **Workers** (src/workers/): Async jobs (email, payments)

## Key Flow: Create User
1. POST /users → validate email format
2. Service: check uniqueness
3. DB: create record
4. Worker: send welcome email async

## Dependencies
Express | TypeORM | Bull
```

---

## Troubleshooting

| Problem | Root Cause | Solution |
|---------|-----------|---------|
| Slow query | Missing index | EXPLAIN ANALYZE; add index on filter column |
| Migration locks table | DDL on large table | CONCURRENT INDEX; background data migration |
| N+1 queries | ORM loop | Batch load: JOIN in one query |
| Tech debt spirals | No tracking | Weekly audit, score, backlog |
| New devs confused | No arch docs | Generate ARCHITECTURE.md + ADRs |
| Monorepo slow CI | No caching | turbo.json outputs + remote cache |
| Merge conflicts | Long-lived branches | Trunk-based, feature flags |
