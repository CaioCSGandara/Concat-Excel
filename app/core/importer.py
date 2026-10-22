"""
Core import engine: validates mappings, deduplicates rows, and appends
new data from the source sheet to the master sheet.
"""
from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from app.models.models import Mapping


@dataclass
class ImportResult:
    """Outcome of a single import operation."""

    success: bool
    rows_imported: int = 0
    rows_skipped: int = 0
    error_message: Optional[str] = None
    log_entries: list[str] = field(default_factory=list)


# Convenience type alias
ProgressCallback = Callable[[float, str], None]


class Importer:
    """Reads, validates, deduplicates, and appends spreadsheet data."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def import_data(
        self,
        master_path: str,
        source_path: str,
        mapping: Mapping,
        progress_callback: ProgressCallback,
    ) -> ImportResult:
        """
        Import rows from *source_path* into *master_path* using *mapping*.

        The callback receives ``(progress: float, message: str)`` where
        *progress* is in ``[0.0, 1.0]``.  A negative value signals an error.

        Duplicate rows (identical values in all mapped target columns) are
        silently skipped.  The master sheet is never modified if a validation
        error or unexpected exception occurs.

        Args:
            master_path: Absolute path to the master ``.xlsx`` file.
            source_path: Absolute path to the source ``.xlsx`` file.
            mapping: Column-mapping configuration to apply.
            progress_callback: UI callback for progress updates.

        Returns:
            An :class:`ImportResult` describing what happened.
        """
        log: list[str] = []

        try:
            # ── 1. Load sheets ────────────────────────────────────────
            progress_callback(0.05, "📂 Carregando planilha mestre…")
            master_df: pd.DataFrame = pd.read_excel(master_path, engine="openpyxl")

            progress_callback(0.10, "📂 Carregando planilha fonte…")
            source_df: pd.DataFrame = pd.read_excel(source_path, engine="openpyxl")

            # ── 2. Validate mapping ───────────────────────────────────
            progress_callback(0.15, "🔍 Validando mapeamento de colunas…")
            errors = self._validate_mapping(master_df, source_df, mapping)
            if errors:
                for err in errors:
                    log.append(f"❌ {err}")
                    progress_callback(-1.0, f"❌ {err}")
                return ImportResult(
                    success=False,
                    error_message="Mapeamento inconsistente. Veja o log.",
                    log_entries=log,
                )

            msg = f"✅ Mapeamento válido — {len(mapping.columns)} coluna(s) mapeada(s)."
            log.append(msg)
            progress_callback(0.20, msg)

            # ── 3. Index existing rows for deduplication ──────────────
            target_cols: list[str] = [c.target for c in mapping.columns]
            existing_hashes: set[str] = {
                self._row_hash(row, target_cols)
                for _, row in master_df.iterrows()
            }
            msg = f"🔎 {len(existing_hashes)} registros existentes indexados."
            log.append(msg)
            progress_callback(0.25, msg)

            # ── 4. Iterate source rows ────────────────────────────────
            total: int = len(source_df)
            if total == 0:
                msg = "ℹ️ A planilha fonte está vazia — nada a importar."
                log.append(msg)
                progress_callback(1.0, msg)
                return ImportResult(success=True, log_entries=log)

            rows_to_add: list[dict[str, object]] = []
            rows_skipped: int = 0
            rows_imported: int = 0

            for idx, source_row in source_df.iterrows():
                row_num: int = int(str(idx)) + 2  # +1 for 1-index, +1 for header
                progress: float = 0.25 + 0.65 * ((int(str(idx)) + 1) / total)

                new_row: dict[str, object] = {
                    col_map.target: source_row[col_map.source]
                    for col_map in mapping.columns
                }

                temp_series: pd.Series = pd.Series(new_row)
                row_hash: str = self._row_hash(temp_series, target_cols)

                if row_hash in existing_hashes:
                    rows_skipped += 1
                    msg = f"⏭️  Linha {row_num}: duplicata — ignorada."
                    log.append(msg)
                    progress_callback(progress, msg)
                else:
                    existing_hashes.add(row_hash)
                    rows_to_add.append(new_row)
                    rows_imported += 1
                    msg = f"✅ Linha {row_num}: importada."
                    log.append(msg)
                    progress_callback(progress, msg)

            # ── 5. Persist ────────────────────────────────────────────
            if rows_to_add:
                progress_callback(0.92, f"💾 Gravando {rows_imported} linha(s) na planilha mestre…")
                new_df: pd.DataFrame = pd.DataFrame(rows_to_add).reindex(
                    columns=master_df.columns
                )
                updated_df: pd.DataFrame = pd.concat(
                    [master_df, new_df], ignore_index=True
                )
                updated_df.to_excel(master_path, index=False, engine="openpyxl")

            final_msg = (
                f"🎉 Concluído! {rows_imported} linha(s) importada(s), "
                f"{rows_skipped} duplicata(s) ignorada(s)."
            )
            log.append(final_msg)
            progress_callback(1.0, final_msg)

            return ImportResult(
                success=True,
                rows_imported=rows_imported,
                rows_skipped=rows_skipped,
                log_entries=log,
            )

        except Exception as exc:  # noqa: BLE001
            msg = f"❌ Erro inesperado: {exc}"
            log.append(msg)
            progress_callback(-1.0, msg)
            return ImportResult(
                success=False,
                error_message=str(exc),
                log_entries=log,
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_mapping(
        master_df: pd.DataFrame,
        source_df: pd.DataFrame,
        mapping: Mapping,
    ) -> list[str]:
        """Return a list of validation error messages (empty when valid)."""
        errors: list[str] = []
        master_cols: set[str] = set(master_df.columns)
        source_cols: set[str] = set(source_df.columns)

        for col_map in mapping.columns:
            if col_map.source not in source_cols:
                errors.append(
                    f"Coluna fonte '{col_map.source}' não encontrada na planilha fonte."
                )
            if col_map.target not in master_cols:
                errors.append(
                    f"Coluna destino '{col_map.target}' não encontrada na planilha mestre."
                )
        return errors

    @staticmethod
    def _row_hash(row: pd.Series, columns: list[str]) -> str:
        """Return an MD5 hex digest of *row* values restricted to *columns*."""
        values: str = "|".join(str(row.get(col, "")) for col in sorted(columns))
        return hashlib.md5(values.encode("utf-8")).hexdigest()
