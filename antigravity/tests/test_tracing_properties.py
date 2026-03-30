"""
Property-based tests for TracingService.
Task 11.1: Write property test cho trace fields completeness (Property 16).
"""

import sys
import os

# Ensure the antigravity/core package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from hypothesis import given, settings, strategies as st
from unittest.mock import patch, MagicMock
from core.tracing import TracingService, SpanWrapper


# ── Property 16: Trace Fields Completeness ───────────────────────────────────

@given(
    model=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    input_tokens=st.one_of(st.none(), st.integers(min_value=0, max_value=100000)),
    output_tokens=st.one_of(st.none(), st.integers(min_value=0, max_value=100000)),
    latency_ms=st.one_of(st.none(), st.floats(min_value=0.0, max_value=10000.0)),
    task_name=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
)
@settings(max_examples=100)
def test_trace_fields_completeness(model, input_tokens, output_tokens, latency_ms, task_name):
    """
    Feature: antigravity-architecture-upgrade, Property 16: Trace Fields Completeness
    
    For any LLM generation call logged by TracingService, span must contain all fields:
    model, input_tokens, output_tokens, latency_ms, task_name.
    If any field is None (API didn't return it), field must be logged as None, not omitted.
    
    Validates: Requirements 6.2, 6.5
    """
    # Create a mock Langfuse span to test the real SpanWrapper behavior
    mock_span = MagicMock()
    mock_span.event = MagicMock()
    mock_span.update = MagicMock()
    
    # Create SpanWrapper with mock
    span_wrapper = SpanWrapper(mock_span)
    
    # Call log_generation with potentially None values
    span_wrapper.log_generation(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        task_name=task_name
    )
    
    # Verify that event was called
    assert mock_span.event.called, "log_generation should call span.event"
    
    # Get the call arguments
    call_args = mock_span.event.call_args
    assert call_args is not None
    
    # Extract the metadata
    event_name = call_args[1]["name"] if "name" in call_args[1] else call_args[0][0]
    metadata = call_args[1]["metadata"] if "metadata" in call_args[1] else call_args[0][1]
    
    # Verify event name
    assert event_name == "llm_generation"
    
    # Verify ALL fields are present (even if None)
    assert "model" in metadata, "model field must be present"
    assert "input_tokens" in metadata, "input_tokens field must be present"
    assert "output_tokens" in metadata, "output_tokens field must be present"
    assert "latency_ms" in metadata, "latency_ms field must be present"
    assert "task_name" in metadata, "task_name field must be present"
    
    # Verify values match (including None)
    assert metadata["model"] == model
    assert metadata["input_tokens"] == input_tokens
    assert metadata["output_tokens"] == output_tokens
    assert metadata["latency_ms"] == latency_ms
    assert metadata["task_name"] == task_name


@given(
    model=st.text(min_size=1, max_size=50),
    input_tokens=st.integers(min_value=1, max_value=100000),
    output_tokens=st.integers(min_value=1, max_value=100000),
    latency_ms=st.floats(min_value=0.1, max_value=10000.0),
    task_name=st.text(min_size=1, max_size=100),
)
@settings(max_examples=100)
def test_trace_fields_completeness_all_present(model, input_tokens, output_tokens, latency_ms, task_name):
    """
    Feature: antigravity-architecture-upgrade, Property 16: Trace Fields Completeness
    
    When all fields are present (not None), verify they are all logged correctly.
    
    Validates: Requirements 6.2, 6.5
    """
    mock_span = MagicMock()
    mock_span.event = MagicMock()
    mock_span.update = MagicMock()
    
    span_wrapper = SpanWrapper(mock_span)
    
    span_wrapper.log_generation(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        task_name=task_name
    )
    
    assert mock_span.event.called
    call_args = mock_span.event.call_args
    event_name = call_args[1]["name"] if "name" in call_args[1] else call_args[0][0]
    metadata = call_args[1]["metadata"] if "metadata" in call_args[1] else call_args[0][1]
    
    assert event_name == "llm_generation"
    
    # All fields must be present and match
    assert metadata["model"] == model
    assert metadata["input_tokens"] == input_tokens
    assert metadata["output_tokens"] == output_tokens
    assert metadata["latency_ms"] == latency_ms
    assert metadata["task_name"] == task_name


@given(
    # Test with all None values
    model=st.just(None),
    input_tokens=st.just(None),
    output_tokens=st.just(None),
    latency_ms=st.just(None),
    task_name=st.just(None),
)
@settings(max_examples=10)
def test_trace_fields_completeness_all_none(model, input_tokens, output_tokens, latency_ms, task_name):
    """
    Feature: antigravity-architecture-upgrade, Property 16: Trace Fields Completeness
    
    When all fields are None (API returned nothing), verify all fields are still logged as None.
    
    Validates: Requirements 6.2, 6.5
    """
    mock_span = MagicMock()
    mock_span.event = MagicMock()
    mock_span.update = MagicMock()
    
    span_wrapper = SpanWrapper(mock_span)
    
    span_wrapper.log_generation(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        task_name=task_name
    )
    
    assert mock_span.event.called
    call_args = mock_span.event.call_args
    event_name = call_args[1]["name"] if "name" in call_args[1] else call_args[0][0]
    metadata = call_args[1]["metadata"] if "metadata" in call_args[1] else call_args[0][1]
    
    assert event_name == "llm_generation"
    
    # All fields must be present (even though all are None)
    assert "model" in metadata
    assert "input_tokens" in metadata
    assert "output_tokens" in metadata
    assert "latency_ms" in metadata
    assert "task_name" in metadata
    
    # All values must be None
    assert metadata["model"] is None
    assert metadata["input_tokens"] is None
    assert metadata["output_tokens"] is None
    assert metadata["latency_ms"] is None
    assert metadata["task_name"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
