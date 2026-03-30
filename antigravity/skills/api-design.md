# API DESIGN PATTERNS

> **Khi nào tải skill này:** API, REST, GraphQL, Endpoint, Route, HTTP

---

## REST API RULES

**REST-001.** ALWAYS dùng proper HTTP methods:
```
GET    /users          → List users
GET    /users/:id      → Get single user
POST   /users          → Create user
PUT    /users/:id      → Replace user
PATCH  /users/:id      → Update user fields
DELETE /users/:id      → Delete user
```

**REST-002.** ALWAYS return proper status codes:
```typescript
// Success
200 OK           - GET, PUT, PATCH success
201 Created      - POST success (include Location header)
204 No Content   - DELETE success

// Client errors
400 Bad Request  - Invalid input
401 Unauthorized - No/invalid auth
403 Forbidden    - Authenticated but not allowed
404 Not Found    - Resource doesn't exist
409 Conflict     - Duplicate/conflict
422 Unprocessable - Validation failed

// Server errors
500 Internal     - Unexpected error
503 Unavailable  - Service down
```

**REST-003.** ALWAYS validate input at edge:
```typescript
import { z } from 'zod';

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2).max(100),
  role: z.enum(['admin', 'user']).default('user'),
});

app.post('/users', async (req, res) => {
  const parsed = CreateUserSchema.safeParse(req.body);

  if (!parsed.success) {
    return res.status(422).json({
      error: 'Validation failed',
      details: parsed.error.flatten(),
    });
  }

  const user = await createUser(parsed.data);
  res.status(201).json(user);
});
```

---

## RESPONSE FORMAT

**RESP-001.** ALWAYS use consistent response structure:
```typescript
// Success response
{
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "requestId": "req_abc123"
  }
}

// List response with pagination
{
  "data": [...],
  "meta": {
    "total": 100,
    "page": 1,
    "perPage": 20,
    "totalPages": 5
  }
}

// Error response
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      { "field": "email", "message": "Invalid email format" }
    ]
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "requestId": "req_abc123"
  }
}
```

---

## PAGINATION

**PAGE-001.** ALWAYS implement cursor-based pagination for large datasets:
```typescript
// Cursor-based (recommended)
GET /posts?cursor=eyJpZCI6MTAwfQ&limit=20

// Response
{
  "data": [...],
  "cursors": {
    "next": "eyJpZCI6MTIwfQ",
    "prev": "eyJpZCI6MTAwfQ"
  },
  "hasMore": true
}

// Implementation
async function getPosts(cursor: string | null, limit: number) {
  const decodedCursor = cursor
    ? JSON.parse(Buffer.from(cursor, 'base64').toString())
    : null;

  const posts = await prisma.post.findMany({
    take: limit + 1,
    cursor: decodedCursor ? { id: decodedCursor.id } : undefined,
    orderBy: { createdAt: 'desc' },
  });

  const hasMore = posts.length > limit;
  const data = hasMore ? posts.slice(0, -1) : posts;

  return {
    data,
    cursors: {
      next: hasMore
        ? Buffer.from(JSON.stringify({ id: data[data.length - 1].id })).toString('base64')
        : null,
    },
    hasMore,
  };
}
```

---

## RATE LIMITING

**RATE-001.** ALWAYS implement rate limiting:
```typescript
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(100, '1 m'), // 100 requests per minute
  analytics: true,
});

async function rateLimitMiddleware(req: Request) {
  const ip = req.headers.get('x-forwarded-for') || 'anonymous';
  const { success, limit, remaining, reset } = await ratelimit.limit(ip);

  if (!success) {
    return new Response('Rate limited', {
      status: 429,
      headers: {
        'X-RateLimit-Limit': limit.toString(),
        'X-RateLimit-Remaining': remaining.toString(),
        'X-RateLimit-Reset': reset.toString(),
        'Retry-After': Math.ceil((reset - Date.now()) / 1000).toString(),
      },
    });
  }

  return null; // Continue
}
```

---

## VERSIONING

**VER-001.** Use URL path versioning:
```typescript
// Recommended
app.use('/api/v1', v1Router);
app.use('/api/v2', v2Router);

// Routes
GET /api/v1/users
GET /api/v2/users
```

---

## IDEMPOTENCY

**IDEM-001.** ALWAYS implement idempotency for mutations:
```typescript
async function createPayment(req: Request) {
  const idempotencyKey = req.headers.get('Idempotency-Key');

  if (!idempotencyKey) {
    return { error: 'Idempotency-Key header required', status: 400 };
  }

  // Check cache
  const cached = await redis.get(`idempotency:${idempotencyKey}`);
  if (cached) {
    return JSON.parse(cached);
  }

  // Process payment
  const result = await processPayment(req.body);

  // Cache result (24 hours)
  await redis.setex(
    `idempotency:${idempotencyKey}`,
    86400,
    JSON.stringify(result)
  );

  return result;
}
```

---

## ERROR HANDLING

**ERR-001.** ALWAYS create structured error classes:
```typescript
class AppError extends Error {
  constructor(
    public code: string,
    public message: string,
    public statusCode: number = 500,
    public details?: unknown
  ) {
    super(message);
  }
}

class ValidationError extends AppError {
  constructor(details: unknown) {
    super('VALIDATION_ERROR', 'Validation failed', 422, details);
  }
}

class NotFoundError extends AppError {
  constructor(resource: string) {
    super('NOT_FOUND', `${resource} not found`, 404);
  }
}

// Global error handler
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      error: {
        code: err.code,
        message: err.message,
        details: err.details,
      },
    });
  }

  // Unexpected error
  console.error(err);
  res.status(500).json({
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred',
    },
  });
});
```

---

## QUICK REFERENCE

| Method | Idempotent | Safe | Cacheable |
|--------|------------|------|-----------|
| GET | Yes | Yes | Yes |
| POST | No | No | No |
| PUT | Yes | No | No |
| PATCH | No | No | No |
| DELETE | Yes | No | No |
