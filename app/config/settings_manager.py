"""
Manages loading and persisting application settings to a local JSON file.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.models.models import AppSettings, ColumnMapping, Mapping


class SettingsManager:
    """Loads and saves :class:`AppSettings` to ``~/.concat-excel/settings.json``."""

    _APP_DIR: str = ".concat-excel"
    _SETTINGS_FILENAME: str = "settings.json"

    def __init__(self) -> None:
        self._settings_dir: Path = Path.home() / self._APP_DIR
        self._settings_file: Path = self._settings_dir / self._SETTINGS_FILENAME
        try:
            self._settings_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> AppSettings:
        """Load settings from disk. Returns default settings if file is absent or corrupt."""
        try:
            if not self._settings_file.exists():
                return self._default_settings()

            with open(self._settings_file, "r", encoding="utf-8") as fh:
                raw: dict[str, Any] = json.load(fh)
            return self._deserialise(raw)
        except (json.JSONDecodeError, KeyError, TypeError, OSError):
            return self._default_settings()

    def save(self, settings: AppSettings) -> None:
        """Persist *settings* to disk."""
        data = self._serialise(settings)
        try:
            self._settings_dir.mkdir(parents=True, exist_ok=True)
            with open(self._settings_file, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _default_settings(self) -> AppSettings:
        default_backup_dir = Path.home() / "Documents" / "ConcatExcel" / "Backups"
        return AppSettings(backup_dir=str(default_backup_dir))

    def _serialise(self, settings: AppSettings) -> dict[str, Any]:
        return {
            "master_sheet_path": settings.master_sheet_path,
            "backup_dir": settings.backup_dir,
            "theme": settings.theme,
            "mappings": [
                {
                    "id": m.id,
                    "name": m.name,
                    "columns": [
                        {"source": col.source, "target": col.target}
                        for col in m.columns
                    ],
                }
                for m in settings.mappings
            ],
        }

    def _deserialise(self, data: dict[str, Any]) -> AppSettings:
        mappings: list[Mapping] = []
        for m_data in data.get("mappings", []):
            columns: list[ColumnMapping] = [
                ColumnMapping(source=c["source"], target=c["target"])
                for c in m_data.get("columns", [])
                if "source" in c and "target" in c
            ]
            mappings.append(
                Mapping(
                    id=m_data.get("id", ""),
                    name=m_data.get("name", "Sem nome"),
                    columns=columns,
                )
            )

        return AppSettings(
            master_sheet_path=data.get("master_sheet_path"),
            backup_dir=data.get("backup_dir"),
            mappings=mappings,
            theme=data.get("theme", "dark"),
        )
