"""
Tests for BudgetGuard — pre-call budget enforcement.

Covers:
- Safe defaults when no config provided
- check_pre_call raises BudgetExceededError when over token budget
- check_pre_call raises BudgetExceededError when over step budget
- check_pre_call raises BudgetExceededError when over repair budget
- record_call accumulates tokens correctly
- get_status returns correct values
- 80% warning threshold is triggered
- finalize doesn't crash

Property tests:
- Property 17: Budget Pre-Call Enforcement (Requirements 7.7)
- Property 18: Budget Termination with Reason (Requirements 7.2)
- Property 19: Token Accumulation Additivity (Requirements 7.3)
"""

from __future__ import annotations

import logging

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from core.budget_guard import BudgetExceededError, BudgetGuard


# ── Unit Tests ────────────────────────────────────────────────────────────────


class TestSafeDefaults:
    def test_default_max_steps(self) -> None:
        guard = BudgetGuard()
        assert guard._max_steps == 50

    def test_default_max_tokens(self) -> None:
        guard = BudgetGuard()
        assert guard._max_tokens == 100_000

    def test_default_max_repair_attempts(self) -> None:
        guard = BudgetGuard()
        assert guard._max_repair_attempts == 5

    def test_initial_usage_is_zero(self) -> None:
        guard = BudgetGuard()
        assert guard._steps_used == 0
        assert guard._tokens_used == 0
        assert guard._repairs_used == 0

    def test_not_terminated_initially(self) -> None:
        guard = BudgetGuard()
        assert guard._terminated is False
        assert guard._termination_reason is None


class TestCheckPreCall:
    def test_does_not_raise_when_within_budget(self) -> None:
        guard = BudgetGuard(max_tokens=10_000)
        # Should not raise
        guard.check_pre_call(estimated_input_tokens=100, max_expected_output_tokens=200)

    def test_raises_when_token_budget_exceeded(self) -> None:
        guard = BudgetGuard(max_tokens=1_000)
        guard._tokens_used = 900
        with pytest.raises(BudgetExceededError) as exc_info:
            guard.check_pre_call(estimated_input_tokens=200, max_expected_output_tokens=200)
        assert exc_info.value.dimension == "tokens"

    def test_raises_when_step_budget_exceeded(self) -> None:
        guard = BudgetGuard(max_steps=5, max_tokens=100_000)
        guard._steps_used = 5
        with pytest.raises(BudgetExceededError) as exc_info:
            guard.check_pre_call(estimated_input_tokens=10, max_expected_output_tokens=10)
        assert exc_info.value.dimension == "steps"

    def test_raises_when_repair_budget_exceeded(self) -> None:
        guard = BudgetGuard(max_repair_attempts=3, max_tokens=100_000)
        guard._repairs_used = 3
        with pytest.raises(BudgetExceededError) as exc_info:
            guard.check_pre_call(estimated_input_tokens=10, max_expected_output_tokens=10)
        assert exc_info.value.dimension == "repairs"

    def test_token_check_takes_priority_over_steps(self) -> None:
        guard = BudgetGuard(max_steps=5, max_tokens=100)
        guard._tokens_used = 99
        guard._steps_used = 5
        with pytest.raises(BudgetExceededError) as exc_info:
            guard.check_pre_call(estimated_input_tokens=50, max_expected_output_tokens=50)
        # tokens checked first
        assert exc_info.value.dimension == "tokens"

    def test_sets_terminated_flag_on_raise(self) -> None:
        guard = BudgetGuard(max_tokens=100)
        guard._tokens_used = 99
        with pytest.raises(BudgetExceededError):
            guard.check_pre_call(50, 50)
        assert guard._terminated is True
        assert guard._termination_reason is not None

    def test_termination_reason_is_non_empty_string(self) -> None:
        guard = BudgetGuard(max_tokens=100)
        guard._tokens_used = 99
        with pytest.raises(BudgetExceededError) as exc_info:
            guard.check_pre_call(50, 50)
        assert isinstance(exc_info.value.termination_reason, str)
        assert len(exc_info.value.termination_reason) > 0

    def test_exact_boundary_does_not_raise(self) -> None:
        guard = BudgetGuard(max_tokens=1_000)
        guard._tokens_used = 0
        # estimated_cost == remaining == 1000 → should NOT raise (remaining >= estimated_cost)
        guard.check_pre_call(500, 500)

    def test_one_over_boundary_raises(self) -> None:
        guard = BudgetGuard(max_tokens=1_000)
        guard._tokens_used = 0
        with pytest.raises(BudgetExceededError):
            guard.check_pre_call(500, 501)


