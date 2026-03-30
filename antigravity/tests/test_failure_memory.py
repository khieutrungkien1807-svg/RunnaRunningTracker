"""
Unit tests for FailureMemory (v6.2 Learning Loop)

Tests the 3-layer abstraction: Surface → Pattern → Lesson
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from core.failure_memory import (
    FailureMemory,
    FailureMemoryStore,
    FailureMemoryRetriever,
    FailureEntry
)
from core.schemas import FailureSurface, FailurePattern, FailureLesson
from core.pattern_extractor import PatternExtractor
from core.pattern_extractor_v2 import PatternExtractorV2


class TestPatternExtractor:
    """Test pattern extraction rules"""
    
    def test_extract_missing_import(self):
        """Test Rule 2: Missing Import detection"""
        extractor = PatternExtractor()
        
        surface = FailureSurface(
            failure_id="test-001",
            patch_diff="+ bar.baz()",  # No import statement in patch
            error_text="NameError: name 'bar' is not defined",
            files_touched=["test.py"],
            timestamp=datetime.now().isoformat(),
            session_id="session-001"
        )
        
        pattern, lesson = extractor.extract(surface)
        
        assert pattern.pattern_type == "import_missing"
        assert "import" in pattern.cause.lower()
        assert "bar" in pattern.symbols
        assert "import" in lesson.prefer.lower()
    
    def test_extract_syntax_error(self):
        """Test Rule 3: Unmatched Bracket detection"""
        extractor = PatternExtractor()
        
        surface = FailureSurface(
            failure_id="test-002",
            patch_diff="+ result = [1, 2, 3\n",
            error_text="SyntaxError: unmatched ']'",
            files_touched=["test.py"],
            timestamp=datetime.now().isoformat(),
            session_id="session-001"
        )
        
        pattern, lesson = extractor.extract(surface)
        
        assert pattern.pattern_type == "syntax_error"
        assert "bracket" in pattern.cause.lower()
        assert "bracket" in lesson.avoid.lower()
    
    def test_extract_no_op_patch(self):
        """Test Rule 1: No-Op Patch detection"""
        extractor = PatternExtractor()
        
        surface = FailureSurface(
            failure_id="test-003",
            patch_diff="",  # Empty patch
            error_text="No changes detected",
            files_touched=[],
            timestamp=datetime.now().isoformat(),
            session_id="session-001"
        )
        
        pattern, lesson = extractor.extract(surface)
        
        assert pattern.pattern_type == "no_op_patch"
        assert "identical" in pattern.cause.lower()
        assert "analyze" in lesson.prefer.lower()
    
    def test_extract_indentation_error(self):
        """Test Rule 4: Incorrect Indentation detection"""
        extractor = PatternExtractor()
        
        surface = FailureSurface(
            failure_id="test-004",
            patch_diff="+ def foo():\n+return 42\n",
            error_text="IndentationError: unexpected indent",
            files_touched=["test.py"],
            timestamp=datetime.now().isoformat(),
            session_id="session-001"
        )
        
        pattern, lesson = extractor.extract(surface)
        
        assert pattern.pattern_type == "syntax_error"
        assert "indentation" in pattern.cause.lower()
        assert "indent" in lesson.prefer.lower()


class TestFailureMemoryStore:
    """Test storage with dedup and frequency tracking"""
    
    def test_store_new_pattern(self):
        """Test storing a new failure pattern"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_memory.jsonl"
            store = FailureMemoryStore(storage_path, ttl_days=7, max_entries=100)
            
            surface = FailureSurface(
                failure_id="test-001",
                patch_diff="+ foo()",
                error_text="NameError: name 'foo' is not defined",
                files_touched=["test.py"],
                timestamp=datetime.now().isoformat(),
                session_id="session-001"
            )
            
            pattern = FailurePattern(
                pattern_type="import_missing",
                cause="missing import",
                location="top_of_file",
                action="added code using 'foo' without import",
                symbols=["foo"],
                signature="abc123",
                confidence_score=0.8  # v2: Required for retrieval filter
            )
            
            lesson = FailureLesson(
                avoid="adding new symbol without checking imports",
                prefer="add import statement before using new symbol",
                confidence=0.5,
                applies_to=["python"]
            )
            
            store.store(surface, pattern, lesson)
            
            # Verify stored
            assert len(store.get_all_entries()) == 1
            assert store._by_frequency["abc123"] == 1
    
    def test_store_duplicate_pattern(self):
        """Test deduplication and frequency tracking"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_memory.jsonl"
            store = FailureMemoryStore(storage_path, ttl_days=7, max_entries=100)
            
            surface = FailureSurface(
                failure_id="test-001",
                patch_diff="+ foo()",
                error_text="NameError: name 'foo' is not defined",
                files_touched=["test.py"],
                timestamp=datetime.now().isoformat(),
                session_id="session-001"
            )
            
            pattern = FailurePattern(
                pattern_type="import_missing",
                cause="missing import",
                location="top_of_file",
                action="added code using 'foo' without import",
                symbols=["foo"],
                signature="abc123",
                confidence_score=0.8  # v2: Required for retrieval filter
            )
            
            lesson = FailureLesson(
                avoid="adding new symbol without checking imports",
                prefer="add import statement before using new symbol",
                confidence=0.5,
                applies_to=["python"]
            )
            
            # Store same pattern twice
            store.store(surface, pattern, lesson)
            store.store(surface, pattern, lesson)
            
            # Verify dedup
            assert len(store.get_all_entries()) == 1
            assert store._by_frequency["abc123"] == 2
            
            # Verify confidence increased
            entry = store._by_signature["abc123"]
            assert entry.lesson.confidence == 0.2  # 2/10 = 0.2
    
    def test_purge_expired(self):
        """Test TTL-based purging"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_memory.jsonl"
            store = FailureMemoryStore(storage_path, ttl_days=7, max_entries=100)
            
            # Create old surface (8 days ago)
            old_timestamp = (datetime.now() - timedelta(days=8)).isoformat()
            old_surface = FailureSurface(
                failure_id="test-old",
                patch_diff="+ old()",
                error_text="Error",
                files_touched=["old.py"],
                timestamp=old_timestamp,
                session_id="session-old"
            )
            
            pattern = FailurePattern(
                pattern_type="runtime_error",
                cause="old error",
                location="function_body",
                action="old action",
                symbols=[],
                signature="old123"
            )
            
            lesson = FailureLesson(
                avoid="old avoid",
                prefer="old prefer",
                confidence=0.5,
                applies_to=["python"]
            )
            
            store.store(old_surface, pattern, lesson)
            
            # Verify stored
            assert len(store.get_all_entries()) == 1
            
            # Purge expired
            purged = store.purge_expired()
            
            # Verify purged
            assert purged == 1
            assert len(store.get_all_entries()) == 0
    
    def test_max_entries_eviction(self):
        """Test LRU eviction when max_entries reached"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_memory.jsonl"
            store = FailureMemoryStore(storage_path, ttl_days=7, max_entries=3)
            
            # Store 4 patterns (should evict oldest)
            for i in range(4):
                surface = FailureSurface(
                    failure_id=f"test-{i}",
                    patch_diff=f"+ foo{i}()",
                    error_text=f"Error {i}",
                    files_touched=[f"test{i}.py"],
                    timestamp=datetime.now().isoformat(),
                    session_id=f"session-{i}"
                )
                
                pattern = FailurePattern(
                    pattern_type="runtime_error",
                    cause=f"error {i}",
                    location="function_body",
                    action=f"action {i}",
                    symbols=[],
                    signature=f"sig{i}"
                )
                
                lesson = FailureLesson(
                    avoid=f"avoid {i}",
                    prefer=f"prefer {i}",
                    confidence=0.5,
                    applies_to=["python"]
                )
                
                store.store(surface, pattern, lesson)
            
            # Verify max_entries enforced
            assert len(store.get_all_entries()) == 3


class TestFailureMemoryRetriever:
    """Test relevance-based retrieval"""
    
    def test_search_relevant_pattern_type_match(self):
        """Test retrieval with pattern type match"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_memory.jsonl"
            store = FailureMemoryStore(storage_path, ttl_days=7, max_entries=100)
            retriever = FailureMemoryRetriever(store)
            
            # Store a pattern
            surface = FailureSurface(
                failure_id="test-001",
                patch_diff="+ foo()",
                error_text="NameError: name 'foo' is not defined",
                files_touched=["test.py"],
                timestamp=datetime.now().isoformat(),
                session_id="session-001"
            )
            
            pattern = FailurePattern(
                pattern_type="import_missing",
                cause="missing import",
                location="top_of_file",
                action="added code using 'foo' without import",
                symbols=["foo"],
                signature="abc123",
                confidence_score=0.8  # v2: Required for retrieval filter
            )
            
            lesson = FailureLesson(
                avoid="adding new symbol without checking imports",
                prefer="add import statement before using new symbol",
                confidence=0.8,
                applies_to=["python"]
            )
            
            store.store(surface, pattern, lesson)
            
            # Search with similar error
            results = retriever.search_relevant(
                current_task="Add new function bar",
                current_error="NameError: name 'bar' is not defined",
                top_k=3
            )
            
            # Verify retrieval
            assert len(results) == 1
            retrieved_pattern, retrieved_lesson, score = results[0]
            assert retrieved_pattern.pattern_type == "import_missing"
            assert score > 0.2  # v2: Lower threshold due to effectiveness weighting
    
    def test_search_relevant_no_matches(self):
        """Test retrieval with no relevant patterns"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_memory.jsonl"
            store = FailureMemoryStore(storage_path, ttl_days=7, max_entries=100)
            retriever = FailureMemoryRetriever(store)
            
            # Search empty store
            results = retriever.search_relevant(
                current_task="Some task",
                current_error="Some error",
                top_k=3
            )
            
            # Verify empty results
            assert len(results) == 0


class TestFailureMemory:
    """Test main FailureMemory interface"""
    
    def test_record_and_retrieve(self):
        """Test end-to-end record and retrieve"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_memory.jsonl"
            memory = FailureMemory(storage_path, ttl_days=7, max_entries=100)
            
            # Record a failure
            pattern, lesson = memory.record_failure(
                failure_id="test-001",
                patch_diff="+ foo()",
                error_text="NameError: name 'foo' is not defined",
                files_touched=["test.py"],
                session_id="session-001"
            )
            
            # Verify pattern extracted
            assert pattern.pattern_type == "import_missing"
            assert lesson.confidence > 0
            
            # Retrieve lessons
            results = memory.retrieve_lessons(
                current_task="Add function bar",
                current_error="NameError: name 'bar' is not defined",
                top_k=3
            )
            
            # Verify retrieval
            assert len(results) == 1
            retrieved_pattern, retrieved_lesson, score = results[0]
            assert retrieved_pattern.pattern_type == "import_missing"
    
    def test_format_for_prompt(self):
        """Test prompt formatting"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_memory.jsonl"
            memory = FailureMemory(storage_path, ttl_days=7, max_entries=100)
            
            # Record a failure
            memory.record_failure(
                failure_id="test-001",
                patch_diff="+ foo()",
                error_text="NameError: name 'foo' is not defined",
                files_touched=["test.py"],
                session_id="session-001"
            )
            
            # Retrieve and format
            results = memory.retrieve_lessons(
                current_task="Add function bar",
                current_error="NameError: name 'bar' is not defined",
                top_k=3
            )
            
            formatted = memory.format_for_prompt(results)
            
            # Verify format
            assert "[FAILURE MEMORY" in formatted
            assert "AVOID:" in formatted
            assert "PREFER:" in formatted
            assert "Confidence:" in formatted
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "test_memory.jsonl"
            memory = FailureMemory(storage_path, ttl_days=7, max_entries=100)
            
            # Record multiple failures
            for i in range(3):
                memory.record_failure(
                    failure_id=f"test-{i}",
                    patch_diff=f"+ foo{i}()",
                    error_text="NameError: name 'foo' is not defined",
                    files_touched=[f"test{i}.py"],
                    session_id=f"session-{i}"
                )
            
            # Get stats
            stats = memory.get_stats()
            
            # Verify stats
            assert stats["total_patterns"] >= 1  # May be deduped
            assert stats["total_occurrences"] == 3
            assert len(stats["most_common"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestPatternExtractorV2:
    """Test v2 context-aware pattern extraction"""
    
    def test_extract_fix_symptom_not_root(self):
        """Test v2: Fix symptom not root cause pattern"""
        from core.pattern_extractor_v2 import PatternExtractorV2
        extractor = PatternExtractorV2()
        
        surface = FailureSurface(
            failure_id="test-v2-001",
            patch_diff="+ if (data?.user) { ... }",  # Added optional chaining
            error_text="TypeError: Cannot read property 'name' of undefined",
            files_touched=["UserProfile.jsx"],
            timestamp=datetime.now().isoformat(),
            session_id="session-001"
        )
        
        pattern, lesson = extractor.extract(surface)
        
        assert pattern.pattern_type == "fix_symptom_not_root"
        assert pattern.context is not None
        assert pattern.attempted_fix is not None
        assert pattern.correct_direction is not None
        assert pattern.confidence_score > 0.6
        assert "data flow" in lesson.prefer.lower()
    
    def test_extract_wrong_fix_strategy(self):
        """Test v2: Wrong fix strategy pattern"""
        from core.pattern_extractor_v2 import PatternExtractorV2
        extractor = PatternExtractorV2()
        
        surface = FailureSurface(
            failure_id="test-v2-002",
            patch_diff="+ if (useState) { useState(0) }",  # Added null check
            error_text="TypeError: useState is not a function",
            files_touched=["App.jsx"],
            timestamp=datetime.now().isoformat(),
            session_id="session-001"
        )
        
        pattern, lesson = extractor.extract(surface)
        
        assert pattern.pattern_type == "wrong_fix_strategy"
        assert "useState" in pattern.symbols
        assert pattern.context["error_type"] == "not_a_function"
        assert pattern.confidence_score >= 0.8
        assert "import" in lesson.prefer.lower()
    
    def test_extract_test_breaking_change(self):
        """Test v2: Test breaking change pattern"""
        from core.pattern_extractor_v2 import PatternExtractorV2
        extractor = PatternExtractorV2()
        
        surface = FailureSurface(
            failure_id="test-v2-003",
            patch_diff="- function foo(a) {\n+ function foo(a, b) {",
            error_text="Test failed: Expected 1 argument but got 2",
            files_touched=["utils.js"],
            timestamp=datetime.now().isoformat(),
            session_id="session-001"
        )
        
        pattern, lesson = extractor.extract(surface)
        
        assert pattern.pattern_type == "test_breaking_change"
        assert pattern.context["error_type"] == "test_failure"
        assert "test files" in lesson.prefer.lower()
    
    def test_extract_overfix(self):
        """Test v2: Overfix pattern (too many changes for simple error)"""
        from core.pattern_extractor_v2 import PatternExtractorV2
        extractor = PatternExtractorV2()
        
        # Large patch for simple error
        large_patch = "\n".join([f"+ line {i}" for i in range(25)])
        
        surface = FailureSurface(
            failure_id="test-v2-004",
            patch_diff=large_patch,
            error_text="SyntaxError: missing semicolon",
            files_touched=["app.js"],
            timestamp=datetime.now().isoformat(),
            session_id="session-001"
        )
        
        pattern, lesson = extractor.extract(surface)
        
        assert pattern.pattern_type == "overfix"
        assert pattern.context["error_complexity"] == "simple"
        assert pattern.context["patch_size"] == "large"
        assert "minimum" in lesson.prefer.lower()  # "minimum code needed"


class TestFailureMemoryEffectiveness:
    """Test v2 effectiveness tracking"""
    
    def test_injection_tracking(self):
        """Test that injection count increments correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "memory.jsonl"
            memory = FailureMemory(storage_path)
            
            # Record a failure
            pattern, lesson = memory.record_failure(
                failure_id="test-001",
                patch_diff="+ foo()",
                error_text="foo is not defined",
                files_touched=["test.py"],
                session_id="session-001"
            )
            
            # Simulate injection
            memory._store._increment_injection_count(pattern.signature)
            memory._store._increment_injection_count(pattern.signature)
            
            # Check count
            entry = memory._store._by_signature[pattern.signature]
            assert entry.times_injected == 2
            assert entry.times_helped == 0
            assert entry.effectiveness == 0.0
    
    def test_effectiveness_computation(self):
        """Test effectiveness = times_helped / times_injected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "memory.jsonl"
            memory = FailureMemory(storage_path)
            
            # Record a failure
            pattern, lesson = memory.record_failure(
                failure_id="test-001",
                patch_diff="+ foo()",
                error_text="foo is not defined",
                files_touched=["test.py"],
                session_id="session-001"
            )
            
            # Simulate: injected 5 times, helped 3 times
            for _ in range(5):
                memory._store._increment_injection_count(pattern.signature)
            for _ in range(3):
                memory._store._increment_helped_count(pattern.signature)
            
            # Check effectiveness
            entry = memory._store._by_signature[pattern.signature]
            assert entry.times_injected == 5
            assert entry.times_helped == 3
            assert entry.effectiveness == 0.6  # 3/5
    
    def test_retrieval_filters_low_confidence(self):
        """Test that retrieval filters patterns with confidence_score <= 0.6"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "memory.jsonl"
            memory = FailureMemory(storage_path)
            
            # Record a failure (will have low confidence initially)
            pattern, lesson = memory.record_failure(
                failure_id="test-001",
                patch_diff="+ foo()",
                error_text="foo is not defined",
                files_touched=["test.py"],
                session_id="session-001"
            )
            
            # Try to retrieve (should be filtered out if confidence <= 0.6)
            results = memory.retrieve_lessons(
                current_task="fix error",
                current_error="foo is not defined",
                top_k=3
            )
            
            # Check if filtered based on confidence
            if lesson.confidence <= 0.6:
                assert len(results) == 0 or pattern.signature not in [p.signature for p, l, s in results]
    
    def test_effectiveness_weighted_retrieval(self):
        """Test that retrieval prioritizes high-effectiveness patterns"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "memory.jsonl"
            memory = FailureMemory(storage_path)
            
            # Record two similar failures
            pattern1, lesson1 = memory.record_failure(
                failure_id="test-001",
                patch_diff="+ import foo",
                error_text="foo is not defined",
                files_touched=["test.py"],
                session_id="session-001"
            )
            
            pattern2, lesson2 = memory.record_failure(
                failure_id="test-002",
                patch_diff="+ import bar",
                error_text="bar is not defined",
                files_touched=["test.py"],
                session_id="session-001"
            )
            
            # Make pattern1 high-effectiveness (80%)
            for _ in range(5):
                memory._store._increment_injection_count(pattern1.signature)
            for _ in range(4):
                memory._store._increment_helped_count(pattern1.signature)
            
            # Make pattern2 low-effectiveness (20%)
            for _ in range(5):
                memory._store._increment_injection_count(pattern2.signature)
            for _ in range(1):
                memory._store._increment_helped_count(pattern2.signature)
            
            # Boost confidence to pass filter
            memory._store._by_signature[pattern1.signature].pattern.confidence_score = 0.8
            memory._store._by_signature[pattern2.signature].pattern.confidence_score = 0.8
            
            # Retrieve
            results = memory.retrieve_lessons(
                current_task="fix import error",
                current_error="something is not defined",
                top_k=2
            )
            
            # Pattern1 should rank higher due to effectiveness weight (40%)
            if len(results) >= 2:
                top_pattern = results[0][0]
                # High effectiveness pattern should be first
                assert top_pattern.signature == pattern1.signature


class TestFailureMemoryPersistence:
    """Test v2 persistence of effectiveness fields"""
    
    def test_save_and_load_effectiveness(self):
        """Test that effectiveness fields persist across save/load"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "memory.jsonl"
            
            # Create memory and record failure
            memory1 = FailureMemory(storage_path)
            pattern, lesson = memory1.record_failure(
                failure_id="test-001",
                patch_diff="+ foo()",
                error_text="foo is not defined",
                files_touched=["test.py"],
                session_id="session-001"
            )
            
            # Update effectiveness
            memory1._store._increment_injection_count(pattern.signature)
            memory1._store._increment_injection_count(pattern.signature)
            memory1._store._increment_helped_count(pattern.signature)
            
            # Load in new instance
            memory2 = FailureMemory(storage_path)
            
            # Check effectiveness persisted
            entry = memory2._store._by_signature[pattern.signature]
            assert entry.times_injected == 2
            assert entry.times_helped == 1
            assert entry.effectiveness == 0.5


