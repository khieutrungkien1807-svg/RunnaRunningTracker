# Phase 1 Final Safety Layer

> **Status:** IN PROGRESS
> **Goal:** Protect the learning loop from noise and bias before Phase 2 evolution

---

## Why This Matters

Phase 2 introduces:
- Pattern mutation
- Pattern deletion
- Pattern splitting

If retrieval/routing is even slightly off, we get **self-reinforcing wrong patterns**—the system looks like it's learning but is actually drifting.

---

## Critical Missing Tests (Priority Order)

### 1. HybridRetriever Properties (HIGH PRIORITY)

This is the **selection brain**. Without these guarantees:
- Good patterns may not be retrieved
- Bad patterns dominate due to scoring quirks
- Non-deterministic behavior under small input changes

**Required Properties:**

#### P1: Monotonicity
```python
@given(query=text(), patterns=lists(pattern_strategy()))
def test_better_match_not_worse_score(query, patterns):
    """Better semantic match → not worse score"""
    # If pattern A is semantically closer to query than B
    # Then score(A) >= score(B)
```

#### P2: Stability
```python
@given(query=text(), small_variation=text())
def test_small_input_small_ranking_change(query, small_variation):
    """Small input change → small ranking change"""
    # Levenshtein(query, variation) < 3
    # → ranking order shouldn't flip dramatically
```

#### P3: Filter Correctness
```python
@given(confidence=floats(0, 1), patterns=lists(pattern_strategy()))
def test_confidence_threshold_predictable(confidence, patterns):
    """Confidence threshold behaves predictably"""
    # All returned patterns have score >= confidence
    # No pattern with score >= confidence is excluded
```

#### P4: Diversity Preservation
```python
@given(patterns=lists(pattern_strategy()), top_k=integers(1, 10))
def test_diversity_not_collapsed(patterns, top_k):
    """Top-k doesn't collapse to near-duplicates"""
    # If 5 distinct pattern types exist
    # Top-5 shouldn't all be variants of one type
```

---

### 2. SLMRouter Properties (HIGH PRIORITY)

This is **cost + fallback control**. Without tests:
- May silently route expensive paths too often
- Or worse: degrade quality under budget pressure

**Required Properties:**

#### P1: Budget Respect
```python
@given(budget=floats(0, 100), task_complexity=floats(0, 1))
def test_never_exceed_budget(budget, task_complexity):
    """Router never exceeds budget constraint"""
    route = router.route(task, budget)
    assert route.estimated_cost <= budget
```

#### P2: Quality Degradation Bounds
```python
@given(budget=floats(0, 100))
def test_quality_degrades_gracefully(budget):
    """Lower budget → predictable quality tradeoff"""
    # Budget cut by 50% → quality drops by at most 30%
    # (Not 90% collapse)
```

---

### 3. Integration Test (MEDIUM, but important)

**One critical test:**

```python
def test_learning_loop_convergence():
    """Pattern used → success → score increases"""

    # 1. Start with random patterns
    initial_patterns = generate_random_patterns(10)

    # 2. Run 5 tasks, mark successes
    for task in tasks:
        pattern = retriever.get_best(task)
        result = execute(pattern, task)
        if result.success:
            feedback.record_success(pattern.id, task.id)

    # 3. Verify: successful patterns rank higher
    final_rankings = retriever.get_rankings()
    assert successful_patterns_moved_up(final_rankings)
```

---

## Implementation Order

1. **HybridRetriever P1-P4** (2-3 hours)
2. **SLMRouter P1-P2** (1 hour)
3. **Integration test** (1 hour)

**Total:** ~5 hours to bulletproof the foundation.

---

## Success Criteria

✅ All 6 properties pass with Hypothesis
✅ Integration test shows learning convergence
✅ No flaky failures over 100 runs

**Then and only then:** Phase 2 is safe.

---

## Why This Isn't Over-Engineering

Phase 1 built:
- ✅ Correct attribution
- ✅ Real signal
- ✅ Feedback loop

But without these tests, Phase 2's evolutionary pressure will **amplify any retrieval bias** into systemic drift.

This is the difference between:
- A system that learns
- A system that **provably** learns

---

**Next Action:** Implement HybridRetriever properties first.
