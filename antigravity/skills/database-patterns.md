# DATABASE PATTERNS

> **Khi nào tải skill này:** Database, SQL, Postgres, Prisma, Query, Migration

---

## PRISMA RULES

**PRISMA-001.** ALWAYS use transactions for related operations:
```typescript
// Multiple related operations
const result = await prisma.$transaction(async (tx) => {
  const order = await tx.order.create({
    data: { userId, total },
  });

  await tx.orderItem.createMany({
    data: items.map(item => ({
      orderId: order.id,
      productId: item.productId,
      quantity: item.quantity,
    })),
  });

  await tx.inventory.updateMany({
    where: { productId: { in: items.map(i => i.productId) } },
    data: { quantity: { decrement: 1 } },
  });

  return order;
});
```

**PRISMA-002.** ALWAYS select only needed fields:
```typescript
// GOOD - Select specific fields
const users = await prisma.user.findMany({
  select: {
    id: true,
    name: true,
    email: true,
  },
});

// GOOD - Exclude sensitive fields
const users = await prisma.user.findMany({
  omit: {
    passwordHash: true,
    ssn: true,
  },
});

// BAD - Select all (wastes bandwidth)
const users = await prisma.user.findMany();
```

**PRISMA-003.** ALWAYS use proper relations:
```typescript
// GOOD - Include related data in one query
const post = await prisma.post.findUnique({
  where: { id },
  include: {
    author: { select: { name: true, avatar: true } },
    comments: {
      take: 10,
      orderBy: { createdAt: 'desc' },
      include: { author: { select: { name: true } } },
    },
  },
});

// BAD - N+1 queries
const posts = await prisma.post.findMany();
for (const post of posts) {
  post.author = await prisma.user.findUnique({ where: { id: post.authorId } });
}
```

---

## MIGRATION RULES

**MIG-001.** ALWAYS use safe migrations:
```sql
-- Add column with default (no lock)
ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active';

-- Create index concurrently (Postgres)
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- Never in production:
-- ALTER TABLE users DROP COLUMN (without backup plan)
-- TRUNCATE TABLE
-- DROP INDEX (without CONCURRENTLY)
```

**MIG-002.** ALWAYS make migrations reversible:
```typescript
// prisma/migrations/XXX_add_user_status/migration.sql
-- Up
ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active';

-- Down (manual rollback script)
ALTER TABLE users DROP COLUMN status;
```

---

## QUERY OPTIMIZATION

**QUERY-001.** ALWAYS add indexes for WHERE/ORDER BY columns:
```prisma
// schema.prisma
model User {
  id        String   @id @default(cuid())
  email     String   @unique
  status    String
  createdAt DateTime @default(now())

  @@index([status])
  @@index([createdAt])
  @@index([status, createdAt])  // Composite for common queries
}
```

**QUERY-002.** Use EXPLAIN ANALYZE for slow queries:
```sql
EXPLAIN ANALYZE
SELECT * FROM orders
WHERE user_id = 'xxx'
AND status = 'pending'
ORDER BY created_at DESC
LIMIT 10;

-- Look for:
-- - Seq Scan (bad for large tables, needs index)
-- - High "actual time"
-- - Estimated vs actual rows mismatch
```

---

## CONNECTION POOLING

**POOL-001.** Configure connection pool properly:
```typescript
// prisma/schema.prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// DATABASE_URL should include pooling params
// postgresql://user:pass@host:5432/db?connection_limit=10&pool_timeout=10
```

**POOL-002.** For serverless, use connection pooler:
```typescript
// Use PgBouncer, Supabase Pooler, or Prisma Accelerate
datasource db {
  provider  = "postgresql"
  url       = env("DATABASE_URL")
  directUrl = env("DIRECT_URL")  // For migrations
}
```

---

## SOFT DELETES

**SOFT-001.** IMPLEMENT soft delete pattern:
```prisma
model Post {
  id        String    @id @default(cuid())
  title     String
  deletedAt DateTime?

  @@index([deletedAt])
}
```

```typescript
// Middleware to auto-filter deleted
prisma.$use(async (params, next) => {
  if (params.model === 'Post') {
    if (params.action === 'findMany' || params.action === 'findFirst') {
      params.args.where = {
        ...params.args.where,
        deletedAt: null,
      };
    }
  }
  return next(params);
});

// Soft delete
await prisma.post.update({
  where: { id },
  data: { deletedAt: new Date() },
});
```

---

## ROW-LEVEL SECURITY

**RLS-001.** Use RLS for multi-tenant:
```sql
-- Enable RLS
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Policy: Users see only their orders
CREATE POLICY user_orders ON orders
  USING (user_id = current_setting('app.current_user_id')::uuid);

-- Set context before query
SELECT set_config('app.current_user_id', $1::text, false);
```

---

## BACKUP & RECOVERY

**BACKUP-001.** ALWAYS have backup strategy:
```bash
# Automated daily backup
pg_dump -Fc $DATABASE_URL > backup_$(date +%Y%m%d).dump

# Point-in-time recovery (WAL archiving)
# Enable in postgresql.conf:
# archive_mode = on
# archive_command = 'cp %p /backups/%f'
```

---

## QUICK REFERENCE

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Primary key lookup | O(1) | Always fast |
| Index scan | O(log n) | Good |
| Sequential scan | O(n) | Avoid on large tables |
| Join | O(n × m) | Use proper indexes |
| LIKE '%term%' | O(n) | Use full-text search |
