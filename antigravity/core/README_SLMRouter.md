# SLMRouter — Intent Classification

## Overview

The SLMRouter classifies user intent using cosine similarity with prototype embeddings to save LLM calls for routing. It operates with <100ms latency on CPU and gracefully degrades if sentence-transformers is unavailable.

## Features

- **Fast Classification**: <100ms latency on CPU using sentence-transformers
- **Configurable Threshold**: Default 0.85 confidence threshold for LLM fallback
- **Hot-Reload**: Update prototypes without restarting the service
- **Graceful Degradation**: Falls back to LLM routing if sentence-transformers unavailable
- **Idempotent**: `classify(x) == classify(classify(x).chosen)`
- **Structured Logging**: JSON-formatted routing decisions for observability

## Requirements

### Optional Dependency

```bash
pip install sentence-transformers
```

If not installed, SLMRouter automatically disables itself and falls through to LLM routing.

## Usage

### Basic Initialization

```python
from pathlib import Path
from core.slm_router import SLMRouter

router = SLMRouter(
    prototypes_path=Path("antigravity/config/slm_prototypes.json"),
    confidence_threshold=0.85,
    embedding_model="all-MiniLM-L6-v2",  # default
)
```

### Classification

```python
from core.schemas import SLMRouteDecision

result = router.classify("create a react component")

if result is not None:
    # High confidence classification
    print(f"Category: {result.chosen}")
    print(f"Confidence: {result.confidence}")
    print(f"Top-K: {result.top_k}")
else:
    # Low confidence - fall through to LLM
    llm_result = llm_client.generate_structured(RouteDecision, query)
```

### Hot-Reload Prototypes

```python
# Update prototypes.json file
# Then reload without restart:
router.reload_prototypes()
```

## Prototypes File Format

```json
{
  "frontend": {
    "examples": [
      "create react component",
      "style button with tailwind",
      "add animation to navbar"
    ]
  },
  "backend": {
    "examples": [
      "create REST API endpoint",
      "add database migration",
      "implement authentication"
    ]
  },
  "debug": {
    "examples": [
      "fix bug in checkout flow",
      "investigate crash",
      "trace error in logs"
    ]
  }
}
```

### With Pre-computed Embeddings

```json
{
  "frontend": {
    "embedding": [0.1, 0.2, 0.3, ...]
  },
  "backend": {
    "embedding": [0.4, 0.5, 0.6, ...]
  }
}
```

## Integration with Orchestrator

```python
# In orchestrator.py

def route_task(self, task: str) -> RouteDecision:
    # Try SLM routing first
    slm_result = self.slm_router.classify(task)

    if slm_result is not None:
        # High confidence - use SLM result
        return RouteDecision(
            domain=slm_result.chosen,
            intent="generate",  # infer from context
            requires_retrieval=True,
            confidence=slm_result.confidence,
            candidate_skills=[],
            reasoning_summary=f"SLM classified as {slm_result.chosen}",
        )
    else:
        # Low confidence - fall through to LLM
        return self.llm_client.generate_structured(
            RouteDecision,
            prompt=f"Classify this task: {task}",
        )
```

## Logging Format

All routing decisions are logged in JSON format:

```json
{
  "chosen": "frontend",
  "confidence": 0.92,
  "top_k": [
    {"label": "frontend", "score": 0.92},
    {"label": "backend", "score": 0.45},
    {"label": "debug", "score": 0.23}
  ]
}
```

## Performance

- **Latency**: <100ms on CPU (tested with all-MiniLM-L6-v2)
- **Model Size**: ~80MB for all-MiniLM-L6-v2
- **Memory**: ~200MB RAM when loaded

## Graceful Degradation

The router handles failures gracefully:

1. **sentence-transformers not installed**: `_enabled=False`, returns `None`
2. **Prototypes file missing**: `_enabled=False`, returns `None`
3. **Model load failure**: `_enabled=False`, returns `None`
4. **Classification error**: Returns `None`, logs error

In all cases, the orchestrator falls back to LLM routing.

## Testing

Run tests:

```bash
pytest antigravity/tests/test_slm_router.py -v
```

Tests cover:
- Graceful degradation (Req 4.6)
- Confidence threshold behavior (Req 4.2, 4.3)
- Hot-reload (Req 4.4)
- Logging format (Req 4.7)
- Idempotence (Req 4.8)

## Requirements Validation

- **4.1**: ✅ Classify using sentence-transformers cosine similarity
- **4.2**: ✅ Return result if confidence >= threshold
- **4.3**: ✅ Return None if confidence < threshold
- **4.4**: ✅ Hot-reload prototypes without restart
- **4.5**: ✅ <100ms latency on CPU
- **4.6**: ✅ Graceful degradation if library unavailable
- **4.7**: ✅ Log routing decisions in JSON format
- **4.8**: ✅ Idempotent classification

## Example Output

```python
>>> router = SLMRouter("prototypes.json", confidence_threshold=0.85)
>>> result = router.classify("create a react component")
>>> print(result)
SLMRouteDecision(
    chosen='frontend',
    confidence=0.94,
    top_k=[
        {'label': 'frontend', 'score': 0.94},
        {'label': 'backend', 'score': 0.32},
        {'label': 'debug', 'score': 0.18}
    ],
    llm_fallback_triggered=False
)
```

## Troubleshooting

### Router always returns None

Check:
1. Is sentence-transformers installed? `pip list | grep sentence-transformers`
2. Does prototypes file exist? Check `prototypes_path`
3. Check logs for initialization errors

### Low classification accuracy

Try:
1. Add more diverse examples to prototypes
2. Lower confidence threshold (e.g., 0.75)
3. Use a larger embedding model (e.g., "all-mpnet-base-v2")

### High latency

Try:
1. Use a smaller model (e.g., "all-MiniLM-L6-v2")
2. Pre-compute embeddings and save in prototypes file
3. Reduce number of prototype categories
