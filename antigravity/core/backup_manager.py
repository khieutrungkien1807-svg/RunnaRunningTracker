"""
BackupManager — Atomic backup and rollback for file operations.

Provides session/operation-scoped backup with manifest-based tracking,
SHA-256 filename collision avoidance, and safe rollback with CRITICAL logging.

Requirements: 3.3, 3.6, 3.7, 3.8
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

# Default backup root: antigravity/backups/
_DEFAULT_BACKUP_ROOT = Path(__file__).parent.parent / "backups"

_MANIFEST_FILENAME = "_manifest.json"


def _sha256_of_path(path: str) -> str:
    """Return SHA-256 hex digest of the original path string (for filename)."""
    return hashlib.sha256(path.encode("utf-8")).hexdigest()


class BackupManager:
    """
    Manages atomic file backups and rollbacks scoped by session_id / operation_id.

    Backup layout:
        <backup_root>/<session_id>/<operation_id>/
            _manifest.json          # maps original_path → backup_filename
            <sha256_of_path>        # actual file content
    """

    def __init__(self, backup_root: Path | None = None) -> None:
        self._backup_root: Path = backup_root if backup_root is not None else _DEFAULT_BACKUP_ROOT

    # ── Public API ────────────────────────────────────────────────────────────

    def create_backup(
        self,
        session_id: str,
        operation_id: str,
        file_paths: list[str],
    ) -> None:
        """
        Copy files into backup_root/{session_id}/{operation_id}/.

        - Preserves file content using shutil.copy2 (metadata preserved).
        - Backup filename = SHA-256 of original path (avoids collisions).
        - Idempotent: same file + same operation_id → overwrites existing backup.
        - Creates parent directories as needed.
        - Updates _manifest.json with original_path → backup_filename mapping.
        """
        backup_dir = self._backup_path(session_id, operation_id)
        backup_dir.mkdir(parents=True, exist_ok=True)

        manifest = self._load_manifest(backup_dir)

        for path_str in file_paths:
            src = Path(path_str)
            if not src.exists():
                logger.warning("BackupManager: source file does not exist, skipping: %s", path_str)
                continue

            backup_filename = _sha256_of_path(path_str)
            dest = backup_dir / backup_filename

            shutil.copy2(src, dest)
            manifest[path_str] = backup_filename
            logger.debug("BackupManager: backed up %s → %s", path_str, dest)

        self._save_manifest(backup_dir, manifest)

    def rollback(self, session_id: str, operation_id: str) -> None:
        """
        Restore files from backup to their original locations.

        - Reads _manifest.json to find original_path → backup_filename mapping.
        - If backup dir or individual file is missing → log CRITICAL, continue (no crash).
        """
        backup_dir = self._backup_path(session_id, operation_id)

        if not backup_dir.exists():
            logger.critical(
                "BackupManager: backup directory missing, cannot rollback. "
                "session_id=%s operation_id=%s path=%s",
                session_id,
                operation_id,
                backup_dir,
            )
            return

        manifest = self._load_manifest(backup_dir)
        if not manifest:
            logger.critical(
                "BackupManager: manifest missing or empty, cannot rollback. "
                "session_id=%s operation_id=%s",
                session_id,
                operation_id,
            )
            return

        for original_path, backup_filename in manifest.items():
            backup_file = backup_dir / backup_filename
            if not backup_file.exists():
                logger.critical(
                    "BackupManager: backup file missing for %s (expected %s), skipping.",
                    original_path,
                    backup_file,
                )
                continue

            dest = Path(original_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_file, dest)
            logger.debug("BackupManager: restored %s → %s", backup_file, original_path)

    def get_backup_files(self, session_id: str, operation_id: str) -> list[Path]:
        """
        List all files in the backup directory (excluding the manifest).

        Returns an empty list if the backup directory does not exist.
        """
        backup_dir = self._backup_path(session_id, operation_id)
        if not backup_dir.exists():
            return []
        return [
            p for p in backup_dir.iterdir()
            if p.is_file() and p.name != _MANIFEST_FILENAME
        ]

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _backup_path(self, session_id: str, operation_id: str) -> Path:
        """Return the backup directory path for a given session/operation pair."""
        return self._backup_root / session_id / operation_id

    def _load_manifest(self, backup_dir: Path) -> dict[str, str]:
        """Load manifest JSON from backup_dir. Returns empty dict if missing."""
        manifest_path = backup_dir / _MANIFEST_FILENAME
        if not manifest_path.exists():
            return {}
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("BackupManager: failed to read manifest at %s: %s", manifest_path, exc)
            return {}

    def _save_manifest(self, backup_dir: Path, manifest: dict[str, str]) -> None:
        """Persist manifest JSON to backup_dir."""
        manifest_path = backup_dir / _MANIFEST_FILENAME
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
