---
name: Software Architect
description: |
  Universal domain-owning specialist consolidating full SDLC, code review, database architecture, and repo health into one expert.
  
  TRIGGERS: "architect [system/codebase/migrations]", "design [schema/system]", "review architecture", "audit codebase", "tech debt", "ADR", "migration strategy", "database optimization", "monorepo setup", "onboard [project]"
  
  This skill handles: requirements through production, code quality gates, schema design and optimization, repository health, database migrations, ADR management, tech debt assessment, architectural onboarding, and migration planning.
---

# Software Architect

This is your specialist for architectural thinking across the full software development lifecycle. Unlike narrow tools, this skill explains *why* patterns exist and helps you understand trade-offs at every scale—from code review feedback to database replication strategies to organizational migrations.

## Core Philosophy

**Every architectural decision is a trade-off.** Your role is to:
1. Understand the constraints (team size, performance SLAs, operational burden, tech maturity)
2. Evaluate options against those constraints
3. Document decisions so future developers understand the reasoning, not just the rule

This skill covers six interconnected domains:

---

## 1. Full Software Development Lifecycle (SDLC)

Why this matters: Projects fail at boundaries between phases, not within them. Integrating requirements → design → build → test → deploy → maintain prevents costly rework.

### Tech Stack Selection

**Why**: Your tech choices compound over years. Wrong picks create hiring friction, slow deployments, and abandoned projects.

**Pattern**: Requirements-driven selection
```
1. List non-negotiables (language, infrastructure, compliance)
2. List critical ilities (performance, scalability, maintainability, security)
3. Evaluate 3 options against these constraints
4. Document trade-offs (ADR format) with failure modes
5. Plan for future cost (team growth, operational overhead)
```

Example ADR structure:
```
# ADR: Use PostgreSQL + TypeScript + Turborepo for monorepo

## Status: Accepted

## Context
- 5 services sharing domain logic
- Team experienced in Node.js
- Complex data relationships (graph-like)

## Decision
PostgreSQL (mature ACID, JSON, extensions) + TypeScript (single language, type safety) + Turborepo (fast caching, task pipelining)

## Consequences
- Benefits: Type safety across API boundary, simpler deploys, strong consistency
- Risks: TypeScript compilation overhead, operational familiarity with Postgres required
- Mitigation: Invest in tooling, runbook documentation
```

### Requirements & Scaffolding

Why: Clear requirements prevent "scope creep" and keep teams aligned on what "done" means.

**Pattern**: MoSCoW Prioritization + User Stories

MoSCoW categorizes requirements by importance:
- **Must Have** (M): Non-negotiable. Project fails without these. Example: "User authentication"
- **Should Have** (S): Important but not critical. Deferred if timeline pressure. Example: "Social login"
- **Could Have** (C): Nice-to-have. Implemented if time allows. Example: "Theme customization"
- **Won't Have** (W): Explicitly out of scope (this release). Prevents scope creep. Example: "Mobile app" (if building web first)

**Application:**
```
Feature: User onboarding
- M: Create account with email/password
- M: Email verification
- S: Social login (GitHub, Google)
- C: Profile picture upload
- W: Video onboarding tutorial (defer to v2)

Timeline impact:
- M+S: 3 weeks (core + polish)
- M+S+C: 5 weeks (fully featured)
- Cut C & W: 3 weeks (lean launch)
```

**User story mapping with acceptance criteria:**
```
As a <user> I want <capability> so that <business value>

Acceptance Criteria:
- Given <condition> When <action> Then <outcome>
- Edge case handling defined
- Performance thresholds documented
- Security constraints explicit
```

Then scaffold:
```bash
# Use generators that enforce your patterns
# Example: Node monorepo
npx create-turbo@latest --example with-tailwind

# Structure: apps/ | packages/ | tooling/
# Each app has: src/, tests/, docs/, config/
```

### Branching & Code Organization

Why: Branching strategy prevents merge conflicts and enables parallel work.

