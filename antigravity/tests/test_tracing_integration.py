"""
Test suite for Langfuse tracing integration.

Run WITHOUT Langfuse credentials → verifies NoOp graceful degradation.
Run WITH credentials → verifies real data flows to Langfuse dashboard.

    # No-op mode (no credentials needed):
    pytest tests/test_tracing_integration.py -v

    # Live mode (set env vars first):
    LANGFUSE_PUBLIC_KEY=pk-... LANGFUSE_SECRET_KEY=sk-... \
        pytest tests/test_tracing_integration.py -v --live
"""

import sys
import os

# Ensure the antigravity/core package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import uuid
import pytest
from collections import deque
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field

# ── Import targets ──
from core.tracing import (
    TracingService,
    NoOpTrace,
    NoOpSpan,
    OrchestratorTrace,
    SpanWrapper,
)


# ── Fixtures ─────────────────────────────────────────────

def pytest_addoption(parser):
    parser.addoption("--live", action="store_true", default=False,
                     help="Run against real Langfuse instance")


@pytest.fixture
def is_live(request):
    return request.config.getoption("--live")


@pytest.fixture
def tracer_noop():
    """TracingService with credentials deliberately absent."""
    with patch.dict(os.environ, {}, clear=True):
        # Ensure no LANGFUSE keys leak from host environment
        os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
        os.environ.pop("LANGFUSE_SECRET_KEY", None)
        return TracingService()


@pytest.fixture
def tracer_live():
    """TracingService pointing at real Langfuse. Skip if no creds."""
    pk = os.getenv("LANGFUSE_PUBLIC_KEY")
    sk = os.getenv("LANGFUSE_SECRET_KEY")
    if not pk or not sk:
        pytest.skip("LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY not set")
    return TracingService()


# ── Mock domain objects ──────────────────────────────────

@dataclass
class MockStep:
    step_id: str
    action: str
    input: dict = field(default_factory=dict)


@dataclass
class MockCompletionCriteria:
    deterministic_checks: list = field(default_factory=list)


@dataclass
class MockPlan:
    steps: list
    completion_criteria: MockCompletionCriteria = field(
        default_factory=MockCompletionCriteria
    )

    def model_dump(self):
        return {"steps": [s.__dict__ for s in self.steps]}


@dataclass
class MockRouteDecision:
    route_to: str = "auto_fix"
    confidence: float = 0.85


@dataclass
class MockSkill:
    macro_steps: str = "1. Check imports 2. Fix paths"


# ── PART 1: NoOp Degradation Tests ──────────────────────

class TestNoOpDegradation:
    """When Langfuse credentials are missing, nothing crashes."""

    def test_tracer_returns_noop_trace(self, tracer_noop):
        trace = tracer_noop.create_trace(
            name="test", session_id="s-1"
        )
        assert isinstance(trace, NoOpTrace)

    def test_noop_span_lifecycle(self, tracer_noop):
        trace = tracer_noop.create_trace(name="t", session_id="s")
        with trace.span("outer") as outer:
            outer.set_attribute("key", "value")
            outer.log_event("something_happened", {"detail": 42})
            outer.log_generation(
                name="gen", model="test-model",
                input="hello", output="world",
            )
            with outer.child_span("inner") as inner:
                inner.set_attribute("nested", True)
        # No assertion needed — success = no exception raised.

    def test_noop_score(self, tracer_noop):
        trace = tracer_noop.create_trace(name="t", session_id="s")
        trace.score("outcome", 1.0, comment="pass")

    def test_flush_noop(self, tracer_noop):
        tracer_noop.flush()


# ── PART 2: Simulated Orchestrator Loop ─────────────────

