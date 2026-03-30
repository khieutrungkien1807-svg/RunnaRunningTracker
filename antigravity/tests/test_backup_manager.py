"""
Tests for BackupManager — atomic backup and rollback.

Covers:
- create_backup creates files in correct location
- create_backup is idempotent (same operation_id → overwrite, no duplicate)
- rollback restores file content correctly (verified by file read)
- rollback with missing backup logs CRITICAL warning and doesn't crash
- _backup_path returns correct path structure

Property tests:
- Property 10: Rollback Round-Trip Invariant (Requirements 3.3, 3.8)
- Property 11: Backup Idempotence (Requirements 3.7)
"""

from __future__ import annotations

import hashlib
import logging
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from core.backup_manager import BackupManager, _sha256_of_path


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_backup_root(tmp_path: Path) -> Path:
    return tmp_path / "backups"


@pytest.fixture
def manager(tmp_backup_root: Path) -> BackupManager:
    return BackupManager(backup_root=tmp_backup_root)


def _write_file(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _sha256_content(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ── Unit Tests ────────────────────────────────────────────────────────────────


class TestCreateBackup:
    def test_creates_backup_file_in_correct_location(
        self, manager: BackupManager, tmp_path: Path, tmp_backup_root: Path
    ) -> None:
        src = _write_file(tmp_path / "src" / "foo.py", "print('hello')")
        session_id = "session-001"
        op_id = "op-001"

        manager.create_backup(session_id, op_id, [str(src)])

        backup_dir = tmp_backup_root / session_id / op_id
        assert backup_dir.exists()
        backup_filename = _sha256_of_path(str(src))
        assert (backup_dir / backup_filename).exists()

    def test_backup_content_matches_original(
        self, manager: BackupManager, tmp_path: Path
    ) -> None:
        content = "original content 123"
        src = _write_file(tmp_path / "file.txt", content)

        manager.create_backup("s1", "o1", [str(src)])

        backup_dir = manager._backup_path("s1", "o1")
        backup_file = backup_dir / _sha256_of_path(str(src))
        assert backup_file.read_text(encoding="utf-8") == content

    def test_creates_manifest_with_correct_mapping(
        self, manager: BackupManager, tmp_path: Path
    ) -> None:
        src = _write_file(tmp_path / "a.py", "x = 1")

        manager.create_backup("s1", "o1", [str(src)])

        manifest = manager._load_manifest(manager._backup_path("s1", "o1"))
        assert str(src) in manifest
        assert manifest[str(src)] == _sha256_of_path(str(src))

    def test_creates_parent_dirs_if_not_exist(
        self, manager: BackupManager, tmp_path: Path
    ) -> None:
        src = _write_file(tmp_path / "deep" / "nested" / "file.py", "pass")
        # backup root doesn't exist yet — should be created
        manager.create_backup("new-session", "new-op", [str(src)])
        assert manager._backup_path("new-session", "new-op").exists()

    def test_skips_nonexistent_source_file(
        self, manager: BackupManager, tmp_path: Path
    ) -> None:
        missing = str(tmp_path / "does_not_exist.py")
        # Should not raise
        manager.create_backup("s1", "o1", [missing])
        backup_dir = manager._backup_path("s1", "o1")
        # Manifest should not contain the missing file
        manifest = manager._load_manifest(backup_dir)
        assert missing not in manifest


class TestCreateBackupIdempotence:
    def test_calling_twice_same_operation_id_does_not_duplicate(
        self, manager: BackupManager, tmp_path: Path
    ) -> None:
        src = _write_file(tmp_path / "file.py", "v1")

        manager.create_backup("s1", "o1", [str(src)])
        # Modify source, call again with same operation_id
        src.write_text("v2", encoding="utf-8")
        manager.create_backup("s1", "o1", [str(src)])

        backup_dir = manager._backup_path("s1", "o1")
        data_files = [
            p for p in backup_dir.iterdir()
            if p.is_file() and p.name != "_manifest.json"
        ]
        # Still only one backup file for this one source file
        assert len(data_files) == 1

    def test_second_call_overwrites_with_latest_content(
        self, manager: BackupManager, tmp_path: Path
    ) -> None:
        src = _write_file(tmp_path / "file.py", "first")
        manager.create_backup("s1", "o1", [str(src)])

        src.write_text("second", encoding="utf-8")
        manager.create_backup("s1", "o1", [str(src)])

        backup_dir = manager._backup_path("s1", "o1")
        backup_file = backup_dir / _sha256_of_path(str(src))
        assert backup_file.read_text(encoding="utf-8") == "second"

    def test_multiple_files_same_operation_id_no_duplicates(
        self, manager: BackupManager, tmp_path: Path
    ) -> None:
        files = [
            _write_file(tmp_path / f"f{i}.py", f"content {i}")
            for i in range(3)
        ]
        paths = [str(f) for f in files]

        manager.create_backup("s1", "o1", paths)
        manager.create_backup("s1", "o1", paths)  # second call

        backup_dir = manager._backup_path("s1", "o1")
        data_files = [
            p for p in backup_dir.iterdir()
            if p.is_file() and p.name != "_manifest.json"
        ]
        assert len(data_files) == len(files)


class TestRollback:
    def test_rollback_restores_file_content(
        self, manager: BackupManager, tmp_path: Path
    ) -> None:
        original_content = "original content"
        src = _write_file(tmp_path / "file.py", original_content)

        manager.create_backup("s1", "o1", [str(src)])

        # Simulate a patch
        src.write_text("patched content", encoding="utf-8")
        assert src.read_text() == "patched content"

        manager.rollback("s1", "o1")

        assert src.read_text(encoding="utf-8") == original_content

    def test_rollback_verifies_sha256_match(
        self, manager: BackupManager, tmp_path: Path
    ) -> None:
        content = "important data"
        src = _write_file(tmp_path / "data.py", content)
        original_hash = _sha256_content(src)

        manager.create_backup("s1", "o1", [str(src)])
        src.write_text("corrupted", encoding="utf-8")
        manager.rollback("s1", "o1")

        assert _sha256_content(src) == original_hash

    def test_rollback_multiple_files(
        self, manager: BackupManager, tmp_path: Path
    ) -> None:
        files = {
            _write_file(tmp_path / f"f{i}.py", f"original {i}"): f"original {i}"
            for i in range(3)
        }
        paths = [str(f) for f in files]

        manager.create_backup("s1", "o1", paths)

        for f in files:
            f.write_text("patched", encoding="utf-8")

        manager.rollback("s1", "o1")

        for f, expected in files.items():
            assert f.read_text(encoding="utf-8") == expected

    def test_rollback_missing_backup_dir_logs_critical_no_crash(
        self, manager: BackupManager, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.CRITICAL, logger="core.backup_manager"):
            # Should not raise
            manager.rollback("nonexistent-session", "nonexistent-op")

        assert any("backup directory missing" in r.message for r in caplog.records)

    def test_rollback_missing_individual_file_logs_critical_continues(
        self, manager: BackupManager, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        src = _write_file(tmp_path / "file.py", "data")
        manager.create_backup("s1", "o1", [str(src)])

        # Manually remove the backup file to simulate corruption
        backup_dir = manager._backup_path("s1", "o1")
        backup_file = backup_dir / _sha256_of_path(str(src))
        backup_file.unlink()

        with caplog.at_level(logging.CRITICAL, logger="core.backup_manager"):
            manager.rollback("s1", "o1")  # must not raise

        assert any("backup file missing" in r.message for r in caplog.records)


class TestBackupPath:
    def test_backup_path_returns_correct_structure(
        self, manager: BackupManager, tmp_backup_root: Path
    ) -> None:
        result = manager._backup_path("my-session", "my-op")
        assert result == tmp_backup_root / "my-session" / "my-op"

    def test_backup_path_different_sessions_are_isolated(
        self, manager: BackupManager, tmp_backup_root: Path
    ) -> None:
        p1 = manager._backup_path("session-A", "op-1")
        p2 = manager._backup_path("session-B", "op-1")
        assert p1 != p2

    def test_backup_path_different_operations_are_isolated(
        self, manager: BackupManager, tmp_backup_root: Path
    ) -> None:
        p1 = manager._backup_path("session-A", "op-1")
        p2 = manager._backup_path("session-A", "op-2")
        assert p1 != p2


class TestGetBackupFiles:
    def test_returns_empty_list_when_no_backup(self, manager: BackupManager) -> None:
        result = manager.get_backup_files("no-session", "no-op")
        assert result == []

    def test_returns_backup_files_excluding_manifest(
        self, manager: BackupManager, tmp_path: Path
    ) -> None:
        files = [_write_file(tmp_path / f"f{i}.py", f"c{i}") for i in range(2)]
        manager.create_backup("s1", "o1", [str(f) for f in files])

        result = manager.get_backup_files("s1", "o1")
        names = {p.name for p in result}

        assert "_manifest.json" not in names
        assert len(result) == 2


# ── Property-Based Tests ──────────────────────────────────────────────────────


@given(
    file_content=st.text(min_size=0, max_size=10000),
    patch_content=st.text(min_size=0, max_size=10000),
)
@settings(max_examples=100)
def test_rollback_round_trip_invariant(file_content: str, patch_content: str) -> None:
    """
    # Feature: antigravity-architecture-upgrade, Property 10: Rollback Round-Trip Invariant
    **Validates: Requirements 3.3, 3.8**

    For any file f and patch operation p, if create_backup() is called before
    applying p, then after rollback() the content of f must be identical to
    the content before p was applied (verified by SHA-256 hash).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src = tmp / "target.py"
        src.write_text(file_content, encoding="utf-8")
        original_hash = hashlib.sha256(src.read_bytes()).hexdigest()

        backup_root = tmp / "backups"
        manager = BackupManager(backup_root=backup_root)

        manager.create_backup("session-prop10", "op-prop10", [str(src)])

        # Apply patch
        src.write_text(patch_content, encoding="utf-8")

        manager.rollback("session-prop10", "op-prop10")

        restored_hash = hashlib.sha256(src.read_bytes()).hexdigest()
        assert restored_hash == original_hash


@given(
    file_contents=st.lists(
        st.text(min_size=0, max_size=1000),
        min_size=1,
        max_size=10,
    ),
    n_calls=st.integers(min_value=2, max_value=5),
)
@settings(max_examples=100, deadline=None)
def test_backup_idempotence(file_contents: list[str], n_calls: int) -> None:
    """
    # Feature: antigravity-architecture-upgrade, Property 11: Backup Idempotence
    **Validates: Requirements 3.7**

    Calling create_backup() multiple times with the same operation_id must
    result in exactly one backup per unique file (overwrite, no duplicates).
    The number of data files in the backup dir must equal the number of unique
    source files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src_files = []
        for i, content in enumerate(file_contents):
            f = tmp / f"file_{i}.py"
            f.write_text(content, encoding="utf-8")
            src_files.append(str(f))

        backup_root = tmp / "backups"
        manager = BackupManager(backup_root=backup_root)

        for _ in range(n_calls):
            manager.create_backup("session-prop11", "op-prop11", src_files)

        backup_dir = manager._backup_path("session-prop11", "op-prop11")
        data_files = [
            p for p in backup_dir.iterdir()
            if p.is_file() and p.name != "_manifest.json"
        ]

        # Number of backup data files == number of unique source files
        assert len(data_files) == len(set(src_files))