**Pattern**: Trunk-based development for <5 engineers, Git Flow for teams
```
# Trunk-based (recommended for high velocity)
main (always deployable)
  ├── feature/auth-migration (short-lived, max 3 days)
  ├── fix/security-patch
  └── chore/deps-update

# Git Flow (for coordinated releases)
main (production)
├── develop (integration)
│   ├── feature/...
│   ├── bugfix/...
│   └── hotfix/... (from main)
```

### Testing Strategy

Why: Tests are your safety net. Without them, refactoring is terrifying.

**Pattern**: Test pyramid (many unit, some integration, few e2e)
```
Testing Pyramid:
         / \
        /E2E\       <5% (full app flow)
       /-----\
      / Integ \     15% (component interactions)
     /--------\
    / Unit     \    80% (functions, classes)
   /----------\

Why: Unit tests are fast (sub-second feedback), integration tests catch real bugs,
E2E tests validate user flows but are slow and brittle.

Minimum Coverage by Layer:
- API handlers: 80% (happy + error paths)
- Business logic: 90% (critical path, edge cases)
- UI components: 60% (major user flows, not pixel-perfect)
- Database queries: 100% (via integration tests on test DB)
- Infrastructure code: 80% (terraform/docker via linting + sample deploys)
```

Example test structure:
```typescript
// Unit: Pure function, no dependencies
describe('calculateDiscount', () => {
  it('applies 10% for orders > $100', () => {
    expect(calculateDiscount(150)).toBe(15);
  });
  it('returns 0 for invalid input', () => {
    expect(calculateDiscount(-10)).toBe(0);
  });
});

// Integration: Real database, mocked external APIs
describe('User.create', () => {
  it('saves user and sends welcome email', async () => {
    const user = await User.create({ email: 'test@example.com' });
    expect(await getUserFromDB(user.id)).toBeDefined();
    expect(emailService.send).toHaveBeenCalledWith('test@example.com', 'welcome');
  });
});

// E2E: Real app, real database (or staging)
describe('Signup flow', () => {
  it('creates account and logs in user', async () => {
    await page.goto('https://app.test/signup');
    await page.fill('input[name=email]', 'new@example.com');
    await page.click('button:has-text("Sign up")');
    await page.waitForURL('**/dashboard');
    expect(await page.locator('text=Welcome').isVisible()).toBe(true);
  });
});
```

### CI/CD & Deployment

Why: Manual deployments are slow and error-prone. Automation enables confidence.

**Pattern**: GitHub Actions / GitLab CI (declarative, version-controlled)
```yaml
# .github/workflows/deploy.yml
name: Deploy on main push

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: npm install
      - run: npm run test:ci
      - run: npm run lint
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: success()
    steps:
      - uses: actions/checkout@v3
      - run: npm run build
      - run: |
          # Blue-green deployment
          NEW_ID=$(npm run deploy:new-version)
          npm run smoke-test:$NEW_ID
          npm run cutover:$NEW_ID
```

Why this order: Tests must pass before build, build before deploy. Fails fast, prevents broken deploys.

### Release Management

Why: Users need predictability. Predictable releases mean fewer hotfixes.

**Pattern**: Semantic Versioning + Changelog
```
MAJOR.MINOR.PATCH
  X        .   Y    .   Z
Breaking    Features  Fixes

Release process:
1. Merge to main (triggers CI)
2. Tag: git tag v1.2.3
3. Generate changelog: git log v1.2.2..v1.2.3 --oneline
4. Create release notes with migration guide (if MAJOR)
5. Deploy to staging, then production
6. Monitor error rates for 30min (automated rollback if >2% increase)
```

### Maintenance & Monitoring

Why: Production is where software lives. Unknown failures kill trust.

**Pattern**: Observability = Logs + Metrics + Traces
```
Logs (what happened):
  ERROR: Payment processing failed for order #123: Stripe API timeout
  Context: user_id=456, amount=$99.99, retry_count=2

Metrics (how much):
  payment_processing_duration_ms (histogram: p50=120, p95=450, p99=2000)
  payment_failures_total (counter: stripe_timeout=15, insufficient_funds=3)

Traces (why it took time):
  Request → ValidateOrder (5ms) → ChargeCard (450ms) → UpdateInventory (20ms)
  Slow span: ChargeCard (network + retries)

Alert thresholds:
- Error rate > 1%: Page on-call
- P99 latency > 2s: Investigate
- Failed deployments: Rollback automatically
```

