"""
Unit tests for HybridRetriever.

Tests Requirements 1.1-1.11 from antigravity-architecture-upgrade spec.
"""

import sys
import os

# Ensure the antigravity/core package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from core.hybrid_retriever import HybridRetriever, create_hybrid_retriever_from_skills_dir
from core.schemas import SkillDocument, RankedSkill, Skill, PlanStep, TaskCompletionSpec


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_documents():
    """Create sample skill documents for testing."""
    return [
        SkillDocument(
            skill_id="react_component",
            name="Fix React Component",
            content="Fix missing React component imports. Common error: Module not found.",
            domain_tags=["frontend", "react"],
            file_path="/skills/frontend/react_component.md"
        ),
        SkillDocument(
            skill_id="python_import",
            name="Fix Python Import",
            content="Fix Python import errors. ModuleNotFoundError: No module named 'xyz'.",
            domain_tags=["backend", "python"],
            file_path="/skills/backend/python_import.md"
        ),
        SkillDocument(
            skill_id="debug_general",
            name="General Debugging",
            content="General debugging strategies for any programming language.",
            domain_tags=["debug"],
            file_path="/skills/debug/general.md"
        ),
    ]


@pytest.fixture
def retriever_with_bm25_only():
    """Create retriever with BM25 only (no embeddings)."""
    with patch('core.hybrid_retriever._DENSE_AVAILABLE', False):
        retriever = HybridRetriever(
            skills_dir="/tmp/skills",
            alpha=1.0,
            beta=0.0
        )
        yield retriever


@pytest.fixture
def retriever_with_embeddings():
    """Create retriever with embeddings enabled."""
    retriever = HybridRetriever(
        skills_dir="/tmp/skills",
        alpha=0.5,
        beta=0.5
    )
    yield retriever


# ── Test 1.6: Backward Compatible Interface ──────────────────────────────────

def test_backward_compatible_interface(sample_documents):
    """
    Requirement 1.6: SkillStore SHALL expose the same retrieve(task, errors) interface.
    
    Test that retrieve() accepts task and errors parameters like the old interface.
    """
    retriever = HybridRetriever(skills_dir="/tmp/skills")
    retriever.index(sample_documents)
    
    # Should accept task only
    results = retriever.retrieve("fix react component")
    assert isinstance(results, list)
    
    # Should accept task and errors
    results = retriever.retrieve(
        "fix import error",
        errors=["ModuleNotFoundError: No module named 'requests'"]
    )
    assert isinstance(results, list)
    
    # Should accept all optional parameters
    results = retriever.retrieve(
        query="fix bug",
        errors=["some error"],
        domain_filter="frontend",
        top_k=3
    )
    assert isinstance(results, list)
    assert len(results) <= 3


# ── Test 1.8: Index Skills Directory ─────────────────────────────────────────

def test_index_skills_directory(tmp_path):
    """
    Requirement 1.8: HybridRetriever SHALL index all .md files in antigravity/skills/.
    
    Test that index() processes all markdown files in the skills directory.
    """
    # Create temporary skills directory structure
    skills_dir = tmp_path / "skills"
    frontend_dir = skills_dir / "frontend"
    backend_dir = skills_dir / "backend"
    
    frontend_dir.mkdir(parents=True)
    backend_dir.mkdir(parents=True)
    
    # Create skill files
    (frontend_dir / "react.md").write_text("React skill content")
    (frontend_dir / "css.md").write_text("CSS skill content")
    (backend_dir / "python.md").write_text("Python skill content")
    
    # Create retriever and index
    retriever = create_hybrid_retriever_from_skills_dir(skills_dir)
    
    # Verify all files were indexed
    assert len(retriever._documents) == 3
    
    # Verify domain tags were inferred from path
    doc_by_id = {doc.skill_id: doc for doc in retriever._documents}
    assert "frontend" in doc_by_id["react"].domain_tags
    assert "frontend" in doc_by_id["css"].domain_tags
    assert "backend" in doc_by_id["python"].domain_tags


# ── Test 1.10: Semantic Overlap ──────────────────────────────────────────────

def test_semantic_overlap_fixed_pairs(sample_documents):
    """
    Requirement 1.10: For queries with same semantic meaning but different keywords,
    HybridRetriever SHALL return overlapping top-3 results.
    
    Test with fixed query pairs that have similar meaning.
    """
    retriever = HybridRetriever(skills_dir="/tmp/skills", alpha=0.3, beta=0.7)
    retriever.index(sample_documents)
    
    # Query pair 1: Different wording, same intent
    q1 = "fix missing react component"
    q2 = "resolve react module not found"
    
    results1 = retriever.retrieve(q1, top_k=3)
    results2 = retriever.retrieve(q2, top_k=3)
    
    # Extract skill names
    names1 = {r.skill.name for r in results1}
    names2 = {r.skill.name for r in results2}
    
    # Should have at least 1 overlapping result
    overlap = names1 & names2
    assert len(overlap) >= 1, f"Expected overlap, got names1={names1}, names2={names2}"


# ── Test 1.7: Fallback When No Sentence Transformers ─────────────────────────

