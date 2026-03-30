from __future__ import annotations
from typing import Literal, List, Optional, ClassVar
from pydantic import BaseModel, Field, field_validator
from core.id_utils import is_valid_time_sortable_id


class RouteDecision(BaseModel):
    domain: Literal["frontend", "backend", "infra", "debug", "architecture", "general"]
    intent: Literal["generate", "edit", "analyze", "debug", "explain", "retrieve"]
    requires_retrieval: bool = Field(default=True)
    confidence: float = Field(ge=0.0, le=1.0)
    candidate_skills: List[str] = Field(default_factory=list, max_length=15)
    reasoning_summary: str = Field(max_length=300)


class RetrievalDecision(BaseModel):
    should_retrieve_more: bool
    missing_topics: list[str] = Field(default_factory=list, max_length=10)
    enough_context_to_code: bool
    confidence: float = Field(ge=0.0, le=1.0)


class PlanStep(BaseModel):
    step_id: int
    action: Literal["generate_code", "analyze", "write_file", "read_file", "run_cmd"]
    agent: str
    input: dict


class ArtifactCheck(BaseModel):
    type: Literal["file_exists", "file_contains", "file_not_empty", "cmd_exit_zero", "json_valid"]
    path: str | None = None
    keyword: str | None = None
    cmd: str | None = None


class TaskCompletionSpec(BaseModel):
    deterministic_checks: list[ArtifactCheck]
    semantic_goal: str


class ExecutionPlan(BaseModel):
    objective: str
    steps: list[PlanStep]
    completion_criteria: TaskCompletionSpec
    risk_flags: list[str] = Field(default_factory=list)


class CodeArtifact(BaseModel):
    path: str
    content: str
    action: Literal["create", "overwrite", "modify"]


class GeneratedCodeResult(BaseModel):
    files: list[CodeArtifact]
    explanation: str


class CompletionCheck(BaseModel):
    completed: bool
    unresolved_items: list[str] = Field(default_factory=list)


class Skill(BaseModel):
    name: str
    description: str
    trigger_patterns: list[str]
    plan_template: list[PlanStep]
    success_criteria: TaskCompletionSpec


# ── New models: Antigravity Architecture Upgrade ──────────────────────────────

class SkillDocument(BaseModel):
    """For HybridRetriever indexing."""
    skill_id: str
    name: str
    content: str
    domain_tags: list[str] = []
    file_path: str


class RankedSkill(BaseModel):
    """For HybridRetriever results."""
    skill: Skill
    bm25_norm: float = Field(ge=0.0, le=1.0)
    cosine_norm: float = Field(ge=0.0, le=1.0)
    final_score: float = Field(ge=0.0, le=1.0)


class ASTNode(BaseModel):
    """For ASTAnalyzer. node_id format: 'file.py::function_name::start_line'"""
    node_id: str
    file_path: str
    function_name: str | None = None
    class_name: str | None = None
    start_line: int
    end_line: int
    scope_path: str
    signature: str | None = None

    @field_validator("node_id")
    @classmethod
    def validate_node_id_format(cls, v: str) -> str:
        parts = v.split("::")
        if len(parts) != 3:
            raise ValueError(f"node_id must have exactly 3 parts separated by '::', got: {v!r}")
        return v


class ASTContract(BaseModel):
    """For ASTAnalyzer output. Serialized JSON must be ≤ 4096 bytes."""
    error_type: str
    affected_nodes: list[ASTNode] = []
    raw_excerpt: str | None = None
    is_fallback: bool = False
    source_files: list[str] = []
    total_size_bytes: int = 0


