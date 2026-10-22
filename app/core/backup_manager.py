"""
Backup management for the master spreadsheet.

Backups are organised as:
    <backup_root>/<master_name>/<master_name>_YYYY-MM-DD_HH-MM-SS.xlsx

Only the last MAX_BACKUPS files are kept per master sheet.
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


class BackupManager:
    """Creates and rotates backups of the master spreadsheet."""

    MAX_BACKUPS: int = 10

    def __init__(self, backup_dir: str) -> None:
        self._backup_root: Path = Path(backup_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_backup(self, master_path: str) -> Path:
        """
        Copy *master_path* into the backup directory, then prune old backups.

        Returns:
            The :class:`Path` of the newly created backup file.

        Raises:
            FileNotFoundError: If *master_path* does not exist.
            OSError: If the backup could not be written.
        """
        source = Path(master_path)
        if not source.exists():
            raise FileNotFoundError(f"Planilha mestre não encontrada: {master_path}")

        sheet_name: str = source.stem
        backup_dir: Path = self._backup_root / sheet_name
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp: str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename: str = f"{sheet_name}_{timestamp}{source.suffix}"
        backup_path: Path = backup_dir / backup_filename

        shutil.copy2(source, backup_path)
        self._prune_old_backups(backup_dir, sheet_name, source.suffix)

        return backup_path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _prune_old_backups(self, backup_dir: Path, sheet_name: str, suffix: str) -> None:
        """Delete oldest backups so only ``MAX_BACKUPS`` are retained."""
        pattern = f"{sheet_name}_*{suffix}"
        backups: list[Path] = sorted(
            backup_dir.glob(pattern),
            key=lambda p: p.stat().st_mtime,
        )
        while len(backups) > self.MAX_BACKUPS:
            oldest = backups.pop(0)
            try:
                oldest.unlink()
            except OSError:
                pass
