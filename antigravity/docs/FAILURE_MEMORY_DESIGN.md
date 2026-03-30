# FailureMemory Design - Data Shape Definition

**Critical:** This document defines the **shape** of learning loop, not just architecture.
**Philosophy:** Structured learning system, NOT log storage.

---

## 🎯 Core Principle

```
Raw Logs → Patterns → Lessons → LLM Injection
   ❌         ✅         ✅          ✅
```

**Wrong:** Store patch + error message (LLM learns nothing)
**Right:** Extract semantic patterns + strategic lessons (LLM learns to avoid)

---

## 📊 3-Layer Abstraction

### Layer 1: Surface (Observable)

```python
@dataclass
class FailureSurface:
    """Raw observable data - what happened"""
    failure_id: str              # SHA-256(patch_content)
    patch_diff: str              # git diff format
    error_delta: ErrorDelta      # from DeterministicChecker
    files_touched: list[str]
    timestamp: datetime
    session_id: str
```

✅ This layer you already have in spec.

---

### Layer 2: Semantic (LLM-Understandable)

```python
@dataclass
class FailurePattern:
    """Extracted semantic pattern - why it failed"""

    # Pattern identification
    pattern_type: Literal[
        "syntax_error",
        "runtime_error",
        "no_op_patch",
        "import_missing",
        "type_mismatch",
        "logic_error"
    ]

    # Root cause
    cause: str  # e.g., "missing import", "incorrect indentation"

    # Location context
    location: Literal[
        "top_of_file",      # imports, globals
        "function_body",
        "class_definition",
        "end_of_file"
    ]

    # Action that caused failure
    action: str  # e.g., "added function without import dependency"

    # Affected symbols
    symbols: list[str]  # e.g., ["foo", "bar"]

    # Pattern signature (for dedup)
    signature: str  # hash of (pattern_type, cause, location)
```

**👉 THIS IS THE MOST IMPORTANT LAYER**

Without this → learning loop is useless.

---

### Layer 3: Strategic (Decision Impact)

```python
@dataclass
class FailureLesson:
    """Strategic lesson - what to do differently"""

    # What to avoid
    avoid: str  # e.g., "adding new symbol without checking imports"

    # What to prefer instead
    prefer: str  # e.g., "modify existing function instead of adding new one"

    # Confidence (based on frequency)
    confidence: float  # 0.0-1.0

    # Applicability context
    applies_to: list[str]  # e.g., ["python", "import_statements"]
```

**👉 THIS IS WHAT GETS INJECTED INTO PROMPT**

---

## 🔧 PatternExtractor - The Brain

### Interface

```python
class PatternExtractor:
    """
    Extract semantic patterns from raw failures.
    Rule-based first, ML later.
    """

    def extract(
        self,
        surface: FailureSurface
    ) -> FailurePattern:
        """
        Main extraction pipeline.

        Pipeline:
            1. Classify error type
            2. Extract cause
            3. Determine location
            4. Identify action
            5. Extract symbols
            6. Compute signature
        """
        error_text = surface.error_delta.errors_introduced[0] if surface.error_delta.errors_introduced else ""

        # Step 1: Classify
        pattern_type = self._classify_error_type(error_text)

        # Step 2: Extract cause
        cause = self._extract_cause(error_text, pattern_type)

        # Step 3: Determine location
        location = self._determine_location(surface.patch_diff, error_text)

        # Step 4: Identify action
        action = self._identify_action(surface.patch_diff, pattern_type)

        # Step 5: Extract symbols
        symbols = self._extract_symbols(surface.patch_diff, error_text)

        # Step 6: Compute signature
        signature = self._compute_signature(pattern_type, cause, location)

        return FailurePattern(
            pattern_type=pattern_type,
            cause=cause,
            location=location,
            action=action,
            symbols=symbols,
            signature=signature
        )
```

---

## 📋 10 Pattern Rules (Rule-Based, No ML Yet)

### Rule 1: Missing Import

