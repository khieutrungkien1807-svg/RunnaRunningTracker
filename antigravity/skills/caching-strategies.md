# CACHING STRATEGIES

> **Khi nào tải skill này:** Cache, Redis, Memcache, Performance, TTL, Invalidation

---

## CACHING PATTERNS

**CACHE-001.** Cache-Aside (Lazy Loading):
```typescript
async function getUser(id: string): Promise<User> {
  const cacheKey = `user:${id}`;

  // 1. Check cache
  const cached = await redis.get(cacheKey);
  if (cached) {
    return JSON.parse(cached);
  }

  // 2. Cache miss - fetch from DB
  const user = await prisma.user.findUnique({ where: { id } });

  if (user) {
    // 3. Store in cache
    await redis.setex(cacheKey, 3600, JSON.stringify(user)); // 1 hour TTL
  }

  return user;
}
```

**CACHE-002.** Write-Through:
```typescript
async function updateUser(id: string, data: UpdateUserDto): Promise<User> {
  // 1. Update DB
  const user = await prisma.user.update({
    where: { id },
    data,
  });

  // 2. Update cache immediately
  await redis.setex(`user:${id}`, 3600, JSON.stringify(user));

  return user;
}
```

**CACHE-003.** Write-Behind (Async):
```typescript
async function incrementViewCount(articleId: string): Promise<void> {
  // 1. Update cache immediately
  await redis.hincrby(`article:${articleId}`, 'views', 1);

  // 2. Queue DB update (batched later)
  await queue.add('sync-views', { articleId }, {
    delay: 60000, // Batch after 1 minute
    jobId: `views-${articleId}`, // Dedupe
  });
}

// Worker
queue.process('sync-views', async (job) => {
  const { articleId } = job.data;
  const views = await redis.hget(`article:${articleId}`, 'views');

  await prisma.article.update({
    where: { id: articleId },
    data: { views: parseInt(views) },
  });
});
```

---

## CACHE INVALIDATION

**INVALID-001.** Event-based invalidation:
```typescript
// After mutation, invalidate related caches
async function createPost(data: CreatePostDto): Promise<Post> {
  const post = await prisma.post.create({ data });

  // Invalidate related caches
  await redis.del(`user:${data.authorId}:posts`);
  await redis.del('posts:latest');
  await redis.del('posts:count');

  return post;
}
```

**INVALID-002.** Tag-based invalidation:
```typescript
class CacheService {
  async set(key: string, value: unknown, tags: string[], ttl = 3600) {
    const pipeline = redis.pipeline();

    // Store value
    pipeline.setex(key, ttl, JSON.stringify(value));

    // Track tags
    for (const tag of tags) {
      pipeline.sadd(`tag:${tag}`, key);
      pipeline.expire(`tag:${tag}`, ttl);
    }

    await pipeline.exec();
  }

  async invalidateByTag(tag: string) {
    const keys = await redis.smembers(`tag:${tag}`);

    if (keys.length > 0) {
      await redis.del(...keys, `tag:${tag}`);
    }
  }
}

// Usage
await cache.set('user:123:posts', posts, ['user:123', 'posts'], 3600);

// Invalidate all user's cached data
await cache.invalidateByTag('user:123');
```

---

## REDIS DATA STRUCTURES

**REDIS-001.** Choose right structure:
```typescript
// String - simple key-value
await redis.set('session:abc', JSON.stringify(sessionData));

// Hash - object with fields
await redis.hset('user:123', {
  name: 'John',
  email: 'john@example.com',
  views: 42,
});
await redis.hincrby('user:123', 'views', 1);

// List - ordered, duplicates allowed
await redis.lpush('notifications:123', JSON.stringify(notification));
await redis.lrange('notifications:123', 0, 9); // Last 10

// Set - unique, unordered
await redis.sadd('user:123:following', 'user:456', 'user:789');
await redis.sismember('user:123:following', 'user:456');

// Sorted Set - scored ordering
await redis.zadd('leaderboard', { score: 100, value: 'user:123' });
await redis.zrevrange('leaderboard', 0, 9); // Top 10

// HyperLogLog - cardinality estimation
await redis.pfadd('visitors:2024-01', visitorId);
await redis.pfcount('visitors:2024-01'); // Unique count
```

---

## HTTP CACHING

**HTTP-001.** Cache headers:
```typescript
// Static assets - long cache with versioning
app.use('/static', express.static('public', {
  maxAge: '1y',
  immutable: true,
}));

// API responses
app.get('/api/products', async (req, res) => {
  const products = await getProducts();

  res.set({
    'Cache-Control': 'public, max-age=60, stale-while-revalidate=300',
    'ETag': generateETag(products),
  });

  res.json(products);
});

// Private data - no caching
app.get('/api/me', authMiddleware, async (req, res) => {
  res.set('Cache-Control', 'private, no-store');
  res.json(req.user);
});
```

**HTTP-002.** Conditional requests:
```typescript
app.get('/api/article/:id', async (req, res) => {
  const article = await getArticle(req.params.id);
  const etag = `"${article.updatedAt.getTime()}"`;

  // Check If-None-Match
  if (req.headers['if-none-match'] === etag) {
    return res.status(304).end();
  }

  res.set('ETag', etag);
  res.json(article);
});
```

---

## CACHING CONSIDERATIONS

**CONSIDER-001.** When NOT to cache:
```typescript
// Don't cache:
// - User-specific sensitive data (without careful key design)
// - Rapidly changing data
// - Large objects that are rarely accessed
// - Data that must be real-time accurate

// DO cache:
// - Static content
// - Computed aggregations
// - Session data
// - Rate limit counters
// - Frequently accessed reference data
```

**CONSIDER-002.** Cache warming:
```typescript
// Pre-populate cache on startup
async function warmCache() {
  // Top products
  const topProducts = await prisma.product.findMany({
    take: 100,
    orderBy: { views: 'desc' },
  });

  await Promise.all(
    topProducts.map((p) =>
      redis.setex(`product:${p.id}`, 3600, JSON.stringify(p))
    )
  );

  console.log(`Warmed cache with ${topProducts.length} products`);
}
```

---

## QUICK REFERENCE

| Pattern | Read | Write | Use Case |
|---------|------|-------|----------|
| Cache-Aside | Cache → DB | DB → Cache | General purpose |
| Write-Through | Cache → DB | DB + Cache | Consistency |
| Write-Behind | Cache → DB | Cache → Queue | High write volume |
| Read-Through | Cache (auto-fetch) | DB → Cache | Simpler code |

| Header | Meaning |
|--------|---------|
| `max-age=60` | Cache for 60 seconds |
| `s-maxage=60` | CDN cache time |
| `no-cache` | Revalidate every time |
| `no-store` | Never cache |
| `private` | Browser only, no CDN |
| `public` | CDN can cache |
| `stale-while-revalidate` | Serve stale while fetching |
