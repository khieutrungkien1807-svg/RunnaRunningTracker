"""
Integration Test: Learning Convergence

Validates that the pattern learning system (PatternExtractor + FailureMemory)
actually learns from feedback and converges to stable rankings.

This is a P0 BLOCKING test that proves the learning system works correctly
before Phase 2 evolution.

Task 3: Integration Test - Learning Convergence
Requirements: Phase 1 Final Safety
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import random
import string
import sys
import os

# Setup path to import from antigravity/core
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set dummy API key for testing
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key-for-testing")

from core.failure_memory import FailureMemory
from core.schemas import FailureSurface


class TestLearningConvergence:
    """Test that learning system converges properly"""
    
    def test_successful_patterns_rank_higher(self):
        """
        Subtask 3.2: Test learning loop
        
        Validates that successful patterns move up in rankings after feedback.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "memory.jsonl"
            memory = FailureMemory(storage_path)
            
            # Record 5 different failure patterns with distinct characteristics
            patterns = []
            error_types = [
                ("+ import module0", "NameError: name 'module0' is not defined"),
                ("+ if (data?.user) { }", "TypeError: Cannot read property 'name' of undefined"),
                ("+ if (useState) { }", "TypeError: useState is not a function"),
                ("+ result = [1, 2, 3", "SyntaxError: unmatched ']'"),
                ("+ def foo():\nreturn 42", "IndentationError: unexpected indent")
            ]
            
            for i, (patch, error) in enumerate(error_types):
                pattern, lesson = memory.record_failure(
                    failure_id=f"test-{i}",
                    patch_diff=patch,
                    error_text=error,
                    files_touched=[f"test{i}.py"],
                    session_id=f"session-{i}"
                )
                patterns.append(pattern)
            
            # Simulate feedback: pattern 0 is most helpful (80% success)
            # Pattern 1 is moderately helpful (50% success)
            # Pattern 2-4 are not helpful (20% success)
            
            # Pattern 0: 10 injections, 8 helped
            for _ in range(10):
                memory._store._increment_injection_count(patterns[0].signature)
            for _ in range(8):
                memory._store._increment_helped_count(patterns[0].signature)
            
            # Pattern 1: 10 injections, 5 helped
            for _ in range(10):
                memory._store._increment_injection_count(patterns[1].signature)
            for _ in range(5):
                memory._store._increment_helped_count(patterns[1].signature)
            
            # Pattern 2-4: 10 injections, 2 helped each
            for i in range(2, 5):
                for _ in range(10):
                    memory._store._increment_injection_count(patterns[i].signature)
                for _ in range(2):
                    memory._store._increment_helped_count(patterns[i].signature)
            
            # Boost confidence to pass retrieval filter
            for pattern in patterns:
                memory._store._by_signature[pattern.signature].pattern.confidence_score = 0.8
            
            # Retrieve lessons - should rank by effectiveness
            results = memory.retrieve_lessons(
                current_task="fix import error",
                current_error="NameError: name 'something' is not defined",
                top_k=5
            )
            
            # Verify we got results (at least the patterns that match)
            assert len(results) >= 1, "Should retrieve at least one pattern"
            
            # Get effectiveness scores
            effectiveness_map = {}
            for retrieved_pattern, _, score in results:
                entry = memory._store._by_signature[retrieved_pattern.signature]
                effectiveness_map[retrieved_pattern.signature] = entry.effectiveness
            
            # Verify patterns have correct effectiveness values
            assert effectiveness_map[patterns[0].signature] == 0.8, \
                f"Pattern 0 should have 0.8 effectiveness, got {effectiveness_map[patterns[0].signature]}"
            
            if patterns[1].signature in effectiveness_map:
                assert effectiveness_map[patterns[1].signature] == 0.5, \
                    f"Pattern 1 should have 0.5 effectiveness"
            
            # Verify high-effectiveness patterns rank higher than low-effectiveness ones
            if len(results) >= 2:
                # Get top 2 effectiveness values
                top_effectiveness = [effectiveness_map[p.signature] for p, _, _ in results[:2]]
                # First should be >= second
                assert top_effectiveness[0] >= top_effectiveness[1], \
                    f"Ranking incorrect: {top_effectiveness}"
            
            print("✅ Successful patterns rank higher after feedback")
            print(f"   Pattern 0 effectiveness: {effectiveness_map[patterns[0].signature]:.1%}")
            if patterns[1].signature in effectiveness_map:
                print(f"   Pattern 1 effectiveness: {effectiveness_map[patterns[1].signature]:.1%}")
    
    def test_convergence_within_20_iterations(self):
        """
        Subtask 3.3: Test convergence
        
        Validates that rankings stabilize within 20 iterations.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "memory.jsonl"
            memory = FailureMemory(storage_path)
            
            # Create 5 patterns with different true effectiveness rates
            # Pattern 0: 80% effective (best)
            # Pattern 1: 60% effective
            # Pattern 2: 40% effective
            # Pattern 3: 20% effective
            # Pattern 4: 10% effective (worst)
            true_effectiveness = [0.8, 0.6, 0.4, 0.2, 0.1]
            
            patterns = []
            for i in range(5):
                pattern, lesson = memory.record_failure(
                    failure_id=f"pattern-{i}",
                    patch_diff=f"+ fix_{i}()",
                    error_text=f"Error type {i}",
                    files_touched=[f"file{i}.py"],
                    session_id=f"session-{i}"
                )
                patterns.append(pattern)
                # Boost confidence to pass filter
                memory._store._by_signature[pattern.signature].pattern.confidence_score = 0.8
            
            # Track ranking changes over iterations
            ranking_history = []
            
            # Run 20 iterations of feedback
            for iteration in range(20):
                # Each iteration: inject all patterns and simulate success based on true effectiveness
                for i, pattern in enumerate(patterns):
                    memory._store._increment_injection_count(pattern.signature)
                    
                    # Simulate success with probability = true_effectiveness[i]
                    if random.random() < true_effectiveness[i]:
                        memory._store._increment_helped_count(pattern.signature)
                
                # Get current rankings
                results = memory.retrieve_lessons(
                    current_task="fix error",
                    current_error="some error occurred",
                    top_k=5
                )
                
                # Extract ranking (order of pattern signatures)
                current_ranking = [p.signature for p, _, _ in results]
                ranking_history.append(current_ranking)
            
            # Check convergence: last 5 rankings should be stable
            last_5_rankings = ranking_history[-5:]
            
            # Count how many times each pattern appears in each position
            position_stability = {}
            for pos in range(min(3, len(last_5_rankings[0]))):  # Check top 3 positions
                patterns_at_pos = [ranking[pos] for ranking in last_5_rankings if len(ranking) > pos]
                # Most common pattern at this position
                most_common = max(set(patterns_at_pos), key=patterns_at_pos.count)
                stability = patterns_at_pos.count(most_common) / len(patterns_at_pos)
                position_stability[pos] = stability
            
            # Verify stability: top 3 positions should be stable (>= 60% same pattern)
            for pos, stability in position_stability.items():
                assert stability >= 0.6, f"Position {pos} not stable: {stability:.1%}"
            
            # Verify best pattern (pattern 0) is in top 3
            final_ranking = ranking_history[-1]
            assert patterns[0].signature in final_ranking[:3], \
                f"Best pattern not in top 3: {final_ranking}"
            
            print("✅ System converges within 20 iterations")
            print(f"   Position stability: {[f'{s:.1%}' for s in position_stability.values()]}")
            print(f"   Final top 3: {[p[:8] for p in final_ranking[:3]]}")
    
    def test_no_silent_regression(self):
        """
        Subtask 3.3: Ensure no regression
        
        Validates that once a pattern is learned as effective, it doesn't
        silently regress to low ranking without new negative feedback.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "memory.jsonl"
            memory = FailureMemory(storage_path)
            
            # Create a highly effective pattern
            pattern, lesson = memory.record_failure(
                failure_id="test-001",
                patch_diff="+ import React",
                error_text="React is not defined",
                files_touched=["App.jsx"],
                session_id="session-001"
            )
            
            # Build up high effectiveness (90%)
            for _ in range(20):
                memory._store._increment_injection_count(pattern.signature)
            for _ in range(18):
                memory._store._increment_helped_count(pattern.signature)
            
            # Boost confidence
            memory._store._by_signature[pattern.signature].pattern.confidence_score = 0.9
            
            # Record initial effectiveness
            entry = memory._store._by_signature[pattern.signature]
            initial_effectiveness = entry.effectiveness
            assert initial_effectiveness == 0.9  # 18/20
            
            # Simulate 10 more iterations with NO new feedback
            # (pattern is not used, but effectiveness should not decay)
            for _ in range(10):
                # Just retrieve, don't update
                results = memory.retrieve_lessons(
                    current_task="fix import",
                    current_error="React is not defined",
                    top_k=3
                )
            
            # Verify effectiveness hasn't changed
            entry_after = memory._store._by_signature[pattern.signature]
            assert entry_after.effectiveness == initial_effectiveness, \
                "Effectiveness regressed without negative feedback"
            
            # Verify pattern still ranks high
            results = memory.retrieve_lessons(
                current_task="fix import",
                current_error="React is not defined",
                top_k=3
            )
            
            assert len(results) > 0
            top_pattern = results[0][0]
            assert top_pattern.signature == pattern.signature, \
                "Effective pattern no longer ranks first"
            
            print("✅ No silent regression detected")
            print(f"   Effectiveness maintained: {entry_after.effectiveness:.1%}")
    
    def test_learning_with_random_patterns(self):
        """
        Subtask 3.1 & 3.2: Setup test environment and test learning loop
        
        Validates learning with randomly generated patterns and feedback.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "memory.jsonl"
            memory = FailureMemory(storage_path)
            
            # Generate 10 random patterns
            patterns = []
            for i in range(10):
                # Random error types
                error_types = [
                    "NameError: name 'X' is not defined",
                    "TypeError: X is not a function",
                    "SyntaxError: unexpected token",
                    "ReferenceError: X is not defined",
                    "ImportError: cannot import X"
                ]
                
                error_text = random.choice(error_types).replace('X', f'var{i}')
                
                pattern, lesson = memory.record_failure(
                    failure_id=f"random-{i}",
                    patch_diff=f"+ {self._random_code()}",
                    error_text=error_text,
                    files_touched=[f"file{i}.py"],
                    session_id=f"session-{i}"
                )
                patterns.append(pattern)
                # Boost confidence
                memory._store._by_signature[pattern.signature].pattern.confidence_score = 0.8
            
            # Assign random true effectiveness to each pattern
            true_effectiveness = {
                p.signature: random.uniform(0.1, 0.9) for p in patterns
            }
            
            # Run 15 iterations of feedback
            for iteration in range(15):
                for pattern in patterns:
                    memory._store._increment_injection_count(pattern.signature)
                    
                    # Simulate success based on true effectiveness
                    if random.random() < true_effectiveness[pattern.signature]:
                        memory._store._increment_helped_count(pattern.signature)
            
            # Verify learned effectiveness correlates with true effectiveness
            learned_effectiveness = {}
            for pattern in patterns:
                entry = memory._store._by_signature[pattern.signature]
                learned_effectiveness[pattern.signature] = entry.effectiveness
            
            # Check correlation: patterns with high true effectiveness should have high learned effectiveness
            high_true = [sig for sig, eff in true_effectiveness.items() if eff > 0.7]
            low_true = [sig for sig, eff in true_effectiveness.items() if eff < 0.3]
            
            if high_true and low_true:
                avg_learned_high = sum(learned_effectiveness[sig] for sig in high_true) / len(high_true)
                avg_learned_low = sum(learned_effectiveness[sig] for sig in low_true) / len(low_true)
                
                # High true effectiveness should result in higher learned effectiveness
                assert avg_learned_high > avg_learned_low, \
                    f"Learning failed: high={avg_learned_high:.2f}, low={avg_learned_low:.2f}"
                
                print("✅ Learning with random patterns successful")
                print(f"   Avg learned effectiveness (high true): {avg_learned_high:.1%}")
                print(f"   Avg learned effectiveness (low true): {avg_learned_low:.1%}")
    
    def _random_code(self) -> str:
        """Generate random code snippet for testing"""
        templates = [
            "import {module}",
            "const {var} = {value}",
            "function {func}() {{ return {value}; }}",
            "if ({var}) {{ {action}(); }}",
            "{var}.{method}()"
        ]
        
        template = random.choice(templates)
        return template.format(
            module=''.join(random.choices(string.ascii_lowercase, k=5)),
            var=''.join(random.choices(string.ascii_lowercase, k=4)),
            value=random.randint(1, 100),
            func=''.join(random.choices(string.ascii_lowercase, k=6)),
            action=''.join(random.choices(string.ascii_lowercase, k=5)),
            method=''.join(random.choices(string.ascii_lowercase, k=4))
        )


class TestLearningSystemIntegration:
    """Test full integration of learning system components"""
    
    def test_pattern_extractor_integration(self):
        """
        Validates that PatternExtractor correctly identifies patterns
        that can be learned from.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "memory.jsonl"
            memory = FailureMemory(storage_path)
            
            # Test various error types
            test_cases = [
                {
                    "patch": "+ foo()",
                    "error": "NameError: name 'foo' is not defined",
                    "expected_type": "import_missing"
                },
                {
                    "patch": "+ if (data?.user) { }",
                    "error": "TypeError: Cannot read property 'name' of undefined",
                    "expected_type": "fix_symptom_not_root"
                },
                {
                    "patch": "+ if (useState) { }",
                    "error": "TypeError: useState is not a function",
                    "expected_type": "wrong_fix_strategy"
                }
            ]
            
            for i, test_case in enumerate(test_cases):
                pattern, lesson = memory.record_failure(
                    failure_id=f"test-{i}",
                    patch_diff=test_case["patch"],
                    error_text=test_case["error"],
                    files_touched=["test.py"],
                    session_id=f"session-{i}"
                )
                
                assert pattern.pattern_type == test_case["expected_type"], \
                    f"Expected {test_case['expected_type']}, got {pattern.pattern_type}"
                
                assert pattern.confidence_score > 0.6, \
                    f"Pattern confidence too low: {pattern.confidence_score}"
            
            print("✅ PatternExtractor integration verified")
            print(f"   Tested {len(test_cases)} pattern types")
    
    def test_retrieval_ranking_correctness(self):
        """
        Validates that retrieval correctly ranks patterns by effectiveness.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "memory.jsonl"
            memory = FailureMemory(storage_path)
            
            # Create 3 patterns with distinct characteristics and known effectiveness
            patterns = []
            effectiveness_values = [0.9, 0.5, 0.1]  # High, medium, low
            
            test_cases = [
                ("+ import React", "React is not defined"),
                ("+ if (data?.user) { }", "Cannot read property 'name' of undefined"),
                ("+ if (useState) { }", "useState is not a function")
            ]
            
            for i, (target_eff, (patch, error)) in enumerate(zip(effectiveness_values, test_cases)):
                pattern, lesson = memory.record_failure(
                    failure_id=f"test-{i}",
                    patch_diff=patch,
                    error_text=error,
                    files_touched=[f"test{i}.py"],
                    session_id=f"session-{i}"
                )
                patterns.append(pattern)
                
                # Set effectiveness to target value
                injections = 10
                helps = int(injections * target_eff)
                
                for _ in range(injections):
                    memory._store._increment_injection_count(pattern.signature)
                for _ in range(helps):
                    memory._store._increment_helped_count(pattern.signature)
                
                # Boost confidence
                memory._store._by_signature[pattern.signature].pattern.confidence_score = 0.8
            
            # Retrieve and verify ranking
            results = memory.retrieve_lessons(
                current_task="fix import",
                current_error="something is not defined",
                top_k=3
            )
            
            assert len(results) >= 1, "Should retrieve at least one pattern"
            
            # Extract effectiveness scores from results
            result_effectiveness = []
            for retrieved_pattern, _, score in results:
                entry = memory._store._by_signature[retrieved_pattern.signature]
                result_effectiveness.append(entry.effectiveness)
            
            # Verify descending order (highest effectiveness first)
            for i in range(len(result_effectiveness) - 1):
                assert result_effectiveness[i] >= result_effectiveness[i + 1], \
                    f"Ranking incorrect: {result_effectiveness}"
            
            print("✅ Retrieval ranking correctness verified")
            print(f"   Ranking: {[f'{e:.1%}' for e in result_effectiveness]}")


if __name__ == "__main__":
    # Run tests
    test_suite = TestLearningConvergence()
    
    print("\n=== Testing Learning Convergence ===\n")
    
    print("Test 1: Successful patterns rank higher")
    test_suite.test_successful_patterns_rank_higher()
    
    print("\nTest 2: Convergence within 20 iterations")
    test_suite.test_convergence_within_20_iterations()
    
    print("\nTest 3: No silent regression")
    test_suite.test_no_silent_regression()
    
    print("\nTest 4: Learning with random patterns")
    test_suite.test_learning_with_random_patterns()
    
    integration_suite = TestLearningSystemIntegration()
    
    print("\nTest 5: PatternExtractor integration")
    integration_suite.test_pattern_extractor_integration()
    
    print("\nTest 6: Retrieval ranking correctness")
    integration_suite.test_retrieval_ranking_correctness()
    
    print("\n✅ All learning convergence tests passed!")
    print("\n=== Summary ===")
    print("✅ Successful patterns rank higher after feedback")
    print("✅ System converges within 20 iterations")
    print("✅ No silent regression detected")
    print("✅ Learning system fully integrated and functional")
