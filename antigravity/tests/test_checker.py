"""
Tests for DeterministicChecker — Task 4: ErrorDelta + severity scoring + no-op detection.

Includes:
- Unit tests for examine() returning ErrorDelta
- Property test for error normalization stability (Property 12)
"""
import sys
import os
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

# Ensure core is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.checker import DeterministicChecker
from core.schemas import ArtifactCheck, ErrorDelta
from core.id_utils import is_valid_time_sortable_id


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def checker():
    return DeterministicChecker()


def _file_check(path: str) -> ArtifactCheck:
    return ArtifactCheck(type="file_exists", path=path)


# ── Unit Tests ────────────────────────────────────────────────────────────────

class TestExamineReturnsErrorDelta:
    def test_no_previous_errors_no_current_errors_net_improvement_true(self, checker, tmp_path):
        """examine() with no previous_errors and no errors → net_improvement=True."""
        f = tmp_path / "hello.txt"
        f.write_text("hi")
        checks = [ArtifactCheck(type="file_exists", path=str(f))]
        delta = checker.examine(checks, project_root=tmp_path)

        assert isinstance(delta, ErrorDelta)
        assert delta.net_improvement is True
        assert delta.new_error_score == 0.0
        assert delta.old_error_score == 0.0
        assert delta.errors_introduced == []
        assert delta.errors_resolved == []

    def test_no_previous_errors_with_current_errors_net_improvement_false(self, checker, tmp_path):
        """examine() with no previous_errors but current errors → net_improvement=False."""
        checks = [ArtifactCheck(type="file_exists", path="nonexistent_file.txt")]
        delta = checker.examine(checks, project_root=tmp_path)

        assert isinstance(delta, ErrorDelta)
        assert delta.net_improvement is False
        assert delta.new_error_score > 0.0
        assert len(delta.errors_introduced) > 0

    def test_previous_errors_detects_resolved(self, checker, tmp_path):
        """examine() detects errors that were in previous but not in current."""
        f = tmp_path / "file.txt"
        f.write_text("content")
        checks = [ArtifactCheck(type="file_exists", path=str(f))]

        # Simulate previous run had an error for this file
        prev_errors = [f"Missing file: {f}"]
        delta = checker.examine(checks, previous_errors=prev_errors, project_root=tmp_path)

        assert delta.net_improvement is True
        assert len(delta.errors_resolved) > 0

    def test_previous_errors_detects_introduced(self, checker, tmp_path):
        """examine() detects newly introduced errors."""
        checks = [ArtifactCheck(type="file_exists", path="new_missing.txt")]
        prev_errors: list[str] = []
        delta = checker.examine(checks, previous_errors=prev_errors, project_root=tmp_path)

        assert delta.net_improvement is False
        assert len(delta.errors_introduced) > 0

    def test_operation_id_is_valid_time_sortable(self, checker, tmp_path):
        """operation_id in returned ErrorDelta must be a valid ULID or UUIDv7."""
        checks: list[ArtifactCheck] = []
        delta = checker.examine(checks)
        assert is_valid_time_sortable_id(delta.operation_id)

    def test_rollback_scenario_net_improvement_false_when_score_increases(self, checker, tmp_path):
        """When new_error_score > old_error_score, net_improvement=False (rollback should trigger)."""
        # Previous run had 0 errors
        prev_errors: list[str] = []
        # Current run has a syntax error (weight=10)
        checks = [ArtifactCheck(type="file_exists", path="missing.py")]
        delta = checker.examine(checks, previous_errors=prev_errors, project_root=tmp_path)

        assert delta.net_improvement is False
        assert delta.new_error_score > delta.old_error_score

    def test_backward_compat_keyword_project_root(self, checker, tmp_path):
        """examine(checks, project_root=some_path) keyword arg still works."""
        f = tmp_path / "compat.txt"
        f.write_text("data")
        checks = [ArtifactCheck(type="file_exists", path=str(f))]
        delta = checker.examine(checks, project_root=str(tmp_path))

        assert isinstance(delta, ErrorDelta)
        assert delta.net_improvement is True


class TestNormalizeErrors:
    def test_strips_windows_paths(self, checker):
        errors = [r"Missing file: C:\Users\<YOUR_USERNAME>\project\src\main.py"]
        result = checker._normalize_errors(errors)
        assert "C:\\" not in result[0]
        assert "<path>" in result[0]

    def test_strips_unix_paths(self, checker):
        errors = ["Error in /home/user/project/src/app.py line 42"]
        result = checker._normalize_errors(errors)
        assert "/home/user" not in result[0]

    def test_strips_iso_timestamps(self, checker):
        errors = ["Error at 2024-01-15T12:34:56.789Z in module"]
        result = checker._normalize_errors(errors)
        assert "2024-01-15" not in result[0]
        assert "<timestamp>" in result[0]

    def test_strips_hex_addresses(self, checker):
        errors = ["Object at 0xDEADBEEF failed"]
        result = checker._normalize_errors(errors)
        assert "0xDEADBEEF" not in result[0]
        assert "<addr>" in result[0]

    def test_same_root_cause_different_path_normalizes_equal(self, checker):
        e1 = r"Missing file: C:\project_a\src\utils.py"
        e2 = r"Missing file: C:\project_b\src\utils.py"
        r1 = checker._normalize_errors([e1])
        r2 = checker._normalize_errors([e2])
        assert r1 == r2


# ── Property-Based Test ───────────────────────────────────────────────────────

# Feature: antigravity-architecture-upgrade, Property 12: Error Normalization Stability
@given(
    root_cause=st.text(min_size=5, max_size=80, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd", "Pc"),
        whitelist_characters=" :_-"
    )),
    path1=st.text(min_size=3, max_size=30, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="_-"
    )),
    path2=st.text(min_size=3, max_size=30, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="_-"
    )),
)
@settings(max_examples=100)
def test_property_12_normalization_stability(root_cause, path1, path2):
    """
    **Validates: Requirements 3.5**
    Property 12: Error Normalization Stability
    Two errors with the same root cause but different paths normalize to the same string.
    """
    checker = DeterministicChecker()
    e1 = f"Error: {root_cause} in /home/{path1}/file.py"
    e2 = f"Error: {root_cause} in /home/{path2}/file.py"
    r1 = checker._normalize_errors([e1])
    r2 = checker._normalize_errors([e2])
    assert r1 == r2
