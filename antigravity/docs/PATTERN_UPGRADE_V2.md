# Pattern Extractor v2: Context-Aware Upgrade

**Critical Issue:** v1 patterns quá generic → LLM đã biết → không tạo signal mới

**Solution:** Context-aware patterns với attempted_fix + correct_direction

---

## 🔥 10 High-Signal Patterns (v2)

### 1. wrong_fix_strategy
```python
pattern = {
    "type": "wrong_fix_strategy",
    "cause": "added null check for undefined function error",
    "context": {
        "error_type": "TypeError: undefined is not a function",
        "file_type": "react_component"
    },
    "attempted_fix": "added null check before function call",
    "correct_direction": "fix import statement - function not imported"
}

lesson = {
    "avoid": "Adding defensive null checks when root cause is missing import",
    "prefer": "Trace error to source - TypeError often means wrong import, not null value"
}
```

### 2. wrong_file_modified
```python
pattern = {
    "type": "wrong_file_modified",
    "cause": "modified component file when error was in parent",
    "context": {
        "error_file": "ParentComponent.jsx",
        "modified_file": "ChildComponent.jsx"
    },
    "attempted_fix": "changed props in child component",
    "correct_direction": "fix prop passing in parent component"
}

lesson = {
    "avoid": "Modifying child components when error trace points to parent",
    "prefer": "Follow stack trace to actual error location before making changes"
}
```

### 3. test_breaking_change
```python
pattern = {
    "type": "test_breaking_change",
    "cause": "changed function signature without updating tests",
    "context": {
        "function": "calculateTotal",
        "test_file": "calculateTotal.test.js",
        "change_type": "added_parameter"
    },
    "attempted_fix": "added new parameter to function",
    "correct_direction": "update all test calls with new parameter"
}

lesson = {
    "avoid": "Changing function signatures without checking test coverage",
    "prefer": "Search for all usages (tests + code) before signature changes"
}
```

### 4. incomplete_fix
```python
pattern = {
    "type": "incomplete_fix",
    "cause": "fixed one occurrence but missed others",
    "context": {
        "symbol": "oldFunctionName",
        "occurrences_fixed": 1,
        "occurrences_remaining": 3
    },
    "attempted_fix": "renamed function in one file",
    "correct_direction": "use find-all-references to rename everywhere"
}

lesson = {
    "avoid": "Fixing only the first occurrence of a problem",
    "prefer": "Use global search to find ALL occurrences before fixing"
}
```

### 5. overfix
```python
pattern = {
    "type": "overfix",
    "cause": "changed multiple unrelated things in one patch",
    "context": {
        "original_error": "missing import useState",
        "changes_made": ["added import", "refactored component", "changed styling"]
    },
    "attempted_fix": "fixed import + refactored entire component",
    "correct_direction": "only add the missing import"
}

lesson = {
    "avoid": "Making multiple unrelated changes when fixing one error",
    "prefer": "Minimal fix - change ONLY what's needed to resolve the error"
}
```

### 6. wrong_assumption_about_type
```python
pattern = {
    "type": "wrong_assumption",
    "cause": "assumed array but got object",
    "context": {
        "variable": "data",
        "assumed_type": "array",
        "actual_type": "object",
        "method_used": "map"
    },
    "attempted_fix": "called .map() on object",
    "correct_direction": "check API response structure or use Object.values()"
}

lesson = {
    "avoid": "Assuming data types without checking API/function return values",
    "prefer": "Add type guards or check actual data structure before operations"
}
```

### 7. dependency_not_updated
```python
pattern = {
    "type": "dependency_not_updated",
    "cause": "used new API without updating package version",
    "context": {
        "package": "react",
        "current_version": "17.0.0",
        "required_version": "18.0.0",
        "api_used": "useId"
    },
    "attempted_fix": "imported useId from react",
    "correct_direction": "upgrade react to v18 first"
}

lesson = {
    "avoid": "Using new APIs without checking package version requirements",
    "prefer": "Check package.json and upgrade dependencies before using new features"
}
```

### 8. incorrect_refactor_scope
```python
pattern = {
    "type": "incorrect_refactor_scope",
    "cause": "refactored too much code at once",
    "context": {
        "files_changed": 5,
        "original_error": "one function bug",
        "refactor_scope": "entire module"
    },
    "attempted_fix": "refactored entire module structure",
    "correct_direction": "fix only the buggy function"
}

lesson = {
    "avoid": "Large refactors when fixing small bugs - introduces new errors",
    "prefer": "Surgical fixes - refactor separately after bug is fixed"
}
```

### 9. fix_symptom_not_root
```python
pattern = {
    "type": "fix_symptom_not_root",
    "cause": "suppressed error instead of fixing cause",
    "context": {
        "error": "Cannot read property 'name' of undefined",
        "symptom_fix": "added optional chaining",
        "root_cause": "data not loaded before render"
    },
    "attempted_fix": "changed user.name to user?.name",
    "correct_direction": "add loading state and wait for data"
}

lesson = {
    "avoid": "Using optional chaining to hide undefined errors",
    "prefer": "Fix data flow - ensure data exists before accessing properties"
}
```

### 10. no_op_patch (upgraded)
```python
pattern = {
    "type": "no_op_patch",
    "cause": "generated identical code",
    "context": {
        "error_type": "syntax_error",
        "patch_size": 0,
        "llm_confidence": "high"  # LLM thought it fixed something
    },
    "attempted_fix": "regenerated same code",
    "correct_direction": "analyze error more carefully - current approach not working"
}

lesson = {
    "avoid": "Regenerating same code when first attempt failed",
    "prefer": "Change strategy completely - try different approach or ask for clarification"
}
```

---

## 🎯 Prompt Injection v2 (Directive Style)

**OLD (weak):**
```
Avoid: missing import
Prefer: add import statement
```

**NEW (strong):**
```
[CRITICAL FAILURE PATTERN #1]
Previous attempt: Added null check for "TypeError: undefined is not a function"
Why it failed: Root cause was missing import, not null value
What you MUST do differently:
  1. When you see "undefined is not a function" → CHECK IMPORTS FIRST
  2. Do NOT add defensive null checks as first response
  3. Trace the function name in error to import statements
Confidence: 90% (seen 9 times)
```

---

## 📊 Effectiveness Tracking

Add to FailureEntry:
```python
@dataclass
class FailureEntry:
    surface: FailureSurface
    pattern: FailurePattern
    lesson: FailureLesson
    frequency: int = 1

    # v2: Effectiveness tracking
    times_injected: int = 0  # How many times this lesson was shown
    times_helped: int = 0    # How many times it prevented same error
    effectiveness: float = 0.0  # times_helped / times_injected
```

---

## 🔍 Retrieval Scoring v2

**OLD:**
- Pattern type match: 40%
- Keyword match: 30%
- Symbol overlap: 20%
- Recency: 10%

**NEW:**
- **Effectiveness score: 40%** ← NEW (only inject high-signal patterns)
- Context match: 30% (file_type, framework, error_type)
- Pattern type match: 20%
- Frequency: 10%

---

## 🚀 Implementation Priority

1. **Upgrade PatternExtractor** with 10 new rules (2 hours)
2. **Upgrade prompt injection** to directive style (1 hour)
3. **Add effectiveness tracking** (1 hour)
4. **Update retrieval scoring** (30 min)

**Total: 4.5 hours** (half day)

---

**This will transform the system from "có học" → "học hiệu quả thật"**
