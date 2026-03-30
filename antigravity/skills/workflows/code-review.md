# CODE REVIEW PATTERNS

> **Khi nào tải skill này:** Review, Code Review, PR, Quality, Feedback

---

## REVIEW CHECKLIST

**REVIEW-001.** Systematic review approach:
```markdown
## Code Review Checklist

### Correctness
- [ ] Logic is correct and handles edge cases
- [ ] Error handling is appropriate
- [ ] No obvious bugs

### Security
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] No SQL injection / XSS vulnerabilities
- [ ] Auth/authz checks in place

### Performance
- [ ] No N+1 queries
- [ ] Appropriate caching
- [ ] No memory leaks
- [ ] Efficient algorithms

### Maintainability
- [ ] Code is readable and self-documenting
- [ ] Functions are small and focused
- [ ] No code duplication
- [ ] Follows project conventions

### Testing
- [ ] Tests cover happy path
- [ ] Tests cover edge cases
- [ ] Tests are maintainable
```

---

## GIVING FEEDBACK

**FEEDBACK-001.** Constructive comment patterns:
```markdown
# Good comment patterns

## Question (explore reasoning)
"What was the thinking behind using X here instead of Y?"

## Suggestion (offer alternative)
"Consider using `map` here instead of `forEach` to make the intent clearer
and avoid the intermediate variable."

## Nitpick (minor, optional)
"nit: Could rename `data` to `userData` for clarity, but not blocking."

## Praise (reinforce good patterns)
"Nice use of early returns here - makes the logic much easier to follow!"

## Blocking (must fix)
"**Blocking**: This SQL query is vulnerable to injection.
Please use parameterized queries."

## Teaching (share knowledge)
"FYI: There's a newer API for this - `AbortController`.
Happy to pair on migrating if you'd like."
```

**FEEDBACK-002.** Comment prefixes:
```
[nit]      → Style/naming, optional
[question] → Seeking clarification
[suggest]  → Improvement idea
[discuss]  → Needs conversation
[blocking] → Must fix before merge
[praise]   → Good work recognition
```

---

## RECEIVING FEEDBACK

**RECEIVE-001.** Responding to reviews:
```markdown
## Good response patterns

✅ "Good catch, fixed in abc123"
✅ "I chose X because [reason]. Happy to change if you still prefer Y"
✅ "Could you explain more? I'm not sure I understand the concern"
✅ "Agreed, will refactor. Created follow-up issue #123"

## Avoid

❌ "Works on my machine"
❌ "That's just how I like it"
❌ "It's fine" (without explanation)
❌ Defensive or dismissive responses
```

---

## PR BEST PRACTICES

**PR-001.** PR description template:
```markdown
## Summary
Brief description of what this PR does.

## Changes
- Added user authentication endpoint
- Updated login form validation
- Added unit tests for auth service

## Testing
- [ ] Unit tests pass
- [ ] Manual testing completed
- [ ] No regressions in existing features

## Screenshots (if UI changes)
Before | After
-------|------
[img]  | [img]

## Related
Fixes #123
Depends on #122
```

**PR-002.** PR sizing guidelines:
```
XS: < 50 lines   → Quick review
S:  50-200 lines → Normal review
M:  200-500 lines → Careful review
L:  500-1000 lines → Split if possible
XL: > 1000 lines → Please split!

Smaller PRs = faster reviews = fewer bugs
```

---

## AUTOMATED CHECKS

**AUTO-001.** Pre-review automation:
```yaml
# .github/workflows/pr-checks.yml
name: PR Checks

on: pull_request

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test -- --coverage
      - uses: codecov/codecov-action@v3

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm audit --audit-level=high
```

---

## COMMON ISSUES TO CATCH

**ISSUE-001.** Security issues:
```typescript
// ❌ Hardcoded secret
const API_KEY = 'sk_live_abc123';

// ❌ SQL injection
const query = `SELECT * FROM users WHERE id = '${userId}'`;

// ❌ XSS vulnerability
element.innerHTML = userInput;

// ❌ Missing auth check
app.delete('/users/:id', deleteUser);  // Anyone can delete!

// ❌ Sensitive data in logs
console.log('User:', { email, password, ssn });
```

**ISSUE-002.** Performance issues:
```typescript
// ❌ N+1 query
const users = await prisma.user.findMany();
for (const user of users) {
  user.posts = await prisma.post.findMany({ where: { authorId: user.id } });
}

// ❌ Blocking operation in loop
for (const file of files) {
  await processFile(file);  // Should use Promise.all
}

// ❌ Missing index
await prisma.order.findMany({
  where: { status: 'pending', createdAt: { gt: yesterday } },
});
// But no index on (status, createdAt)
```

---

## QUICK REFERENCE

| Review Focus | Questions to Ask |
|--------------|------------------|
| Logic | Does it do what it claims? |
| Edge cases | What if null/empty/huge? |
| Security | Can this be exploited? |
| Performance | Will this scale? |
| Tests | Are edge cases covered? |
| Readability | Can I understand in 30s? |

| PR Size | Review Time |
|---------|-------------|
| < 50 lines | 5-10 min |
| 50-200 lines | 15-30 min |
| 200-500 lines | 30-60 min |
| > 500 lines | Split it! |