```python
def _rule_missing_import(error_text: str, patch_diff: str) -> FailurePattern | None:
    """
    Pattern: Added code uses undefined name
    Cause: Missing import statement
    """
    if "NameError" in error_text or "is not defined" in error_text:
        # Extract symbol name
        match = re.search(r"name '(\w+)' is not defined", error_text)
        if match:
            symbol = match.group(1)

            # Check if symbol appears in patch but no import added
            if symbol in patch_diff and "import" not in patch_diff:
                return FailurePattern(
                    pattern_type="import_missing",
                    cause="missing import",
                    location="top_of_file",
                    action=f"added code using '{symbol}' without import",
                    symbols=[symbol],
                    signature=hash_pattern("import_missing", "missing_import", "top_of_file")
                )
    return None
```

**Lesson:**
```
avoid: "adding new symbol without checking imports"
prefer: "add import statement before using new symbol"
```

---

### Rule 2: Unmatched Bracket

```python
def _rule_unmatched_bracket(error_text: str, patch_diff: str) -> FailurePattern | None:
    """
    Pattern: Syntax error with unmatched bracket
    Cause: Missing closing bracket
    """
    if "SyntaxError" in error_text and any(kw in error_text for kw in ["unmatched", "expected ']'", "expected ')'"]):
        # Determine bracket type
        if "']'" in error_text or "'['" in error_text:
            bracket_type = "square bracket"
        elif "')'" in error_text or "'('" in error_text:
            bracket_type = "parenthesis"
        else:
            bracket_type = "bracket"

        return FailurePattern(
            pattern_type="syntax_error",
            cause=f"unmatched {bracket_type}",
            location="function_body",
            action=f"added code with unmatched {bracket_type}",
            symbols=[],
            signature=hash_pattern("syntax_error", f"unmatched_{bracket_type}", "function_body")
        )
    return None
```

**Lesson:**
```
avoid: "writing complex expressions without bracket matching"
prefer: "use simpler expressions or verify bracket pairs"
```

---

### Rule 3: No-Op Patch

```python
def _rule_no_op_patch(surface: FailureSurface) -> FailurePattern | None:
    """
    Pattern: Patch doesn't change anything
    Cause: Identical content before/after
    """
    # Check if patch is empty or only whitespace changes
    if not surface.patch_diff.strip() or all(line.startswith(' ') for line in surface.patch_diff.split('\n')):
        return FailurePattern(
            pattern_type="no_op_patch",
            cause="identical content",
            location="function_body",
            action="generated patch with no semantic changes",
            symbols=[],
            signature=hash_pattern("no_op_patch", "identical_content", "function_body")
        )
    return None
```

**Lesson:**
```
avoid: "generating patches that don't change logic"
prefer: "analyze error carefully before suggesting changes"
```

---

### Rule 4: Incorrect Indentation

```python
def _rule_incorrect_indentation(error_text: str, patch_diff: str) -> FailurePattern | None:
    """
    Pattern: IndentationError
    Cause: Wrong indentation level
    """
    if "IndentationError" in error_text or "unexpected indent" in error_text:
        return FailurePattern(
            pattern_type="syntax_error",
            cause="incorrect indentation",
            location="function_body",
            action="added code with wrong indentation level",
            symbols=[],
            signature=hash_pattern("syntax_error", "incorrect_indentation", "function_body")
        )
    return None
```

**Lesson:**
```
avoid: "mixing tabs and spaces or wrong indent level"
prefer: "match existing indentation style (4 spaces for Python)"
```

---

### Rule 5: Type Mismatch

```python
def _rule_type_mismatch(error_text: str, patch_diff: str) -> FailurePattern | None:
    """
    Pattern: TypeError
    Cause: Wrong type passed to function
    """
    if "TypeError" in error_text:
        # Extract expected vs actual types
        match = re.search(r"expected (\w+), got (\w+)", error_text)
        if match:
            expected, actual = match.groups()
            return FailurePattern(
                pattern_type="type_mismatch",
                cause=f"passed {actual} instead of {expected}",
                location="function_body",
                action=f"called function with wrong type",
                symbols=[],
                signature=hash_pattern("type_mismatch", f"{actual}_to_{expected}", "function_body")
            )
    return None
```