class TestRecordCall:
    def test_accumulates_tokens(self) -> None:
        guard = BudgetGuard(max_tokens=100_000)
        guard.record_call(500)
        guard.record_call(300)
        assert guard._tokens_used == 800

    def test_zero_tokens_is_valid(self) -> None:
        guard = BudgetGuard()
        guard.record_call(0)
        assert guard._tokens_used == 0


class TestRecordStep:
    def test_increments_step_counter(self) -> None:
        guard = BudgetGuard()
        guard.record_step()
        guard.record_step()
        assert guard._steps_used == 2


class TestRecordRepair:
    def test_increments_repair_counter(self) -> None:
        guard = BudgetGuard()
        guard.record_repair()
        assert guard._repairs_used == 1


class TestGetStatus:
    def test_returns_correct_used_values(self) -> None:
        guard = BudgetGuard(max_steps=10, max_tokens=1_000, max_repair_attempts=3)
        guard._steps_used = 3
        guard._tokens_used = 400
        guard._repairs_used = 1

        status = guard.get_status()

        assert status.steps_used == 3
        assert status.tokens_used == 400
        assert status.repairs_used == 1

    def test_returns_correct_remaining_values(self) -> None:
        guard = BudgetGuard(max_steps=10, max_tokens=1_000, max_repair_attempts=3)
        guard._steps_used = 3
        guard._tokens_used = 400
        guard._repairs_used = 1

        status = guard.get_status()

        assert status.steps_remaining == 7
        assert status.tokens_remaining == 600
        assert status.repairs_remaining == 2

    def test_warning_threshold_not_reached_initially(self) -> None:
        guard = BudgetGuard()
        status = guard.get_status()
        assert status.warning_threshold_reached is False

    def test_warning_threshold_reached_at_80_percent(self) -> None:
        guard = BudgetGuard(max_steps=10)
        guard._steps_used = 8  # exactly 80%
        status = guard.get_status()
        assert status.warning_threshold_reached is True

    def test_termination_reason_none_when_not_terminated(self) -> None:
        guard = BudgetGuard()
        status = guard.get_status()
        assert status.termination_reason is None

    def test_termination_reason_set_after_budget_exceeded(self) -> None:
        guard = BudgetGuard(max_tokens=100)
        guard._tokens_used = 99
        with pytest.raises(BudgetExceededError):
            guard.check_pre_call(50, 50)
        status = guard.get_status()
        assert status.termination_reason is not None

    def test_remaining_never_negative(self) -> None:
        guard = BudgetGuard(max_steps=5)
        guard._steps_used = 10  # over limit
        status = guard.get_status()
        assert status.steps_remaining == 0