---

## 2. Code Review Excellence

Why this matters: Code lives longer than the developer who wrote it. Reviews catch bugs early and spread knowledge.

### Review Checklist

**Correctness** (Does it work?)
```
- Logic matches requirements
- Edge cases handled (null, empty, boundary conditions)
- Off-by-one errors in loops
- Variable names match intent
- No TODO/FIXME left behind without issue tracking
- Tests exist and pass
```

**Security** (Can it be attacked?)
```
- Input validation present (SQL injection, XSS, path traversal)
- Auth checks before sensitive operations
- Secrets not logged or hardcoded
- Cryptographic functions used correctly (never implement crypto yourself)
- Rate limiting on public endpoints
- CORS headers appropriate for use case
```

**Performance** (Will it scale?)
```
- No N+1 queries (batch load related data)
- Database indexes on filter columns
- Caching strategy documented (TTL, invalidation)
- No blocking operations in hot paths
- Algorithm complexity appropriate for data size
```

**Language Idioms** (Is it idiomatic?)
```
# Python
- Type hints on public APIs
- Use dataclasses over dicts for structured data
- Prefer comprehensions over map/filter
- Exception handling specific, not bare except

# JavaScript/TypeScript
- const by default, let sparingly, never var
- Avoid callback hell (use async/await)
- Type safety: unknown → typed through guards
- No side effects in pure functions

# Go
- Errors explicit: if err != nil { handle }
- Interfaces defined at consumption point
- Goroutines with context for cancellation
- Defer for cleanup (file handles, locks)

# Bash
- Set -e and -o pipefail for safety
- Quote variables: "${var}" not $var
- Use functions for reusable logic
- Test paths exist before using them
```

### Delivering Feedback (The Why Matters)

**Instead of**: "This is inefficient"

**Say**: "This loads all users then filters in memory. With 100k users, this will OOM. Recommend pushing the WHERE to the database query so Postgres handles filtering before returning rows."

**Instead of**: "Add error handling"

**Say**: "If CreateOrder fails, the user gets a blank page. Add try/catch to show a 'Please try again' message, log the error to Sentry, and retry once automatically for transient failures."

---

## 3. Database Architecture & Optimization

Why this matters: Databases are the slowest layer. Bad schemas cause cascading problems for years.

### Schema Design Principles

**Normalization trade-off**: 3NF prevents update anomalies but requires joins. Denormalization is faster but requires careful invalidation.

```sql
-- 3NF: Normalized (fewer anomalies, more joins)
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

-- Query: SELECT SUM(unit_price * quantity) FROM order_items WHERE order_id = $1
-- Pro: Single source of truth, no stale data
-- Con: Requires JOIN, computed on read

-- Denormalized (faster reads, staleness risk)
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  total_amount DECIMAL(10,2), -- Cached, computed async
  item_count INT,              -- Cached, updated via trigger
  created_at TIMESTAMP
);

-- Pro: SELECT total_amount FROM orders WHERE id = $1 is instant
-- Con: Trigger needed to keep total_amount in sync; risk of staleness
```

### Indexing Strategy

Why: Indexes make specific queries fast but slow writes. Choose carefully.

```sql
-- Start with WHERE and JOIN columns
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- Composite index for multi-column filters
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at DESC);

-- For full-text search (PostgreSQL)
ALTER TABLE articles ADD COLUMN search_vec TSVECTOR;
CREATE INDEX idx_articles_search ON articles USING GIN(search_vec);

-- Query: SELECT * FROM articles WHERE search_vec @@ plainto_tsquery($1)

-- For range queries, use BRIN (block range index) if data is sorted
CREATE INDEX idx_events_ts_brin ON events USING BRIN(created_at);

-- Test your indexes
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = $1 AND created_at > NOW() - '30 days'::interval;
-- Look for "Seq Scan" (bad) vs "Bitmap Index Scan" (good)
```

### Query Optimization

**Pattern**: EXPLAIN ANALYZE before and after optimization

