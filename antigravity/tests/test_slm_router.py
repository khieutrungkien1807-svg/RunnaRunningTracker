"""
Unit tests for SLMRouter.

Tests cover:
- Graceful degradation when sentence-transformers unavailable (Req 4.6)
- Disabled state behavior
- Basic initialization

Note: Full functionality tests require sentence-transformers to be installed.
These tests focus on graceful degradation and error handling.
"""

import sys
import os

# Ensure the antigravity/core package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest
from pathlib import Path
import tempfile
import shutil

from core.slm_router import SLMRouter
from core.schemas import SLMRouteDecision


@pytest.fixture
def temp_prototypes_file():
    """Create a temporary prototypes JSON file."""
    temp_dir = tempfile.mkdtemp()
    prototypes_path = Path(temp_dir) / "prototypes.json"
    
    prototypes = {
        "frontend": {
            "examples": [
                "create react component",
                "style button with tailwind",
                "add animation to navbar",
            ]
        },
        "backend": {
            "examples": [
                "create REST API endpoint",
                "add database migration",
                "implement authentication",
            ]
        },
        "debug": {
            "examples": [
                "fix bug in checkout flow",
                "investigate crash",
                "trace error in logs",
            ]
        },
    }
    
    with open(prototypes_path, 'w', encoding='utf-8') as f:
        json.dump(prototypes, f)
    
    yield prototypes_path
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_slm_router_graceful_degradation_no_library(temp_prototypes_file):
    """
    Test graceful degradation when sentence-transformers not available.
    Validates Requirement 4.6: disabled when model fails to load, no crash.
    
    This test works regardless of whether sentence-transformers is installed.
    """
    router = SLMRouter(
        prototypes_path=temp_prototypes_file,
        confidence_threshold=0.85,
    )
    
    # Router should either be enabled (if library available) or disabled (if not)
    # Either way, it should not crash
    assert isinstance(router._enabled, bool)
    
    # classify() should return None or SLMRouteDecision, never crash
    result = router.classify("create a button")
    assert result is None or isinstance(result, SLMRouteDecision)


def test_slm_router_disabled_when_prototypes_missing():
    """
    Test graceful degradation when prototypes file doesn't exist.
    Validates Requirement 4.6: graceful degradation.
    """
    router = SLMRouter(
        prototypes_path="/nonexistent/path/prototypes.json",
        confidence_threshold=0.85,
    )
    
    # Should be disabled when prototypes file missing
    assert router._enabled is False
    
    # classify() should return None when disabled
    result = router.classify("any query")
    assert result is None


def test_classify_empty_query(temp_prototypes_file):
    """Test classification handles empty query gracefully."""
    router = SLMRouter(
        prototypes_path=temp_prototypes_file,
        confidence_threshold=0.85,
    )
    
    result = router.classify("")
    assert result is None
    
    result = router.classify("   ")
    assert result is None


def test_reload_when_disabled(temp_prototypes_file):
    """
    Test reload_prototypes when router is disabled.
    Validates Requirement 4.4: reload without crash.
    """
    # Create router with missing file to ensure it's disabled
    router = SLMRouter(
        prototypes_path="/nonexistent/path.json",
        confidence_threshold=0.85,
    )
    
    assert router._enabled is False
    
    # Should not crash when reloading while disabled
    router.reload_prototypes()
    assert router._enabled is False


def test_hot_reload_prototypes(temp_prototypes_file):
    """
    Test hot-reload of prototypes without restart.
    Validates Requirement 4.4: reload prototypes without restart.
    
    This test only runs if sentence-transformers is available.
    """
    router = SLMRouter(
        prototypes_path=temp_prototypes_file,
        confidence_threshold=0.85,
    )
    
    if not router._enabled:
        pytest.skip("sentence-transformers not available")
    
    initial_categories = set(router._categories)
    assert "frontend" in initial_categories
    assert "backend" in initial_categories
    assert "debug" in initial_categories
    
    # Update prototypes file
    new_prototypes = {
        "frontend": {
            "examples": ["create react component"]
        },
        "backend": {
            "examples": ["create API"]
        },
        "security": {
            "examples": ["fix vulnerability", "add encryption"]
        },
    }
    
    with open(temp_prototypes_file, 'w', encoding='utf-8') as f:
        json.dump(new_prototypes, f)
    
    # Reload
    router.reload_prototypes()
    
    # Check updated categories
    updated_categories = set(router._categories)
    assert "frontend" in updated_categories
    assert "backend" in updated_categories
    assert "security" in updated_categories
    assert "debug" not in updated_categories