class TestWarnIfApproaching:
    def test_logs_warning_at_80_percent_tokens(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        guard = BudgetGuard(max_tokens=1_000)
        with caplog.at_level(logging.WARNING, logger="core.budget_guard"):
            guard._tokens_used = 800
            guard._warn_if_approaching()
        assert any("tokens" in r.message for r in caplog.records)

    def test_logs_warning_at_80_percent_steps(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        guard = BudgetGuard(max_steps=10)
        with caplog.at_level(logging.WARNING, logger="core.budget_guard"):
            guard._steps_used = 8
            guard._warn_if_approaching()
        assert any("steps" in r.message for r in caplog.records)

    def test_no_warning_below_80_percent(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        guard = BudgetGuard(max_tokens=1_000)
        with caplog.at_level(logging.WARNING, logger="core.budget_guard"):
            guard._tokens_used = 799
            guard._warn_if_approaching()
        assert not any("tokens" in r.message for r in caplog.records)

    def test_warning_message_format(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        guard = BudgetGuard(max_tokens=1_000)
        with caplog.at_level(logging.WARNING, logger="core.budget_guard"):
            guard._tokens_used = 900
            guard._warn_if_approaching()
        assert any("BudgetGuard WARNING" in r.message for r in caplog.records)


class TestFinalize:
    def test_finalize_does_not_crash(self) -> None:
        guard = BudgetGuard()
        guard.record_step()
        guard.record_call(500)
        guard.record_repair()
        guard.finalize()  # must not raise

    def test_finalize_logs_info(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        guard = BudgetGuard()
        with caplog.at_level(logging.INFO, logger="core.budget_guard"):
            guard.finalize()
        assert any("finalized" in r.message.lower() for r in caplog.records)


# ── Property-Based Tests ──────────────────────────────────────────────────────


@given(
    tokens_used=st.integers(min_value=0, max_value=90_000),
    estimated_input=st.integers(min_value=1, max_value=5_000),
    max_output=st.integers(min_value=1, max_value=5_000),
)
@settings(max_examples=100)
def test_budget_pre_call_enforcement(
    tokens_used: int, estimated_input: int, max_output: int
) -> None:
    """
    # Feature: antigravity-architecture-upgrade, Property 17: Budget Pre-Call Enforcement
    **Validates: Requirements 7.7**

    For any BudgetGuard state with remaining_token_budget < estimated_call_cost,
    check_pre_call() must raise BudgetExceededError and the LLM call must not proceed.
    estimated_call_cost = estimated_input_tokens + max_expected_output_tokens.
    """
    guard = BudgetGuard(max_tokens=100_000)
    guard._tokens_used = tokens_used

    estimated_cost = estimated_input + max_output
    remaining = 100_000 - tokens_used

    if remaining < estimated_cost:
        with pytest.raises(BudgetExceededError) as exc_info:
            guard.check_pre_call(estimated_input, max_output)
        assert exc_info.value.dimension == "tokens"
    else:
        # Should not raise for token dimension (steps/repairs are 0, well within limits)
        guard.check_pre_call(estimated_input, max_output)


@given(
    dimension=st.sampled_from(["tokens", "steps", "repairs"]),
    extra=st.integers(min_value=1, max_value=100),
)
@settings(max_examples=100)
def test_budget_termination_with_reason(dimension: str, extra: int) -> None:
    """
    # Feature: antigravity-architecture-upgrade, Property 18: Budget Termination with Reason
    **Validates: Requirements 7.2**

    When any budget limit is exceeded, execution must terminate and
    BudgetStatus.termination_reason must clearly identify which dimension was exceeded.
    The termination_reason must be a non-empty string.
    """
    guard = BudgetGuard(max_steps=10, max_tokens=1_000, max_repair_attempts=3)

    if dimension == "tokens":
        guard._tokens_used = 1_000  # at limit; estimated_cost will exceed remaining
        with pytest.raises(BudgetExceededError) as exc_info:
            guard.check_pre_call(extra, extra)
        err = exc_info.value
    elif dimension == "steps":
        guard._steps_used = 10  # at limit
        with pytest.raises(BudgetExceededError) as exc_info:
            guard.check_pre_call(1, 1)
        err = exc_info.value
    else:  # repairs
        guard._repairs_used = 3  # at limit
        with pytest.raises(BudgetExceededError) as exc_info:
            guard.check_pre_call(1, 1)
        err = exc_info.value

    # termination_reason must be a non-empty string
    assert isinstance(err.termination_reason, str)
    assert len(err.termination_reason) > 0

    # dimension field must match what was exceeded
    assert err.dimension == dimension

    # get_status must also reflect the termination reason
    status = guard.get_status()
    assert status.termination_reason is not None
    assert len(status.termination_reason) > 0


@given(
    token_counts=st.lists(
        st.integers(min_value=0, max_value=5_000),
        min_size=1,
        max_size=20,
    )
)
@settings(max_examples=100)
def test_token_accumulation_additivity(token_counts: list[int]) -> None:
    """
    # Feature: antigravity-architecture-upgrade, Property 19: Token Accumulation Additivity
    **Validates: Requirements 7.3**

    For any sequence of n LLM calls with token counts [t1, t2, ..., tn],
    BudgetGuard._tokens_used after all calls must equal sum(ti).
    Token tracking must be additive and lossless.
    """
    guard = BudgetGuard(max_tokens=10_000_000)  # large enough to never trigger budget
    for t in token_counts:
        guard.record_call(t)
    assert guard._tokens_used == sum(token_counts)