```sql
-- BEFORE (slow)
EXPLAIN ANALYZE
SELECT o.id, o.total_amount, u.name, COUNT(oi.id) as item_count
FROM orders o
JOIN users u ON o.user_id = u.id
LEFT JOIN order_items oi ON o.id = oi.order_id
WHERE o.created_at > NOW() - '30 days'::interval
GROUP BY o.id, u.id, u.name
ORDER BY o.created_at DESC;

-- Output might show:
-- Seq Scan on orders o (slow, scans all rows)
-- Hash Join (expensive)
-- GroupAggregate (computes on every row)

-- AFTER (optimized)
-- 1. Add index on created_at
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);

-- 2. Pre-aggregate item_count (denormalize)
ALTER TABLE orders ADD COLUMN item_count INT DEFAULT 0;

-- 3. Simplified query
SELECT o.id, o.total_amount, u.name, o.item_count
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.created_at > NOW() - '30 days'::interval
ORDER BY o.created_at DESC;

-- Output should show:
-- Index Scan using idx_orders_created_at
-- Nested Loop (faster for small result sets)
-- Finalized in <50ms vs 5000ms
```

### Migrations & Zero-Downtime Deploys

Why: Users can't wait for deployments. Migrations must not lock tables.

**Pattern**: Expand, migrate data, contract

```sql
-- Step 1: Add new column (non-blocking)
ALTER TABLE users ADD COLUMN age_range VARCHAR(20);

-- Step 2: Populate new column (in batches, app continues)
UPDATE users SET age_range = 
  CASE 
    WHEN age < 18 THEN 'minor'
    WHEN age < 65 THEN 'adult'
    ELSE 'senior'
  END
WHERE age_range IS NULL
LIMIT 1000;

-- (Run in cron/background job until all rows updated)

-- Step 3: Remove old column (once app updated)
ALTER TABLE users DROP COLUMN age;

-- Deployment timeline:
-- 1. Deploy app (handles both age AND age_range columns)
-- 2. Run migration (add column)
-- 3. Background job (populate new column) — App continues serving
-- 4. Verify data integrity
-- 5. Deploy new version (uses age_range only)
-- 6. Run cleanup migration (drop age column)

-- This keeps the app live throughout
```

### ORMs & Database Access

Why: ORMs prevent SQL injection and reduce boilerplate, but they can hide performance problems.

**Pattern**: Use ORM for CRUD, raw SQL for complex queries

```python
# ORM (safe, simple)
from sqlalchemy import Session
from models import User

def get_user(session: Session, user_id: str) -> User:
    return session.query(User).filter(User.id == user_id).first()

# Raw SQL (explicit, fast, needs parameterization)
def get_users_by_date_range(session: Session, start: datetime, end: datetime):
    return session.execute(
        """
        SELECT id, name, created_at
        FROM users
        WHERE created_at BETWEEN :start AND :end
        ORDER BY created_at DESC
        """,
        {"start": start, "end": end}
    )

# Why parameterized queries: 
# SAFE: VALUES are passed separately, preventing SQL injection
# UNSAFE: f"WHERE created_at > {start}" allows injected SQL
```

### Connection Pooling

Why: Creating DB connections is expensive. Reuse them.

```
Pool size = (num_app_instances × avg_queries_per_request) + buffer
Example: 3 app servers × 10 queries/request = 30 connections + 5 buffer = 35

Too small: App waits for connections, requests timeout
Too large: Database exhausted, connections idle waste memory

Configuration:
  min_idle: 5 (always ready)
  max_size: 35 (absolute ceiling)
  max_lifetime: 30min (recycle stale connections)
  idle_timeout: 5min (close unused connections)
```

### PostgreSQL Backup & Maintenance

**Logical Backups with pg_dump:**
```bash
# Backup single database
pg_dump -U postgres -d production_db > backup_$(date +%Y%m%d).sql

# Backup with compression (recommended)
pg_dump -U postgres -d production_db | gzip > backup_$(date +%Y%m%d).sql.gz

# Backup all databases
pg_dumpall -U postgres | gzip > full_backup_$(date +%Y%m%d).sql.gz

# Restore
gunzip < backup_20260101.sql.gz | psql -U postgres -d production_db

# Why pg_dump over physical backups:
# - Portable across PostgreSQL versions
# - Can restore to different hardware
# - Smaller filesize (logical, not block-by-block)
# - Can exclude specific tables: pg_dump -d db -T sensitive_table | gzip > backup.gz
```

