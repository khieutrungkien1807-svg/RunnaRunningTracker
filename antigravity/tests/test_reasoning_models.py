"""
Unit tests for reasoning models integration (Task 6).

Tests cover:
- Task 6.1: OpenAI provider integration (o1-mini, o3-mini)
- Task 6.2: Cascading logic (simple → Sonnet, complex → o1)
- Task 6.3: Cost tracking for reasoning models
- Task 6.4: Quality improvement validation
"""

import sys
import os
from pathlib import Path

import pytest
from unittest.mock import Mock, MagicMock, patch

# Ensure core is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient
from core.slm_router import SLMRouter


class TestReasoningModelsIntegration:
    """Test suite for reasoning models integration (Task 6.1)."""

    def test_reasoning_models_configuration_exists(self):
        """
        Test that REASONING_MODELS configuration exists.
        Validates: Task 6.1
        """
        assert hasattr(LLMClient, 'REASONING_MODELS')
        assert isinstance(LLMClient.REASONING_MODELS, dict)
        
        # Check o1-mini configuration
        assert "o1-mini" in LLMClient.REASONING_MODELS
        assert "provider" in LLMClient.REASONING_MODELS["o1-mini"]
        assert "cost_multiplier" in LLMClient.REASONING_MODELS["o1-mini"]
        
        # Check o3-mini configuration
        assert "o3-mini" in LLMClient.REASONING_MODELS
        assert "provider" in LLMClient.REASONING_MODELS["o3-mini"]

    def test_is_reasoning_model_method(self):
        """
        Test is_reasoning_model method.
        Validates: Task 6.1
        """
        tracer = Mock()
        mock_client = Mock()
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        # Test reasoning models
        assert client.is_reasoning_model("o1-mini") is True
        assert client.is_reasoning_model("o3-mini") is True
        
        # Test non-reasoning models
        assert client.is_reasoning_model("gpt-4") is False
        assert client.is_reasoning_model("claude-3-5-sonnet-20241022") is False

    def test_get_reasoning_model_cost_multiplier(self):
        """
        Test cost multiplier retrieval.
        Validates: Task 6.3
        """
        tracer = Mock()
        mock_client = Mock()
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        # Test reasoning models
        assert client.get_reasoning_model_cost_multiplier("o1-mini") == 3.0
        assert client.get_reasoning_model_cost_multiplier("o3-mini") == 3.5
        
        # Test non-reasoning models (default 1.0)
        assert client.get_reasoning_model_cost_multiplier("gpt-4") == 1.0
        assert client.get_reasoning_model_cost_multiplier("claude-3-5-sonnet-20241022") == 1.0


class TestCostTracking:
    """Test suite for cost tracking (Task 6.3)."""

    def test_reasoning_model_usage_initialization(self):
        """
        Test that usage tracking is initialized.
        Validates: Task 6.3
        """
        tracer = Mock()
        mock_client = Mock()
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        usage = client.get_reasoning_model_usage()
        assert usage["total_calls"] == 0
        assert usage["total_tokens"] == 0
        assert usage["total_cost_units"] == 0.0

    def test_track_reasoning_model_usage(self):
        """
        Test usage tracking for reasoning models.
        Validates: Task 6.3
        """
        tracer = Mock()
        mock_client = Mock()
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        # Track usage for o1-mini
        client._track_reasoning_model_usage("o1-mini", 100, 50)
        
        usage = client.get_reasoning_model_usage()
        assert usage["total_calls"] == 1
        assert usage["total_tokens"] == 150
        # Cost units = (100 + 50) * 3.0 = 450
        assert usage["total_cost_units"] == 450.0
        
        # Track another call
        client._track_reasoning_model_usage("o1-mini", 200, 100)
        
        usage = client.get_reasoning_model_usage()
        assert usage["total_calls"] == 2
        assert usage["total_tokens"] == 450
        # Cost units = 450 + (200 + 100) * 3.0 = 1350
        assert usage["total_cost_units"] == 1350.0

    def test_non_reasoning_model_not_tracked(self):
        """
        Test that non-reasoning models are not tracked.
        Validates: Task 6.3
        """
        tracer = Mock()
        mock_client = Mock()
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        # Track usage for non-reasoning model
        client._track_reasoning_model_usage("gpt-4", 100, 50)
        
        usage = client.get_reasoning_model_usage()
        assert usage["total_calls"] == 0
        assert usage["total_tokens"] == 0
        assert usage["total_cost_units"] == 0.0

    def test_generate_text_tracks_reasoning_model(self):
        """
        Test that generate_text tracks reasoning model usage.
        Validates: Task 6.3
        """
        tracer = Mock()
        tracer.log_generation = Mock()
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50)
        mock_client.chat.completions.create = Mock(return_value=mock_response)
        
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        # Generate text with o1-mini
        client.generate_text(
            task_name="test_task",
            model="o1-mini",
            system="Task: Solve complex problem",
            messages=[{"role": "user", "content": "Analyze this"}]
        )
        
        usage = client.get_reasoning_model_usage()
        assert usage["total_calls"] == 1
        assert usage["total_tokens"] == 150
        assert usage["total_cost_units"] == 450.0