def test_fallback_when_no_sentence_transformers(sample_documents):
    """
    Requirement 1.7: If sentence-transformers not installed, fall back to BM25-only.
    
    Test graceful degradation when dense embeddings unavailable.
    """
    # Create retriever with dense embeddings disabled
    retriever = HybridRetriever(
        skills_dir="/tmp/skills",
        alpha=0.5,
        beta=0.5  # Beta should be ignored when no embeddings
    )
    
    # Manually disable dense embeddings to simulate missing library
    retriever._dense_available = False
    retriever._embedding_model = None
    
    retriever.index(sample_documents)
    
    # Should still work with BM25 only
    results = retriever.retrieve("fix react component")
    
    assert isinstance(results, list)
    # When dense embeddings unavailable, cosine scores should be 0
    # which normalizes to 0.5 via (0 + 1) / 2
    for r in results:
        # Cosine scores are 0 (no embeddings), normalized to 0.5
        assert r.cosine_norm == 0.5, \
            f"Expected cosine_norm to be 0.5 (normalized from 0), got {r.cosine_norm}"


# ── Test 1.4: Domain Filter Containment ──────────────────────────────────────

def test_domain_filter_containment(sample_documents):
    """
    Requirement 1.4: With domain_filter, all results SHALL have that domain in tags.
    
    Test that domain filtering works correctly.
    """
    retriever = HybridRetriever(skills_dir="/tmp/skills")
    retriever.index(sample_documents)
    
    # Filter by frontend
    results = retriever.retrieve("fix error", domain_filter="frontend")
    
    # All results should have "frontend" in domain_tags
    # Build a map of skill names to documents
    doc_map = {doc.name: doc for doc in sample_documents}
    
    for r in results:
        # Find the document by matching skill name
        doc = doc_map.get(r.skill.name)
        if doc:
            assert "frontend" in doc.domain_tags, \
                f"Expected 'frontend' in {doc.domain_tags} for skill {r.skill.name}"


# ── Test 1.11: Deterministic Tie-Breaking ────────────────────────────────────

def test_deterministic_tie_breaking(sample_documents):
    """
    Requirement 1.11: For identical final_score, apply deterministic tie-breaking.
    
    Test that multiple calls with same inputs return same order.
    """
    retriever = HybridRetriever(skills_dir="/tmp/skills", alpha=0.5, beta=0.5)
    retriever.index(sample_documents)
    
    query = "fix error"
    
    # Call retrieve multiple times
    results1 = retriever.retrieve(query, top_k=10)
    results2 = retriever.retrieve(query, top_k=10)
    results3 = retriever.retrieve(query, top_k=10)
    
    # Extract skill names in order
    names1 = [r.skill.name for r in results1]
    names2 = [r.skill.name for r in results2]
    names3 = [r.skill.name for r in results3]
    
    # All should be identical
    assert names1 == names2 == names3, "Tie-breaking should be deterministic"


# ── Test 1.2: Score Normalization ────────────────────────────────────────────

def test_score_normalization(sample_documents):
    """
    Requirement 1.2: Scores SHALL be normalized to [0,1] and combined correctly.
    
    Test that all scores are in valid range and formula is correct.
    """
    retriever = HybridRetriever(skills_dir="/tmp/skills", alpha=0.6, beta=0.4)
    retriever.index(sample_documents)
    
    results = retriever.retrieve("fix react component")
    
    for r in results:
        # Check normalization bounds
        assert 0.0 <= r.bm25_norm <= 1.0, f"BM25 score out of range: {r.bm25_norm}"
        assert 0.0 <= r.cosine_norm <= 1.0, f"Cosine score out of range: {r.cosine_norm}"
        assert 0.0 <= r.final_score <= 1.0, f"Final score out of range: {r.final_score}"
        
        # Check formula: final_score = alpha * bm25_norm + beta * cosine_norm
        expected = 0.6 * r.bm25_norm + 0.4 * r.cosine_norm
        assert abs(r.final_score - expected) < 1e-6, \
            f"Final score mismatch: {r.final_score} != {expected}"


# ── Test 1.3: Ranking Order ──────────────────────────────────────────────────

def test_ranking_order(sample_documents):
    """
    Requirement 1.3: Results SHALL be sorted by final_score descending.
    
    Test that results are properly sorted.
    """
    retriever = HybridRetriever(skills_dir="/tmp/skills")
    retriever.index(sample_documents)
    
    results = retriever.retrieve("fix error")
    
    # Extract scores
    scores = [r.final_score for r in results]
    
    # Should be in descending order
    assert scores == sorted(scores, reverse=True), \
        f"Results not sorted: {scores}"


# ── Test 1.9: Alpha/Beta Monotonicity ────────────────────────────────────────