**VACUUM & Autovacuum (Maintenance):**
```sql
-- VACUUM reclaims space from deleted rows, updates statistics
VACUUM ANALYZE;  -- Full vacuum with stats update

-- Autovacuum runs in background (recommended for production)
ALTER TABLE orders SET (autovacuum_vacuum_scale_factor = 0.01);  -- Vacuum at 1% growth
ALTER TABLE orders SET (autovacuum_vacuum_cost_delay = 5);      -- Throttle CPU usage

-- Check autovacuum stats
SELECT schemaname, tablename, last_vacuum, last_autovacuum
FROM pg_stat_user_tables
ORDER BY last_autovacuum DESC;

-- Why VACUUM matters:
-- - Deleted rows create "dead tuples" that waste space
-- - Sequential scans slow down (must skip dead rows)
-- - Autovacuum keeps this automatic; manual VACUUM during off-hours for aggressive cleanup
```

### pgvector: Embedding & Vector Search

PostgreSQL extension for storing and searching vector embeddings (useful for AI-powered search, recommendations):

```sql
-- Install extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table with vector column
CREATE TABLE embeddings (
  id UUID PRIMARY KEY,
  content TEXT NOT NULL,
  embedding vector(1536)  -- OpenAI embeddings are 1536-dim
);

-- Create index for fast similarity search
CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Insert embeddings (from Python via your embedding service)
-- Example: embedding = embedding_service.embed(content)
INSERT INTO embeddings (id, content, embedding)
VALUES ('doc-1', 'Climate change affects ...',  '[0.1, 0.2, ..., 0.9]'::vector);

-- Similarity search: find most relevant documents
SELECT id, content, 1 - (embedding <=> query_embedding) AS similarity
FROM embeddings
ORDER BY embedding <=> query_embedding
LIMIT 5;

-- Why pgvector:
-- - Integrates with existing PostgreSQL database (no separate vector DB)
-- - Efficient HNSW/IVFFlat indexes for high-dimensional search
-- - Combines vector search with traditional SQL (metadata filtering, joins)
```

### Replication & High Availability

Why: Single-instance databases fail. Replication enables recovery.

```
Primary (write) 
  ↓ Write-Ahead Log (WAL)
Replica (read-only, sync or async)
  ↓ Used for backups + read-scaling

Setup:
1. Primary: WAL level = replica
2. Replica: streaming_replication_timeout = 60s
3. Monitor replication lag (should be <1s)
4. For failover: Use patroni/etcd to elect new primary

Sync vs Async:
- Sync: Transaction returns only after replica ACKs (safe but slower)
- Async: Transaction returns immediately (fast but risk of data loss if primary crashes)
```

---

## 4. Repository Health Audit

Why this matters: Unmaintained repos become technical debt. Regular audits prevent decay.

### Audit Checklist

```
STRUCTURE
□ Clear folder organization (src/, tests/, docs/, config/)
□ Entry points documented (main.py, index.ts, etc.)
□ No orphaned directories or hidden configs
□ Appropriate .gitignore (no secrets, no build artifacts)

CONTENT QUALITY
□ README exists with setup & usage
□ Contributing guidelines (CONTRIBUTING.md)
□ License specified (LICENSE file)
□ Changelog maintained (for libraries)
□ Code comments explain "why" not "what"
□ No dead code or unused imports

LINK INTEGRITY
□ Links in README are valid (test with curl)
□ References to issues/PRs are correct
□ Documentation links aren't broken

DEPENDENCY HEALTH
□ lock file committed (package-lock.json, Pipfile.lock, go.sum)
□ No security vulnerabilities (npm audit, safety, trivy)
□ Dependencies up to date (but not recklessly)
□ Unused dependencies removed

AI-READINESS (for LLMs to understand the code)
□ Architecture documented (ADRs in docs/adr/)
□ Key flows described (e.g., "User authentication flow")
□ API contracts documented (OpenAPI/GraphQL schema)
□ Error patterns documented
```

