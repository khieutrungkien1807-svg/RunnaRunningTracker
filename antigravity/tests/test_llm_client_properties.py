"""
Property-based tests for LLMClient prefix caching functionality.

Uses Hypothesis to verify universal properties across all valid inputs.
Tests cover Property 15: Static Prefix Invariant (Requirements 5.6, 5.8).
"""

import sys
import os
from pathlib import Path

import pytest
from unittest.mock import Mock
from hypothesis import given, settings, strategies as st
from pydantic import BaseModel

# Ensure core is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient


class SampleResponse(BaseModel):
    """Sample Pydantic model for testing."""
    result: str


# Feature: antigravity-architecture-upgrade, Property 15: Static Prefix Invariant
@given(
    static_prefix=st.text(min_size=10, max_size=1000),
    dynamic_suffix_1=st.text(min_size=5, max_size=500),
    dynamic_suffix_2=st.text(min_size=5, max_size=500),
)
@settings(max_examples=100)
def test_static_prefix_invariant_property(static_prefix, dynamic_suffix_1, dynamic_suffix_2):
    """
    Property 15: Static Prefix Invariant
    
    For any two LLM calls c1 and c2 in the same session with the same static_prefix,
    the prefix portion in the system message of both calls must be identical (byte-for-byte).
    Dynamic suffix can differ.
    
    Validates: Requirements 5.6, 5.8
    """
    tracer = Mock()
    tracer.log_generation = Mock()
    
    # Mock OpenAI client
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Response"))]
    mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50)
    mock_client.chat.completions.create = Mock(return_value=mock_response)
    mock_client.__class__.__name__ = "OpenAI"
    
    client = LLMClient(tracer=tracer, provider_client=mock_client)
    
    # Set static prefix once (simulating session initialization)
    client.set_static_prefix(static_prefix)
    
    # Make two calls with different dynamic content
    client.generate_text(
        task_name="task1",
        model="gpt-4",
        system=dynamic_suffix_1,
        messages=[{"role": "user", "content": "Request 1"}]
    )
    
    client.generate_text(
        task_name="task2",
        model="gpt-4",
        system=dynamic_suffix_2,
        messages=[{"role": "user", "content": "Request 2"}]
    )
    
    # Extract system messages from both calls
    calls = mock_client.chat.completions.create.call_args_list
    assert len(calls) == 2
    
    system_msg_1 = calls[0][1]["messages"][0]["content"]
    system_msg_2 = calls[1][1]["messages"][0]["content"]
    
    # Property: Both system messages must start with the same static prefix (byte-for-byte)
    assert system_msg_1.startswith(static_prefix), \
        "First call must include static prefix"
    assert system_msg_2.startswith(static_prefix), \
        "Second call must include static prefix"
    
    # Extract prefix portions (everything before the dynamic suffix)
    prefix_1 = system_msg_1[:len(static_prefix)]
    prefix_2 = system_msg_2[:len(static_prefix)]
    
    # Invariant: Prefix portions must be identical byte-for-byte
    assert prefix_1 == prefix_2 == static_prefix, \
        "Static prefix must be identical across all calls in the same session"
    
    # Verify dynamic suffixes are different (to ensure we're testing the right thing)
    if dynamic_suffix_1 != dynamic_suffix_2:
        assert system_msg_1 != system_msg_2, \
            "System messages should differ when dynamic suffixes differ"


# Feature: antigravity-architecture-upgrade, Property 15: Static Prefix Invariant (Anthropic variant)
@given(
    static_prefix=st.text(min_size=10, max_size=1000),
    dynamic_suffix_1=st.text(min_size=5, max_size=500),
    dynamic_suffix_2=st.text(min_size=5, max_size=500),
)
@settings(max_examples=100)
def test_static_prefix_invariant_anthropic_property(static_prefix, dynamic_suffix_1, dynamic_suffix_2):
    """
    Property 15: Static Prefix Invariant (Anthropic variant)
    
    For Anthropic API, verify that the static prefix block with cache_control annotation
    remains identical across multiple calls in the same session.
    
    Validates: Requirements 5.3, 5.6, 5.8
    """
    tracer = Mock()
    tracer.log_generation = Mock()
    
    # Mock Anthropic client
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Response"))]
    mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50)
    mock_client.chat.completions.create = Mock(return_value=mock_response)
    mock_client.__class__.__name__ = "Anthropic"
    
    client = LLMClient(tracer=tracer, provider_client=mock_client)
    
    # Set static prefix once
    client.set_static_prefix(static_prefix)
    
    # Make two calls with different dynamic content
    client.generate_text(
        task_name="task1",
        model="claude-3-sonnet",
        system=dynamic_suffix_1,
        messages=[{"role": "user", "content": "Request 1"}]
    )
    
    client.generate_text(
        task_name="task2",
        model="claude-3-sonnet",
        system=dynamic_suffix_2,
        messages=[{"role": "user", "content": "Request 2"}]
    )
    
    # Extract system messages from both calls
    calls = mock_client.chat.completions.create.call_args_list
    assert len(calls) == 2
    
    system_msg_1 = calls[0][1]["messages"][0]["content"]
    system_msg_2 = calls[1][1]["messages"][0]["content"]
    
    # For Anthropic, system message should be a list
    assert isinstance(system_msg_1, list), "Anthropic should use list format"
    assert isinstance(system_msg_2, list), "Anthropic should use list format"
    assert len(system_msg_1) == 2, "Should have 2 blocks: static + dynamic"
    assert len(system_msg_2) == 2, "Should have 2 blocks: static + dynamic"
    
    # Extract static prefix blocks (first block in each)
    static_block_1 = system_msg_1[0]
    static_block_2 = system_msg_2[0]
    
    # Property: Static prefix blocks must be identical (byte-for-byte)
    assert static_block_1 == static_block_2, \
        "Static prefix blocks must be identical across all calls"
    
    # Verify structure of static block
    assert static_block_1["type"] == "text"
    assert static_block_1["text"] == static_prefix
    assert static_block_1["cache_control"] == {"type": "ephemeral"}
    
    # Verify dynamic blocks differ when suffixes differ
    if dynamic_suffix_1 != dynamic_suffix_2:
        assert system_msg_1[1]["text"] != system_msg_2[1]["text"], \
            "Dynamic blocks should differ when suffixes differ"


