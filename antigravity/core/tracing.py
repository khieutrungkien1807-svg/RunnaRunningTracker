"""
Langfuse tracing integration for Orchestrator.
- Set LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST env vars to enable.
- When env vars are missing, all operations gracefully degrade to no-ops.
"""

import os
import time
from contextlib import contextmanager
from typing import Generator

class NoOpSpan:
    """Null-object pattern: every method is a silent no-op."""

    def log_generation(self, **kwargs) -> None:
        pass

    def set_attribute(self, key: str, value) -> None:
        pass

    def log_event(self, name: str, metadata: dict | None = None) -> None:
        pass

    def update(self, **kwargs) -> None:
        pass

    def log_error(self, message: str) -> None:
        pass

    def log_replan_triggered(self, error_delta) -> None:
        pass

    def link_patch_metadata(self, patch_id: str, error_delta, rollback_triggered: bool) -> None:
        pass

    @contextmanager
    def child_span(self, name: str, metadata: dict | None = None) -> Generator["NoOpSpan", None, None]:
        yield self

    @contextmanager
    def span(self, name: str, metadata: dict | None = None) -> Generator["NoOpSpan", None, None]:
        yield self


class NoOpTrace:
    """Null-object pattern for traces."""

    @contextmanager
    def span(self, name: str, metadata: dict | None = None) -> Generator["NoOpSpan", None, None]:
        yield NoOpSpan()

    def score(self, value: float, name: str = "task_completion", comment: str = "") -> None:
        pass

    @contextmanager
    def trace_session(self, name: str, session_id: str) -> Generator["NoOpTrace", None, None]:
        yield self


class SpanWrapper:
    """Thin ergonomic wrapper around a Langfuse span."""

    def __init__(self, span):
        self._span = span
        self._metadata: dict = {}

    def log_generation(
        self,
        model: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        latency_ms: float | None = None,
        task_name: str | None = None,
        **kwargs
    ) -> None:
        """
        Log LLM generation with full details. None values are logged as None.
        Requirement 6.2, 6.5: Log every LLM generation call with full fields.
        """
        generation_data = {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
            "task_name": task_name,
        }
        # Add any additional kwargs
        generation_data.update(kwargs)
        
        # Log as event with all fields (including None values)
        self.log_event("llm_generation", metadata=generation_data)

    def set_attribute(self, key: str, value) -> None:
        self._metadata[key] = value
        self._span.update(metadata=self._metadata)

    def log_event(self, name: str, metadata: dict | None = None) -> None:
        self._span.event(name=name, metadata=metadata or {})

    def update(self, **kwargs) -> None:
        self._span.update(**kwargs)

    def log_error(self, message: str) -> None:
        self._span.update(level="ERROR", status_message=message[:500])

    def log_replan_triggered(self, error_delta) -> None:
        """
        Log replan_triggered event with ErrorDelta context.
        Requirement 6.4: Log replan event with ErrorDelta context.
        """
        metadata = {
            "operation_id": error_delta.operation_id,
            "errors_resolved": error_delta.errors_resolved,
            "errors_introduced": error_delta.errors_introduced,
            "old_error_score": error_delta.old_error_score,
            "new_error_score": error_delta.new_error_score,
            "net_improvement": error_delta.net_improvement,
        }
        self.log_event("replan_triggered", metadata=metadata)

    def link_patch_metadata(self, patch_id: str, error_delta, rollback_triggered: bool) -> None:
        """
        Link patch_id, error_delta, and rollback_triggered in current span.
        Requirement 6.5: Link patch metadata in same span.
        """
        metadata = {
            "patch_id": patch_id,
            "operation_id": error_delta.operation_id,
            "old_error_score": error_delta.old_error_score,
            "new_error_score": error_delta.new_error_score,
            "net_improvement": error_delta.net_improvement,
            "rollback_triggered": rollback_triggered,
        }
        self.set_attribute("patch_metadata", metadata)

    @contextmanager
    def child_span(self, name: str, metadata: dict | None = None) -> Generator["SpanWrapper", None, None]:
        child = self._span.span(name=name, metadata=metadata or {})
        wrapper = SpanWrapper(child)
        start = time.perf_counter()
        try:
            yield wrapper
        except Exception as e:
            child.update(level="ERROR", status_message=str(e)[:500])
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            wrapper.set_attribute("duration_ms", duration_ms)
            child.end()

    def span(self, name: str, metadata: dict | None = None):
        return self.child_span(name, metadata)