**Lesson:**
```
avoid: "passing wrong types without checking function signature"
prefer: "verify parameter types before calling functions"
```

---

### Rule 6: Missing Colon

```python
def _rule_missing_colon(error_text: str, patch_diff: str) -> FailurePattern | None:
    """
    Pattern: SyntaxError with missing colon
    Cause: Forgot colon after if/for/def/class
    """
    if "SyntaxError" in error_text and "expected ':'" in error_text:
        # Determine statement type
        for stmt in ["if", "for", "while", "def", "class"]:
            if stmt in patch_diff:
                return FailurePattern(
                    pattern_type="syntax_error",
                    cause="missing colon",
                    location="function_body",
                    action=f"added {stmt} statement without colon",
                    symbols=[],
                    signature=hash_pattern("syntax_error", "missing_colon", "function_body")
                )
    return None
```

**Lesson:**
```
avoid: "forgetting colon after control flow statements"
prefer: "always add colon after if/for/while/def/class"
```

---

### Rule 7: Undefined Variable

```python
def _rule_undefined_variable(error_text: str, patch_diff: str) -> FailurePattern | None:
    """
    Pattern: NameError for local variable
    Cause: Used variable before assignment
    """
    if "NameError" in error_text and "local variable" in error_text:
        match = re.search(r"local variable '(\w+)'", error_text)
        if match:
            var_name = match.group(1)
            return FailurePattern(
                pattern_type="runtime_error",
                cause="used before assignment",
                location="function_body",
                action=f"used variable '{var_name}' before defining it",
                symbols=[var_name],
                signature=hash_pattern("runtime_error", "undefined_variable", "function_body")
            )
    return None
```

**Lesson:**
```
avoid: "using variables before assigning values"
prefer: "initialize variables before use"
```

---

### Rule 8: Attribute Error

```python
def _rule_attribute_error(error_text: str, patch_diff: str) -> FailurePattern | None:
    """
    Pattern: AttributeError
    Cause: Object doesn't have attribute
    """
    if "AttributeError" in error_text:
        match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error_text)
        if match:
            obj_type, attr_name = match.groups()
            return FailurePattern(
                pattern_type="runtime_error",
                cause=f"attribute '{attr_name}' doesn't exist on {obj_type}",
                location="function_body",
                action=f"accessed non-existent attribute",
                symbols=[attr_name],
                signature=hash_pattern("runtime_error", "attribute_error", "function_body")
            )
    return None
```

**Lesson:**
```
avoid: "accessing attributes without checking object type"
prefer: "verify object has attribute before accessing"
```

---

### Rule 9: Index Out of Range

```python
def _rule_index_out_of_range(error_text: str, patch_diff: str) -> FailurePattern | None:
    """
    Pattern: IndexError
    Cause: Accessed list index that doesn't exist
    """
    if "IndexError" in error_text and "out of range" in error_text:
        return FailurePattern(
            pattern_type="runtime_error",
            cause="index out of range",
            location="function_body",
            action="accessed list index without bounds check",
            symbols=[],
            signature=hash_pattern("runtime_error", "index_out_of_range", "function_body")
        )
    return None
```

**Lesson:**
```
avoid: "accessing list indices without checking length"
prefer: "check list length before accessing or use try/except"
```

---

### Rule 10: Division by Zero

```python
def _rule_division_by_zero(error_text: str, patch_diff: str) -> FailurePattern | None:
    """
    Pattern: ZeroDivisionError
    Cause: Divided by zero
    """
    if "ZeroDivisionError" in error_text:
        return FailurePattern(
            pattern_type="runtime_error",
            cause="division by zero",
            location="function_body",
            action="performed division without zero check",
            symbols=[],
            signature=hash_pattern("runtime_error", "division_by_zero", "function_body")
        )
    return None
```