class ErrorDelta(BaseModel):
    """For DeterministicChecker."""
    operation_id: str
    errors_resolved: list[str] = []
    errors_introduced: list[str] = []
    old_error_score: float = Field(ge=0.0)
    new_error_score: float = Field(ge=0.0)
    net_improvement: bool

    ERROR_WEIGHTS: ClassVar[dict[str, int]] = {
        "syntax_error": 10,
        "runtime_error": 7,
        "lint_warning": 1,
    }

    @field_validator("operation_id")
    @classmethod
    def validate_operation_id(cls, v: str) -> str:
        if not is_valid_time_sortable_id(v):
            raise ValueError(f"operation_id must be UUIDv7 or ULID: {v!r}")
        return v

    @classmethod
    def compute_score(cls, errors: list[str]) -> float:
        """Classify errors by keyword matching and sum weighted scores."""
        score = 0.0
        for err in errors:
            err_lower = err.lower()
            if any(k in err_lower for k in ["syntaxerror", "syntax error", "invalid syntax"]):
                score += cls.ERROR_WEIGHTS["syntax_error"]
            elif any(k in err_lower for k in ["runtimeerror", "traceback", "exception", "error:"]):
                score += cls.ERROR_WEIGHTS["runtime_error"]
            else:
                score += cls.ERROR_WEIGHTS["lint_warning"]
        return score


class SLMRouteDecision(BaseModel):
    """For SLMRouter."""
    chosen: str
    confidence: float = Field(ge=0.0, le=1.0)
    top_k: list[dict[str, float]] = []
    llm_fallback_triggered: bool = False


class BudgetStatus(BaseModel):
    """For BudgetGuard."""
    steps_used: int
    steps_remaining: int
    tokens_used: int
    tokens_remaining: int
    repairs_used: int
    repairs_remaining: int
    warning_threshold_reached: bool
    termination_reason: str | None = None


class SessionContext(BaseModel):
    """For Orchestrator. session_id and trace_id must be UUIDv7 or ULID."""
    session_id: str
    notebook_id: str | None = None
    trace_id: str | None = None

    @field_validator("session_id", "trace_id")
    @classmethod
    def validate_time_sortable(cls, v: str | None) -> str | None:
        if v is not None and not is_valid_time_sortable_id(v):
            raise ValueError(f"ID must be UUIDv7 or ULID: {v!r}")
        return v


# ── FailureMemory Models (v6.2 Learning Loop) ─────────────────────────────────

class FailureSurface(BaseModel):
    """Layer 1: Observable - what happened"""
    failure_id: str
    patch_diff: str
    error_text: str
    files_touched: list[str]
    timestamp: str  # ISO format
    session_id: str


class FailurePattern(BaseModel):
    """Layer 2: Semantic - why it failed (LLM-understandable)"""
    pattern_type: Literal[
        "syntax_error",
        "runtime_error",
        "no_op_patch",
        "import_missing",
        "type_mismatch",
        "logic_error",
        "wrong_fix_strategy",
        "wrong_file_modified",
        "test_breaking_change",
        "incomplete_fix",
        "overfix",
        "wrong_assumption",
        "dependency_not_updated",
        "incorrect_refactor_scope",
        "fix_symptom_not_root"
    ]
    cause: str
    location: Literal[
        "top_of_file",
        "function_body",
        "class_definition",
        "end_of_file"
    ]
    action: str
    symbols: list[str]
    signature: str
    
    # v2: Context-aware fields (critical for signal strength)
    context: dict[str, str] = {}  # e.g., {"file_type": "react_component", "framework": "react"}
    attempted_fix: str | None = None  # What was tried but failed
    correct_direction: str | None = None  # What should have been done instead
    
    # v2: Decision-critical fields
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)  # v2: Increased default to pass filter
    anti_pattern_signature: dict[str, list[str]] = {}  # {"error_regex": [...], "code_signal": [...]}
    
    # v4: Intent signatures for precise usage detection (Phase 1d.1)
    usage_signals: list[str] | None = None  # Structured signals to detect pattern usage in patch


class FailureLesson(BaseModel):
    """Layer 3: Strategic - what to do differently (decision impact)"""
    avoid: str
    prefer: str
    confidence: float = Field(ge=0.0, le=1.0)
    applies_to: list[str]
