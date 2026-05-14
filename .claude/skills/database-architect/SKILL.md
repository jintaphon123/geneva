---
name: database-architect
description: Database schema design, query optimization, migration management, and natural language to SQL. Auto-invoke when Bond asks to design a database schema, optimize slow queries, plan a migration, write SQL, choose between databases, design indexes, generate TypeScript types from schema, or debug database performance issues. Trigger phrases: "design a database", "schema design", "optimize this query", "write SQL for", "database migration", "add an index", "N+1 query", "TypeScript types from schema", "ERD diagram", "which database should I use", "database is slow", "normalize this", "foreign key design".
---

# Database Architect

Three modes: **design** (schema + ERD), **query** (SQL + optimization), **migrate** (zero-downtime migrations).

---

## Mode 1 — Design

### Schema Design Principles

1. **Naming conventions** — consistent, lowercase, snake_case
   - Tables: plural nouns (`users`, `orders`, `order_items`)
   - Primary keys: `id` (UUID preferred over integer for distributed systems)
   - Foreign keys: `{table_singular}_id` (`user_id`, `order_id`)
   - Timestamps: `created_at`, `updated_at` (always include both)
   - Booleans: `is_` prefix (`is_active`, `is_verified`)

2. **Normalization target:** 3NF for most tables. Denormalize deliberately for read-heavy query patterns.

3. **Constraints first:** Foreign keys, unique constraints, and check constraints encode business rules in the DB — don't rely only on application-layer validation.

### Schema Template (PostgreSQL)

```sql
-- Users table (example)
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) NOT NULL UNIQUE,
    name        VARCHAR(100) NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Updated_at trigger (auto-update)
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### Index Strategy

```sql
-- Single column (equality lookups)
CREATE INDEX idx_users_email ON users(email);

-- Composite (multi-column — equality columns first, then range)
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- Partial (filtered queries — smaller, faster)
CREATE INDEX idx_active_orders ON orders(created_at)
    WHERE status = 'active';

-- Covering (include non-indexed columns to avoid table lookup)
CREATE INDEX idx_users_email_name ON users(email)
    INCLUDE (name, id);

-- GIN (full-text search, JSONB)
CREATE INDEX idx_posts_search ON posts
    USING gin(to_tsvector('english', title || ' ' || body));
```

**Index decision rules:**
- Every foreign key column needs an index
- Columns frequently in WHERE, JOIN ON, or ORDER BY → index candidate
- Columns with < 10% cardinality (e.g., boolean, status enum) → partial index
- Over-indexing slows writes — audit indexes quarterly

### TypeScript Types from Schema

```typescript
// Generate with: prisma generate, drizzle-kit generate, or manually
interface User {
    id: string;           // UUID
    email: string;
    name: string;
    is_active: boolean;
    created_at: Date;
    updated_at: Date;
}

// Prisma schema equivalent
model User {
    id         String   @id @default(uuid())
    email      String   @unique
    name       String
    is_active  Boolean  @default(true)
    created_at DateTime @default(now())
    updated_at DateTime @updatedAt
}
```

---

## Mode 2 — Query

### Natural Language to SQL

When Bond describes a query in natural language, translate to optimized SQL with explanation.

**Pattern:**
1. Parse intent (what data, what filter, what aggregation)
2. Identify tables and relationships
3. Write SQL with appropriate JOINs
4. Add query plan hint if optimization needed

```sql
-- "Get all users with their order count, sorted by most orders"
SELECT
    u.id,
    u.name,
    u.email,
    COUNT(o.id) AS order_count
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
GROUP BY u.id, u.name, u.email
ORDER BY order_count DESC;

-- "Total revenue by product category for last 30 days"
SELECT
    p.category,
    SUM(oi.quantity * oi.unit_price) AS revenue
FROM order_items oi
JOIN products p ON p.id = oi.product_id
JOIN orders o ON o.id = oi.order_id
WHERE o.created_at >= NOW() - INTERVAL '30 days'
    AND o.status = 'completed'
GROUP BY p.category
ORDER BY revenue DESC;
```

### Query Optimization

**Diagnose first:**
```sql
EXPLAIN ANALYZE
SELECT * FROM orders WHERE user_id = 'abc' AND status = 'active';
-- Look for: Seq Scan (bad) → add index
-- Look for: Index Scan (good)
-- Check actual vs estimated rows (big gap = stale stats → ANALYZE)
```

**N+1 Pattern (most common performance issue):**
```typescript
// BAD — N+1: 1 query for users + N queries for orders
const users = await db.query('SELECT * FROM users');
for (const user of users) {
    user.orders = await db.query('SELECT * FROM orders WHERE user_id = $1', [user.id]);
}

// GOOD — single JOIN
const users = await db.query(`
    SELECT u.*, json_agg(o.*) FILTER (WHERE o.id IS NOT NULL) AS orders
    FROM users u
    LEFT JOIN orders o ON o.user_id = u.id
    GROUP BY u.id
`);
```

**Common fixes:**
| Problem | Fix |
|---------|-----|
| Seq Scan on large table | Add index on filter column |
| Slow COUNT(*) | Use `EXPLAIN` to find bottleneck; partial index if filtered |
| Slow ORDER BY | Add index on sort column(s) |
| High stale rows | `ANALYZE table_name` or configure autovacuum |
| N+1 queries | Use JOIN + GROUP BY or DataLoader pattern |

---

## Mode 3 — Migrate

### Zero-Downtime Migration Pattern (Expand-Contract)

**Never** drop a column or rename a column in a single migration on a live DB.

**Phase 1 — Expand (safe to deploy):**
```sql
-- Add new column (nullable, no default required yet)
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- Add new table
CREATE TABLE user_preferences (
    id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    key     VARCHAR(100) NOT NULL,
    value   TEXT,
    UNIQUE(user_id, key)
);
```

**Phase 2 — Backfill (run as background job):**
```sql
-- Fill new column for existing rows
UPDATE users SET phone = legacy_phone WHERE phone IS NULL;
```

**Phase 3 — Contract (after old code is fully removed):**
```sql
-- Add NOT NULL constraint after backfill
ALTER TABLE users ALTER COLUMN phone SET NOT NULL;

-- Drop old column (only after all code references are removed)
ALTER TABLE users DROP COLUMN legacy_phone;
```

### Migration File Template
```sql
-- migrations/20260501_add_user_phone.sql
-- Description: Add phone number to users table

BEGIN;

-- Up
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
CREATE INDEX idx_users_phone ON users(phone) WHERE phone IS NOT NULL;

-- Verify
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'phone'
    ) THEN
        RAISE EXCEPTION 'Migration failed: phone column not created';
    END IF;
END $$;

COMMIT;
```

---

## Database Selection Quick Reference

```
PostgreSQL   → default choice. ACID, complex queries, full-text search, JSONB.
MongoDB      → flexible schema, document-oriented, rapid schema iteration.
Redis        → cache, sessions, rate limiting, pub/sub, sorted sets for leaderboards.
SQLite       → local dev, embedded, single-file. Not for production multi-user.
pgvector     → vector similarity search on top of PostgreSQL (Second Brain memory).

Scale:
  <1M rows    → PostgreSQL single instance
  1M-100M     → PostgreSQL + read replicas
  >100M       → CockroachDB, Cassandra, or DynamoDB
```
