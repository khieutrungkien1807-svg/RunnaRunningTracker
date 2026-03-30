# GIT WORKFLOW

> **Khi nào tải skill này:** Git, Commit, Branch, Merge, Rebase, Version

---

## COMMIT CONVENTIONS

**COMMIT-001.** Use Conventional Commits:
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code change, no feature/fix
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes
- `build`: Build system changes

**Examples:**
```bash
# Feature
git commit -m "feat(auth): add OAuth2 login with Google"

# Bug fix
git commit -m "fix(api): handle null response from external service"

# Breaking change
git commit -m "feat(api)!: change response format to JSON:API spec

BREAKING CHANGE: Response structure changed from {data} to {data, meta, links}"
```

---

## BRANCHING STRATEGY

**BRANCH-001.** GitHub Flow (recommended for most teams):
```
main (production-ready)
  └── feature/add-user-auth
  └── feature/payment-integration
  └── fix/login-redirect-bug
  └── hotfix/security-patch
```

**Branch naming:**
```bash
feature/description    # New features
fix/description        # Bug fixes
hotfix/description     # Urgent production fixes
refactor/description   # Code refactoring
docs/description       # Documentation updates
```

**BRANCH-002.** Git Flow (for release cycles):
```
main (production)
  └── develop (integration)
        └── feature/xxx
        └── release/v1.2.0
              └── (merged to main + develop)
        └── hotfix/xxx
              └── (merged to main + develop)
```

---

## MERGE VS REBASE

**MERGE-001.** When to use each:
```bash
# Merge - preserves history, good for feature branches
git checkout main
git merge feature/add-auth

# Rebase - clean linear history, good before merging
git checkout feature/add-auth
git rebase main

# Squash merge - combines all commits into one
git checkout main
git merge --squash feature/add-auth
git commit -m "feat(auth): add user authentication"
```

**MERGE-002.** Interactive rebase for cleanup:
```bash
# Squash/reword commits before PR
git rebase -i HEAD~5

# In editor:
pick abc1234 feat: add login form
squash def5678 fix typo
squash ghi9012 add validation
reword jkl3456 add tests
drop mno7890 debugging code
```

---

## COMMON OPERATIONS

**OP-001.** Undo changes:
```bash
# Unstage file
git reset HEAD <file>

# Discard working changes
git checkout -- <file>

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Create revert commit
git revert <commit-hash>
```

**OP-002.** Stash changes:
```bash
# Stash current changes
git stash

# Stash with message
git stash push -m "WIP: feature X"

# List stashes
git stash list

# Apply and remove
git stash pop

# Apply without removing
git stash apply stash@{0}

# Drop stash
git stash drop stash@{0}
```

**OP-003.** Cherry-pick:
```bash
# Apply specific commit to current branch
git cherry-pick <commit-hash>

# Cherry-pick without committing
git cherry-pick -n <commit-hash>
```

---

## PR WORKFLOW

**PR-001.** Before creating PR:
```bash
# Update from main
git checkout main
git pull origin main
git checkout feature/my-feature
git rebase main

# Fix any conflicts, then:
git push -f origin feature/my-feature
```

**PR-002.** PR checklist:
- [ ] Rebased on latest main
- [ ] All tests passing
- [ ] Code reviewed by self
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No console.logs or debug code
- [ ] Linked to issue/ticket

---

## HOOKS

**HOOK-001.** Pre-commit hooks with Husky + lint-staged:
```json
// package.json
{
  "scripts": {
    "prepare": "husky"
  },
  "lint-staged": {
    "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.{json,md}": ["prettier --write"]
  }
}
```

```bash
# .husky/pre-commit
npm run lint-staged
```

```bash
# .husky/commit-msg
npx commitlint --edit $1
```

**HOOK-002.** Commitlint config:
```js
// commitlint.config.js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', [
      'feat', 'fix', 'docs', 'style', 'refactor',
      'perf', 'test', 'chore', 'ci', 'build'
    ]],
    'subject-case': [2, 'always', 'lower-case'],
  },
};
```

---

## TROUBLESHOOTING

**TROUBLE-001.** Fix common issues:
```bash
# Wrong branch, uncommitted changes
git stash
git checkout correct-branch
git stash pop

# Committed to wrong branch
git checkout correct-branch
git cherry-pick <commit-hash>
git checkout wrong-branch
git reset --hard HEAD~1

# Need to edit old commit
git rebase -i <commit-hash>^
# Change 'pick' to 'edit' for target commit
# Make changes, then:
git add .
git rebase --continue

# Resolve merge conflict
# Edit conflicted files, then:
git add <resolved-files>
git rebase --continue
# Or abort:
git rebase --abort
```

---

## QUICK REFERENCE

| Command | Purpose |
|---------|---------|
| `git log --oneline` | Compact history |
| `git diff --staged` | Staged changes |
| `git branch -d` | Delete merged branch |
| `git branch -D` | Force delete branch |
| `git push -u origin` | Push and track |
| `git fetch --prune` | Clean stale remotes |
| `git reflog` | Recovery history |
