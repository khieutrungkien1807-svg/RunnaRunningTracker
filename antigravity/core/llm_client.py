import time
import os
from pydantic import BaseModel, ValidationError

try:
    import instructor
    from openai import OpenAI
    # Use the new import path for instructor exceptions
    try:
        from instructor.core import InstructorRetryException
    except ImportError:
        # Fallback to old path if new one doesn't exist
        from instructor.exceptions import InstructorRetryException
except ImportError:
    instructor = None
    OpenAI = None
    InstructorRetryException = Exception

class LLMClient:
    """Adapter API (Phase 1). Centralizes all model calls, tracing, and structured output."""
    
    # Reasoning models configuration (Task 6.1)
    REASONING_MODELS = {
        "o1-mini": {
            "provider": "openai",
            "supports_structured": False,  # o1 models don't support structured output yet
            "cost_multiplier": 3.0,  # Approximate cost vs GPT-4
        },
        "o3-mini": {
            "provider": "openai",
            "supports_structured": False,
            "cost_multiplier": 3.5,
        },
    }
    
    def __init__(self, tracer, provider_client=None):
        self.tracer = tracer
        if provider_client:
            self.client = provider_client
        elif instructor and OpenAI:
            # Fallback to default OpenAI setup mapped through Instructor
            self.client = instructor.from_openai(OpenAI())
        else:
            self.client = None
            print("[LLM_CLIENT] Warning: openai or instructor package not found.")
        
        # Prefix caching support (Requirement 5)
        self._static_prefix: str | None = None
        self._static_prefix_set_count: int = 0
        
        # Cost tracking for reasoning models (Task 6.3)
        self._reasoning_model_usage = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_cost_units": 0.0,
        }

    def set_static_prefix(self, content: str) -> None:
        """
        Set the static prefix for prompt caching (Requirement 5.5).
        
        The static prefix (CONSTITUTION + MASTER_ROUTER) is loaded once at initialization
        and reused across all calls in the session. This enables Anthropic/OpenAI prompt caching.
        
        Args:
            content: Static content to be cached (CONSTITUTION, MASTER_ROUTER, etc.)
        
        Validates: Requirements 5.1, 5.2, 5.5, 5.6, 5.7
        """
        if self._static_prefix is not None and self._static_prefix != content:
            # Log WARNING if static_prefix changes after first set (cache invalidation)
            print(f"[LLM_CLIENT] WARNING: static_prefix changed after initialization. "
                  f"This will invalidate the prompt cache. (Requirement 5.7)")
        
        self._static_prefix = content
        self._static_prefix_set_count += 1

    def _build_system_prompt(self, dynamic_suffix: str) -> str | list:
        """
        Build system prompt by combining static_prefix + dynamic_suffix (Requirement 5.2).
        
        For Anthropic API: returns a list with cache_control annotation on static_prefix block.
        For OpenAI-compatible API: returns a single string (automatic prefix caching).
        
        Args:
            dynamic_suffix: Task-specific dynamic content
            
        Returns:
            str for OpenAI-compatible, or list for Anthropic with cache_control
            
        Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.8
        """
        if self._static_prefix is None:
            # No static prefix set, return dynamic_suffix only
            return dynamic_suffix
        
        # Detect provider type from client
        provider = self._detect_provider()
        
        if provider == "anthropic":
            # Anthropic: use cache_control annotation (Requirement 5.3)
            return [
                {
                    "type": "text",
                    "text": self._static_prefix,
                    "cache_control": {"type": "ephemeral"}
                },
                {
                    "type": "text",
                    "text": dynamic_suffix
                }
            ]
        else:
            # OpenAI-compatible: concatenate as single string (Requirement 5.4)
            # OpenAI automatic prefix caching doesn't require explicit annotation
            return f"{self._static_prefix}\n\n{dynamic_suffix}"

    def _detect_provider(self) -> str:
        """
        Detect LLM provider type from client configuration.
        
        Returns:
            "anthropic", "openai", or "unknown"
        """
        if not self.client:
            return "unknown"
        
        # Check for Anthropic client - check both class name and type string
        client_class_name = self.client.__class__.__name__
        client_str = str(type(self.client)).lower()
        
        if "anthropic" in client_class_name.lower() or "anthropic" in client_str:
            return "anthropic"
        elif "openai" in client_class_name.lower() or "openai" in client_str:
            return "openai"
        
        # Check base_url for Anthropic endpoint
        if hasattr(self.client, "base_url"):
            base_url = str(getattr(self.client, "base_url", "")).lower()
            if "anthropic" in base_url:
                return "anthropic"
        
        # Default to OpenAI-compatible
        return "openai"

    def _get_token_usage(self, response):
        """Safely extract tokens to avoid crashes."""
        usage = getattr(response, "usage", None)
        if not usage:
            return None, None
        return getattr(usage, "prompt_tokens", None), getattr(usage, "completion_tokens", None)

    def is_reasoning_model(self, model: str) -> bool:
        """
        Check if a model is a reasoning model (o1-mini, o3-mini).
        
        Args:
            model: Model name
            
        Returns:
            True if model is a reasoning model
            
        Validates: Task 6.1
        """
        return model in self.REASONING_MODELS
    
    def get_reasoning_model_cost_multiplier(self, model: str) -> float:
        """
        Get cost multiplier for reasoning model.
        
        Args:
            model: Model name
            
        Returns:
            Cost multiplier (default 1.0 for non-reasoning models)
            
        Validates: Task 6.3
        """
        if model in self.REASONING_MODELS:
            return self.REASONING_MODELS[model]["cost_multiplier"]
        return 1.0
    
    def get_reasoning_model_usage(self) -> dict:
        """
        Get usage statistics for reasoning models.
        
        Returns:
            Dictionary with total_calls, total_tokens, total_cost_units
            
        Validates: Task 6.3
        """
        return self._reasoning_model_usage.copy()
    
    def _track_reasoning_model_usage(self, model: str, in_tokens: int | None, out_tokens: int | None):
        """
        Track usage for reasoning models.
        
        Args:
            model: Model name
            in_tokens: Input tokens
            out_tokens: Output tokens
            
        Validates: Task 6.3
        """
        if not self.is_reasoning_model(model):
            return
        
        self._reasoning_model_usage["total_calls"] += 1
        
        if in_tokens:
            self._reasoning_model_usage["total_tokens"] += in_tokens
        if out_tokens:
            self._reasoning_model_usage["total_tokens"] += out_tokens
        
        # Calculate cost units (tokens * multiplier)
        cost_multiplier = self.get_reasoning_model_cost_multiplier(model)
        total_tokens = (in_tokens or 0) + (out_tokens or 0)
        self._reasoning_model_usage["total_cost_units"] += total_tokens * cost_multiplier

    def generate_text(self, task_name: str, model: str, system: str, messages: list, **kwargs) -> str:
        """Freeform text generation block with 429 backoff."""
        start = time.perf_counter()
        
        if not self.client:
            return "[Placeholder generated code / response]"

        for attempt in range(3):
            try:
                # Build system prompt with prefix caching support (Requirement 5.1, 5.2)
                system_prompt = self._build_system_prompt(system)
                full_messages = [{"role": "system", "content": system_prompt}] + messages
                response = self.client.chat.completions.create(
                    model=model,
                    messages=full_messages,
                    **kwargs
                )
                text_result = response.choices[0].message.content
                latency_ms = (time.perf_counter() - start) * 1000
                
                in_tokens, out_tokens = self._get_token_usage(response)
                
                # Track reasoning model usage (Task 6.3)
                self._track_reasoning_model_usage(model, in_tokens, out_tokens)
                
                if hasattr(self.tracer, "log_generation"):
                    self.tracer.log_generation(
                        task_name=task_name,
                        model=model,
                        latency_ms=latency_ms,
                        input_tokens=in_tokens,
                        output_tokens=out_tokens,
                        success=True,
                    )
                return text_result
            except Exception as e:
                err_msg = str(e).lower()
                if ("429" in err_msg or "quota" in err_msg) and attempt < 2:
                    wait_time = (attempt + 1) * 20 # 20s, 40s...
                    print(f"[LLM_CLIENT] Quota hit (429). Backing off for {wait_time}s... (Attempt {attempt+1}/3)")
                    time.sleep(wait_time)
                    continue

                latency_ms = (time.perf_counter() - start) * 1000
                if hasattr(self.tracer, "log_generation"):
                    self.tracer.log_generation(
                        task_name=task_name,
                        model=model,
                        latency_ms=latency_ms,
                        success=False,
                        error=str(e),
                    )
                raise e

    def generate_structured(self, task_name: str, model: str, system: str, messages: list, response_model: type[BaseModel], **kwargs):
        """Schema-enforced structured generation block with 429 backoff."""
        start = time.perf_counter()
        retries = 0
        raw_output = None
        
        if not self.client:
            print(f"[LLM_CLIENT] Fake structured output returned for {response_model.__name__}. Forcing Exception to trigger Fallback.")
            raise Exception("No LLM Provider Configured. Testing Fallback.")

        # Build system prompt with prefix caching support (Requirement 5.1, 5.2)
        dynamic_content = system + f"\n\n**You must respond with valid JSON matching exactly the requested schema.** Return ONLY JSON."
        sys_prompt = self._build_system_prompt(dynamic_content)
        current_messages = [{"role": "system", "content": sys_prompt}] + messages

        for attempt in range(4): # More attempts for structured because of validation
            try:
                # instructor wrapper logic
                raw_output = self.client.chat.completions.create(
                    model=model,
                    response_model=response_model,
                    messages=current_messages,
                    **kwargs
                )
                latency_ms = (time.perf_counter() - start) * 1000
                in_tokens, out_tokens = self._get_token_usage(raw_output._raw_response if hasattr(raw_output, '_raw_response') else raw_output)

                if hasattr(self.tracer, "log_generation"):
                    self.tracer.log_generation(
                        task_name=task_name,
                        model=model,
                        latency_ms=latency_ms,
                        success=True,
                        parse_success=True,
                        retry_count=retries,
                        schema_name=response_model.__name__,
                        input_tokens=in_tokens,
                        output_tokens=out_tokens,
                    )
                return raw_output
            
            except Exception as e: 
                err_msg = str(e).lower()
                # If 429/Quota error, sleep and retry
                if ("429" in err_msg or "quota" in err_msg) and attempt < 3:
                    wait_time = (attempt + 1) * 30 # 30s, 60s, 90s...
                    print(f"[LLM_CLIENT] Quota hit (429). Backing off for {wait_time}s... (Attempt {attempt+1}/4)")
                    time.sleep(wait_time)
                    continue

                retries += 1
                # If Syntax error, retry with prompt nudge (only once)
                if isinstance(e, (ValidationError, ValueError)) and retries == 1:
                    current_messages.append({
                        "role": "user",
                        "content": "Return valid JSON matching the schema exactly. No prose."
                    })
                    continue
                
                latency_ms = (time.perf_counter() - start) * 1000
                if hasattr(self.tracer, "log_generation"):
                    self.tracer.log_generation(
                        task_name=task_name,
                        model=model,
                        latency_ms=latency_ms,
                        success=False,
                        parse_success=False,
                        retry_count=retries,
                        schema_name=response_model.__name__,
                        error=str(e),
                        raw_output=str(raw_output) if raw_output else None,
                    )
                raise e

        raise Exception(f"Failed to generate structured logic for {task_name} after {attempt+1} attempts.")