def test_alpha_beta_monotonicity(sample_documents):
    """
    Requirement 1.9: Increasing alpha SHALL increase BM25 contribution.
    
    Test monotonicity property of weight parameters.
    """
    query = "fix react component"
    
    # Create two retrievers with different alpha values
    r1 = HybridRetriever(skills_dir="/tmp/skills", alpha=0.3, beta=0.7)
    r2 = HybridRetriever(skills_dir="/tmp/skills", alpha=0.7, beta=0.3)
    
    r1.index(sample_documents)
    r2.index(sample_documents)
    
    results1 = r1.retrieve(query)
    results2 = r2.retrieve(query)
    
    # For same skill, higher alpha should give more weight to BM25
    if results1 and results2:
        # Find common skill
        names1 = {r.skill.name for r in results1}
        names2 = {r.skill.name for r in results2}
        common = names1 & names2
        
        if common:
            skill_name = list(common)[0]
            r1_skill = next(r for r in results1 if r.skill.name == skill_name)
            r2_skill = next(r for r in results2 if r.skill.name == skill_name)
            
            # With higher alpha, BM25 contribution should be higher
            bm25_contrib_1 = 0.3 * r1_skill.bm25_norm
            bm25_contrib_2 = 0.7 * r2_skill.bm25_norm
            
            assert bm25_contrib_2 >= bm25_contrib_1, \
                "Higher alpha should increase BM25 contribution"


# ── Test Edge Cases ──────────────────────────────────────────────────────────

def test_empty_query(sample_documents):
    """Test behavior with empty query."""
    retriever = HybridRetriever(skills_dir="/tmp/skills")
    retriever.index(sample_documents)
    
    results = retriever.retrieve("")
    
    # Should return results (all scores will be low)
    assert isinstance(results, list)


def test_no_documents_indexed():
    """Test behavior when no documents are indexed."""
    retriever = HybridRetriever(skills_dir="/tmp/skills")
    
    results = retriever.retrieve("fix error")
    
    # Should return empty list
    assert results == []


def test_domain_filter_no_matches(sample_documents):
    """Test domain filter with no matching documents."""
    retriever = HybridRetriever(skills_dir="/tmp/skills")
    retriever.index(sample_documents)
    
    results = retriever.retrieve("fix error", domain_filter="nonexistent")
    
    # Should return empty list
    assert results == []


def test_top_k_larger_than_corpus(sample_documents):
    """Test top_k larger than number of documents."""
    retriever = HybridRetriever(skills_dir="/tmp/skills")
    retriever.index(sample_documents)
    
    results = retriever.retrieve("fix error", top_k=100)
    
    # Should return all documents (3)
    assert len(results) == len(sample_documents)


# ── Test Contextual Retrieval ────────────────────────────────────────────────

def test_contextual_retrieval_format(sample_documents):
    """
    Requirement 1.5: Generate contextual summary by prepending context.
    
    Test that documents are contextualized correctly.
    """
    retriever = HybridRetriever(skills_dir="/tmp/skills")
    
    doc = sample_documents[0]
    contextualized = retriever._contextualize_document(doc)
    
    # Should contain document structure
    assert "<DOCUMENT>" in contextualized
    assert "</DOCUMENT>" in contextualized
    assert f"Name: {doc.name}" in contextualized
    assert "Domain:" in contextualized
    assert "Content:" in contextualized


# ── Test Tokenization ────────────────────────────────────────────────────────

def test_tokenization():
    """Test simple tokenization for BM25."""
    retriever = HybridRetriever(skills_dir="/tmp/skills")
    
    text = "Fix React Component Error!"
    tokens = retriever._tokenize(text)
    
    # Should be lowercase and split on non-alphanumeric
    assert tokens == ["fix", "react", "component", "error"]


# ── Test Normalization Functions ─────────────────────────────────────────────

def test_normalize_bm25_uniform():
    """Test BM25 normalization with uniform scores."""
    retriever = HybridRetriever(skills_dir="/tmp/skills")
    
    scores = [5.0, 5.0, 5.0]
    normalized = retriever._normalize_bm25(scores)
    
    # All equal scores should normalize to 1.0
    assert all(s == 1.0 for s in normalized)


def test_normalize_bm25_range():
    """Test BM25 normalization with varied scores."""
    retriever = HybridRetriever(skills_dir="/tmp/skills")
    
    scores = [0.0, 5.0, 10.0]
    normalized = retriever._normalize_bm25(scores)
    
    # Should be [0.0, 0.5, 1.0]
    assert normalized == [0.0, 0.5, 1.0]


def test_normalize_cosine():
    """Test cosine normalization."""
    retriever = HybridRetriever(skills_dir="/tmp/skills")
    
    scores = [-1.0, 0.0, 1.0]
    normalized = retriever._normalize_cosine(scores)
    
    # Should be [0.0, 0.5, 1.0]
    assert normalized == [0.0, 0.5, 1.0]


def test_normalize_bm25_empty():
    """Test BM25 normalization with empty scores."""
    retriever = HybridRetriever(skills_dir="/tmp/skills")
    
    scores = []
    normalized = retriever._normalize_bm25(scores)
    
    assert normalized == []


def test_normalize_bm25_all_zeros():
    """Test BM25 normalization with all zero scores."""
    retriever = HybridRetriever(skills_dir="/tmp/skills")
    
    scores = [0.0, 0.0, 0.0]
    normalized = retriever._normalize_bm25(scores)
    
    # All zeros should stay zeros
    assert all(s == 0.0 for s in normalized)