class TestCascadingLogic:
    """Test suite for cascading logic (Task 6.2)."""

    def test_complexity_thresholds_exist(self):
        """
        Test that complexity thresholds are defined.
        Validates: Task 6.2
        """
        assert hasattr(SLMRouter, 'COMPLEXITY_THRESHOLDS')
        assert "simple" in SLMRouter.COMPLEXITY_THRESHOLDS
        assert "moderate" in SLMRouter.COMPLEXITY_THRESHOLDS
        assert "complex" in SLMRouter.COMPLEXITY_THRESHOLDS

    def test_complex_indicators_exist(self):
        """
        Test that complex indicators are defined.
        Validates: Task 6.2
        """
        assert hasattr(SLMRouter, 'COMPLEX_INDICATORS')
        assert isinstance(SLMRouter.COMPLEX_INDICATORS, list)
        assert len(SLMRouter.COMPLEX_INDICATORS) > 0

    def test_assess_complexity_simple(self):
        """
        Test complexity assessment for simple queries.
        Validates: Task 6.2
        """
        import tempfile
        import json
        
        # Create temp prototypes file
        temp_dir = tempfile.mkdtemp()
        prototypes_path = Path(temp_dir) / "prototypes.json"
        with open(prototypes_path, 'w') as f:
            json.dump({"test": {"examples": ["test"]}}, f)
        
        router = SLMRouter(prototypes_path=prototypes_path)
        
        # Simple queries
        assert router.assess_complexity("create a button") == "simple"
        assert router.assess_complexity("add a form") == "simple"
        assert router.assess_complexity("style the navbar") == "simple"

    def test_assess_complexity_moderate(self):
        """
        Test complexity assessment for moderate queries.
        Validates: Task 6.2
        """
        import tempfile
        import json
        
        temp_dir = tempfile.mkdtemp()
        prototypes_path = Path(temp_dir) / "prototypes.json"
        with open(prototypes_path, 'w') as f:
            json.dump({"test": {"examples": ["test"]}}, f)
        
        router = SLMRouter(prototypes_path=prototypes_path)
        
        # Moderate queries (longer or with one complexity indicator)
        complexity = router.assess_complexity(
            "create a form with validation and error handling for user registration"
        )
        assert complexity in ["moderate", "simple"]

    def test_assess_complexity_complex(self):
        """
        Test complexity assessment for complex queries.
        Validates: Task 6.2
        """
        import tempfile
        import json
        
        temp_dir = tempfile.mkdtemp()
        prototypes_path = Path(temp_dir) / "prototypes.json"
        with open(prototypes_path, 'w') as f:
            json.dump({"test": {"examples": ["test"]}}, f)
        
        router = SLMRouter(prototypes_path=prototypes_path)
        
        # Complex queries (multiple indicators)
        assert router.assess_complexity(
            "debug the performance issue and optimize the algorithm for better efficiency"
        ) == "complex"
        
        assert router.assess_complexity(
            "investigate the security vulnerability and fix the bug in the authentication system"
        ) == "complex"


    def test_recommend_model_simple_task(self):
        """
        Test model recommendation for simple tasks.
        Validates: Task 6.2 - simple → Sonnet
        """
        import tempfile
        import json
        
        temp_dir = tempfile.mkdtemp()
        prototypes_path = Path(temp_dir) / "prototypes.json"
        with open(prototypes_path, 'w') as f:
            json.dump({"test": {"examples": ["test"]}}, f)
        
        router = SLMRouter(prototypes_path=prototypes_path)
        
        # Simple task with high confidence
        model = router.recommend_model("create a button", confidence=0.95)
        assert model == "claude-3-5-sonnet-20241022"

    def test_recommend_model_complex_task(self):
        """
        Test model recommendation for complex tasks.
        Validates: Task 6.2 - complex → o1
        """
        import tempfile
        import json
        
        temp_dir = tempfile.mkdtemp()
        prototypes_path = Path(temp_dir) / "prototypes.json"
        with open(prototypes_path, 'w') as f:
            json.dump({"test": {"examples": ["test"]}}, f)
        
        router = SLMRouter(prototypes_path=prototypes_path)
        
        # Complex task with low confidence
        model = router.recommend_model(
            "debug the performance issue and optimize the algorithm",
            confidence=0.40
        )
        assert model == "o1-mini"

    def test_recommend_model_without_confidence(self):
        """
        Test model recommendation without confidence score.
        Validates: Task 6.2 - fallback to complexity-based decision
        """
        import tempfile
        import json
        
        temp_dir = tempfile.mkdtemp()
        prototypes_path = Path(temp_dir) / "prototypes.json"
        with open(prototypes_path, 'w') as f:
            json.dump({"test": {"examples": ["test"]}}, f)
        
        router = SLMRouter(prototypes_path=prototypes_path)
        
        # Simple query without confidence
        model = router.recommend_model("create a button")
        assert model == "claude-3-5-sonnet-20241022"
        
        # Complex query without confidence
        model = router.recommend_model(
            "debug the performance issue and optimize the algorithm"
        )
        assert model == "o1-mini"