class OrchestratorTrace:
    """Wraps a Langfuse trace with orchestrator-specific conveniences."""

    def __init__(self, trace):
        self._trace = trace

    @contextmanager
    def span(self, name: str, metadata: dict | None = None) -> Generator[SpanWrapper, None, None]:
        raw_span = self._trace.span(name=name, metadata=metadata or {})
        wrapper = SpanWrapper(raw_span)
        start = time.perf_counter()
        try:
            yield wrapper
        except Exception as e:
            raw_span.update(level="ERROR", status_message=str(e)[:500])
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            wrapper.set_attribute("duration_ms", duration_ms)
            raw_span.end()
            
    @contextmanager
    def trace_session(self, name: str, session_id: str) -> Generator["OrchestratorTrace", None, None]:
        # Compatibility wrapper for existing code
        yield self

    def score(self, value: float, name: str = "task_completion", comment: str = "") -> None:
        """
        Call trace.score() with 1.0 on success, 0.0 on max repairs.
        Requirement 6.6: Score trace with 1.0 on success, 0.0 on max repairs.
        """
        self._trace.score(name=name, value=value, comment=comment)


class TracingService:
    """
    Entry point. Lazy-initializes Langfuse client on first use.
    If credentials are missing, returns NoOpTrace so callers never need
    to check `if tracing_enabled:` themselves.
    
    Requirement 6.1: Initialize real Langfuse client when env vars present.
    Requirement 6.7: Graceful degradation to NoOp if credentials missing/invalid.
    """

    def __init__(self):
        self._client = None
        self._enabled: bool = all([
            os.getenv("LANGFUSE_PUBLIC_KEY"),
            os.getenv("LANGFUSE_SECRET_KEY"),
        ])

    @property
    def client(self):
        if self._client is None and self._enabled:
            try:
                from langfuse import Langfuse
                self._client = Langfuse(
                    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
                )
            except ImportError:
                print("[TRACING] Langfuse module not installed. Defaulting to NoOp.")
                self._enabled = False
            except Exception as e:
                print(f"[TRACING] Failed to initialize Langfuse: {e}. Defaulting to NoOp.")
                self._enabled = False
        return self._client

    def create_trace(
        self,
        name: str,
        session_id: str,
        notebook_id: str | None = None,
        user_id: str | None = None,
        metadata: dict | None = None,
    ) -> "OrchestratorTrace | NoOpTrace":
        """
        Create a trace with session_id and notebook_id tags.
        Requirement 6.9: Tag each trace with session_id and notebook_id.
        """
        if not self._enabled or self.client is None:
            return NoOpTrace()
        
        # Merge session_id and notebook_id into metadata
        trace_metadata = metadata or {}
        trace_metadata["session_id"] = session_id
        if notebook_id:
            trace_metadata["notebook_id"] = notebook_id
            
        trace = self.client.trace(
            name=name,
            session_id=session_id,
            user_id=user_id,
            metadata=trace_metadata,
        )
        return OrchestratorTrace(trace)

    @contextmanager
    def trace_session(self, name: str, session_id: str, notebook_id: str | None = None) -> Generator["OrchestratorTrace | NoOpTrace", None, None]:
        """
        Context manager for trace session with automatic flush.
        Requirement 6.8: Flush all pending traces when session ends.
        """
        trace = self.create_trace(name=name, session_id=session_id, notebook_id=notebook_id)
        try:
            yield trace
        finally:
            self.flush()

    def flush(self) -> None:
        """
        Flush all pending traces to Langfuse.
        Requirement 6.8: Ensure flush() is called in finally block.
        """
        if self._enabled and self._client:
            self._client.flush()

    def log_event(self, event_name: str, metadata: dict | None = None) -> None:
        """
        Log a standalone event (for compatibility).
        """
        # Events are typically logged within spans, but this provides a fallback
        pass

    def log_replan_triggered(self, error_delta) -> None:
        """
        Log replan_triggered event (for compatibility).
        Should be called on a span, but this provides a fallback.
        """
        pass

    def link_patch_metadata(self, patch_id: str, error_delta, rollback_triggered: bool) -> None:
        """
        Link patch metadata (for compatibility).
        Should be called on a span, but this provides a fallback.
        """
        pass
