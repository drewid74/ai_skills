---
name: database-architecture
description: "Use this skill whenever the user wants to design, optimize, migrate, or troubleshoot databases. Triggers include: any mention of 'database', 'DB', 'SQL', 'PostgreSQL', 'Postgres', 'MySQL', 'MariaDB', 'SQLite', 'MongoDB', 'Redis', 'DynamoDB', 'Supabase', 'schema design', 'data model', 'normalization', 'denormalization', 'index', 'indexing', 'query optimization', 'slow query', 'EXPLAIN', 'EXPLAIN ANALYZE', 'N+1', 'ORM', 'Prisma', 'Drizzle', 'SQLAlchemy', 'TypeORM', 'Sequelize', 'migration', 'schema migration', 'Alembic', 'Flyway', 'connection pool', 'pgbouncer', 'replication', 'read replica', 'sharding', 'partitioning', 'backup', 'pg_dump', 'point-in-time recovery', 'PITR', 'transaction', 'ACID', 'deadlock', 'vacuum', 'MVCC', 'foreign key', 'constraint', 'stored procedure', 'trigger', 'view', 'materialized view', 'CTE', 'window function', 'JSON column', 'JSONB', 'full-text search', 'pgvector', 'vector database', 'time-series', 'graph database', 'database selection', or any request to design a schema, optimize queries, plan a migration, set up replication, or choose between databases. Also use when the user shows slow queries, asks about data modeling patterns, or says 'which database should I use?'. If someone has any database-related question or task, use this skill."
---

## Overview
Comprehensive database architecture covering selection, schema design, query optimization, migrations, ORMs, replication, and operations across relational, document, key-value, vector, and graph databases.

## Database Selection Guide
Choose the right database for your use case:

- **PostgreSQL**: Default choice for most applications. Relational data with JSONB flexibility, full-text search, pgvector for embeddings, PostGIS for geography. If in doubt, use Postgres.
- **MySQL/MariaDB**: When specific applications require it (WordPress, legacy PHP apps). MariaDB is the community fork with more features.
- **SQLite**: Embedded, serverless, single-file database. Perfect for: local development, mobile apps, prototyping, small websites, CLI tools. Avoid: high concurrency writes, multi-server setups.
- **MongoDB**: Genuinely schema-less data with rapid prototyping where schema evolves constantly. Usually overused — Postgres JSONB handles most "document" needs better.
- **Redis**: In-memory caching, sessions, pub/sub, rate limiting, job queues. Volatile by default, so use persistence config if data matters.
- **TimescaleDB/InfluxDB**: Time-series databases optimized for append-heavy, time-ordered sensor data, metrics, IoT applications.
- **pgvector/Qdrant/Pinecone**: Vector databases for embeddings, semantic search, RAG pipelines. Use pgvector if already on Postgres, Qdrant for dedicated performance.
- **Neo4j/FalkorDB**: Graph databases for relationship-heavy queries, knowledge graphs, recommendation engines.

## Schema Design