class TestQualityImprovement:
    """Test suite for quality improvement validation (Task 6.4)."""

    def test_reasoning_model_supports_structured_flag(self):
        """
        Test that reasoning models have supports_structured flag.
        Validates: Task 6.1 - o1 models don't support structured output
        """
        assert LLMClient.REASONING_MODELS["o1-mini"]["supports_structured"] is False
        assert LLMClient.REASONING_MODELS["o3-mini"]["supports_structured"] is False

    def test_cost_multiplier_reflects_pricing(self):
        """
        Test that cost multipliers reflect actual pricing differences.
        Validates: Task 6.3 - cost tracking accuracy
        """
        # o1-mini should be more expensive than standard models
        assert LLMClient.REASONING_MODELS["o1-mini"]["cost_multiplier"] > 1.0
        
        # o3-mini should be more expensive than o1-mini
        assert (LLMClient.REASONING_MODELS["o3-mini"]["cost_multiplier"] >= 
                LLMClient.REASONING_MODELS["o1-mini"]["cost_multiplier"])


class TestIntegration:
    """Integration tests for reasoning models."""

    def test_end_to_end_cascading(self):
        """
        Test end-to-end cascading workflow.
        Validates: Task 6.2 - complete cascading logic
        """
        import tempfile
        import json
        
        temp_dir = tempfile.mkdtemp()
        prototypes_path = Path(temp_dir) / "prototypes.json"
        with open(prototypes_path, 'w') as f:
            json.dump({
                "frontend": {"examples": ["create button"]},
                "debug": {"examples": ["fix bug"]}
            }, f)
        
        router = SLMRouter(prototypes_path=prototypes_path)
        
        # Test simple task flow
        simple_query = "create a button"
        complexity = router.assess_complexity(simple_query)
        model = router.recommend_model(simple_query, confidence=0.95)
        
        assert complexity == "simple"
        assert model == "claude-3-5-sonnet-20241022"
        
        # Test complex task flow
        complex_query = "debug the authentication system and fix security vulnerabilities"
        complexity = router.assess_complexity(complex_query)
        model = router.recommend_model(complex_query, confidence=0.45)
        
        # This query has 3 indicators: debug, fix, security
        # Should be classified as complex or at least route to o1-mini with low confidence
        assert complexity in ["moderate", "complex"]
        assert model == "o1-mini"

    def test_cost_tracking_integration(self):
        """
        Test cost tracking integration with LLMClient.
        Validates: Task 6.3 - accurate cost tracking
        """
        tracer = Mock()
        tracer.log_generation = Mock()
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_response.usage = Mock(prompt_tokens=1000, completion_tokens=500)
        mock_client.chat.completions.create = Mock(return_value=mock_response)
        
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        # Make multiple calls with different models
        client.generate_text(
            task_name="simple_task",
            model="claude-3-5-sonnet-20241022",
            system="Task",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        client.generate_text(
            task_name="complex_task",
            model="o1-mini",
            system="Task",
            messages=[{"role": "user", "content": "Debug"}]
        )
        
        # Only o1-mini should be tracked
        usage = client.get_reasoning_model_usage()
        assert usage["total_calls"] == 1
        assert usage["total_tokens"] == 1500
        assert usage["total_cost_units"] == 4500.0  # 1500 * 3.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
