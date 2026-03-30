# FORMS & VALIDATION PATTERNS

> **Khi nào tải skill này:** Form, Validation, Input, Schema, Submit, Field

---

## FORM LIBRARY RULES

**FORM-001.** Use React Hook Form + Zod for type-safe forms:
```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Min 8 characters'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
});

type FormData = z.infer<typeof schema>;

function SignupForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    await createUser(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} />
      {errors.email && <span>{errors.email.message}</span>}

      <input type="password" {...register('password')} />
      {errors.password && <span>{errors.password.message}</span>}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Loading...' : 'Sign Up'}
      </button>
    </form>
  );
}
```

---

## VALIDATION SCHEMAS

**VAL-001.** Common Zod patterns:
```typescript
import { z } from 'zod';

// Email with custom error
const email = z.string().email({ message: 'Invalid email format' });

// Password with requirements
const password = z.string()
  .min(8, 'At least 8 characters')
  .regex(/[A-Z]/, 'Need uppercase letter')
  .regex(/[0-9]/, 'Need number');

// Phone number
const phone = z.string().regex(/^\+?[1-9]\d{1,14}$/, 'Invalid phone');

// URL
const url = z.string().url('Invalid URL');

// Date range
const dateRange = z.object({
  start: z.coerce.date(),
  end: z.coerce.date(),
}).refine((data) => data.end > data.start, {
  message: 'End date must be after start',
  path: ['end'],
});

// File upload
const fileSchema = z.instanceof(File)
  .refine((f) => f.size < 5_000_000, 'Max 5MB')
  .refine((f) => ['image/jpeg', 'image/png'].includes(f.type), 'Only JPG/PNG');
```

**VAL-002.** Conditional validation:
```typescript
const schema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('individual'),
    firstName: z.string().min(1),
    lastName: z.string().min(1),
  }),
  z.object({
    type: z.literal('company'),
    companyName: z.string().min(1),
    taxId: z.string().regex(/^\d{9}$/),
  }),
]);
```

---

## INPUT COMPONENTS

**INPUT-001.** Create reusable form input:
```tsx
import { forwardRef } from 'react';
import { FieldError } from 'react-hook-form';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: FieldError;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, id, ...props }, ref) => {
    const inputId = id || label.toLowerCase().replace(/\s/g, '-');

    return (
      <div className="space-y-1">
        <label htmlFor={inputId} className="block text-sm font-medium">
          {label}
        </label>
        <input
          ref={ref}
          id={inputId}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : undefined}
          className={`
            w-full px-3 py-2 border rounded-lg
            ${error ? 'border-red-500' : 'border-gray-300'}
            focus:outline-none focus:ring-2
          `}
          {...props}
        />
        {error && (
          <p id={`${inputId}-error`} className="text-sm text-red-500">
            {error.message}
          </p>
        )}
      </div>
    );
  }
);
```

---

## FORM STATE PATTERNS

**STATE-001.** Handle async submission:
```tsx
function ContactForm() {
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    handleSubmit,
    setError,
    formState: { isSubmitting },
  } = useForm<FormData>();

  const onSubmit = async (data: FormData) => {
    try {
      setServerError(null);
      await submitForm(data);
    } catch (err) {
      if (err instanceof ValidationError) {
        // Set field-specific errors from server
        err.fields.forEach(({ field, message }) => {
          setError(field as keyof FormData, { message });
        });
      } else {
        setServerError('Something went wrong. Please try again.');
      }
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {serverError && <Alert type="error">{serverError}</Alert>}
      {/* fields */}
    </form>
  );
}
```

**STATE-002.** Multi-step forms:
```tsx
function MultiStepForm() {
  const [step, setStep] = useState(1);
  const methods = useForm<FullFormData>({
    mode: 'onChange',
  });

  const nextStep = async () => {
    const fields = stepFields[step];
    const isValid = await methods.trigger(fields);
    if (isValid) setStep((s) => s + 1);
  };

  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)}>
        {step === 1 && <PersonalInfo />}
        {step === 2 && <AddressInfo />}
        {step === 3 && <PaymentInfo />}

        <div className="flex gap-4">
          {step > 1 && (
            <button type="button" onClick={() => setStep((s) => s - 1)}>
              Back
            </button>
          )}
          {step < 3 ? (
            <button type="button" onClick={nextStep}>
              Next
            </button>
          ) : (
            <button type="submit">Submit</button>
          )}
        </div>
      </form>
    </FormProvider>
  );
}
```

---

## ACCESSIBILITY

**A11Y-001.** ALWAYS associate labels and errors:
```tsx
<div>
  <label htmlFor="email">Email</label>
  <input
    id="email"
    type="email"
    aria-invalid={!!errors.email}
    aria-describedby="email-error email-hint"
  />
  <p id="email-hint">We'll never share your email</p>
  {errors.email && (
    <p id="email-error" role="alert">
      {errors.email.message}
    </p>
  )}
</div>
```

**A11Y-002.** Announce form submission state:
```tsx
<div aria-live="polite" className="sr-only">
  {isSubmitting && 'Submitting form...'}
  {isSuccess && 'Form submitted successfully'}
  {isError && 'Form submission failed'}
</div>
```

---

## QUICK REFERENCE

| Pattern | Library |
|---------|---------|
| Form state | react-hook-form |
| Validation | zod |
| Resolver | @hookform/resolvers |
| Server validation | setError() |
| Field arrays | useFieldArray |
| Watch values | watch(), useWatch() |
| Form context | FormProvider |