**Lesson:**
```
avoid: "dividing without checking denominator is non-zero"
prefer: "add zero check before division or use try/except"
```

---

## 🔍 Retrieval Strategy (Mini HybridRetriever)

### NOT Naive "Last 3 Failures"

```python
class FailureMemoryRetriever:
    """
    Intelligent retrieval of relevant failures.
    Similar to HybridRetriever but for patterns.
    """

    def search_relevant(
        self,
        current_task: str,
        current_error: str,
        top_k: int = 3
    ) -> list[tuple[FailurePattern, FailureLesson, float]]:
        """
        Search for relevant past failures.

        Ranking factors:
        1. Pattern type match (syntax vs runtime)
        2. Cause similarity (keyword matching)
        3. Recency (newer = more relevant)
        4. Frequency (common patterns = more important)

        Returns: [(pattern, lesson, relevance_score)]
        """
        candidates = []

        for entry in self._memory.values():
            score = self._compute_relevance(
                entry.pattern,
                current_task,
                current_error
            )
            candidates.append((entry.pattern, entry.lesson, score))

        # Sort by relevance score descending
        candidates.sort(key=lambda x: x[2], reverse=True)

        return candidates[:top_k]

    def _compute_relevance(
        self,
        pattern: FailurePattern,
        task: str,
        error: str
    ) -> float:
        """
        Compute relevance score (0.0-1.0).

        Factors:
        - Pattern type match: +0.4
        - Cause keyword match: +0.3
        - Symbol overlap: +0.2
        - Recency: +0.1
        """
        score = 0.0

        # Pattern type match
        if pattern.pattern_type in error.lower():
            score += 0.4

        # Cause keyword match
        cause_keywords = pattern.cause.lower().split()
        if any(kw in error.lower() for kw in cause_keywords):
            score += 0.3

        # Symbol overlap
        if pattern.symbols:
            task_words = set(task.lower().split())
            symbol_overlap = len(set(pattern.symbols) & task_words)
            score += 0.2 * (symbol_overlap / len(pattern.symbols))

        # Recency (placeholder - would use timestamp)
        score += 0.1

        return min(score, 1.0)
```

---

## 🗄️ Storage Strategy

### NOT Global Infinite Append-Only

```python
class FailureMemoryStore:
    """
    Persistent storage with TTL, dedup, and frequency tracking.
    """

    def __init__(
        self,
        storage_path: Path,
        ttl_days: int = 7,
        max_entries: int = 1000
    ):
        self._storage_path = storage_path
        self._ttl = timedelta(days=ttl_days)
        self._max_entries = max_entries

        # In-memory index
        self._by_signature: dict[str, FailureEntry] = {}  # dedup
        self._by_frequency: dict[str, int] = {}           # count

    def store(
        self,
        surface: FailureSurface,
        pattern: FailurePattern,
        lesson: FailureLesson
    ) -> None:
        """
        Store failure with dedup and frequency tracking.
        """
        # Check if pattern already exists (dedup)
        if pattern.signature in self._by_signature:
            # Increment frequency
            self._by_frequency[pattern.signature] += 1

            # Update lesson confidence based on frequency
            existing = self._by_signature[pattern.signature]
            existing.lesson.confidence = min(
                1.0,
                self._by_frequency[pattern.signature] / 10.0
            )
        else:
            # New pattern
            entry = FailureEntry(
                surface=surface,
                pattern=pattern,
                lesson=lesson
            )
            self._by_signature[pattern.signature] = entry
            self._by_frequency[pattern.signature] = 1

        # Enforce max entries (LRU eviction)
        if len(self._by_signature) > self._max_entries:
            self._evict_oldest()

    def purge_expired(self) -> int:
        """Remove entries older than TTL."""
        now = datetime.now()
        expired = [
            sig for sig, entry in self._by_signature.items()
            if now - entry.surface.timestamp > self._ttl
        ]

        for sig in expired:
            del self._by_signature[sig]
            del self._by_frequency[sig]

        return len(expired)
```

---

## 💉 Prompt Injection Format

