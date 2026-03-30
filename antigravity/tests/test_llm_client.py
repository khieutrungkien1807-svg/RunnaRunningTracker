"""
Unit tests for LLMClient prefix caching functionality.

Tests cover Requirements 5.1-5.8 from the Antigravity Architecture Upgrade spec.
"""

import sys
import os
from pathlib import Path

import pytest
from unittest.mock import Mock, MagicMock, patch
from pydantic import BaseModel

# Ensure core is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient


class SampleResponse(BaseModel):
    """Sample Pydantic model for testing structured generation."""
    result: str
    confidence: float


class TestLLMClientPrefixCaching:
    """Test suite for LLMClient prefix caching (Task 10)."""

    def test_set_static_prefix_method_exists(self):
        """
        Test that set_static_prefix method exists and is callable.
        Validates: Requirement 5.5
        """
        tracer = Mock()
        mock_client = Mock()
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        assert hasattr(client, 'set_static_prefix')
        assert callable(client.set_static_prefix)

    def test_set_static_prefix_stores_content(self):
        """
        Test that set_static_prefix stores the provided content.
        Validates: Requirement 5.5, 5.6
        """
        tracer = Mock()
        mock_client = Mock()
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        static_content = "CONSTITUTION: Always be helpful.\nMASTER_ROUTER: Route tasks efficiently."
        client.set_static_prefix(static_content)
        
        assert client._static_prefix == static_content
        assert client._static_prefix_set_count == 1

    def test_set_static_prefix_warns_on_change(self, capsys):
        """
        Test that changing static_prefix after first set logs a warning.
        Validates: Requirement 5.7
        """
        tracer = Mock()
        mock_client = Mock()
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        # First set
        client.set_static_prefix("Original prefix")
        
        # Second set with different content - should warn
        client.set_static_prefix("Changed prefix")
        
        captured = capsys.readouterr()
        assert "WARNING" in captured.out
        assert "static_prefix changed" in captured.out
        assert "invalidate the prompt cache" in captured.out
        assert client._static_prefix_set_count == 2

    def test_set_static_prefix_no_warn_on_same_content(self, capsys):
        """
        Test that setting the same static_prefix multiple times doesn't warn.
        Validates: Requirement 5.7
        """
        tracer = Mock()
        mock_client = Mock()
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        content = "Same prefix"
        client.set_static_prefix(content)
        client.set_static_prefix(content)  # Same content
        
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out

    def test_build_system_prompt_without_prefix(self):
        """
        Test that _build_system_prompt returns dynamic_suffix when no prefix is set.
        Validates: Requirement 5.2
        """
        tracer = Mock()
        mock_client = Mock()
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        dynamic_suffix = "Task: Fix the bug in module X"
        result = client._build_system_prompt(dynamic_suffix)
        
        assert result == dynamic_suffix

    def test_build_system_prompt_with_prefix_openai(self):
        """
        Test that _build_system_prompt concatenates prefix + suffix for OpenAI.
        Validates: Requirement 5.1, 5.2, 5.4
        """
        tracer = Mock()
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_client.__class__.__name__ = "OpenAI"
        
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        static_prefix = "CONSTITUTION: Be helpful."
        dynamic_suffix = "Task: Write code"
        
        client.set_static_prefix(static_prefix)
        result = client._build_system_prompt(dynamic_suffix)
        
        # For OpenAI, should be concatenated string
        assert isinstance(result, str)
        assert static_prefix in result
        assert dynamic_suffix in result
        assert result == f"{static_prefix}\n\n{dynamic_suffix}"

    def test_build_system_prompt_with_prefix_anthropic(self):
        """
        Test that _build_system_prompt returns list with cache_control for Anthropic.
        Validates: Requirement 5.1, 5.2, 5.3
        """
        tracer = Mock()
        
        # Mock Anthropic client
        mock_client = Mock()
        mock_client.__class__.__name__ = "Anthropic"
        
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        static_prefix = "CONSTITUTION: Be helpful."
        dynamic_suffix = "Task: Write code"
        
        client.set_static_prefix(static_prefix)
        result = client._build_system_prompt(dynamic_suffix)
        
        # For Anthropic, should be list with cache_control
        assert isinstance(result, list)
        assert len(result) == 2
        
        # First block: static prefix with cache_control
        assert result[0]["type"] == "text"
        assert result[0]["text"] == static_prefix
        assert result[0]["cache_control"] == {"type": "ephemeral"}
        
        # Second block: dynamic suffix
        assert result[1]["type"] == "text"
        assert result[1]["text"] == dynamic_suffix

    def test_detect_provider_anthropic(self):
        """Test provider detection for Anthropic client."""
        tracer = Mock()
        mock_client = Mock()
        mock_client.__class__.__name__ = "Anthropic"
        
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        assert client._detect_provider() == "anthropic"

    def test_detect_provider_openai(self):
        """Test provider detection for OpenAI client."""
        tracer = Mock()
        mock_client = Mock()
        mock_client.__class__.__name__ = "OpenAI"
        
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        assert client._detect_provider() == "openai"

    def test_detect_provider_unknown(self):
        """Test provider detection defaults to openai for unknown clients."""
        tracer = Mock()
        mock_client = Mock()
        mock_client.__class__.__name__ = "CustomClient"
        
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        assert client._detect_provider() == "openai"

    def test_detect_provider_no_client(self):
        """Test provider detection when no client is configured."""
        tracer = Mock()
        mock_client = Mock()
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        client.client = None  # Simulate no client
        
        assert client._detect_provider() == "unknown"

    def test_generate_text_uses_prefix_caching(self):
        """
        Test that generate_text uses _build_system_prompt for prefix caching.
        Validates: Requirement 5.1, 5.2, 5.6
        """
        tracer = Mock()
        tracer.log_generation = Mock()
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Generated text"))]
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50)
        mock_client.chat.completions.create = Mock(return_value=mock_response)
        
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        # Set static prefix
        static_prefix = "CONSTITUTION: Be helpful."
        client.set_static_prefix(static_prefix)
        
        # Generate text
        result = client.generate_text(
            task_name="test_task",
            model="gpt-4",
            system="Task: Write code",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        # Verify result
        assert result == "Generated text"
        
        # Verify that the system message includes the prefix
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        system_message = messages[0]
        
        assert system_message["role"] == "system"
        assert static_prefix in system_message["content"]

    def test_generate_structured_uses_prefix_caching(self):
        """
        Test that generate_structured uses _build_system_prompt for prefix caching.
        Validates: Requirement 5.1, 5.2, 5.6
        """
        tracer = Mock()
        tracer.log_generation = Mock()
        
        # Mock OpenAI client with instructor wrapper
        mock_client = Mock()
        mock_response = SampleResponse(result="success", confidence=0.95)
        mock_response._raw_response = Mock(usage=Mock(prompt_tokens=100, completion_tokens=50))
        mock_client.chat.completions.create = Mock(return_value=mock_response)
        
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        # Set static prefix
        static_prefix = "CONSTITUTION: Be helpful."
        client.set_static_prefix(static_prefix)
        
        # Generate structured
        result = client.generate_structured(
            task_name="test_task",
            model="gpt-4",
            system="Task: Analyze data",
            messages=[{"role": "user", "content": "Analyze this"}],
            response_model=SampleResponse
        )
        
        # Verify result
        assert isinstance(result, SampleResponse)
        assert result.result == "success"
        
        # Verify that the system message includes the prefix
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        system_message = messages[0]
        
        assert system_message["role"] == "system"
        assert static_prefix in system_message["content"]

    def test_static_prefix_invariant_across_calls(self):
        """
        Test that static_prefix remains identical across multiple calls in same session.
        Validates: Requirement 5.8 - Property 15: Static Prefix Invariant
        """
        tracer = Mock()
        tracer.log_generation = Mock()
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50)
        mock_client.chat.completions.create = Mock(return_value=mock_response)
        
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        # Set static prefix once
        static_prefix = "CONSTITUTION: Be helpful.\nMASTER_ROUTER: Route efficiently."
        client.set_static_prefix(static_prefix)
        
        # Make multiple calls with different dynamic content
        client.generate_text(
            task_name="task1",
            model="gpt-4",
            system="Task 1: Fix bug",
            messages=[{"role": "user", "content": "Fix this"}]
        )
        
        client.generate_text(
            task_name="task2",
            model="gpt-4",
            system="Task 2: Write tests",
            messages=[{"role": "user", "content": "Test this"}]
        )
        
        # Verify both calls used the same static prefix
        calls = mock_client.chat.completions.create.call_args_list
        assert len(calls) == 2
        
        system_msg_1 = calls[0][1]["messages"][0]["content"]
        system_msg_2 = calls[1][1]["messages"][0]["content"]
        
        # Both should start with the same static prefix
        assert system_msg_1.startswith(static_prefix)
        assert system_msg_2.startswith(static_prefix)

    def test_prefix_caching_backward_compatible(self):
        """
        Test that LLMClient works without setting static_prefix (backward compatible).
        Validates: Requirement 5.6
        """
        tracer = Mock()
        tracer.log_generation = Mock()
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50)
        mock_client.chat.completions.create = Mock(return_value=mock_response)
        
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        # Don't set static_prefix - should still work
        result = client.generate_text(
            task_name="test_task",
            model="gpt-4",
            system="Task: Write code",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        assert result == "Response"
        
        # Verify system message is just the dynamic content
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        system_message = messages[0]
        
        assert system_message["role"] == "system"
        assert system_message["content"] == "Task: Write code"


class TestLLMClientPrefixCachingIntegration:
    """Integration tests for prefix caching with real-world scenarios."""

    def test_constitution_and_master_router_caching(self):
        """
        Test realistic scenario: caching CONSTITUTION + MASTER_ROUTER content.
        Validates: Requirements 5.1, 5.2, 5.6
        """
        tracer = Mock()
        tracer.log_generation = Mock()
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Task routed"))]
        mock_response.usage = Mock(prompt_tokens=1000, completion_tokens=100)
        mock_client.chat.completions.create = Mock(return_value=mock_response)
        
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        # Simulate loading CONSTITUTION and MASTER_ROUTER at initialization
        constitution = """
        CONSTITUTION:
        1. Always prioritize user safety
        2. Write secure, tested code
        3. Follow best practices
        """
        
        master_router = """
        MASTER_ROUTER:
        - Frontend tasks → React/TypeScript skills
        - Backend tasks → Python/API skills
        - Debug tasks → Systematic debugging protocol
        """
        
        static_content = f"{constitution}\n\n{master_router}"
        client.set_static_prefix(static_content)
        
        # Make multiple calls - static content should be reused
        for i in range(3):
            client.generate_text(
                task_name=f"task_{i}",
                model="gpt-4",
                system=f"Dynamic task {i}: Implement feature X",
                messages=[{"role": "user", "content": f"Request {i}"}]
            )
        
        # Verify all calls included the static prefix
        calls = mock_client.chat.completions.create.call_args_list
        assert len(calls) == 3
        
        for call in calls:
            system_msg = call[1]["messages"][0]["content"]
            assert constitution.strip() in system_msg
            assert master_router.strip() in system_msg

    def test_cache_invalidation_warning_scenario(self, capsys):
        """
        Test that cache invalidation warning appears in realistic scenario.
        Validates: Requirement 5.7
        """
        tracer = Mock()
        mock_client = Mock()
        client = LLMClient(tracer=tracer, provider_client=mock_client)
        
        # Initial setup with CONSTITUTION
        client.set_static_prefix("CONSTITUTION v1")
        
        # Later, someone tries to update it (bad practice)
        client.set_static_prefix("CONSTITUTION v2 - UPDATED")
        
        captured = capsys.readouterr()
        assert "WARNING" in captured.out
        assert "invalidate the prompt cache" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