---

## 5. Database Migrations & Service Migrations

Why this matters: Migrations move data and infrastructure between states. Failures here cause downtime.

### Migration Patterns

**Expand-Migrate-Contract** (safest):
```
Phase 1 (Expand): Add new column/service
Phase 2 (Migrate): Populate data, sync state
Phase 3 (Contract): Remove old column/service

Allows rollback at any phase without data loss.
```

**Strangler Pattern** (for service migrations):
```
Old Service        New Service
     ↑                  ↑
     └──── Router ─────┘

Route X% to new, monitor errors, increase % gradually.
If new service fails, revert routes instantly.

Example: 5% → 25% → 50% → 100% over 5 deployments
```

### Rollback Strategies

```sql
-- Forward migration
CREATE TABLE users_v2 (id UUID, email VARCHAR, created_at TIMESTAMP);
INSERT INTO users_v2 SELECT id, email, created_at FROM users;

-- Rollback (keep old table)
DROP TABLE users_v2;
-- Old queries still work on original 'users' table

-- Or: Blue-green
CREATE TABLE users_blue (original)
CREATE TABLE users_green (new schema)
-- Switch via view/alias once green is verified
```

---

## 6. Tech Debt Tracking & Scoring

Why: Tech debt compounds. Track it to prioritize refactoring.

### Automated Scanning

```bash
# Find TODOs and FIXMEs
git grep -i "TODO\|FIXME" -- '*.py' '*.ts' | wc -l

# Complexity (Python)
radon cc src/ --show-complexity

# Outdated dependencies
npm outdated

# Missing test coverage
coverage run -m pytest && coverage report

# Security: SAST scanning
semgrep --config p/security-audit --json src/ > report.json
```

### Tech Debt Score

```
Score = (Complexity + Outdated Dependencies + Missing Tests + Violations) / Max

Scoring:
- High cyclomatic complexity (>10): +5 points
- Outdated major version: +3 points per dependency
- <60% test coverage: +2 points per 10% gap
- Security violations: +10 points each

Priority:
- Score >50: Refactor soon (within quarter)
- Score 20-50: Monitor (add to backlog)
- Score <20: Accept (document trade-off)
```

---

## 7. ADR (Architecture Decision Record) Management

Why: Future developers need to understand your reasoning, not just the rules.

### ADR Template

```
# ADR-001: Use PostgreSQL for transactional data

## Status: Accepted

## Context
- Application requires ACID transactions
- Team familiar with SQL
- Data relationships are hierarchical

## Decision
We will use PostgreSQL as the primary database for transactional data.

## Consequences
- Benefits: Strong consistency, mature ecosystem, excellent JSON support
- Risks: Operational overhead (backups, replication), scaling requires expertise
- Mitigation: Use managed service (RDS), invest in monitoring

## Alternatives Considered
- MySQL: Simpler operations but weaker consistency until recently
- MongoDB: Better horizontal scaling but eventual consistency
```

### Cross-referencing

```
ADRs should reference each other:

ADR-001 (PostgreSQL) 
  ↓ informed
ADR-002 (No distributed transactions, use eventual consistency)
  ↓ informed
ADR-003 (Implement event sourcing for audit trail)

Tools to link:
- Index: docs/adr/README.md lists all ADRs with status
- In code: Link to ADR in comments explaining unusual patterns
```

---

## 8. Codebase Onboarding Generator

Why: New developers waste weeks understanding the codebase. Auto-generate starter docs.

### Auto-Generated Artifacts

```
docs/
├── ARCHITECTURE.md (generated from code structure)
├── SETUP.md (generated from dockerfile, requirements.txt)
├── KEY_FLOWS.md (traced from main entry points)
├── GLOSSARY.md (extracted from codebase + comments)
└── architecture.mmd (Mermaid diagram)
```

**Example ARCHITECTURE.md** (generated):
```markdown
# Architecture Overview

## Components
- **API Server** (src/server.ts): Handles HTTP requests, validates input
- **Business Logic** (src/services/): Domain logic, no side effects
- **Database Layer** (src/db/): SQL queries, connection pooling
- **Workers** (src/workers/): Async jobs (email, payments)

## Flow: Create User
1. API (POST /users) validates email format
2. Service checks email uniqueness
3. Database creates user record
4. Worker sends welcome email asynchronously

## Dependencies
- Express (HTTP framework)
- TypeORM (database access)
- Bull (job queue)
```

