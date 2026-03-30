# AUTHENTICATION PATTERNS

> **Khi nào tải skill này:** Auth, JWT, Session, OAuth, Login, Token, Password

---

## JWT AUTHENTICATION

**JWT-001.** ALWAYS use short-lived access tokens + refresh tokens:
```typescript
const ACCESS_TOKEN_EXPIRY = '15m';  // Short-lived
const REFRESH_TOKEN_EXPIRY = '7d';  // Longer-lived

async function generateTokens(userId: string) {
  const accessToken = jwt.sign(
    { sub: userId, type: 'access' },
    process.env.JWT_SECRET!,
    { expiresIn: ACCESS_TOKEN_EXPIRY }
  );

  const refreshToken = jwt.sign(
    { sub: userId, type: 'refresh' },
    process.env.JWT_REFRESH_SECRET!,
    { expiresIn: REFRESH_TOKEN_EXPIRY }
  );

  // Store refresh token hash in DB for revocation
  await prisma.refreshToken.create({
    data: {
      userId,
      tokenHash: await hash(refreshToken),
      expiresAt: addDays(new Date(), 7),
    },
  });

  return { accessToken, refreshToken };
}
```

**JWT-002.** Token refresh flow:
```typescript
async function refreshAccessToken(refreshToken: string) {
  try {
    const payload = jwt.verify(refreshToken, process.env.JWT_REFRESH_SECRET!);

    if (payload.type !== 'refresh') {
      throw new Error('Invalid token type');
    }

    // Check if token is revoked
    const stored = await prisma.refreshToken.findFirst({
      where: {
        userId: payload.sub,
        tokenHash: await hash(refreshToken),
        expiresAt: { gt: new Date() },
        revokedAt: null,
      },
    });

    if (!stored) {
      throw new Error('Token revoked or expired');
    }

    // Generate new access token
    return jwt.sign(
      { sub: payload.sub, type: 'access' },
      process.env.JWT_SECRET!,
      { expiresIn: ACCESS_TOKEN_EXPIRY }
    );
  } catch (error) {
    throw new UnauthorizedError('Invalid refresh token');
  }
}
```

---

## SESSION AUTHENTICATION

**SESSION-001.** Secure session configuration:
```typescript
import session from 'express-session';
import RedisStore from 'connect-redis';
import { createClient } from 'redis';

const redisClient = createClient({ url: process.env.REDIS_URL });

app.use(session({
  store: new RedisStore({ client: redisClient }),
  secret: process.env.SESSION_SECRET!,
  name: '__session',  // Custom name, not 'connect.sid'
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    sameSite: 'strict',
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
  },
}));
```

---

## PASSWORD HANDLING

**PASS-001.** ALWAYS use Argon2 or bcrypt:
```typescript
import { hash, verify } from '@node-rs/argon2';

const HASH_OPTIONS = {
  memoryCost: 65536,  // 64MB
  timeCost: 3,
  parallelism: 4,
};

async function hashPassword(password: string): Promise<string> {
  return hash(password, HASH_OPTIONS);
}

async function verifyPassword(password: string, hash: string): Promise<boolean> {
  try {
    return await verify(hash, password);
  } catch {
    return false;
  }
}
```

**PASS-002.** ALWAYS validate password strength:
```typescript
import { z } from 'zod';

const passwordSchema = z.string()
  .min(8, 'Minimum 8 characters')
  .max(128, 'Maximum 128 characters')
  .regex(/[a-z]/, 'Need lowercase letter')
  .regex(/[A-Z]/, 'Need uppercase letter')
  .regex(/[0-9]/, 'Need number')
  .regex(/[^a-zA-Z0-9]/, 'Need special character');
```

---

## OAUTH 2.0 / OIDC

**OAUTH-001.** Implement OAuth flow with PKCE:
```typescript
import { generateCodeVerifier, generateCodeChallenge } from 'oauth4webapi';

// Step 1: Generate auth URL
async function getAuthUrl(provider: 'google' | 'github') {
  const codeVerifier = generateCodeVerifier();
  const codeChallenge = await generateCodeChallenge(codeVerifier);
  const state = crypto.randomUUID();

  // Store verifier and state in session
  await redis.setex(`oauth:${state}`, 600, JSON.stringify({ codeVerifier, provider }));

  const params = new URLSearchParams({
    client_id: config[provider].clientId,
    redirect_uri: config[provider].redirectUri,
    response_type: 'code',
    scope: config[provider].scope,
    state,
    code_challenge: codeChallenge,
    code_challenge_method: 'S256',
  });

  return `${config[provider].authUrl}?${params}`;
}

// Step 2: Handle callback
async function handleOAuthCallback(code: string, state: string) {
  const stored = await redis.get(`oauth:${state}`);
  if (!stored) throw new Error('Invalid state');

  const { codeVerifier, provider } = JSON.parse(stored);
  await redis.del(`oauth:${state}`);

  // Exchange code for tokens
  const tokens = await exchangeCode(provider, code, codeVerifier);
  const userInfo = await getUserInfo(provider, tokens.access_token);

  // Find or create user
  const user = await prisma.user.upsert({
    where: { email: userInfo.email },
    update: { lastLogin: new Date() },
    create: {
      email: userInfo.email,
      name: userInfo.name,
      provider,
      providerId: userInfo.id,
    },
  });

  return generateTokens(user.id);
}
```

---

## MIDDLEWARE PATTERNS

**MIDDLE-001.** Auth middleware:
```typescript
async function authMiddleware(req: Request, res: Response, next: NextFunction) {
  const token = req.headers.authorization?.replace('Bearer ', '');

  if (!token) {
    return res.status(401).json({ error: 'No token provided' });
  }

  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET!);

    if (payload.type !== 'access') {
      throw new Error('Invalid token type');
    }

    req.userId = payload.sub;
    next();
  } catch (error) {
    return res.status(401).json({ error: 'Invalid token' });
  }
}
```

**MIDDLE-002.** Role-based access control:
```typescript
function requireRole(...roles: string[]) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = await prisma.user.findUnique({
      where: { id: req.userId },
      select: { role: true },
    });

    if (!user || !roles.includes(user.role)) {
      return res.status(403).json({ error: 'Insufficient permissions' });
    }

    next();
  };
}

// Usage
app.delete('/admin/users/:id', authMiddleware, requireRole('admin'), deleteUser);
```

---

## LOGOUT & REVOCATION

**LOGOUT-001.** Implement proper logout:
```typescript
async function logout(userId: string, refreshToken?: string) {
  if (refreshToken) {
    // Revoke specific token
    await prisma.refreshToken.updateMany({
      where: {
        userId,
        tokenHash: await hash(refreshToken),
      },
      data: { revokedAt: new Date() },
    });
  } else {
    // Revoke all tokens (logout everywhere)
    await prisma.refreshToken.updateMany({
      where: { userId },
      data: { revokedAt: new Date() },
    });
  }
}
```

---

## QUICK REFERENCE

| Method | Use Case |
|--------|----------|
| JWT | Stateless APIs, microservices |
| Sessions | Traditional web apps, SSR |
| OAuth | Third-party login |
| API Keys | Server-to-server |
| mTLS | High-security services |
