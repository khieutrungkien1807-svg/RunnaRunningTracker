# ERROR HANDLING PATTERNS

> **Khi nào tải skill này:** Error, Exception, Handling, Recovery, Try, Catch

---

## ERROR CLASS HIERARCHY

**ERR-001.** Create structured error classes:
```typescript
// Base error class
export class AppError extends Error {
  constructor(
    public code: string,
    message: string,
    public statusCode: number = 500,
    public details?: unknown,
    public isOperational: boolean = true
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace(this, this.constructor);
  }

  toJSON() {
    return {
      code: this.code,
      message: this.message,
      details: this.details,
    };
  }
}

// Specific errors
export class ValidationError extends AppError {
  constructor(details: unknown) {
    super('VALIDATION_ERROR', 'Validation failed', 422, details);
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string, id?: string) {
    super('NOT_FOUND', `${resource}${id ? ` with id ${id}` : ''} not found`, 404);
  }
}

export class UnauthorizedError extends AppError {
  constructor(message = 'Unauthorized') {
    super('UNAUTHORIZED', message, 401);
  }
}

export class ForbiddenError extends AppError {
  constructor(message = 'Access denied') {
    super('FORBIDDEN', message, 403);
  }
}

export class ConflictError extends AppError {
  constructor(message: string) {
    super('CONFLICT', message, 409);
  }
}

export class RateLimitError extends AppError {
  constructor(retryAfter: number) {
    super('RATE_LIMITED', 'Too many requests', 429, { retryAfter });
  }
}
```

---

## GLOBAL ERROR HANDLER

**ERR-002.** Express global error handler:
```typescript
function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
) {
  // Log error
  const requestId = req.headers['x-request-id'] || crypto.randomUUID();

  logger.error({
    requestId,
    error: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method,
    userId: req.userId,
  });

  // Handle known errors
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      error: err.toJSON(),
      meta: { requestId },
    });
  }

  // Handle Prisma errors
  if (err instanceof Prisma.PrismaClientKnownRequestError) {
    if (err.code === 'P2002') {
      return res.status(409).json({
        error: { code: 'CONFLICT', message: 'Resource already exists' },
        meta: { requestId },
      });
    }
    if (err.code === 'P2025') {
      return res.status(404).json({
        error: { code: 'NOT_FOUND', message: 'Resource not found' },
        meta: { requestId },
      });
    }
  }

  // Handle Zod validation errors
  if (err instanceof z.ZodError) {
    return res.status(422).json({
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Validation failed',
        details: err.flatten(),
      },
      meta: { requestId },
    });
  }

  // Unknown error - don't leak details
  res.status(500).json({
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred',
    },
    meta: { requestId },
  });
}

app.use(errorHandler);
```

---

## ASYNC ERROR WRAPPER

**ERR-003.** Wrap async route handlers:
```typescript
// Wrapper function
function asyncHandler<T>(
  fn: (req: Request, res: Response, next: NextFunction) => Promise<T>
) {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

// Usage
app.get('/users/:id', asyncHandler(async (req, res) => {
  const user = await prisma.user.findUnique({
    where: { id: req.params.id },
  });

  if (!user) {
    throw new NotFoundError('User', req.params.id);
  }

  res.json({ data: user });
}));
```

---

## RESULT PATTERN

**ERR-004.** Use Result type for expected failures:
```typescript
type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

function ok<T>(data: T): Result<T, never> {
  return { success: true, data };
}

function err<E>(error: E): Result<never, E> {
  return { success: false, error };
}

// Usage
async function parseConfig(path: string): Promise<Result<Config, string>> {
  try {
    const content = await fs.readFile(path, 'utf-8');
    const config = JSON.parse(content);
    return ok(config);
  } catch (e) {
    if (e.code === 'ENOENT') {
      return err('Config file not found');
    }
    return err('Invalid JSON in config');
  }
}

// Consuming
const result = await parseConfig('./config.json');
if (!result.success) {
  console.error(result.error);
  process.exit(1);
}
console.log(result.data);
```

---

## RETRY PATTERNS

**ERR-005.** Exponential backoff retry:
```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  options: {
    maxAttempts?: number;
    baseDelayMs?: number;
    maxDelayMs?: number;
    shouldRetry?: (error: Error) => boolean;
  } = {}
): Promise<T> {
  const {
    maxAttempts = 3,
    baseDelayMs = 1000,
    maxDelayMs = 30000,
    shouldRetry = () => true,
  } = options;

  let lastError: Error;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      if (attempt === maxAttempts || !shouldRetry(lastError)) {
        throw lastError;
      }

      const delay = Math.min(
        baseDelayMs * Math.pow(2, attempt - 1),
        maxDelayMs
      );

      // Add jitter
      const jitter = delay * 0.2 * Math.random();
      await sleep(delay + jitter);
    }
  }

  throw lastError!;
}

// Usage
const data = await withRetry(
  () => fetchExternalAPI(),
  {
    maxAttempts: 3,
    shouldRetry: (err) => err.message.includes('timeout'),
  }
);
```

---

## CIRCUIT BREAKER

**ERR-006.** Implement circuit breaker:
```typescript
class CircuitBreaker {
  private failures = 0;
  private lastFailure: number = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  constructor(
    private threshold: number = 5,
    private resetTimeMs: number = 30000
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailure > this.resetTimeMs) {
        this.state = 'half-open';
      } else {
        throw new Error('Circuit breaker is open');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess() {
    this.failures = 0;
    this.state = 'closed';
  }

  private onFailure() {
    this.failures++;
    this.lastFailure = Date.now();

    if (this.failures >= this.threshold) {
      this.state = 'open';
    }
  }
}

// Usage
const externalApiBreaker = new CircuitBreaker(5, 30000);

async function callExternalAPI() {
  return externalApiBreaker.execute(() => fetch('https://api.external.com'));
}
```

---

## QUICK REFERENCE

| Error Type | HTTP Status | Use Case |
|------------|-------------|----------|
| ValidationError | 422 | Invalid input |
| NotFoundError | 404 | Resource not exists |
| UnauthorizedError | 401 | No/invalid auth |
| ForbiddenError | 403 | No permission |
| ConflictError | 409 | Duplicate/conflict |
| RateLimitError | 429 | Too many requests |
| AppError | 500 | Unexpected error |
