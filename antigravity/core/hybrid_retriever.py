"""
HybridRetriever: BM25 + Dense Embedding Retrieval for SkillStore

Combines sparse (BM25) and dense (cosine similarity) search with configurable weights.
Supports domain filtering, graceful degradation, and deterministic tie-breaking.

Requirements: 1.1-1.11 from antigravity-architecture-upgrade spec.
"""

from __future__ import annotations
import logging
import re
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from core.schemas import Skill, SkillDocument, RankedSkill

logger = logging.getLogger(__name__)


# ── Graceful Degradation: Optional Dependencies ──────────────────────────────

try:
    from rank_bm25 import BM25Okapi
    _BM25_AVAILABLE = True
except ImportError:
    logger.warning("rank-bm25 not installed. BM25 search will be unavailable.")
    _BM25_AVAILABLE = False
    BM25Okapi = None

try:
    from sentence_transformers import SentenceTransformer
    _DENSE_AVAILABLE = True
except ImportError:
    logger.warning(
        "sentence-transformers not installed. Dense embedding search will be unavailable. "
        "Install with: pip install sentence-transformers"
    )
    _DENSE_AVAILABLE = False
    SentenceTransformer = None


# ── HybridRetriever Implementation ────────────────────────────────────────────

class HybridRetriever:
    """
    Hybrid retrieval combining BM25 sparse search and dense embedding search.
    
    Graceful degradation:
    - If sentence-transformers unavailable: BM25-only mode
    - If rank-bm25 unavailable: embedding-only mode
    - If both unavailable: keyword-only fallback
    
    Tie-breaking order (deterministic):
    1. cosine_norm descending
    2. bm25_norm descending
    3. skill_id lexicographic ascending
    """
    
    def __init__(
        self,
        skills_dir: Path | str,
        alpha: float = 0.5,
        beta: float = 0.5,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize HybridRetriever.
        
        Args:
            skills_dir: Path to directory containing skill .md files
            alpha: Weight for BM25 scores (0.0-1.0)
            beta: Weight for cosine similarity scores (0.0-1.0)
            embedding_model: SentenceTransformer model name
        """
        self.skills_dir = Path(skills_dir)
        self.alpha = alpha
        self.beta = beta
        self.embedding_model_name = embedding_model
        
        # State
        self._documents: list[SkillDocument] = []
        self._skills_map: dict[str, Skill] = {}
        
        # BM25 components
        self._bm25_index: Optional[BM25Okapi] = None
        self._bm25_available = _BM25_AVAILABLE
        
        # Dense embedding components
        self._embedding_model: Optional[SentenceTransformer] = None
        self._embeddings: Optional[list] = None
        self._dense_available = False
        
        # Initialize embedding model if available
        if _DENSE_AVAILABLE:
            try:
                self._embedding_model = SentenceTransformer(embedding_model)
                self._dense_available = True
                logger.info(f"Loaded embedding model: {embedding_model}")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}. Falling back to BM25-only.")
                self._dense_available = False
        
        if not self._bm25_available and not self._dense_available:
            logger.warning(
                "Neither BM25 nor dense embeddings available. "
                "Retrieval will use keyword-only fallback."
            )
    
    def index(self, documents: list[SkillDocument]) -> None:
        """
        Build BM25 index and embedding matrix from skill documents.
        
        Args:
            documents: List of SkillDocument objects to index
        """
        if not documents:
            logger.warning("No documents provided for indexing")
            return
        
        self._documents = documents
        
        # Build skills map for quick lookup
        for doc in documents:
            # Parse skill from document (simplified - in production would parse from file)
            skill = self._document_to_skill(doc)
            self._skills_map[doc.skill_id] = skill
        
        # Build BM25 index
        if self._bm25_available:
            tokenized_corpus = [self._tokenize(doc.content) for doc in documents]
            self._bm25_index = BM25Okapi(tokenized_corpus)
            logger.info(f"Built BM25 index with {len(documents)} documents")
        
        # Build embedding matrix
        if self._dense_available and self._embedding_model:
            # Apply contextual retrieval: prepend document context
            contextualized_texts = [
                self._contextualize_document(doc) for doc in documents
            ]
            self._embeddings = self._embedding_model.encode(
                contextualized_texts,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            logger.info(f"Built embedding matrix with {len(documents)} documents")
    
    def retrieve(
        self,
        query: str,
        errors: Optional[list[str]] = None,
        domain_filter: Optional[str] = None,
        top_k: int = 5,
    ) -> list[RankedSkill]:
        """
        Retrieve and rank skills using hybrid search.
        
        Backward compatible with SkillStore.retrieve(task, errors) interface.
        
        Args:
            query: Search query (task description)
            errors: Optional error messages to incorporate into query
            domain_filter: Optional domain tag to filter by
            top_k: Number of results to return
        
        Returns:
            List of RankedSkill objects sorted by final_score descending
        """
        if not self._documents:
            logger.warning("No documents indexed. Call index() first.")
            return []
        
        # Augment query with error context if provided
        augmented_query = query
        if errors:
            augmented_query = f"{query} {' '.join(errors)}"
        
        # Apply domain filter
        candidate_docs = self._documents
        if domain_filter:
            candidate_docs = [
                doc for doc in self._documents
                if domain_filter in doc.domain_tags
            ]
            if not candidate_docs:
                logger.warning(f"No documents match domain filter: {domain_filter}")
                return []
        
        # Compute BM25 scores
        bm25_scores = self._compute_bm25_scores(augmented_query, candidate_docs)
        
        # Compute cosine similarity scores
        cosine_scores = self._compute_cosine_scores(augmented_query, candidate_docs)
        
        # Normalize scores
        bm25_norm = self._normalize_bm25(bm25_scores)
        cosine_norm = self._normalize_cosine(cosine_scores)
        
        # Combine scores
        results = []
        for i, doc in enumerate(candidate_docs):
            skill = self._skills_map.get(doc.skill_id)
            if not skill:
                continue
            
            final_score = self.alpha * bm25_norm[i] + self.beta * cosine_norm[i]
            
            ranked_skill = RankedSkill(
                skill=skill,
                bm25_norm=bm25_norm[i],
                cosine_norm=cosine_norm[i],
                final_score=final_score
            )
            results.append(ranked_skill)
        
        # Sort with deterministic tie-breaking
        results.sort(key=self._sort_key, reverse=True)
        
        return results[:top_k]
    
    # ── Private Methods ───────────────────────────────────────────────────────
    
    def _compute_bm25_scores(
        self,
        query: str,
        documents: list[SkillDocument]
    ) -> list[float]:
        """Compute BM25 scores for query against documents."""
        if not self._bm25_available or not self._bm25_index:
            # Fallback: return zeros
            return [0.0] * len(documents)
        
        # Get indices of documents in full corpus
        doc_indices = [self._documents.index(doc) for doc in documents]
        
        # Tokenize query
        tokenized_query = self._tokenize(query)
        
        # Get scores for all documents
        all_scores = self._bm25_index.get_scores(tokenized_query)
        
        # Extract scores for candidate documents
        scores = [all_scores[i] for i in doc_indices]
        
        return scores
    
    def _compute_cosine_scores(
        self,
        query: str,
        documents: list[SkillDocument]
    ) -> list[float]:
        """Compute cosine similarity scores for query against documents."""
        if not self._dense_available or self._embeddings is None:
            # Fallback: return zeros
            return [0.0] * len(documents)
        
        # Encode query
        query_embedding = self._embedding_model.encode(
            [query],
            show_progress_bar=False,
            convert_to_numpy=True
        )[0]
        
        # Get indices of documents in full corpus
        doc_indices = [self._documents.index(doc) for doc in documents]
        
        # Compute cosine similarity
        import numpy as np
        scores = []
        for i in doc_indices:
            doc_embedding = self._embeddings[i]
            # Cosine similarity: dot product of normalized vectors
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )
            scores.append(float(similarity))
        
        return scores
    
    def _normalize_bm25(self, scores: list[float]) -> list[float]:
        """
        Normalize BM25 scores to [0, 1] using min-max normalization.
        
        Args:
            scores: Raw BM25 scores
        
        Returns:
            Normalized scores in [0, 1]
        """
        if not scores or all(s == 0 for s in scores):
            return [0.0] * len(scores)
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            # All scores equal - return uniform distribution
            return [1.0] * len(scores)
        
        normalized = [
            (score - min_score) / (max_score - min_score)
            for score in scores
        ]
        
        return normalized
    
    def _normalize_cosine(self, scores: list[float]) -> list[float]:
        """
        Normalize cosine similarity scores to [0, 1].
        
        Cosine similarity is in [-1, 1], so we use (score + 1) / 2.
        
        Args:
            scores: Raw cosine similarity scores
        
        Returns:
            Normalized scores in [0, 1]
        """
        normalized = [(score + 1.0) / 2.0 for score in scores]
        return normalized
    
    def _sort_key(self, ranked_skill: RankedSkill) -> tuple:
        """
        Generate sort key for deterministic tie-breaking.
        
        Order:
        1. final_score descending (negated for reverse sort)
        2. cosine_norm descending (negated)
        3. bm25_norm descending (negated)
        4. skill_id lexicographic ascending
        """
        return (
            -ranked_skill.final_score,  # Higher is better
            -ranked_skill.cosine_norm,  # Higher is better
            -ranked_skill.bm25_norm,    # Higher is better
            ranked_skill.skill.name     # Lexicographic ascending
        )
    
    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization for BM25."""
        # Lowercase and split on non-alphanumeric
        tokens = re.findall(r'\w+', text.lower())
        return tokens
    
    def _contextualize_document(self, doc: SkillDocument) -> str:
        """
        Apply contextual retrieval by prepending document context.
        
        Format: "<DOCUMENT>\nName: {name}\nDomain: {domains}\nContent: {content}\n</DOCUMENT>"
        """
        domains_str = ", ".join(doc.domain_tags) if doc.domain_tags else "general"
        context = (
            f"<DOCUMENT>\n"
            f"Name: {doc.name}\n"
            f"Domain: {domains_str}\n"
            f"Content: {doc.content}\n"
            f"</DOCUMENT>"
        )
        return context
    
    def _document_to_skill(self, doc: SkillDocument) -> Skill:
        """
        Convert SkillDocument to Skill object.
        
        In production, this would parse the markdown file.
        For now, create a minimal Skill object.
        """
        from core.schemas import PlanStep, TaskCompletionSpec, ArtifactCheck
        
        # Extract trigger patterns from content (simplified)
        trigger_patterns = self._extract_trigger_patterns(doc.content)
        
        skill = Skill(
            name=doc.name,
            description=doc.content[:200],  # First 200 chars as description
            trigger_patterns=trigger_patterns,
            plan_template=[
                PlanStep(
                    step_id=1,
                    action="analyze",
                    agent="general",
                    input={"instruction": f"Apply skill: {doc.name}"}
                )
            ],
            success_criteria=TaskCompletionSpec(
                deterministic_checks=[],
                semantic_goal=f"Successfully applied {doc.name}"
            )
        )
        
        return skill
    
    def _extract_trigger_patterns(self, content: str) -> list[str]:
        """Extract trigger patterns from skill content."""
        # Look for common error patterns in content
        patterns = []
        
        # Extract quoted strings as potential patterns
        quoted = re.findall(r'"([^"]+)"', content)
        patterns.extend(quoted[:5])  # Limit to 5
        
        # Extract common error keywords
        error_keywords = [
            "error", "missing", "not found", "undefined", "failed",
            "invalid", "cannot", "unable"
        ]
        content_lower = content.lower()
        for keyword in error_keywords:
            if keyword in content_lower:
                patterns.append(keyword)
        
        return patterns[:10] if patterns else ["general"]


# ── Backward Compatibility Helper ────────────────────────────────────────────

def create_hybrid_retriever_from_skills_dir(
    skills_dir: Path | str,
    alpha: float = 0.5,
    beta: float = 0.5,
) -> HybridRetriever:
    """
    Factory function to create and index HybridRetriever from skills directory.
    
    Scans skills_dir for .md files and indexes them automatically.
    
    Args:
        skills_dir: Path to skills directory
        alpha: BM25 weight
        beta: Cosine similarity weight
    
    Returns:
        Initialized and indexed HybridRetriever
    """
    retriever = HybridRetriever(
        skills_dir=skills_dir,
        alpha=alpha,
        beta=beta
    )
    
    # Scan directory for .md files
    skills_path = Path(skills_dir)
    if not skills_path.exists():
        logger.warning(f"Skills directory does not exist: {skills_dir}")
        return retriever
    
    documents = []
    for md_file in skills_path.rglob("*.md"):
        # Infer domain from path
        relative_path = md_file.relative_to(skills_path)
        domain_tags = [part for part in relative_path.parts[:-1]]  # Exclude filename
        
        # Read content
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read {md_file}: {e}")
            continue
        
        # Create document
        doc = SkillDocument(
            skill_id=md_file.stem,  # Use filename without extension as ID
            name=md_file.stem.replace("-", " ").replace("_", " ").title(),
            content=content,
            domain_tags=domain_tags,
            file_path=str(md_file)
        )
        documents.append(doc)
    
    logger.info(f"Found {len(documents)} skill documents in {skills_dir}")
    
    # Index documents
    if documents:
        retriever.index(documents)
    
    return retriever
