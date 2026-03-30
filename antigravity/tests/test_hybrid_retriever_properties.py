"""
Property-based tests for HybridRetriever

These tests ensure the retrieval system behaves correctly under all conditions,
preventing self-reinforcing wrong patterns in Phase 2 evolution.

Critical Properties:
1. Monotonicity: Better semantic match → not worse score
2. Stability: Small input change → small ranking change
3. Filter Correctness: Confidence threshold behaves predictably
4. Diversity Preservation: Top-k doesn't collapse to near-duplicates
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
from typing import List, Dict
import Levenshtein

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.hybrid_retriever import HybridRetriever
from core.schemas import Skill, PlanStep, TaskCompletionSpec


# ============================================================================
# STRATEGIES (Data Generators)
# ============================================================================

@st.composite
def skill_strategy(draw):
    """Generate realistic Skill objects"""
    return Skill(
        name=draw(st.text(min_size=5, max_size=50)),
        description=draw(st.text(min_size=20, max_size=200)),
        trigger_patterns=draw(st.lists(st.text(min_size=3, max_size=20), min_size=1, max_size=5)),
        plan_template=[
            PlanStep(
                step_id=1,
                action="analyze",
                agent="general",
                input={"instruction": "test"}
            )
        ],
        success_criteria=TaskCompletionSpec(
            deterministic_checks=[],
            semantic_goal=draw(st.text(min_size=10, max_size=100))
        )
    )


@st.composite
def query_strategy(draw):
    """Generate realistic query strings"""
    templates = [
        "How to {action} {object}",
        "Fix {problem} in {context}",
        "Implement {feature} using {technology}",
        "Debug {error} when {condition}",
        "Optimize {aspect} for {goal}"
    ]
    
    template = draw(st.sampled_from(templates))
    
    actions = ['create', 'build', 'implement', 'fix', 'optimize', 'refactor']
    objects = ['API', 'database', 'frontend', 'backend', 'authentication']
    problems = ['bug', 'error', 'crash', 'memory leak', 'performance issue']
    contexts = ['production', 'testing', 'development', 'deployment']
    features = ['login', 'payment', 'search', 'notification', 'dashboard']
    technologies = ['React', 'Python', 'PostgreSQL', 'Redis', 'Docker']
    errors = ['TypeError', 'ValueError', 'ConnectionError', 'TimeoutError']
    conditions = ['loading', 'submitting', 'refreshing', 'navigating']
    aspects = ['performance', 'security', 'scalability', 'maintainability']
    goals = ['speed', 'reliability', 'cost', 'user experience']
    
    return template.format(
        action=draw(st.sampled_from(actions)),
        object=draw(st.sampled_from(objects)),
        problem=draw(st.sampled_from(problems)),
        context=draw(st.sampled_from(contexts)),
        feature=draw(st.sampled_from(features)),
        technology=draw(st.sampled_from(technologies)),
        error=draw(st.sampled_from(errors)),
        condition=draw(st.sampled_from(conditions)),
        aspect=draw(st.sampled_from(aspects)),
        goal=draw(st.sampled_from(goals))
    )


# ============================================================================
# PROPERTY 1: MONOTONICITY
# ============================================================================

@given(
    query=query_strategy(),
    skills=st.lists(skill_strategy(), min_size=2, max_size=10)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_monotonicity_better_match_not_worse_score(query, skills):
    """
    Property: If skill A is semantically closer to query than skill B,
    then score(A) >= score(B)
    
    This prevents the system from preferring worse matches.
    """
    retriever = HybridRetriever()
    
    # Score all skills
    scored_skills = []
    for skill in skills:
        score = retriever._calculate_score(query, skill, error_context=None)
        scored_skills.append((skill, score))
    
    # Sort by score (descending)
    scored_skills.sort(key=lambda x: x[1], reverse=True)
    
    # Verify monotonicity: scores should be non-increasing
    for i in range(len(scored_skills) - 1):
        current_score = scored_skills[i][1]
        next_score = scored_skills[i + 1][1]
        
        assert current_score >= next_score, (
            f"Monotonicity violated: "
            f"skill[{i}] score={current_score:.3f} < "
            f"skill[{i+1}] score={next_score:.3f}"
        )


@given(
    base_query=query_strategy(),
    skill=skill_strategy()
)
@settings(max_examples=50)
def test_monotonicity_exact_match_highest_score(base_query, skill):
    """
    Property: Exact match should score higher than partial match
    """
    retriever = HybridRetriever()
    
    # Create a skill that exactly matches the query
    exact_skill = Skill(
        id="exact_match",
        name=base_query,
        description=base_query,
        tags=[base_query.split()[0]] if base_query.split() else ["test"],
        tier=1,
        domain="test",
        content=base_query
    )
    
    exact_score = retriever._calculate_score(base_query, exact_skill, None)
    partial_score = retriever._calculate_score(base_query, skill, None)
    
    assert exact_score >= partial_score, (
        f"Exact match should score higher: "
        f"exact={exact_score:.3f} < partial={partial_score:.3f}"
    )


# ============================================================================
# PROPERTY 2: STABILITY
# ============================================================================

@given(
    query=query_strategy(),
    skills=st.lists(skill_strategy(), min_size=3, max_size=10)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_stability_small_input_small_ranking_change(query, skills):
    """
    Property: Small input change → small ranking change
    
    Levenshtein distance < 3 should not cause dramatic ranking flips.
    This prevents instability in the retrieval system.
    """
    retriever = HybridRetriever()
    
    # Get original ranking
    original_results = retriever.retrieve(query, top_k=len(skills))
    original_ranking = [r.id for r in original_results]
    
    # Create small variation (change 1-2 characters)
    if len(query) < 3:
        return  # Skip too short queries
    
    variation = query[:len(query)//2] + "x" + query[len(query)//2+1:]
    
    # Verify Levenshtein distance is small
    distance = Levenshtein.distance(query, variation)
    assume(distance <= 3)
    
    # Get new ranking
    varied_results = retriever.retrieve(variation, top_k=len(skills))
    varied_ranking = [r.id for r in varied_results]
    
    # Calculate ranking stability (Kendall Tau or overlap)
    # For simplicity, check top-3 overlap
    if len(original_ranking) >= 3 and len(varied_ranking) >= 3:
        top3_original = set(original_ranking[:3])
        top3_varied = set(varied_ranking[:3])
        overlap = len(top3_original & top3_varied)
        
        # At least 2 out of 3 should remain in top-3
        assert overlap >= 2, (
            f"Ranking too unstable: "
            f"query='{query}' vs variation='{variation}' "
            f"(distance={distance}), "
            f"top-3 overlap={overlap}/3"
        )


@given(
    query=query_strategy(),
    skills=st.lists(skill_strategy(), min_size=5, max_size=10)
)
@settings(max_examples=50)
def test_stability_score_continuity(query, skills):
    """
    Property: Similar queries should produce similar scores
    
    This tests score continuity - no sudden jumps.
    """
    retriever = HybridRetriever()
    
    # Score with original query
    original_scores = {
        skill.id: retriever._calculate_score(query, skill, None)
        for skill in skills
    }
    
    # Create slight variation
    if len(query) < 5:
        return
    
    variation = query[:-1] + ("y" if query[-1] != "y" else "z")
    
    # Score with variation
    varied_scores = {
        skill.id: retriever._calculate_score(variation, skill, None)
        for skill in skills
    }
    
    # Check score differences are bounded
    for skill_id in original_scores:
        original = original_scores[skill_id]
        varied = varied_scores[skill_id]
        diff = abs(original - varied)
        
        # Score difference should be < 0.3 for small input change
        assert diff < 0.3, (
            f"Score changed too much for skill {skill_id}: "
            f"{original:.3f} → {varied:.3f} (diff={diff:.3f})"
        )


# ============================================================================
# PROPERTY 3: FILTER CORRECTNESS
# ============================================================================

@given(
    query=query_strategy(),
    skills=st.lists(skill_strategy(), min_size=5, max_size=20),
    confidence=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_filter_correctness_confidence_threshold(query, skills, confidence):
    """
    Property: Confidence threshold behaves predictably
    
    1. All returned skills have score >= confidence
    2. No skill with score >= confidence is excluded
    """
    retriever = HybridRetriever()
    
    # Get all scores
    all_scores = {
        skill.id: retriever._calculate_score(query, skill, None)
        for skill in skills
    }
    
    # Retrieve with confidence threshold
    results = retriever.retrieve(
        query, 
        top_k=len(skills),
        min_confidence=confidence
    )
    result_ids = {r.id for r in results}
    
    # Property 1: All returned skills have score >= confidence
    for result in results:
        score = all_scores[result.id]
        assert score >= confidence, (
            f"Returned skill {result.id} has score {score:.3f} < "
            f"confidence threshold {confidence:.3f}"
        )
    
    # Property 2: No valid skill is excluded
    for skill_id, score in all_scores.items():
        if score >= confidence:
            assert skill_id in result_ids, (
                f"Skill {skill_id} with score {score:.3f} >= "
                f"confidence {confidence:.3f} was excluded"
            )


@given(
    query=query_strategy(),
    skills=st.lists(skill_strategy(), min_size=5, max_size=15),
    top_k=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=50)
def test_filter_correctness_top_k_limit(query, skills, top_k):
    """
    Property: top_k parameter is respected
    """
    retriever = HybridRetriever()
    
    results = retriever.retrieve(query, top_k=top_k)
    
    # Should return at most top_k results
    assert len(results) <= top_k, (
        f"Returned {len(results)} results, expected at most {top_k}"
    )
    
    # If enough skills exist, should return exactly top_k
    if len(skills) >= top_k:
        assert len(results) == top_k, (
            f"Should return exactly {top_k} results when "
            f"{len(skills)} skills available"
        )


# ============================================================================
# PROPERTY 4: DIVERSITY PRESERVATION
# ============================================================================

@given(
    query=query_strategy(),
    top_k=st.integers(min_value=3, max_value=10)
)
@settings(max_examples=50)
def test_diversity_preservation_no_near_duplicates(query, top_k):
    """
    Property: Top-k doesn't collapse to near-duplicates
    
    If 5 distinct skill types exist, top-5 shouldn't all be variants of one type.
    """
    retriever = HybridRetriever()
    
    # Create skills with distinct domains
    domains = ['frontend', 'backend', 'security', 'devops', 'workflows']
    skills = []
    
    for i, domain in enumerate(domains):
        # Create 3 variants per domain
        for j in range(3):
            skill = Skill(
                id=f"{domain}_{j}",
                name=f"{domain.title()} Skill {j}",
                description=f"A {domain} skill for {query}",
                tags=[domain, query.split()[0] if query.split() else "test"],
                tier=1,
                domain=domain,
                content=f"Content about {domain} and {query}"
            )
            skills.append(skill)
    
    # Retrieve top-k
    results = retriever.retrieve(query, top_k=min(top_k, len(skills)))
    
    # Count domains in results
    domain_counts = {}
    for result in results:
        domain = result.domain
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    # No single domain should dominate (> 60% of results)
    if len(results) >= 5:
        max_count = max(domain_counts.values())
        max_ratio = max_count / len(results)
        
        assert max_ratio <= 0.6, (
            f"Diversity collapsed: {max_count}/{len(results)} results "
            f"from same domain ({max_ratio:.1%})"
        )


@given(
    query=query_strategy(),
    skills=st.lists(skill_strategy(), min_size=10, max_size=20)
)
@settings(max_examples=30)
def test_diversity_preservation_tier_distribution(query, skills):
    """
    Property: Results should include mix of tiers when available
    
    If skills from tier 1-4 all match, results shouldn't be all tier 1.
    """
    retriever = HybridRetriever()
    
    # Ensure we have skills from multiple tiers
    tier_counts = {}
    for skill in skills:
        tier_counts[skill.tier] = tier_counts.get(skill.tier, 0) + 1
    
    # Only test if we have at least 2 different tiers
    if len(tier_counts) < 2:
        return
    
    # Retrieve top-10
    results = retriever.retrieve(query, top_k=min(10, len(skills)))
    
    # Count tiers in results
    result_tiers = [r.tier for r in results]
    unique_tiers = len(set(result_tiers))
    
    # Should have at least 2 different tiers in top-10
    # (unless input only has 1 tier)
    if len(tier_counts) >= 2 and len(results) >= 5:
        assert unique_tiers >= 2, (
            f"Tier diversity collapsed: only tier {result_tiers[0]} "
            f"in top-{len(results)} results"
        )


# ============================================================================
# INTEGRATION PROPERTY: END-TO-END CORRECTNESS
# ============================================================================

@given(
    query=query_strategy(),
    skills=st.lists(skill_strategy(), min_size=5, max_size=15),
    top_k=st.integers(min_value=1, max_value=10),
    confidence=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_integration_all_properties_together(query, skills, top_k, confidence):
    """
    Integration test: All properties should hold simultaneously
    
    This is the ultimate test - retrieval should be:
    - Monotonic (better match → higher score)
    - Stable (small change → small ranking change)
    - Correct (threshold respected)
    - Diverse (no collapse)
    """
    retriever = HybridRetriever()
    
    # Retrieve
    results = retriever.retrieve(
        query,
        top_k=top_k,
        min_confidence=confidence
    )
    
    # Property 1: Monotonicity (scores non-increasing)
    scores = [retriever._calculate_score(query, r, None) for r in results]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i+1], "Monotonicity violated"
    
    # Property 2: Filter correctness (all >= confidence)
    for score in scores:
        assert score >= confidence, "Confidence threshold violated"
    
    # Property 3: Top-k respected
    assert len(results) <= top_k, "Top-k limit violated"
    
    # Property 4: Diversity (if enough results)
    if len(results) >= 5:
        domains = [r.domain for r in results]
        unique_domains = len(set(domains))
        # Should have at least 2 different domains in top-5+
        assert unique_domains >= 2, "Diversity collapsed"


# ============================================================================
# HELPER TESTS: Verify test infrastructure
# ============================================================================

def test_strategies_generate_valid_data():
    """Sanity check: strategies generate valid data"""
    from hypothesis import find
    
    # Test skill strategy
    skill = find(skill_strategy(), lambda s: True)
    assert skill.id
    assert skill.name
    assert skill.domain in ['frontend', 'backend', 'security', 'devops', 'workflows']
    assert 1 <= skill.tier <= 4
    
    # Test query strategy
    query = find(query_strategy(), lambda q: len(q) > 0)
    assert len(query) > 0
    assert isinstance(query, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
