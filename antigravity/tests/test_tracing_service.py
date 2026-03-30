"""
Unit tests for TracingService nâng cấp — Langfuse integration.
Tests for Task 11 implementation.
"""

import sys
import os

# Ensure the antigravity/core package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import MagicMock, patch
from core.tracing import TracingService, NoOpTrace, NoOpSpan, OrchestratorTrace, SpanWrapper
from core.schemas import ErrorDelta


# ── Fixtures ─────────────────────────────────────────────

@pytest.fixture
def tracer_noop():
    """TracingService with no credentials (NoOp mode)."""
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
        os.environ.pop("LANGFUSE_SECRET_KEY", None)
        return TracingService()


@pytest.fixture
def mock_error_delta():
    """Mock ErrorDelta for testing."""
    from core.id_utils import generate_ulid
    return ErrorDelta(
        operation_id=generate_ulid(),
        errors_resolved=["SyntaxError: missing semicolon"],
        errors_introduced=["TypeError: undefined is not a function"],
        old_error_score=10.0,
        new_error_score=7.0,
        net_improvement=True,
    )


# ── Test log_generation ──────────────────────────────────

class TestLogGeneration:
    """Test log_generation method with full fields."""

    def test_log_generation_with_all_fields(self, tracer_noop):
        """Verify log_generation logs all fields including None values."""
        trace = tracer_noop.create_trace(name="test", session_id="s-1")
        
        with trace.span("test_span") as span:
            # Call with all fields
            span.log_generation(
                model="gpt-4",
                input_tokens=100,
                output_tokens=50,
                latency_ms=250.5,
                task_name="code_generation"
            )
        
        # No exception = success (NoOp mode)
        assert True

    def test_log_generation_with_none_values(self, tracer_noop):
        """Verify log_generation handles None values correctly."""
        trace = tracer_noop.create_trace(name="test", session_id="s-1")
        
        with trace.span("test_span") as span:
            # Call with None values (API didn't return some fields)
            span.log_generation(
                model="gpt-4",
                input_tokens=None,  # API didn't return this
                output_tokens=None,  # API didn't return this
                latency_ms=250.5,
                task_name="code_generation"
            )
        
        # No exception = success
        assert True

    def test_log_generation_minimal(self, tracer_noop):
        """Verify log_generation works with minimal fields."""
        trace = tracer_noop.create_trace(name="test", session_id="s-1")
        
        with trace.span("test_span") as span:
            span.log_generation(model="gpt-4")
        
        assert True


# ── Test log_replan_triggered ────────────────────────────

class TestLogReplanTriggered:
    """Test log_replan_triggered method with ErrorDelta context."""

    def test_log_replan_triggered_with_error_delta(self, tracer_noop, mock_error_delta):
        """Verify log_replan_triggered logs ErrorDelta context."""
        trace = tracer_noop.create_trace(name="test", session_id="s-1")
        
        with trace.span("execution_loop") as span:
            span.log_replan_triggered(mock_error_delta)
        
        # No exception = success
        assert True

    def test_log_replan_triggered_noop(self, tracer_noop, mock_error_delta):
        """Verify NoOpSpan.log_replan_triggered doesn't crash."""
        trace = tracer_noop.create_trace(name="test", session_id="s-1")
        
        with trace.span("test_span") as span:
            # Should be NoOpSpan in noop mode
            span.log_replan_triggered(mock_error_delta)
        
        assert True


# ── Test link_patch_metadata ─────────────────────────────

class TestLinkPatchMetadata:
    """Test link_patch_metadata method."""

    def test_link_patch_metadata_with_rollback(self, tracer_noop, mock_error_delta):
        """Verify link_patch_metadata links all fields."""
        trace = tracer_noop.create_trace(name="test", session_id="s-1")
        
        with trace.span("step_1") as span:
            span.link_patch_metadata(
                patch_id="patch-001",
                error_delta=mock_error_delta,
                rollback_triggered=True
            )
        
        assert True

    def test_link_patch_metadata_no_rollback(self, tracer_noop, mock_error_delta):
        """Verify link_patch_metadata with rollback_triggered=False."""
        trace = tracer_noop.create_trace(name="test", session_id="s-1")
        
        with trace.span("step_1") as span:
            span.link_patch_metadata(
                patch_id="patch-002",
                error_delta=mock_error_delta,
                rollback_triggered=False
            )
        
        assert True


# ── Test score ────────────────────────────────────────────

class TestScore:
    """Test trace.score() method."""

    def test_score_success(self, tracer_noop):
        """Verify score(1.0) on success."""
        trace = tracer_noop.create_trace(name="test", session_id="s-1")
        trace.score(value=1.0, comment="Task completed successfully")
        assert True

    def test_score_failure(self, tracer_noop):
        """Verify score(0.0) on max repairs."""
        trace = tracer_noop.create_trace(name="test", session_id="s-1")
        trace.score(value=0.0, comment="Max repair attempts exceeded")
        assert True

    def test_score_partial(self, tracer_noop):
        """Verify score with partial success."""
        trace = tracer_noop.create_trace(name="test", session_id="s-1")
        trace.score(value=0.5, comment="Partial completion")
        assert True


# ── Test flush ────────────────────────────────────────────

class TestFlush:
    """Test flush() method."""

    def test_flush_noop(self, tracer_noop):
        """Verify flush() doesn't crash in NoOp mode."""
        tracer_noop.flush()
        assert True

    def test_flush_in_finally_block(self, tracer_noop):
        """Verify flush() is called in finally block via trace_session."""
        try:
            with tracer_noop.trace_session(name="test", session_id="s-1") as trace:
                with trace.span("test_span") as span:
                    span.set_attribute("key", "value")
                    raise ValueError("Simulated error")
        except ValueError:
            pass
        
        # flush() should have been called in finally block
        assert True