# Feature: antigravity-architecture-upgrade, Property 15: Static Prefix Invariant (Multiple calls)
@given(
    static_prefix=st.text(min_size=10, max_size=500),
    dynamic_suffixes=st.lists(st.text(min_size=5, max_size=200), min_size=2, max_size=10),
)
@settings(max_examples=50)
def test_static_prefix_invariant_multiple_calls_property(static_prefix, dynamic_suffixes):
    """
    Property 15: Static Prefix Invariant (Multiple calls variant)
    
    For any sequence of N LLM calls in the same session with the same static_prefix,
    all calls must have identical prefix portions in their system messages.
    
    Validates: Requirements 5.6, 5.8
    """
    tracer = Mock()
    tracer.log_generation = Mock()
    
    # Mock OpenAI client
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Response"))]
    mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50)
    mock_client.chat.completions.create = Mock(return_value=mock_response)
    mock_client.__class__.__name__ = "OpenAI"
    
    client = LLMClient(tracer=tracer, provider_client=mock_client)
    
    # Set static prefix once
    client.set_static_prefix(static_prefix)
    
    # Make N calls with different dynamic content
    for i, suffix in enumerate(dynamic_suffixes):
        client.generate_text(
            task_name=f"task_{i}",
            model="gpt-4",
            system=suffix,
            messages=[{"role": "user", "content": f"Request {i}"}]
        )
    
    # Extract all system messages
    calls = mock_client.chat.completions.create.call_args_list
    assert len(calls) == len(dynamic_suffixes)
    
    system_messages = [call[1]["messages"][0]["content"] for call in calls]
    
    # Property: All system messages must start with the same static prefix
    for i, msg in enumerate(system_messages):
        assert msg.startswith(static_prefix), \
            f"Call {i} must include static prefix"
    
    # Extract all prefix portions
    prefixes = [msg[:len(static_prefix)] for msg in system_messages]
    
    # Invariant: All prefix portions must be identical
    assert all(p == static_prefix for p in prefixes), \
        "Static prefix must be identical across all calls in the same session"
    
    # Verify that all prefixes are equal to each other
    assert len(set(prefixes)) == 1, \
        "All prefix portions must be exactly the same"


# Feature: antigravity-architecture-upgrade, Property 15: Static Prefix Invariant (No prefix change)
@given(
    static_prefix=st.text(min_size=10, max_size=500),
    dynamic_suffix=st.text(min_size=5, max_size=200),
    num_calls=st.integers(min_value=2, max_value=20),
)
@settings(max_examples=50)
def test_static_prefix_never_changes_property(static_prefix, dynamic_suffix, num_calls):
    """
    Property 15: Static Prefix Invariant (Immutability variant)
    
    Once set, the static_prefix should never change during the session,
    regardless of how many calls are made.
    
    Validates: Requirements 5.6, 5.7, 5.8
    """
    tracer = Mock()
    tracer.log_generation = Mock()
    
    # Mock OpenAI client
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Response"))]
    mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50)
    mock_client.chat.completions.create = Mock(return_value=mock_response)
    mock_client.__class__.__name__ = "OpenAI"
    
    client = LLMClient(tracer=tracer, provider_client=mock_client)
    
    # Set static prefix once
    client.set_static_prefix(static_prefix)
    
    # Verify internal state
    assert client._static_prefix == static_prefix
    initial_prefix = client._static_prefix
    
    # Make multiple calls
    for i in range(num_calls):
        client.generate_text(
            task_name=f"task_{i}",
            model="gpt-4",
            system=dynamic_suffix,
            messages=[{"role": "user", "content": f"Request {i}"}]
        )
        
        # Property: Static prefix should never change
        assert client._static_prefix == initial_prefix, \
            f"Static prefix changed after call {i}"
        assert client._static_prefix == static_prefix, \
            f"Static prefix no longer matches original value after call {i}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
