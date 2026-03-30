# VALIDATION PATTERNS

> **Khi nào tải skill này:** Validation, Zod, Schema, Input, Sanitize

---

## ZOD BASICS

**ZOD-001.** Define schemas:
```typescript
import { z } from 'zod';

// Primitive types
const stringSchema = z.string();
const numberSchema = z.number();
const booleanSchema = z.boolean();
const dateSchema = z.date();

// With constraints
const email = z.string().email();
const password = z.string().min(8).max(100);
const age = z.number().int().min(0).max(150);
const url = z.string().url();
const uuid = z.string().uuid();

// Optional & nullable
const optional = z.string().optional();  // string | undefined
const nullable = z.string().nullable();  // string | null
const nullish = z.string().nullish();    // string | null | undefined

// Default values
const role = z.enum(['admin', 'user']).default('user');
```

---

## OBJECT SCHEMAS

**ZOD-002.** Complex object validation:
```typescript
const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  name: z.string().min(2).max(100),
  age: z.number().int().min(13).optional(),
  role: z.enum(['admin', 'user', 'guest']),
  metadata: z.record(z.string()),  // { [key: string]: string }
  tags: z.array(z.string()).max(10),
  createdAt: z.coerce.date(),
});

type User = z.infer<typeof UserSchema>;

// Partial (all fields optional)
const UpdateUserSchema = UserSchema.partial();

// Pick specific fields
const CreateUserSchema = UserSchema.pick({
  email: true,
  name: true,
  role: true,
});

// Omit fields
const PublicUserSchema = UserSchema.omit({
  role: true,
  metadata: true,
});

// Extend
const AdminUserSchema = UserSchema.extend({
  permissions: z.array(z.string()),
});
```

---

## ADVANCED PATTERNS

**ZOD-003.** Discriminated unions:
```typescript
const EventSchema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('click'),
    x: z.number(),
    y: z.number(),
  }),
  z.object({
    type: z.literal('keypress'),
    key: z.string(),
    modifiers: z.array(z.string()),
  }),
  z.object({
    type: z.literal('scroll'),
    direction: z.enum(['up', 'down']),
    amount: z.number(),
  }),
]);
```

**ZOD-004.** Refinements & transforms:
```typescript
// Custom validation
const passwordSchema = z.string()
  .min(8)
  .refine(
    (val) => /[A-Z]/.test(val) && /[a-z]/.test(val) && /[0-9]/.test(val),
    { message: 'Password must contain uppercase, lowercase, and number' }
  );

// Transform input
const trimmedString = z.string().transform(s => s.trim());

const parsedDate = z.string().transform(s => new Date(s));

// Coerce types
const numericString = z.coerce.number();  // "123" → 123
const dateString = z.coerce.date();       // "2024-01-01" → Date

// Preprocess
const normalizedEmail = z.preprocess(
  (val) => typeof val === 'string' ? val.toLowerCase().trim() : val,
  z.string().email()
);
```

**ZOD-005.** Cross-field validation:
```typescript
const PasswordFormSchema = z.object({
  password: z.string().min(8),
  confirmPassword: z.string(),
}).refine(
  (data) => data.password === data.confirmPassword,
  {
    message: "Passwords don't match",
    path: ['confirmPassword'],  // Error attached to this field
  }
);

const DateRangeSchema = z.object({
  startDate: z.coerce.date(),
  endDate: z.coerce.date(),
}).refine(
  (data) => data.endDate > data.startDate,
  {
    message: 'End date must be after start date',
    path: ['endDate'],
  }
);
```

---

## API VALIDATION

**API-001.** Request validation middleware:
```typescript
import { z, ZodSchema } from 'zod';
import { Request, Response, NextFunction } from 'express';

function validate<T extends ZodSchema>(schema: T) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse({
      body: req.body,
      query: req.query,
      params: req.params,
    });

    if (!result.success) {
      return res.status(422).json({
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Validation failed',
          details: result.error.flatten(),
        },
      });
    }

    req.validated = result.data;
    next();
  };
}

// Usage
const CreateUserRequest = z.object({
  body: z.object({
    email: z.string().email(),
    name: z.string().min(2),
  }),
});

app.post('/users', validate(CreateUserRequest), (req, res) => {
  const { email, name } = req.validated.body;
  // ...
});
```

---

## SANITIZATION

**SANITIZE-001.** Input sanitization:
```typescript
import DOMPurify from 'isomorphic-dompurify';

// HTML sanitization
const cleanHtml = DOMPurify.sanitize(userHtml, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
  ALLOWED_ATTR: ['href'],
});

// String sanitization schema
const sanitizedInput = z.string()
  .trim()
  .transform(s => s.replace(/[<>]/g, ''))  // Remove HTML brackets
  .refine(s => !s.includes('javascript:'), 'No javascript: allowed');

// File name sanitization
const safeFileName = z.string()
  .transform(s => s.replace(/[^a-zA-Z0-9.-]/g, '_'))
  .refine(s => !s.startsWith('.'), 'No hidden files');
```

---

## ERROR FORMATTING

**ERROR-001.** Format Zod errors:
```typescript
function formatZodError(error: z.ZodError) {
  return error.errors.map(err => ({
    field: err.path.join('.'),
    message: err.message,
    code: err.code,
  }));
}

// Or use flatten
const flattened = error.flatten();
// {
//   formErrors: [],
//   fieldErrors: {
//     email: ['Invalid email'],
//     name: ['String must contain at least 2 character(s)'],
//   }
// }
```

---

## QUICK REFERENCE

| Method | Purpose |
|--------|---------|
| `.parse()` | Validate, throw on error |
| `.safeParse()` | Validate, return result object |
| `.partial()` | Make all fields optional |
| `.required()` | Make all fields required |
| `.pick()` | Select specific fields |
| `.omit()` | Remove specific fields |
| `.extend()` | Add new fields |
| `.merge()` | Combine schemas |
| `.refine()` | Custom validation |
| `.transform()` | Transform value |

| Type | Example |
|------|---------|
| `z.string()` | Basic string |
| `z.number()` | Number (incl. float) |
| `z.coerce.number()` | Parse string to number |
| `z.enum()` | Fixed set of values |
| `z.array()` | Array of type |
| `z.object()` | Object shape |
| `z.union()` | One of types |
| `z.discriminatedUnion()` | Tagged union |
