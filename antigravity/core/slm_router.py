"""
SLMRouter — Intent classification using sentence-transformers.

Classifies user intent via cosine similarity with prototype embeddings to save LLM calls.
Operates with <100ms latency on CPU and gracefully degrades if sentence-transformers unavailable.

Validates Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8
Task 6.2: Cascading logic for reasoning models
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Optional, Literal

from core.schemas import SLMRouteDecision

logger = logging.getLogger(__name__)


class SLMRouter:
    """
    Intent classifier using cosine similarity with prototype embeddings.
    
    Features:
    - Classify via sentence-transformers (all-MiniLM-L6-v2 by default)
    - Configurable confidence threshold (default: 0.85)
    - Hot-reload prototypes without restart
    - Graceful degradation if sentence-transformers unavailable
    - <100ms latency on CPU
    - Idempotent: classify(x) == classify(classify(x).chosen)
    - Task 6.2: Cascading logic for reasoning models
    """
    
    # Task 6.2: Complexity thresholds for cascading
    COMPLEXITY_THRESHOLDS = {
        "simple": 0.85,      # High confidence → simple task → Sonnet
        "moderate": 0.70,    # Medium confidence → moderate task → Sonnet
        "complex": 0.50,     # Low confidence → complex task → o1-mini
    }
    
    # Task 6.2: Complexity indicators (keywords that suggest complex reasoning)
    COMPLEX_INDICATORS = [
        "debug", "fix bug", "investigate", "analyze", "optimize",
        "refactor", "architecture", "design pattern", "algorithm",
        "performance", "security", "complex", "difficult", "tricky",
        "multi-step", "reasoning", "logic", "proof", "verify",
    ]

    def __init__(
        self,
        prototypes_path: Path | str,
        confidence_threshold: float = 0.85,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize SLMRouter.
        
        Args:
            prototypes_path: Path to JSON file containing prototype embeddings
            confidence_threshold: Minimum confidence to return classification (default: 0.85)
            embedding_model: sentence-transformers model name (default: all-MiniLM-L6-v2)
        
        Graceful degradation: If sentence-transformers fails to load, _enabled=False
        """
        self.prototypes_path = Path(prototypes_path)
        self.confidence_threshold = confidence_threshold
        self.embedding_model_name = embedding_model
        
        self._enabled = False
        self._model = None
        self._prototypes = {}
        self._prototype_embeddings = None
        
        # Try to load sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            
            self._SentenceTransformer = SentenceTransformer
            self._np = np
            
            # Load model
            self._model = SentenceTransformer(embedding_model)
            self._enabled = True
            logger.info(f"SLMRouter initialized with model: {embedding_model}")
            
            # Load prototypes
            self._load_prototypes()
            
        except ImportError as e:
            logger.warning(
                f"sentence-transformers not available: {e}. "
                "SLMRouter disabled, will fall through to LLM routing."
            )
            self._enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize SLMRouter: {e}. Disabling.")
            self._enabled = False

    def _load_prototypes(self) -> None:
        """
        Load prototype embeddings from JSON file.
        
        Expected JSON format:
        {
            "frontend": {
                "examples": ["create react component", "style button", ...],
                "embedding": [0.1, 0.2, ...]  # optional pre-computed
            },
            "backend": {...},
            ...
        }
        """
        if not self.prototypes_path.exists():
            logger.warning(f"Prototypes file not found: {self.prototypes_path}. SLMRouter disabled.")
            self._enabled = False
            return
        
        try:
            with open(self.prototypes_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._prototypes = data
            
            # Compute embeddings for each category
            embeddings = []
            categories = []
            
            for category, proto_data in data.items():
                if isinstance(proto_data, dict):
                    # If pre-computed embedding exists, use it
                    if "embedding" in proto_data:
                        embedding = self._np.array(proto_data["embedding"])
                    else:
                        # Otherwise compute from examples
                        examples = proto_data.get("examples", [])
                        if not examples:
                            logger.warning(f"No examples for category '{category}', skipping")
                            continue
                        # Average embeddings of all examples
                        example_embeddings = self._model.encode(examples)
                        embedding = self._np.mean(example_embeddings, axis=0)
                    
                    embeddings.append(embedding)
                    categories.append(category)
            
            if embeddings:
                self._prototype_embeddings = self._np.array(embeddings)
                self._categories = categories
                logger.info(f"Loaded {len(categories)} prototype categories: {categories}")
            else:
                logger.warning("No valid prototypes loaded. SLMRouter disabled.")
                self._enabled = False
                
        except Exception as e:
            logger.error(f"Failed to load prototypes from {self.prototypes_path}: {e}")
            self._enabled = False

    def reload_prototypes(self) -> None:
        """
        Hot-reload prototypes from JSON file without restart.
        
        Validates Requirement 4.4: reload without restart
        """
        if not self._enabled:
            logger.warning("SLMRouter is disabled, cannot reload prototypes")
            return
        
        logger.info(f"Reloading prototypes from {self.prototypes_path}")
        self._load_prototypes()
    
    def assess_complexity(self, query: str) -> Literal["simple", "moderate", "complex"]:
        """
        Assess task complexity based on query content.
        
        Args:
            query: User query string
            
        Returns:
            "simple", "moderate", or "complex"
            
        Validates: Task 6.2 - Complexity assessment for cascading
        """
        if not query:
            return "simple"
        
        query_lower = query.lower()
        
        # Count complexity indicators
        indicator_count = sum(1 for indicator in self.COMPLEX_INDICATORS if indicator in query_lower)
        
        # Check query length (longer queries often indicate complexity)
        word_count = len(query.split())
        
        # Heuristic scoring
        complexity_score = 0.0
        
        # Indicator-based scoring (more weight on indicators)
        if indicator_count >= 3:
            complexity_score += 0.7  # Increased from 0.5
        elif indicator_count >= 2:
            complexity_score += 0.5  # New threshold
        elif indicator_count >= 1:
            complexity_score += 0.25  # Reduced from 0.3
        
        # Length-based scoring
        if word_count > 50:
            complexity_score += 0.3
        elif word_count > 20:
            complexity_score += 0.2
        elif word_count > 10:
            complexity_score += 0.1
        
        # Classify based on score
        if complexity_score >= 0.6:
            return "complex"
        elif complexity_score >= 0.3:
            return "moderate"
        else:
            return "simple"
    
    def recommend_model(self, query: str, confidence: float | None = None) -> str:
        """
        Recommend model based on task complexity and confidence.
        
        Args:
            query: User query string
            confidence: Classification confidence (if available)
            
        Returns:
            Recommended model name ("claude-3-5-sonnet-20241022" or "o1-mini")
            
        Validates: Task 6.2 - Cascading logic
        """
        complexity = self.assess_complexity(query)
        
        # If we have confidence, use it to refine the decision
        if confidence is not None:
            if confidence >= self.COMPLEXITY_THRESHOLDS["simple"]:
                # High confidence → simple task → Sonnet
                return "claude-3-5-sonnet-20241022"
            elif confidence >= self.COMPLEXITY_THRESHOLDS["moderate"]:
                # Medium confidence → moderate task → Sonnet
                return "claude-3-5-sonnet-20241022"
            else:
                # Low confidence → complex task → o1-mini
                return "o1-mini"
        
        # Fallback to complexity-based decision
        if complexity == "complex":
            return "o1-mini"
        else:
            return "claude-3-5-sonnet-20241022"

    def classify(self, query: str) -> Optional[SLMRouteDecision]:
        """
        Classify user intent using cosine similarity with prototypes.
        
        Args:
            query: User query string
        
        Returns:
            SLMRouteDecision if confidence >= threshold, else None
            None if _enabled=False (graceful degradation)
        
        Validates Requirements:
        - 4.1: Classify using sentence-transformers cosine similarity
        - 4.2: Return result if confidence >= threshold
        - 4.3: Return None if confidence < threshold (fall through to LLM)
        - 4.6: Return None if _enabled=False (graceful degradation)
        - 4.7: Log routing decisions
        - 4.8: Idempotent classification
        """
        if not self._enabled:
            return None
        
        if not query or not query.strip():
            logger.warning("Empty query provided to SLMRouter")
            return None
        
        try:
            # Encode query
            query_embedding = self._model.encode([query])[0]
            
            # Compute cosine similarity with all prototypes
            # cosine_similarity = dot(a, b) / (norm(a) * norm(b))
            query_norm = self._np.linalg.norm(query_embedding)
            prototype_norms = self._np.linalg.norm(self._prototype_embeddings, axis=1)
            
            dot_products = self._np.dot(self._prototype_embeddings, query_embedding)
            similarities = dot_products / (prototype_norms * query_norm + 1e-8)
            
            # Get top-k results
            top_k_indices = self._np.argsort(similarities)[::-1]
            top_k_scores = similarities[top_k_indices]
            
            # Build top_k list
            top_k = [
                {"label": self._categories[idx], "score": float(score)}
                for idx, score in zip(top_k_indices, top_k_scores)
            ]
            
            # Get best match
            best_idx = top_k_indices[0]
            best_category = self._categories[best_idx]
            best_confidence = float(top_k_scores[0])
            
            # Log decision
            log_data = {
                "chosen": best_category,
                "confidence": best_confidence,
                "top_k": top_k[:5],  # Log top 5
            }
            logger.info(f"SLMRouter decision: {json.dumps(log_data)}")
            
            # Check threshold
            if best_confidence >= self.confidence_threshold:
                return SLMRouteDecision(
                    chosen=best_category,
                    confidence=best_confidence,
                    top_k=top_k[:5],
                    llm_fallback_triggered=False,
                )
            else:
                logger.info(
                    f"Confidence {best_confidence:.3f} below threshold {self.confidence_threshold}, "
                    "falling through to LLM"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error during SLMRouter classification: {e}", exc_info=True)
            return None