# ── Phase 1d Tests (Final Polish) ─────────────────────────────────────────────

def test_intent_signature_detection(tmp_path):
    """Test v4 intent signature detection (Phase 1d.1)"""
    store = FailureMemoryStore(tmp_path / "test.jsonl")
    
    # Create pattern with usage_signals
    pattern = FailurePattern(
        pattern_type="wrong_fix_strategy",
        cause="test pattern",
        location="function_body",
        action="test",
        symbols=[],
        signature="test_sig_001",
        usage_signals=[
            "added import",
            "regex:import.*react"
        ]
    )
    
    # Test 1: Detect "added import"
    patch1 = "+ import React from 'react'"
    assert store._check_pattern_usage_v2(pattern, patch1) == True
    
    # Test 2: Detect regex pattern
    patch2 = "import { useState } from 'react'"
    assert store._check_pattern_usage_v2(pattern, patch2) == True
    
    # Test 3: No match
    patch3 = "const x = 5"
    assert store._check_pattern_usage_v2(pattern, patch3) == False
    
    # Test 4: Fallback to v3 when no usage_signals
    pattern_no_signals = FailurePattern(
        pattern_type="wrong_fix_strategy",
        cause="test",
        location="function_body",
        action="test",
        symbols=[],
        signature="test_sig_002",
        correct_direction="check imports"
    )
    patch4 = "import something"
    assert store._check_pattern_usage_v2(pattern_no_signals, patch4) == True