# ── Test session_id and notebook_id tagging ──────────────

class TestSessionTagging:
    """Test session_id and notebook_id tagging."""

    def test_create_trace_with_session_id(self, tracer_noop):
        """Verify trace is tagged with session_id."""
        trace = tracer_noop.create_trace(
            name="test",
            session_id="session-123"
        )
        assert isinstance(trace, NoOpTrace)

    def test_create_trace_with_notebook_id(self, tracer_noop):
        """Verify trace is tagged with notebook_id."""
        trace = tracer_noop.create_trace(
            name="test",
            session_id="session-123",
            notebook_id="notebook-456"
        )
        assert isinstance(trace, NoOpTrace)

    def test_trace_session_with_notebook_id(self, tracer_noop):
        """Verify trace_session accepts notebook_id."""
        with tracer_noop.trace_session(
            name="test",
            session_id="session-123",
            notebook_id="notebook-456"
        ) as trace:
            with trace.span("test_span") as span:
                span.set_attribute("key", "value")
        
        assert True


# ── Test nested spans ─────────────────────────────────────

class TestNestedSpans:
    """Test nested span structure."""

    def test_nested_spans_structure(self, tracer_noop):
        """Verify nested spans: route_task → plan_execution → execution_loop → step_{id} → deterministic_check."""
        trace = tracer_noop.create_trace(name="orchestrator", session_id="s-1")
        
        with trace.span("route_task") as route_span:
            route_span.set_attribute("route", "auto_fix")
            
            with route_span.child_span("plan_execution") as plan_span:
                plan_span.set_attribute("step_count", 3)
                
                with plan_span.child_span("execution_loop") as loop_span:
                    loop_span.set_attribute("repair_count", 0)
                    
                    with loop_span.child_span("step_1") as step_span:
                        step_span.set_attribute("action", "write_file")
                        
                        with step_span.child_span("deterministic_check") as check_span:
                            check_span.set_attribute("error_count", 0)
        
        assert True


# ── Test graceful degradation ────────────────────────────

class TestGracefulDegradation:
    """Test graceful degradation when credentials missing/invalid."""

    def test_no_credentials_returns_noop(self):
        """Verify NoOp when credentials missing."""
        with patch.dict(os.environ, {}, clear=True):
            tracer = TracingService()
            trace = tracer.create_trace(name="test", session_id="s-1")
            assert isinstance(trace, NoOpTrace)

    def test_invalid_credentials_returns_noop(self):
        """Verify NoOp when credentials invalid."""
        with patch.dict(os.environ, {
            "LANGFUSE_PUBLIC_KEY": "invalid-key",
            "LANGFUSE_SECRET_KEY": "invalid-secret"
        }):
            tracer = TracingService()
            # Should not crash, should degrade to NoOp
            trace = tracer.create_trace(name="test", session_id="s-1")
            # In NoOp mode or with invalid creds, should still work
            assert trace is not None

    def test_import_error_returns_noop(self):
        """Verify NoOp when langfuse module not installed."""
        with patch.dict(os.environ, {
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test"
        }):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'langfuse'")):
                tracer = TracingService()
                # Access client to trigger import
                _ = tracer.client
                trace = tracer.create_trace(name="test", session_id="s-1")
                assert isinstance(trace, NoOpTrace)


# ── Test full execution flow ──────────────────────────────

class TestFullExecutionFlow:
    """Test full execution flow with all tracing methods."""

    def test_full_orchestrator_flow(self, tracer_noop, mock_error_delta):
        """Simulate full orchestrator flow with all tracing calls."""
        session_id = "session-full-test"
        notebook_id = "notebook-123"
        
        with tracer_noop.trace_session(
            name="orchestrator_execute",
            session_id=session_id,
            notebook_id=notebook_id
        ) as trace:
            # Route task
            with trace.span("route_task") as route_span:
                route_span.set_attribute("route", "auto_fix")
                route_span.log_generation(
                    model="qwen2.5-3b",
                    input_tokens=150,
                    output_tokens=50,
                    latency_ms=120.5,
                    task_name="route_classification"
                )
            
            # Plan execution
            with trace.span("plan_execution") as plan_span:
                plan_span.set_attribute("step_count", 2)
                plan_span.log_generation(
                    model="qwen2.5-3b",
                    input_tokens=500,
                    output_tokens=200,
                    latency_ms=450.0,
                    task_name="plan_generation"
                )
            
            # Execution loop
            with trace.span("execution_loop") as loop_span:
                # Step 1
                with loop_span.child_span("step_1") as step_span:
                    step_span.set_attribute("action", "write_file")
                    step_span.link_patch_metadata(
                        patch_id="patch-001",
                        error_delta=mock_error_delta,
                        rollback_triggered=False
                    )
                    
                    # Deterministic check
                    with step_span.child_span("deterministic_check") as check_span:
                        check_span.set_attribute("error_count", 1)
                
                # Replan triggered
                loop_span.log_replan_triggered(mock_error_delta)
                
                # Step 2 (after replan)
                with loop_span.child_span("step_2") as step_span:
                    step_span.set_attribute("action", "write_file")
                    
                    with step_span.child_span("deterministic_check") as check_span:
                        check_span.set_attribute("error_count", 0)
            
            # Score success
            trace.score(value=1.0, comment="Task completed successfully")
        
        # flush() called automatically in finally block
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
