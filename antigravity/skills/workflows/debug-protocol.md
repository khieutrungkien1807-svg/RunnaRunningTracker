# DEBUG PROTOCOL

> **Khi nào tải skill này:** Debug, Bug, Error, Fix, Troubleshoot, Issue

---

## DEBUG METHODOLOGY

**DEBUG-001.** Systematic debugging approach:
```
1. REPRODUCE → Recreate the bug consistently
2. ISOLATE   → Find minimal reproduction case
3. IDENTIFY  → Locate the root cause
4. FIX       → Implement the solution
5. VERIFY    → Confirm fix works
6. PREVENT   → Add tests/safeguards
```

---

## REPRODUCE

**REPRO-001.** Gather information:
```markdown
## Bug Report Template

**Environment:**
- OS: Windows 11 / macOS 14 / Ubuntu 22.04
- Node: v20.10.0
- Browser: Chrome 120

**Steps to reproduce:**
1. Navigate to /dashboard
2. Click "Create New"
3. Fill form and submit
4. Error appears

**Expected:** Success message
**Actual:** "TypeError: Cannot read property 'id' of undefined"

**Frequency:** Always / Sometimes / Once

**Screenshots/Logs:**
[Attach relevant data]
```

---

## ISOLATE

**ISOLATE-001.** Binary search debugging:
```typescript
// Narrow down the problem area
async function processOrder(order: Order) {
  console.log('Step 1: Validating order', order); // Check here

  const validated = await validateOrder(order);
  console.log('Step 2: Order validated', validated); // Or here

  const payment = await processPayment(validated);
  console.log('Step 3: Payment processed', payment); // Or here

  const confirmation = await sendConfirmation(payment);
  console.log('Step 4: Confirmation sent', confirmation); // Or here

  return confirmation;
}
```

**ISOLATE-002.** Create minimal reproduction:
```typescript
// Instead of debugging full app, create isolated test
// minimal-repro.ts
import { processPayment } from './payment';

const testOrder = {
  id: 'test-123',
  items: [{ productId: 'prod-1', quantity: 2 }],
  userId: undefined, // This is likely the issue
};

processPayment(testOrder).then(console.log).catch(console.error);
```

---

## IDENTIFY ROOT CAUSE

**ROOT-001.** Common bug patterns:
```typescript
// 1. Null/undefined access
const name = user.profile.name; // user.profile is undefined
// Fix: Optional chaining
const name = user?.profile?.name;

// 2. Async race condition
const data = await Promise.all([fetchA(), fetchB()]);
// One rejected → both fail
// Fix: Handle individually
const [a, b] = await Promise.allSettled([fetchA(), fetchB()]);

// 3. Stale closure
useEffect(() => {
  const interval = setInterval(() => {
    console.log(count); // Always logs initial value
  }, 1000);
  return () => clearInterval(interval);
}, []); // Missing dependency
// Fix: Add count to dependencies

// 4. Memory leak
useEffect(() => {
  const subscription = api.subscribe(handler);
  // Missing cleanup!
  return () => subscription.unsubscribe();
}, []);

// 5. Type coercion
if (value == false) { } // "" == false is true!
// Fix: Use strict equality
if (value === false) { }
```

---

## DEBUGGING TOOLS

**TOOLS-001.** Browser DevTools:
```javascript
// Breakpoints
debugger; // Pauses execution

// Console methods
console.log(obj);           // Basic
console.table(arrayOfObjs); // Table view
console.trace();            // Stack trace
console.time('label');      // Start timer
console.timeEnd('label');   // End timer
console.group('Group');     // Group logs
console.groupEnd();
console.assert(condition, 'Failed!'); // Conditional log
```

**TOOLS-002.** Node.js debugging:
```bash
# Start with inspector
node --inspect src/server.ts

# Break on first line
node --inspect-brk src/server.ts

# With ts-node
node --inspect -r ts-node/register src/server.ts
```

**TOOLS-003.** Memory debugging:
```javascript
// Check memory usage
console.log(process.memoryUsage());

// Heap snapshot (Chrome DevTools)
// Performance tab → Memory → Take heap snapshot

// Node.js heap dump
const v8 = require('v8');
v8.writeHeapSnapshot();
```

---

## LOGGING BEST PRACTICES

**LOG-001.** Structured logging:
```typescript
import pino from 'pino';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  transport: {
    target: 'pino-pretty',
    options: { colorize: true },
  },
});

// Usage
logger.info({ userId, action: 'login' }, 'User logged in');
logger.error({ error, requestId }, 'Payment failed');

// Levels: trace < debug < info < warn < error < fatal
```

**LOG-002.** Correlation IDs:
```typescript
// Middleware to add request ID
app.use((req, res, next) => {
  req.requestId = req.headers['x-request-id'] || crypto.randomUUID();
  res.setHeader('x-request-id', req.requestId);
  next();
});

// Use in logs
logger.info({ requestId: req.requestId }, 'Processing request');
```

---

## ERROR ANALYSIS

**ANALYZE-001.** Read stack traces:
```
TypeError: Cannot read properties of undefined (reading 'email')
    at UserService.getProfile (/app/src/services/user.ts:45:23)
    ^^^^ Method that threw
    at async UserController.profile (/app/src/controllers/user.ts:12:18)
    ^^^^ Called from here
    at async /app/src/middleware/async.ts:8:7
```

**Key info:**
- Error type: `TypeError`
- Property: `email`
- File: `user.ts`
- Line: 45
- Call stack: controller → service

---

## FIX PATTERNS

**FIX-001.** Defensive coding:
```typescript
// Before
function getUsername(user: User) {
  return user.profile.username;
}

// After - with guards
function getUsername(user: User | null | undefined) {
  if (!user?.profile?.username) {
    return 'Anonymous';
  }
  return user.profile.username;
}
```

**FIX-002.** Add validation:
```typescript
// Before
async function deleteUser(id: string) {
  await prisma.user.delete({ where: { id } });
}

// After - with validation
async function deleteUser(id: string) {
  const user = await prisma.user.findUnique({ where: { id } });

  if (!user) {
    throw new NotFoundError('User', id);
  }

  if (user.role === 'admin') {
    throw new ForbiddenError('Cannot delete admin users');
  }

  await prisma.user.delete({ where: { id } });
}
```

---

## QUICK REFERENCE

| Symptom | Likely Cause |
|---------|--------------|
| "undefined is not a function" | Missing import, typo |
| "Cannot read property of undefined" | Null access |
| Infinite loop | Missing exit condition |
| Memory grows | Event listener leak |
| Stale data | Cache not invalidated |
| Race condition | Async timing issue |
| CORS error | Server config |
| 404 on refresh | SPA routing |