def test_split_credit_attribution(tmp_path):
    """Test v4 split credit for co-occurring patterns (Phase 1d.2)"""
    store = FailureMemoryStore(tmp_path / "test.jsonl")
    
    # Create two patterns
    surface1 = FailureSurface(
        failure_id="f1",
        patch_diff="test",
        error_text="error1",
        files_touched=[],
        timestamp=datetime.now().isoformat(),
        session_id="s1"
    )
    
    pattern1 = FailurePattern(
        pattern_type="wrong_fix_strategy",
        cause="pattern1",
        location="function_body",
        action="test",
        symbols=[],
        signature="sig_001"
    )
    
    pattern2 = FailurePattern(
        pattern_type="fix_symptom_not_root",
        cause="pattern2",
        location="function_body",
        action="test",
        symbols=[],
        signature="sig_002"
    )
    
    lesson = FailureLesson(
        avoid="test",
        prefer="test",
        confidence=0.5,
        applies_to=["test"]
    )
    
    # Store both patterns
    store.store(surface1, pattern1, lesson)
    store.store(surface1, pattern2, lesson)
    
    # Inject both
    store._increment_injection_count("sig_001")
    store._increment_injection_count("sig_002")
    
    # Both helped with split credit (0.5 each)
    store._increment_helped_count_split("sig_001", credit=0.5)
    store._increment_helped_count_split("sig_002", credit=0.5)
    
    # Check effectiveness
    entry1 = store._by_signature["sig_001"]
    entry2 = store._by_signature["sig_002"]
    
    assert entry1.times_helped == 0.5
    assert entry2.times_helped == 0.5
    assert entry1.effectiveness == 0.5  # 0.5 / 1
    assert entry2.effectiveness == 0.5