---

## 9. Schema Designer from Natural Language

Why: Design database schema faster by expressing intent in English.

### Pattern: Spec → Schema → Types → Seed

```
INPUT (Natural Language Spec):
"Users have email and name. Orders belong to users, contain items.
Items have product references and quantities. Products have descriptions and prices."

OUTPUT (Generated SQL):
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR UNIQUE NOT NULL,
  name VARCHAR NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE products (
  id UUID PRIMARY KEY,
  description TEXT,
  price DECIMAL(10,2) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
  id UUID PRIMARY KEY,
  order_id UUID NOT NULL REFERENCES orders(id),
  product_id UUID NOT NULL REFERENCES products(id),
  quantity INT NOT NULL DEFAULT 1
);

OUTPUT (Generated TypeScript Types):
interface User { id: string; email: string; name: string; createdAt: Date; }
interface Order { id: string; userId: string; createdAt: Date; }
interface OrderItem { id: string; orderId: string; productId: string; quantity: number; }

OUTPUT (Generated RLS Policies):
CREATE POLICY user_can_view_own_orders ON orders
  FOR SELECT USING (user_id = current_user_id());
```

---

## 10. Monorepo Navigation

Why: Monorepos are powerful but complex. Navigate them systematically.

### Workspace Structure (Turborepo example)

```
.
├── apps/
│   ├── web (Next.js)
│   ├── api (Node.js)
│   └── mobile (React Native)
├── packages/
│   ├── shared (domain types, utilities)
│   ├── ui (reusable components)
│   └── database (schema, migrations)
├── turbo.json (task orchestration)
└── pnpm-workspace.yaml
```

### Impact Analysis

When changing `packages/shared`:
```bash
# What depends on it?
npm ls @myorg/shared

# What tests should run?
turbo run test --filter='...[shared]'

# What should rebuild?
turbo run build --filter='...[shared]'

# Selective deploy (only changed apps)
turbo run deploy --filter='[HEAD~1]' --changed-only
```

---

## Quick Reference: Review Checklist

```
BEFORE REVIEWING:
□ PR description explains "why", not just "what"
□ Tests added or documented as N/A
□ CI passes

DURING REVIEW:
□ Does it work? (correctness)
□ Can it break? (security, edge cases)
□ Will it scale? (performance, resource usage)
□ Is it idiomatic? (language conventions)
□ Is it documented? (code comments explain why, README updated)

DELIVERING FEEDBACK:
□ Explain the consequence, not the rule
□ Offer solutions, not just problems
□ Praise good decisions (learning moment)
□ Request changes only for critical issues
□ Approve with suggestions for optional improvements
```

---

## Troubleshooting Table

| Problem | Root Cause | Solution |
|---------|-----------|----------|
| Slow queries | Missing index | Run EXPLAIN ANALYZE, add index on filter column |
| Migrations lock table | DDL on large table | Use CONCURRENT INDEX, add column in background job |
| N+1 queries | ORM fetching in loop | Batch load: query with JOIN, not loop with separate queries |
| Tech debt spirals | No tracking | Weekly debt audit, score, add to backlog |
| New devs confused | No architecture docs | Generate onboarding docs from code + ADRs |
| Monorepo slow | No caching | Add turbo.json with outputs, enable remote caching |
| Merge conflicts | Wrong branching | Switch to trunk-based (shorter branches) |
| Deployments break | No staging | Add blue-green or canary, require manual cutover approval |

---

## Your Next Steps

1. **Assess**: Run repository health audit (section 4)
2. **Design**: Document architecture in ADRs (section 7)
3. **Improve**: Fix tech debt hotspots (section 6)
4. **Maintain**: Set up monitoring and release process (section 1)
5. **Onboard**: Generate codebase docs for new developers (section 8)

Architecture is not about perfection—it's about *making the right trade-offs for your constraints* and documenting them so future developers understand your reasoning.