### Normalization
- **1NF**: Atomic values, no repeating groups
- **2NF**: No partial dependencies (every non-key column depends on the full primary key)
- **3NF**: No transitive dependencies (non-key columns don't depend on other non-key columns)
- When to normalize: transactional systems where data integrity is critical
- When to denormalize: read-heavy workloads, reporting/analytics, pre-computed aggregations

### Common Patterns
- **Soft delete**: `deleted_at TIMESTAMP NULL` instead of DELETE. Preserves audit trail and allows undelete.
- **Timestamps**: Always include `created_at` and `updated_at` (use database triggers or ORM hooks for automatic updates).
- **UUIDs vs auto-increment**: UUID for distributed systems, public-facing IDs, and API resources. Auto-increment for internal, sequential, compact data.
- **Enums**: Use Postgres ENUM type or check constraints, never magic numbers.
- **JSON columns**: JSONB for flexible schema within relational model. Index with GIN for query performance. Don't store data you need to JOIN on in JSON.
- **Polymorphic associations**: Use discriminator column + constraints or separate tables. Avoid: single table with many nullable columns.

### Naming Conventions
- **Tables**: Plural, snake_case (`users`, `order_items`)
- **Columns**: snake_case (`first_name`, `created_at`)
- **Primary keys**: `id` (simple) or `<table>_id` (explicit)
- **Foreign keys**: `<referenced_table>_id` (e.g., `user_id`)
- **Indexes**: `idx_<table>_<columns>` (e.g., `idx_users_email`)
- **Constraints**: `fk_<table>_<ref>`, `uq_<table>_<column>`, `ck_<table>_<rule>`

## Indexing Strategy

### Index Types (PostgreSQL)
- **B-tree** (default): Equality and range queries (`=`, `<`, `>`, `BETWEEN`, `ORDER BY`). Use for most columns.
- **GIN** (Generalized Inverted): JSONB, arrays, full-text search, pgvector. Use for containment queries (`@>`, `?`, `@@`).
- **GiST**: Geometric/spatial data (PostGIS), range types, full-text search.
- **BRIN**: Physically ordered data (timestamps, sequential IDs). Tiny index with great performance for append-only tables.
- **HNSW** (pgvector): Approximate nearest neighbor for vector similarity search with better recall than IVFFlat.
- **Hash**: Exact equality only. Rarely better than B-tree.

### Indexing Rules
- Index columns used in WHERE, JOIN, ORDER BY, GROUP BY clauses
- Composite indexes: put equality columns first, range columns last: `CREATE INDEX idx ON orders (status, created_at)`
- Covering indexes: Include frequently selected columns to avoid table lookup: `INCLUDE (name, email)`
- Partial indexes: Index only rows that matter: `WHERE active = true` — smaller and faster
- Avoid over-indexing: each index slows writes and uses storage. Start with none, add based on real query patterns.
- Monitor unused indexes: Query `pg_stat_user_indexes` to see usage counts

## Query Optimization

### Reading EXPLAIN ANALYZE
```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) SELECT ...
```
Key patterns to look for:
- **Seq Scan on large table**: Missing index (unless reading most of the table)
- **Nested Loop with high row count**: Possible N+1 query, consider rewrite or batch
- **Sort with high cost**: Missing index for ORDER BY or sort exceeded work_mem
- **Actual rows vs estimated**: Large mismatch means stale statistics — run `ANALYZE table_name`

### Common Optimizations
- **N+1 queries**: ORM fetches related records one-by-one instead of batch. Fix: eager loading with JOIN, `SELECT ... IN (...)`, or ORM includes.
- **SELECT ***: Fetches all columns including large text/blob. Fix: select only needed columns.
- **Missing LIMIT**: Unbounded queries on large tables. Fix: always paginate results.
- **Implicit casts**: Comparing `varchar` to `integer` prevents index use. Fix: match column types.
- **Functions on indexed columns**: `WHERE LOWER(email) = '...'` can't use B-tree index. Fix: expression index: `CREATE INDEX idx ON users (LOWER(email))`

### CTEs and Window Functions
```sql
WITH recent_orders AS (
    SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '30 days'
)
SELECT u.name, COUNT(*) as order_count
FROM users u JOIN recent_orders o ON u.id = o.user_id
GROUP BY u.name;

SELECT date, amount,
    SUM(amount) OVER (ORDER BY date) as running_total,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY date DESC) as rank
FROM transactions;
```
CTEs improve readability and reusability within a single query. Window functions enable analytics without collapsing groups via GROUP BY.

## ORM Patterns

### When to Use an ORM
- CRUD-heavy apps with standard query patterns save development time
- Complex reporting queries: write raw SQL (ORMs struggle with analytics)
- Use ORM's migration tool even if you write raw SQL for complex queries

### ORM Selection
- **Python**: SQLAlchemy (full-featured, async support), Tortoise ORM (async-first), Django ORM (if using Django)
- **TypeScript**: Prisma (type-safe schema-first), Drizzle (SQL-like, lightweight), TypeORM (decorator-based), Kysely (type-safe query builder)
- **Go**: sqlx (query builder + raw SQL), GORM (full ORM), ent (schema-as-code)

### ORM Anti-Patterns
- Lazy loading in loops (N+1): Always eager-load relationships you'll access
- Ignoring generated SQL: Enable query logging, review what the ORM actually sends
- Fighting the ORM for complex queries: Switch to raw SQL for analytics/reporting
- Mixing ORM and raw SQL without transaction awareness

## Migrations

### Principles
- Migrations are version-controlled, sequential, and irreversible in production
- Every schema change is a migration (never modify tables manually in production)
- Test migrations on a copy of production data before applying
- Backward-compatible changes: add columns (nullable or with default), add tables, add indexes. Never: remove columns, rename columns, change types — do these in multiple steps.

### Zero-Downtime Migration Pattern
1. **Add** new column (nullable, no default constraint)
2. **Backfill** data from old column to new column
3. **Update** application to write to both old and new
4. **Switch** application to read from new column
5. **Drop** old column (in a later release)

### Migration Tools
- **Alembic** (Python/SQLAlchemy): `alembic revision --autogenerate`, `alembic upgrade head`
- **Prisma Migrate** (TypeScript): `prisma migrate dev`, `prisma migrate deploy`
- **Flyway** (Java, multi-language): SQL-based, language-agnostic
- **golang-migrate**: CLI tool for any language, SQL-based
- **pg_dump → psql**: Manual but reliable for small databases

## Connection Pooling

### Why Pool Connections
Database connections are expensive: TCP handshake, authentication, memory allocation. Most apps need far fewer active connections than concurrent requests. Pooling reuses connections, reducing overhead and preventing exhaustion.

### PgBouncer
External connection pooler for PostgreSQL. Three modes: session (safest), transaction (most efficient), statement (most restrictive). Use transaction mode for most web apps.

### Application-Level Pooling
Most ORMs and drivers include built-in pooling:
- **SQLAlchemy**: `pool_size=20, max_overflow=10, pool_timeout=30`
- **Prisma**: `connection_limit` in connection string
- **Node pg**: `Pool({ max: 20 })`
- **Rule of thumb**: `pool_size = (core_count * 2) + spindle_count`

## Replication & High Availability

### Read Replicas
Primary handles writes, replicas handle reads. Use for: read-heavy workloads, reporting queries, geographic distribution. Replicas may lag behind primary (eventual consistency).

### PostgreSQL Streaming Replication
Built-in asynchronous replication (configurable synchronous). Use `pg_basebackup` for initial copy, WAL streaming for ongoing replication. Monitor with `pg_stat_replication` view.

### Backup Strategy
- **pg_dump**: Logical backup, portable, can restore individual tables. Slow for large databases.
- **pg_basebackup**: Physical backup, fast, full cluster restore. Enables PITR (Point-In-Time Recovery).
- **WAL archiving + PITR**: Continuous backup, restore to any point in time.
- **3-2-1 rule**: 3 copies, 2 different media, 1 offsite.
- Test restores regularly — untested backups are not backups.

## PostgreSQL Operations

### VACUUM and Maintenance
MVCC creates dead tuples on UPDATE/DELETE. VACUUM reclaims space and prevents table bloat.
- Autovacuum: Enabled by default, tune thresholds for heavy-write tables
- `VACUUM ANALYZE`: Reclaims space AND updates statistics (do both)
- Monitor: `pg_stat_user_tables` shows dead tuple count, last vacuum time

### Configuration Tuning
- `shared_buffers`: ~25% of system RAM
- `effective_cache_size`: ~75% of system RAM (tells planner about OS cache)
- `work_mem`: Per-sort memory, start at 4-16MB, increase for complex queries
- `maintenance_work_mem`: For VACUUM, CREATE INDEX — 256MB-1GB
- `max_connections`: Keep low (100-200), use pooler for more
- Use https://pgtune.leopard.in.ua/ for initial tuning

## Full-Text Search (PostgreSQL)
Built-in `tsvector` and `tsquery` types with GIN indexing:
```sql
CREATE INDEX idx_content_fts ON articles USING GIN(to_tsvector('english', content));
SELECT * FROM articles
WHERE to_tsvector('english', content) @@ to_tsquery('english', 'search & terms')
ORDER BY ts_rank(to_tsvector('english', content), query) DESC;
```
Use when: moderate search needs without Elasticsearch overhead. Upgrade when: complex search UI, faceted search, fuzzy matching, auto-suggest.

## Troubleshooting
- **Slow queries**: Check EXPLAIN ANALYZE, look for seq scans, add missing indexes
- **Connection refused**: Check max_connections limit, verify pooler, check pg_hba.conf
- **Table bloat**: High dead tuple count — tune autovacuum settings or manual VACUUM
- **Lock contention / deadlocks**: Check `pg_locks`, review transaction duration, keep transactions short
- **Replication lag**: Check WAL sender/receiver status, verify network bandwidth, reduce replica load
- **OOM on complex queries**: Increase work_mem for session or optimize query to reduce memory footprint
- **Disk full**: Check WAL retention, vacuum to reclaim space, archive old data