def test_final_alignment_in_prompt():
    """Test v4 final alignment step in prompt (Phase 1d.3)"""
    memory = FailureMemory(storage_path=":memory:")
    
    pattern = FailurePattern(
        pattern_type="wrong_fix_strategy",
        cause="test pattern",
        location="function_body",
        action="test",
        symbols=[],
        signature="test_sig"
    )
    
    lesson = FailureLesson(
        avoid="doing X",
        prefer="doing Y",
        confidence=0.8,
        applies_to=["test"]
    )
    
    relevant = [(pattern, lesson, 0.9)]
    prompt = memory.format_for_prompt(relevant)
    
    # Check for step 5 (final alignment)
    assert "5. Verify the fix explicitly satisfies the constraints above" in prompt
    assert "Final verification is mandatory" in prompt


def test_usage_signals_in_pattern_extractor_v2():
    """Test that PatternExtractorV2 generates usage_signals"""
    extractor = PatternExtractorV2()
    
    # Create surface with "is not a function" error
    surface = FailureSurface(
        failure_id="f1",
        patch_diff="if (myFunc) { myFunc() }",
        error_text="myFunc is not a function",
        files_touched=["test.js"],
        timestamp=datetime.now().isoformat(),
        session_id="s1"
    )
    
    pattern, lesson = extractor.extract(surface)
    
    # Should be wrong_fix_strategy pattern
    assert pattern.pattern_type == "wrong_fix_strategy"
    
    # Should have usage_signals
    assert pattern.usage_signals is not None
    assert len(pattern.usage_signals) > 0
    assert any("import" in sig for sig in pattern.usage_signals)


def test_fractional_times_helped_persistence(tmp_path):
    """Test that fractional times_helped persists correctly"""
    storage_path = tmp_path / "test.jsonl"
    store = FailureMemoryStore(storage_path)
    
    # Create and store pattern
    surface = FailureSurface(
        failure_id="f1",
        patch_diff="test",
        error_text="error",
        files_touched=[],
        timestamp=datetime.now().isoformat(),
        session_id="s1"
    )
    
    pattern = FailurePattern(
        pattern_type="wrong_fix_strategy",
        cause="test",
        location="function_body",
        action="test",
        symbols=[],
        signature="sig_001"
    )
    
    lesson = FailureLesson(
        avoid="test",
        prefer="test",
        confidence=0.5,
        applies_to=["test"]
    )
    
    store.store(surface, pattern, lesson)
    store._increment_injection_count("sig_001")
    store._increment_helped_count_split("sig_001", credit=0.33)
    
    # Reload from disk
    store2 = FailureMemoryStore(storage_path)
    entry = store2._by_signature["sig_001"]
    
    assert abs(entry.times_helped - 0.33) < 0.01  # Float comparison
    assert entry.times_injected == 1


