"""
Unit tests for new Pydantic schemas in antigravity/core/schemas.py.
Covers: ASTNode node_id validator, ErrorDelta.compute_score(),
        SessionContext ID validation, ErrorDelta operation_id validation.
"""
import sys
import os

# Ensure the antigravity/core package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from hypothesis import given, settings, strategies as st
from pydantic import ValidationError
from core.schemas import ASTNode, ASTContract, ErrorDelta, SessionContext
from core.id_utils import generate_ulid, generate_uuidv7


# ── ASTNode node_id validator ─────────────────────────────────────────────────

class TestASTNodeValidator:
    def test_valid_node_id(self):
        node = ASTNode(
            node_id="myfile.py::my_function::42",
            file_path="myfile.py",
            start_line=42,
            end_line=55,
            scope_path="my_function",
        )
        assert node.node_id == "myfile.py::my_function::42"

    def test_valid_node_id_with_class(self):
        node = ASTNode(
            node_id="module.py::MyClass.method::10",
            file_path="module.py",
            start_line=10,
            end_line=20,
            scope_path="MyClass.method",
        )
        assert node.node_id == "module.py::MyClass.method::10"

    def test_invalid_node_id_two_parts(self):
        with pytest.raises(ValidationError) as exc_info:
            ASTNode(
                node_id="myfile.py::my_function",
                file_path="myfile.py",
                start_line=1,
                end_line=5,
                scope_path="my_function",
            )
        assert "3 parts" in str(exc_info.value)

    def test_invalid_node_id_four_parts(self):
        with pytest.raises(ValidationError):
            ASTNode(
                node_id="a::b::c::d",
                file_path="a",
                start_line=1,
                end_line=2,
                scope_path="b",
            )

    def test_invalid_node_id_no_separator(self):
        with pytest.raises(ValidationError):
            ASTNode(
                node_id="myfile_my_function_42",
                file_path="myfile.py",
                start_line=42,
                end_line=50,
                scope_path="my_function",
            )

    def test_invalid_node_id_empty_string(self):
        with pytest.raises(ValidationError):
            ASTNode(
                node_id="",
                file_path="myfile.py",
                start_line=1,
                end_line=2,
                scope_path="fn",
            )

    def test_optional_fields_default_none(self):
        node = ASTNode(
            node_id="f.py::fn::1",
            file_path="f.py",
            start_line=1,
            end_line=5,
            scope_path="fn",
        )
        assert node.function_name is None
        assert node.class_name is None
        assert node.signature is None


# ── ErrorDelta.compute_score() ────────────────────────────────────────────────

class TestErrorDeltaComputeScore:
    def test_syntax_error_weight(self):
        score = ErrorDelta.compute_score(["SyntaxError: invalid syntax"])
        assert score == 10.0

    def test_syntax_error_lowercase(self):
        score = ErrorDelta.compute_score(["syntax error near token"])
        assert score == 10.0

    def test_invalid_syntax_keyword(self):
        score = ErrorDelta.compute_score(["invalid syntax at line 5"])
        assert score == 10.0

    def test_runtime_error_weight(self):
        score = ErrorDelta.compute_score(["RuntimeError: something went wrong"])
        assert score == 7.0

    def test_traceback_weight(self):
        score = ErrorDelta.compute_score(["Traceback (most recent call last):"])
        assert score == 7.0

    def test_exception_keyword(self):
        score = ErrorDelta.compute_score(["Exception raised in handler"])
        assert score == 7.0

    def test_error_colon_keyword(self):
        score = ErrorDelta.compute_score(["ValueError: invalid value"])
        assert score == 7.0

    def test_lint_warning_weight(self):
        score = ErrorDelta.compute_score(["unused variable 'x'"])
        assert score == 1.0

    def test_empty_list(self):
        assert ErrorDelta.compute_score([]) == 0.0

    def test_multiple_errors_additive(self):
        errors = [
            "SyntaxError: invalid syntax",   # 10
            "RuntimeError: crash",            # 7
            "unused import",                  # 1
        ]
        assert ErrorDelta.compute_score(errors) == 18.0

    def test_adding_one_error_increases_score(self):
        base = ["unused import"]
        extended = ["unused import", "SyntaxError: bad token"]
        assert ErrorDelta.compute_score(extended) == ErrorDelta.compute_score(base) + 10


# ── ErrorDelta operation_id validation ───────────────────────────────────────

class TestErrorDeltaOperationId:
    def _make_delta(self, operation_id: str) -> ErrorDelta:
        return ErrorDelta(
            operation_id=operation_id,
            old_error_score=5.0,
            new_error_score=3.0,
            net_improvement=True,
        )

    def test_valid_ulid(self):
        ulid = generate_ulid()
        delta = self._make_delta(ulid)
        assert delta.operation_id == ulid

    def test_valid_uuidv7(self):
        uuid7 = generate_uuidv7()
        delta = self._make_delta(uuid7)
        assert delta.operation_id == uuid7

    def test_invalid_plain_string(self):
        with pytest.raises(ValidationError) as exc_info:
            self._make_delta("not-a-valid-id")
        assert "UUIDv7 or ULID" in str(exc_info.value)

    def test_invalid_uuidv4(self):
        # UUIDv4 should fail (version digit is 4, not 7)
        with pytest.raises(ValidationError):
            self._make_delta("550e8400-e29b-41d4-a716-446655440000")

    def test_invalid_empty_string(self):
        with pytest.raises(ValidationError):
            self._make_delta("")


