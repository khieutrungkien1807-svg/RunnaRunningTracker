# SECURITY ATTACK VECTORS

> **Khi nào tải skill này:** XSS, SQL Injection, CSRF, SSRF, Security, Attack, Vulnerability

---

## XSS (CROSS-SITE SCRIPTING)

**XSS-001.** NEVER render untrusted data without escaping:
```typescript
// BAD - Direct HTML insertion
element.innerHTML = userInput;
document.write(userInput);

// GOOD - Use textContent or framework escaping
element.textContent = userInput;

// React auto-escapes by default
<div>{userInput}</div>  // Safe

// BAD - dangerouslySetInnerHTML
<div dangerouslySetInnerHTML={{ __html: userInput }} />  // DANGEROUS!
```

**XSS-002.** ALWAYS sanitize if HTML is required:
```typescript
import DOMPurify from 'dompurify';

const clean = DOMPurify.sanitize(userHtml, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p'],
  ALLOWED_ATTR: ['href'],
});
```

**XSS-003.** ALWAYS set proper CSP headers:
```typescript
// Strict CSP
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'strict-dynamic';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' https://api.example.com;
  frame-ancestors 'none';
```

---

## SQL INJECTION

**SQL-001.** NEVER concatenate user input into queries:
```typescript
// BAD - SQL Injection vulnerable
const query = `SELECT * FROM users WHERE email = '${email}'`;

// GOOD - Parameterized queries
const users = await prisma.user.findMany({
  where: { email },
});

// GOOD - Raw with parameters
const users = await prisma.$queryRaw`
  SELECT * FROM users WHERE email = ${email}
`;
```

**SQL-002.** ALWAYS validate and type input:
```typescript
import { z } from 'zod';

const QuerySchema = z.object({
  id: z.string().uuid(),
  limit: z.coerce.number().min(1).max(100).default(20),
  orderBy: z.enum(['createdAt', 'name']).default('createdAt'),
});
```

---

## CSRF (CROSS-SITE REQUEST FORGERY)

**CSRF-001.** ALWAYS use CSRF tokens for state-changing requests:
```typescript
// Generate token
import { randomBytes } from 'crypto';

function generateCSRFToken(): string {
  return randomBytes(32).toString('hex');
}

// Set in cookie (httpOnly: false so JS can read)
res.cookie('csrf_token', token, {
  httpOnly: false,
  sameSite: 'strict',
  secure: true,
});

// Validate on server
function validateCSRF(req: Request): boolean {
  const cookieToken = req.cookies.csrf_token;
  const headerToken = req.headers['x-csrf-token'];

  return cookieToken && headerToken && cookieToken === headerToken;
}
```

**CSRF-002.** ALWAYS use SameSite cookies:
```typescript
res.cookie('session', sessionId, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict',  // or 'lax' for GET requests
  maxAge: 24 * 60 * 60 * 1000,
});
```

---

## SSRF (SERVER-SIDE REQUEST FORGERY)

**SSRF-001.** NEVER fetch user-controlled URLs without validation:
```typescript
const ALLOWED_DOMAINS = ['api.stripe.com', 'cdn.example.com'];
const PRIVATE_IP_RANGES = [
  /^127\./,
  /^10\./,
  /^172\.(1[6-9]|2\d|3[01])\./,
  /^192\.168\./,
  /^169\.254\./,  // Cloud metadata!
  /^0\./,
];

async function safeFetch(userUrl: string): Promise<Response> {
  const parsed = new URL(userUrl);

  // Protocol check
  if (parsed.protocol !== 'https:') {
    throw new Error('Only HTTPS allowed');
  }

  // Domain allowlist
  if (!ALLOWED_DOMAINS.includes(parsed.hostname)) {
    throw new Error('Domain not allowed');
  }

  // DNS resolution check
  const ips = await dns.resolve(parsed.hostname);
  for (const ip of ips) {
    for (const range of PRIVATE_IP_RANGES) {
      if (range.test(ip)) {
        throw new Error('Private IP blocked');
      }
    }
  }

  return fetch(userUrl, {
    redirect: 'error',  // Prevent redirect to internal
    signal: AbortSignal.timeout(5000),
  });
}
```

---

## PROTOTYPE POLLUTION

**PP-001.** NEVER merge untrusted objects recursively:
```typescript
const DANGEROUS_KEYS = new Set([
  '__proto__',
  'constructor',
  'prototype',
]);

function safeMerge(target: object, source: object): object {
  if (typeof source !== 'object' || source === null) return target;

  const result = { ...target };

  for (const key of Object.keys(source)) {
    if (DANGEROUS_KEYS.has(key)) continue;

    const value = (source as any)[key];
    if (typeof value === 'object' && value !== null) {
      (result as any)[key] = safeMerge((result as any)[key] || {}, value);
    } else {
      (result as any)[key] = value;
    }
  }

  return result;
}
```

---

## JWT SECURITY

**JWT-001.** ALWAYS verify signature và claims:
```typescript
import jwt from 'jsonwebtoken';

function verifyToken(token: string): JWTPayload {
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET!, {
      algorithms: ['HS256'],  // Explicit algorithm
      issuer: 'myapp',
      audience: 'myapp-users',
    });

    return decoded as JWTPayload;
  } catch (error) {
    throw new Error('Invalid token');
  }
}
```

**JWT-002.** NEVER store sensitive data in JWT payload:
```typescript
// GOOD - Only store ID, fetch details from DB
const payload = {
  sub: user.id,
  iat: Math.floor(Date.now() / 1000),
  exp: Math.floor(Date.now() / 1000) + 3600,
};

// BAD - Exposing sensitive data
const payload = {
  email: user.email,
  role: user.role,
  ssn: user.ssn,  // NEVER!
};
```

---

## INPUT VALIDATION CHECKLIST

| Input Type | Validation |
|------------|------------|
| Email | Regex + DNS check |
| URL | Protocol + domain allowlist |
| File | Extension + MIME + size |
| HTML | DOMPurify sanitization |
| JSON | Schema validation (Zod) |
| SQL params | Parameterized queries |
| Path | Normalize + prevent traversal |

---

## SECURITY HEADERS

```typescript
// Essential security headers
{
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
}
```