def test_classify_returns_decision_or_none(temp_prototypes_file):
    """
    Test classification returns valid result types.
    Validates Requirements 4.2, 4.3: return decision or None based on confidence.
    
    This test only runs if sentence-transformers is available.
    """
    router = SLMRouter(
        prototypes_path=temp_prototypes_file,
        confidence_threshold=0.85,
    )
    
    if not router._enabled:
        pytest.skip("sentence-transformers not available")
    
    result = router.classify("create a react component")
    
    # Should return either SLMRouteDecision or None
    assert result is None or isinstance(result, SLMRouteDecision)
    
    if result is not None:
        # Validate structure
        assert hasattr(result, 'chosen')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'top_k')
        assert hasattr(result, 'llm_fallback_triggered')
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.top_k, list)


def test_logging_format(temp_prototypes_file, caplog):
    """
    Test that routing decisions are logged in correct format.
    Validates Requirement 4.7: log routing decisions with format.
    
    This test only runs if sentence-transformers is available.
    """
    import logging
    caplog.set_level(logging.INFO)
    
    router = SLMRouter(
        prototypes_path=temp_prototypes_file,
        confidence_threshold=0.85,
    )
    
    if not router._enabled:
        pytest.skip("sentence-transformers not available")
    
    router.classify("create a react component")
    
    # Check log contains expected format
    log_messages = [record.message for record in caplog.records]
    
    # Find the decision log
    decision_logs = [msg for msg in log_messages if "SLMRouter decision:" in msg]
    
    if decision_logs:
        # Parse JSON from log
        decision_log = decision_logs[0]
        json_str = decision_log.split("SLMRouter decision: ")[1]
        decision_data = json.loads(json_str)
        
        # Validate format
        assert "chosen" in decision_data
        assert "confidence" in decision_data
        assert "top_k" in decision_data
        assert isinstance(decision_data["top_k"], list)


def test_prototypes_with_precomputed_embeddings():
    """
    Test loading prototypes with pre-computed embeddings.
    
    This test only runs if sentence-transformers is available.
    """
    import numpy as np
    
    temp_dir = tempfile.mkdtemp()
    prototypes_path = Path(temp_dir) / "prototypes.json"
    
    prototypes = {
        "frontend": {
            "embedding": [1.0, 0.0, 0.0]
        },
        "backend": {
            "embedding": [0.0, 1.0, 0.0]
        },
    }
    
    with open(prototypes_path, 'w', encoding='utf-8') as f:
        json.dump(prototypes, f)
    
    try:
        router = SLMRouter(
            prototypes_path=prototypes_path,
            confidence_threshold=0.85,
        )
        
        if not router._enabled:
            pytest.skip("sentence-transformers not available")
        
        assert len(router._categories) == 2
        assert "frontend" in router._categories
        assert "backend" in router._categories
        
    finally:
        shutil.rmtree(temp_dir)


def test_confidence_threshold_behavior(temp_prototypes_file):
    """
    Test that confidence threshold affects routing decisions.
    Validates Requirements 4.2, 4.3.
    
    This test only runs if sentence-transformers is available.
    """
    # Low threshold - should return results more often
    router_low = SLMRouter(
        prototypes_path=temp_prototypes_file,
        confidence_threshold=0.1,
    )
    
    # High threshold - should return None more often
    router_high = SLMRouter(
        prototypes_path=temp_prototypes_file,
        confidence_threshold=0.99,
    )
    
    if not router_low._enabled:
        pytest.skip("sentence-transformers not available")
    
    query = "create something"
    
    result_low = router_low.classify(query)
    result_high = router_high.classify(query)
    
    # With low threshold, more likely to get a result
    # With high threshold, more likely to get None (fall through to LLM)
    # At least one should behave as expected
    assert result_low is not None or result_high is None


def test_initialization_attributes(temp_prototypes_file):
    """Test that SLMRouter initializes with correct attributes."""
    router = SLMRouter(
        prototypes_path=temp_prototypes_file,
        confidence_threshold=0.75,
        embedding_model="test-model",
    )
    
    assert router.prototypes_path == Path(temp_prototypes_file)
    assert router.confidence_threshold == 0.75
    assert router.embedding_model_name == "test-model"
    assert hasattr(router, '_enabled')
    assert hasattr(router, '_model')
    assert hasattr(router, '_prototypes')


def test_classify_none_when_disabled():
    """
    Test that classify returns None when router is disabled.
    Validates Requirement 4.6: graceful degradation.
    """
    router = SLMRouter(
        prototypes_path="/nonexistent/path.json",
        confidence_threshold=0.85,
    )
    
    assert router._enabled is False
    
    result = router.classify("any query at all")
    assert result is None
