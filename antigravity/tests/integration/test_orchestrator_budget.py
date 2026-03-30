"""
Integration test: Budget terminates before LLM call

Validates Requirement 7.7: Budget pre-call enforcement
Task 13.1
"""

import pytest
from pathlib import Path
import sys
import os

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set dummy API key for testing
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key-for-testing")

from scripts.orchestrator import AntigravityOrchestrator
from core.budget_guard import BudgetExceededError


def test_budget_terminates_before_llm_call():
    """
    Test that budget_guard.check_pre_call() is called before LLM call
    and terminates correctly when budget exceeded.
    
    Validates: Requirement 7.7
    """
    # Create orchestrator with very low token budget
    orchestrator = AntigravityOrchestrator()
    orchestrator.budget_guard._max_tokens = 100  # Very low limit
    orchestrator.budget_guard._tokens_used = 50   # Already used half
    
    # Task that would require more tokens than available
    task = {
        "description": "Create a complex React application with authentication, database, and API integration",
        "completion_criteria": {
            "file_exists": "test_output.txt"
        }
    }
    
    # Execute should raise BudgetExceededError or return budget_exceeded status
    result = orchestrator.execute(task)
    
    # Verify budget exceeded
    assert result["status"] == "budget_exceeded"
    assert "reason" in result
    assert "tokens" in result["reason"].lower() or result.get("dimension") == "tokens"
    
    print(f"✅ Budget enforcement test passed: {result['reason']}")


def test_budget_check_prevents_llm_call():
    """
    Test that check_pre_call() prevents LLM call when budget insufficient.
    """
    orchestrator = AntigravityOrchestrator()
    
    # Set budget to nearly exhausted
    orchestrator.budget_guard._max_tokens = 1000
    orchestrator.budget_guard._tokens_used = 950
    
    # Try to make a call that would exceed budget
    with pytest.raises(BudgetExceededError) as exc_info:
        orchestrator.budget_guard.check_pre_call(
            estimated_input_tokens=100,
            max_expected_output_tokens=100
        )
    
    assert "Token budget exceeded" in str(exc_info.value)
    assert exc_info.value.dimension == "tokens"
    
    print("✅ Pre-call budget check test passed")


def test_budget_allows_call_when_sufficient():
    """
    Test that check_pre_call() allows LLM call when budget sufficient.
    """
    orchestrator = AntigravityOrchestrator()
    
    # Set budget with plenty of room
    orchestrator.budget_guard._max_tokens = 10000
    orchestrator.budget_guard._tokens_used = 100
    
    # This should not raise
    orchestrator.budget_guard.check_pre_call(
        estimated_input_tokens=100,
        max_expected_output_tokens=100
    )
    
    print("✅ Sufficient budget test passed")


if __name__ == "__main__":
    test_budget_terminates_before_llm_call()
    test_budget_check_prevents_llm_call()
    test_budget_allows_call_when_sufficient()
    print("\n✅ All budget integration tests passed!")