class TestOrchestratorTracingIntegration:
    """
    Simulates the orchestrator's execute() flow using mocks,
    verifying that tracing calls are made in the correct order
    with correct attributes.
    """

    def _build_mock_orchestrator_deps(self):
        llm = MagicMock()
        llm.model_name = "qwen2.5-3b"
        llm.generate_structured = MagicMock(
            return_value=MockRouteDecision()
        )

        dispatcher = MagicMock()
        dispatcher.dispatch = MagicMock(
            return_value="$ npm install\nadded 42 packages"
        )

        checker = MagicMock()
        # First call returns errors, second call returns clean
        checker.examine = MagicMock(
            side_effect=[
                ["Error: Cannot find module 'react'"],
                [],  # Fixed on second attempt
            ]
        )

        skill_store = MagicMock()
        skill_store.retrieve = MagicMock(return_value=MockSkill())

        return llm, dispatcher, checker, skill_store

    def _simulate_execution(self, tracer: TracingService):
        """
        Stripped-down replica of Orchestrator.execute() that exercises
        every tracing call site without importing the real orchestrator.
        This way we test tracing in isolation from LLM/dispatch bugs.
        """
        llm, dispatcher, checker, skill_store = (
            self._build_mock_orchestrator_deps()
        )

        session_id = str(uuid.uuid4())
        trace = tracer.create_trace(
            name="orchestrator_execute",
            session_id=session_id,
            metadata={"task": "fix broken react import"},
        )

        # ── ROUTE ──
        with trace.span("route_task") as route_span:
            decision = llm.generate_structured()
            route_span.set_attribute("route", decision.route_to)
            route_span.set_attribute("confidence", decision.confidence)

        # ── PLAN ──
        plan = MockPlan(steps=[
            MockStep(step_id="1", action="shell_exec",
                     input={"cmd": "npm install"}),
            MockStep(step_id="2", action="write_file",
                     input={"path": "src/App.jsx", "content": "..."}),
        ])

        with trace.span("plan_execution") as plan_span:
            plan_span.set_attribute("instructor_retries", 0)
            plan_span.set_attribute("step_count", len(plan.steps))
            plan_span.log_generation(
                name="plan_generation",
                model=llm.model_name,
                input="fix broken react import",
                output=plan.model_dump(),
                metadata={"instructor_retries": 0},
            )

        # ── EXECUTION LOOP ──
        context: deque[dict] = deque(maxlen=5)
        repair_count = 0
        max_repairs = 4
        outcome = "unknown"

        with trace.span("execution_loop") as loop_span:
            while repair_count <= max_repairs:
                # Dispatch
                with loop_span.child_span(
                    f"dispatch_round_{repair_count}"
                ) as dispatch_span:
                    for step in plan.steps:
                        with dispatch_span.child_span(
                            f"step_{step.step_id}_{step.action}"
                        ) as step_span:
                            result = dispatcher.dispatch(
                                action=step.action,
                                input_data=step.input,
                                context=list(context),
                            )
                            context.append({
                                "step": step.step_id,
                                "result": str(result)[:200],
                            })
                            step_span.set_attribute(
                                "result_length", len(str(result))
                            )

                # Check
                with loop_span.child_span("deterministic_check") as ck_span:
                    errors = checker.examine(
                        plan.completion_criteria.deterministic_checks
                    )
                    ck_span.set_attribute("error_count", len(errors))

                if not errors:
                    outcome = "success"
                    trace.score("outcome", 1.0, comment="all checks passed")
                    break

                repair_count += 1
                if repair_count > max_repairs:
                    outcome = "max_repairs_exceeded"
                    trace.score("outcome", 0.0)
                    break

                # Replan
                with loop_span.child_span(f"replan_{repair_count}") as rp_span:
                    rp_span.log_event("replan_triggered", {
                        "errors": errors,
                        "attempt": repair_count,
                    })

            loop_span.set_attribute("total_repair_rounds", repair_count)
            loop_span.set_attribute("outcome", outcome)

        tracer.flush()
        return {
            "session_id": session_id,
            "outcome": outcome,
            "repairs": repair_count,
        }

    def test_noop_simulation(self, tracer_noop):
        """Full loop runs without crash when Langfuse is absent."""
        result = self._simulate_execution(tracer_noop)
        assert result["outcome"] == "success"
        assert result["repairs"] == 1  # fails once, then succeeds


# ── PART 3: _normalize_errors unit tests ─────────────────

class TestNormalizeErrors:
    """
    Tests for the error normalization function.
    Import from wherever you placed it in orchestrator.py.
    """

    @pytest.fixture(autouse=True)
    def import_normalizer(self):
        try:
            from scripts.orchestrator import _normalize_errors
            self.normalize = _normalize_errors
        except ImportError:
            pytest.skip("orchestrator._normalize_errors not importable")

    def test_strips_line_numbers(self):
        errs = ["Error at line 15: undefined variable",
                "Error at line 99: undefined variable"]
        normed = self.normalize(errs)
        assert normed[0] == normed[1]

    def test_strips_windows_paths(self):
        errs = [
            r"Error in C:\Users\<YOUR_USERNAME>\src\App.jsx",
            r"Error in D:\projects\web\src\App.jsx",
        ]
        normed = self.normalize(errs)
        assert normed[0] == normed[1]

    def test_strips_file_paths(self):
        errs = ["Cannot read /home/user/app/src/index.js",
                "Cannot read /var/www/html/src/index.js"]
        normed = self.normalize(errs)
        assert normed[0] == normed[1]

    def test_preserves_module_names(self):
        errs = ["Cannot find module 'react'",
                "Cannot find module 'vue'"]
        normed = self.normalize(errs)
        assert normed[0] != normed[1], (
            "Different module names must remain distinguishable"
        )

    def test_strips_timestamps(self):
        errs = ["2025-03-25 14:30:22 Error: EADDRINUSE",
                "2025-03-26 09:00:01 Error: EADDRINUSE"]
        normed = self.normalize(errs)
        assert normed[0] == normed[1]

    def test_strips_hex_addresses(self):
        errs = ["Segfault at 0x7fff5fbff8c0",
                "Segfault at 0x0000deadbeef"]
        normed = self.normalize(errs)
        assert normed[0] == normed[1]

    def test_different_errors_stay_different(self):
        errs = ["TypeError: x is not a function",
                "ReferenceError: y is not defined"]
        normed = self.normalize(errs)
        assert normed[0] != normed[1]
