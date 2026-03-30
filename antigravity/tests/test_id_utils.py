"""
Unit tests for antigravity/core/id_utils.py

Tests basic functionality of ULID, UUIDv7, validation, and new_id().
"""

import re
import time

import pytest
from hypothesis import given, settings, strategies as st

from core.id_utils import (
    ULID_PATTERN,
    UUIDV7_PATTERN,
    generate_ulid,
    generate_uuidv7,
    is_valid_time_sortable_id,
    new_id,
)


# ── generate_ulid ─────────────────────────────────────────────────────────────

class TestGenerateUlid:
    def test_returns_26_chars(self):
        uid = generate_ulid()
        assert len(uid) == 26

    def test_matches_crockford_pattern(self):
        uid = generate_ulid()
        assert ULID_PATTERN.match(uid), f"ULID '{uid}' does not match pattern"

    def test_unique_ids(self):
        ids = {generate_ulid() for _ in range(100)}
        assert len(ids) == 100

    def test_time_sortable(self):
        id1 = generate_ulid()
        time.sleep(0.002)
        id2 = generate_ulid()
        assert id1 < id2, "Later ULID should be lexicographically greater"

    def test_uppercase_only(self):
        uid = generate_ulid()
        assert uid == uid.upper()

    def test_no_invalid_crockford_chars(self):
        # Crockford Base32 excludes I, L, O, U
        uid = generate_ulid()
        for ch in "ILOU":
            assert ch not in uid, f"Invalid Crockford char '{ch}' found in ULID"


# ── generate_uuidv7 ───────────────────────────────────────────────────────────

class TestGenerateUuidv7:
    def test_matches_uuid_format(self):
        uid = generate_uuidv7()
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        )
        assert uuid_pattern.match(uid), f"UUIDv7 '{uid}' does not match UUID format"

    def test_version_is_7(self):
        uid = generate_uuidv7()
        # Version is the first char of the 3rd group
        version_char = uid.split("-")[2][0]
        assert version_char == "7", f"Expected version 7, got '{version_char}'"

    def test_variant_bits(self):
        uid = generate_uuidv7()
        # Variant: first char of 4th group must be 8, 9, a, or b
        variant_char = uid.split("-")[3][0]
        assert variant_char in "89ab", f"Invalid variant char '{variant_char}'"

    def test_unique_ids(self):
        ids = {generate_uuidv7() for _ in range(100)}
        assert len(ids) == 100

    def test_time_sortable(self):
        id1 = generate_uuidv7()
        time.sleep(0.002)
        id2 = generate_uuidv7()
        assert id1 < id2, "Later UUIDv7 should be lexicographically greater"

    def test_matches_validation_pattern(self):
        uid = generate_uuidv7()
        assert UUIDV7_PATTERN.match(uid)


# ── is_valid_time_sortable_id ─────────────────────────────────────────────────

class TestIsValidTimeSortableId:
    def test_valid_ulid(self):
        uid = generate_ulid()
        assert is_valid_time_sortable_id(uid) is True

    def test_valid_uuidv7(self):
        uid = generate_uuidv7()
        assert is_valid_time_sortable_id(uid) is True

    def test_invalid_empty_string(self):
        assert is_valid_time_sortable_id("") is False

    def test_invalid_uuid4(self):
        import uuid
        uid = str(uuid.uuid4())
        assert is_valid_time_sortable_id(uid) is False

    def test_invalid_random_string(self):
        assert is_valid_time_sortable_id("not-an-id") is False

    def test_invalid_wrong_length_ulid(self):
        assert is_valid_time_sortable_id("01ARZ3NDEKTSV4RRFFQ69G5FA") is False  # 25 chars

    def test_invalid_non_string(self):
        assert is_valid_time_sortable_id(None) is False  # type: ignore
        assert is_valid_time_sortable_id(12345) is False  # type: ignore

    def test_accepts_uuidv7_case_insensitive(self):
        uid = generate_uuidv7()
        assert is_valid_time_sortable_id(uid.upper()) is True
        assert is_valid_time_sortable_id(uid.lower()) is True

    def test_invalid_uuidv4_version(self):
        # A UUID with version 4 should not be accepted
        assert is_valid_time_sortable_id("550e8400-e29b-41d4-a716-446655440000") is False

    def test_invalid_ulid_with_lowercase(self):
        uid = generate_ulid().lower()
        assert is_valid_time_sortable_id(uid) is False


# ── new_id ────────────────────────────────────────────────────────────────────

class TestNewId:
    def test_returns_valid_id(self):
        uid = new_id()
        assert is_valid_time_sortable_id(uid) is True

    def test_returns_ulid_by_default(self):
        uid = new_id()
        # ULID is 26 chars with no hyphens
        assert len(uid) == 26
        assert "-" not in uid

    def test_unique_ids(self):
        ids = {new_id() for _ in range(50)}
        assert len(ids) == 50

    def test_time_sortable(self):
        id1 = new_id()
        time.sleep(0.002)
        id2 = new_id()
        assert id1 < id2


# ── Property-Based Tests ──────────────────────────────────────────────────────

# Feature: antigravity-architecture-upgrade, Property 20: Time-Sortable ID Invariant
# **Validates: Requirements 8.1, 8.3**
@given(n_ids=st.integers(min_value=2, max_value=50))
@settings(max_examples=100, deadline=None)
def test_time_sortable_id_invariant(n_ids: int) -> None:
    """
    Property 20: For any sequence of IDs generated in chronological order,
    sorting them lexicographically must produce the same order as their
    creation timestamps.
    
    This validates that all system-generated IDs (session_id, operation_id,
    patch_id, trace_id) maintain time-sortable ordering.
    """
    ids = []
    for _ in range(n_ids):
        ids.append(new_id())
        time.sleep(0.001)  # Small delay to ensure timestamp difference
    
    # Verify all IDs are valid
    assert all(is_valid_time_sortable_id(id_) for id_ in ids)
    
    # Property: lexicographic sort == chronological order
    sorted_ids = sorted(ids)
    assert sorted_ids == ids, (
        f"Time-sortable invariant violated: "
        f"chronological order {ids} != lexicographic order {sorted_ids}"
    )