### What Gets Injected

```python
def format_for_prompt(
    relevant_failures: list[tuple[FailurePattern, FailureLesson, float]]
) -> str:
    """
    Format failures for LLM prompt injection.

    Focus on LESSONS, not raw data.
    """
    if not relevant_failures:
        return ""

    lines = ["[FAILURE MEMORY - LEARN FROM PAST MISTAKES]"]
    lines.append("Previous failed attempts with similar patterns:\n")

    for i, (pattern, lesson, score) in enumerate(relevant_failures, 1):
        lines.append(f"{i}. Pattern: {pattern.cause} ({pattern.pattern_type})")
        lines.append(f"   ❌ AVOID: {lesson.avoid}")
        lines.append(f"   ✅ PREFER: {lesson.prefer}")
        lines.append(f"   Confidence: {lesson.confidence:.0%}\n")

    lines.append("Apply these lessons to your repair strategy.")

    return "\n".join(lines)
```

**Example Output:**
```
[FAILURE MEMORY - LEARN FROM PAST MISTAKES]
Previous failed attempts with similar patterns:

1. Pattern: missing import (import_missing)
   ❌ AVOID: adding new symbol without checking imports
   ✅ PREFER: add import statement before using new symbol
   Confidence: 80%

2. Pattern: unmatched square bracket (syntax_error)
   ❌ AVOID: writing complex expressions without bracket matching
   ✅ PREFER: use simpler expressions or verify bracket pairs
   Confidence: 60%

3. Pattern: incorrect indentation (syntax_error)
   ❌ AVOID: mixing tabs and spaces or wrong indent level
   ✅ PREFER: match existing indentation style (4 spaces for Python)
   Confidence: 90%

Apply these lessons to your repair strategy.
```

---

## ✅ Success Criteria (Measurable)

After implementation, MUST measure:

1. **Retry Reduction:**
   ```python
   retry_reduction_rate = (
       (avg_retries_before - avg_retries_after) / avg_retries_before
   ) * 100
   # Target: > 30%
   ```

2. **No-Op Patch Reduction:**
   ```python
   no_op_reduction = (
       (no_op_count_before - no_op_count_after) / no_op_count_before
   ) * 100
   # Target: > 50%
   ```

3. **Rollback Rate Reduction:**
   ```python
   rollback_reduction = (
       (rollback_rate_before - rollback_rate_after) / rollback_rate_before
   ) * 100
   # Target: > 20%
   ```

**If these 3 metrics don't improve → Learning loop is placebo.**

---

## 🚀 Minimal Implementation Plan (4 Days)

### Day 1-2: Core Pipeline
```python
# Files to create:
antigravity/core/pattern_extractor.py  # 10 rules
antigravity/core/failure_memory.py     # store + retrieve
antigravity/core/schemas.py            # add 3 dataclasses
```

### Day 3: Integration
```python
# Files to modify:
antigravity/scripts/orchestrator.py    # inject memory
```

### Day 4: Dedup + Frequency
```python
# Enhance:
antigravity/core/failure_memory.py     # add dedup logic
```

**DON'T DO YET:**
- ❌ Embedding-based similarity (rule-based first)
- ❌ ML pattern extraction (rules sufficient)
- ❌ Complex retrieval (keyword matching enough)

---

## 🎯 Final Shape Lock

```
FailureSurface (what happened)
    ↓
PatternExtractor (10 rules)
    ↓
FailurePattern (why it failed)
    ↓
LessonGenerator (avoid/prefer)
    ↓
FailureLesson (what to do)
    ↓
FailureMemoryStore (dedup + frequency)
    ↓
FailureMemoryRetriever (relevance search)
    ↓
PromptInjector (top-3 lessons)
    ↓
LLM Repair (learns from past)
```

**This shape is LOCKED. No refactor needed later.**

---

**Status:** SHAPE LOCKED ✅
**Ready to code:** YES
**Risk of refactor:** MINIMAL (shape is correct)
**Next:** Implement Day 1-2 (Core Pipeline)