# ── SessionContext ID validation ──────────────────────────────────────────────

class TestSessionContextValidation:
    def test_valid_session_id_ulid(self):
        ctx = SessionContext(session_id=generate_ulid())
        assert ctx.trace_id is None
        assert ctx.notebook_id is None

    def test_valid_session_id_uuidv7(self):
        ctx = SessionContext(session_id=generate_uuidv7())
        assert ctx.session_id is not None

    def test_valid_trace_id(self):
        ctx = SessionContext(
            session_id=generate_ulid(),
            trace_id=generate_uuidv7(),
        )
        assert ctx.trace_id is not None

    def test_trace_id_none_allowed(self):
        ctx = SessionContext(session_id=generate_ulid(), trace_id=None)
        assert ctx.trace_id is None

    def test_invalid_session_id(self):
        with pytest.raises(ValidationError) as exc_info:
            SessionContext(session_id="bad-id")
        assert "UUIDv7 or ULID" in str(exc_info.value)

    def test_invalid_trace_id(self):
        with pytest.raises(ValidationError):
            SessionContext(
                session_id=generate_ulid(),
                trace_id="not-valid",
            )

    def test_notebook_id_is_free_string(self):
        # notebook_id has no ID format constraint
        ctx = SessionContext(
            session_id=generate_ulid(),
            notebook_id="my-notebook-123",
        )
        assert ctx.notebook_id == "my-notebook-123"


# ── Property-Based Tests ──────────────────────────────────────────────────────

# Feature: antigravity-architecture-upgrade, Property 9: ErrorDelta Score Computation
# **Validates: Requirements 3.1**
@given(
    errors=st.lists(
        st.sampled_from([
            "SyntaxError: invalid syntax",
            "RuntimeError: crash",
            "unused variable",
            "Traceback (most recent call last):",
            "Exception: something failed",
            "lint warning: style issue",
        ]),
        min_size=0,
        max_size=20,
    )
)
@settings(max_examples=100, deadline=None)
def test_error_delta_score_computation_property(errors: list[str]) -> None:
    """
    Property 9: For any list of errors, ErrorDelta.compute_score(errors)
    must equal Σ(weight[type] * count) with weights:
    - syntax_error=10
    - runtime_error=7
    - lint_warning=1
    
    Adding one error to the list must increase the score by exactly
    the weight of that error's type.
    """
    base_score = ErrorDelta.compute_score(errors)
    
    # Verify score is non-negative
    assert base_score >= 0.0
    
    # Test additivity: adding a SyntaxError increases score by 10
    errors_with_syntax = errors + ["SyntaxError: new error"]
    new_score = ErrorDelta.compute_score(errors_with_syntax)
    assert new_score == base_score + 10.0, (
        f"Adding SyntaxError should increase score by 10, "
        f"but {new_score} != {base_score} + 10"
    )
    
    # Test additivity: adding a RuntimeError increases score by 7
    errors_with_runtime = errors + ["RuntimeError: new error"]
    runtime_score = ErrorDelta.compute_score(errors_with_runtime)
    assert runtime_score == base_score + 7.0, (
        f"Adding RuntimeError should increase score by 7, "
        f"but {runtime_score} != {base_score} + 7"
    )
    
    # Test additivity: adding a lint warning increases score by 1
    errors_with_lint = errors + ["unused import"]
    lint_score = ErrorDelta.compute_score(errors_with_lint)
    assert lint_score == base_score + 1.0, (
        f"Adding lint warning should increase score by 1, "
        f"but {lint_score} != {base_score} + 1"
    )


# Feature: antigravity-architecture-upgrade, Property 7: Node ID Format Invariant
# **Validates: Requirements 2.7**
@given(
    filename=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="._-"
    )),
    function_name=st.text(min_size=1, max_size=30, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"
    )),
    line_number=st.integers(min_value=1, max_value=10000),
)
@settings(max_examples=100, deadline=None)
def test_node_id_format_invariant(filename: str, function_name: str, line_number: int) -> None:
    """
    Property 7: For any Python file parsed by ASTAnalyzer, all node_id values
    in ASTContract.affected_nodes must match the format:
    "<filename>::<function_name>::<start_line>"
    
    Three parts separated by "::", with the last part being a positive integer.
    """
    node_id = f"{filename}::{function_name}::{line_number}"
    
    # Create ASTNode with this node_id
    node = ASTNode(
        node_id=node_id,
        file_path=filename,
        start_line=line_number,
        end_line=line_number + 10,
        scope_path=function_name,
    )
    
    # Verify format: must have exactly 3 parts
    parts = node.node_id.split("::")
    assert len(parts) == 3, f"node_id must have 3 parts, got {len(parts)}: {node.node_id}"
    
    # Verify last part is numeric
    assert parts[2].isdigit(), f"Last part must be numeric, got: {parts[2]}"
    
    # Verify last part matches line number
    assert int(parts[2]) == line_number
