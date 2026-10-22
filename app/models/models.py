"""
Data models for the Concat Excel application.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ColumnMapping:
    """Represents a single column mapping between source and target sheets."""

    source: str
    target: str


@dataclass
class Mapping:
    """A named set of column mappings that can be reused across import sessions."""

    name: str
    columns: list[ColumnMapping] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class AppSettings:
    """Persistent application settings serialised to JSON on disk."""

    master_sheet_path: Optional[str] = None
    backup_dir: Optional[str] = None
    mappings: list[Mapping] = field(default_factory=list)
    theme: str = "dark"
