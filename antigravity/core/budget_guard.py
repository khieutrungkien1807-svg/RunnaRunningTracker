"""
BudgetGuard — Execution budget enforcement for Antigravity Orchestrator.

Enforces limits on steps, tokens, and repair attempts BEFORE each LLM call.
Requirements: 7.1–7.8
"""

from __future__ import annotations

import logging

from core.schemas import BudgetStatus

logger = logging.getLogger(__name__)

_WARN_THRESHOLD = 0.80  # 80%


class BudgetExceededError(Exception):
    """Raised by BudgetGuard.check_pre_call() when a budget limit is exceeded."""

    def __init__(self, termination_reason: str, dimension: str) -> None:
        super().__init__(termination_reason)
        self.termination_reason: str = termination_reason
        self.dimension: str = dimension  # "steps", "tokens", or "repairs"


class BudgetGuard:
    """
    Enforce execution budget BEFORE each LLM call.

    Tracks steps, tokens, and repair attempts. Raises BudgetExceededError
    pre-emptively when a call would exceed the configured limits.
    """

    def __init__(
        self,
        max_steps: int = 50,
        max_tokens: int = 100_000,
        max_repair_attempts: int = 5,
    ) -> None:
        self._max_steps = max_steps
        self._max_tokens = max_tokens
        self._max_repair_attempts = max_repair_attempts

        self._steps_used: int = 0
        self._tokens_used: int = 0
        self._repairs_used: int = 0

        self._terminated: bool = False
        self._termination_reason: str | None = None

    # ── Public API ────────────────────────────────────────────────────────────

    def check_pre_call(
        self,
        estimated_input_tokens: int,
        max_expected_output_tokens: int,
    ) -> None:
        """
        Raise BudgetExceededError if any budget limit would be exceeded.

        Checks (in order):
        1. Token budget: remaining < estimated_cost
        2. Step budget: steps_used >= max_steps
        3. Repair budget: repairs_used >= max_repair_attempts
        """
        estimated_cost = estimated_input_tokens + max_expected_output_tokens
        remaining = self._max_tokens - self._tokens_used

        if remaining < estimated_cost:
            reason = (
                f"Token budget exceeded: {self._tokens_used} used, "
                f"{remaining} remaining, {estimated_cost} estimated cost"
            )
            self._terminated = True
            self._termination_reason = reason
            raise BudgetExceededError(reason, "tokens")

        if self._steps_used >= self._max_steps:
            reason = (
                f"Step budget exceeded: {self._steps_used}/{self._max_steps} steps used"
            )
            self._terminated = True
            self._termination_reason = reason
            raise BudgetExceededError(reason, "steps")

        if self._repairs_used >= self._max_repair_attempts:
            reason = (
                f"Repair budget exceeded: {self._repairs_used}/{self._max_repair_attempts} "
                "repair attempts used"
            )
            self._terminated = True
            self._termination_reason = reason
            raise BudgetExceededError(reason, "repairs")

        self._warn_if_approaching()

    def record_call(self, actual_tokens: int) -> None:
        """Accumulate token usage after a successful LLM call."""
        self._tokens_used += actual_tokens
        self._warn_if_approaching()

    def record_step(self) -> None:
        """Increment the step counter."""
        self._steps_used += 1
        self._warn_if_approaching()

    def record_repair(self) -> None:
        """Increment the repair attempt counter."""
        self._repairs_used += 1
        self._warn_if_approaching()

    def get_status(self) -> BudgetStatus:
        """Return a snapshot of current budget usage."""
        any_warning = (
            self._steps_used / self._max_steps >= _WARN_THRESHOLD
            or self._tokens_used / self._max_tokens >= _WARN_THRESHOLD
            or self._repairs_used / self._max_repair_attempts >= _WARN_THRESHOLD
        )
        return BudgetStatus(
            steps_used=self._steps_used,
            steps_remaining=max(0, self._max_steps - self._steps_used),
            tokens_used=self._tokens_used,
            tokens_remaining=max(0, self._max_tokens - self._tokens_used),
            repairs_used=self._repairs_used,
            repairs_remaining=max(0, self._max_repair_attempts - self._repairs_used),
            warning_threshold_reached=any_warning,
            termination_reason=self._termination_reason,
        )

    def finalize(self) -> None:
        """Mark session as complete and log final usage stats."""
        logger.info(
            "BudgetGuard finalized: steps=%d/%d, tokens=%d/%d, repairs=%d/%d",
            self._steps_used,
            self._max_steps,
            self._tokens_used,
            self._max_tokens,
            self._repairs_used,
            self._max_repair_attempts,
        )

    # ── Internal ──────────────────────────────────────────────────────────────

    def _warn_if_approaching(self) -> None:
        """Log a WARNING if any dimension is at or above 80% of its limit."""
        checks = [
            ("steps", self._steps_used, self._max_steps),
            ("tokens", self._tokens_used, self._max_tokens),
            ("repairs", self._repairs_used, self._max_repair_attempts),
        ]
        for dimension, used, max_val in checks:
            if max_val > 0:
                pct = used / max_val
                if pct >= _WARN_THRESHOLD:
                    logger.warning(
                        "BudgetGuard WARNING: %s at %.0f%% (%d/%d)",
                        dimension,
                        pct * 100,
                        used,
                        max_val,
                    )
