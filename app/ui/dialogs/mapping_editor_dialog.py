"""
Mapping editor dialog — allows the user to create or edit a named column mapping.

Source columns are loaded from an optional reference .xlsx file chosen by
the user (representing a typical daily source file).  Target columns are
loaded from the current master sheet (if one is configured).
"""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk
import pandas as pd

from app.models.models import ColumnMapping, Mapping


class MappingEditorDialog(ctk.CTkToplevel):
    """Modal dialog for creating or editing a :class:`Mapping`."""

    def __init__(
        self,
        parent: ctk.CTk | ctk.CTkToplevel,
        master_sheet_path: Optional[str],
        mapping: Optional[Mapping] = None,
    ) -> None:
        super().__init__(parent)

        self._master_sheet_path: Optional[str] = master_sheet_path
        self._editing: Optional[Mapping] = mapping

        # Result is set when the user confirms; None means cancelled.
        self.result: Optional[Mapping] = None

        # Column name lists
        self._master_cols: list[str] = self._load_columns(master_sheet_path)
        self._source_cols: list[str] = []

        # Row-pair widgets storage: list of (source_var, target_var, frame)
        self._pairs: list[tuple[ctk.StringVar, ctk.StringVar, ctk.CTkFrame]] = []

        self._build_ui()
        self._populate_existing()

        # Make modal
        self.transient(parent)
        self.grab_set()
        self.focus_set()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        title = "Editar Mapeamento" if self._editing else "Novo Mapeamento"
        self.title(title)
        self.geometry("700x620")
        self.resizable(True, True)
        self.minsize(600, 500)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Header ────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(24, 12), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="Nome do mapeamento",
            font=ctk.CTkFont(size=13),
        ).grid(row=0, column=0, sticky="w")

        self._name_var: ctk.StringVar = ctk.StringVar(
            value=self._editing.name if self._editing else ""
        )
        ctk.CTkEntry(
            header, textvariable=self._name_var, placeholder_text="Ex.: Relatório Diário"
        ).grid(row=0, column=1, padx=(12, 0), sticky="ew")

        # ── Source file loader ────────────────────────────────────────
        src_bar = ctk.CTkFrame(self, fg_color="transparent")
        src_bar.grid(row=1, column=0, padx=24, pady=(0, 8), sticky="ew")
        src_bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            src_bar,
            text="Planilha fonte de referência",
            font=ctk.CTkFont(size=13),
        ).grid(row=0, column=0, sticky="w")

        self._src_label = ctk.CTkLabel(
            src_bar,
            text="Nenhuma selecionada",
            text_color=("gray50", "gray60"),
            anchor="w",
        )
        self._src_label.grid(row=0, column=1, padx=12, sticky="ew")

        ctk.CTkButton(
            src_bar,
            text="Selecionar…",
            width=110,
            command=self._load_source_file,
        ).grid(row=0, column=2)

        # ── Column-pair list (scrollable) ─────────────────────────────
        pairs_outer = ctk.CTkFrame(self)
        pairs_outer.grid(row=2, column=0, padx=24, pady=4, sticky="nsew")
        pairs_outer.grid_columnconfigure(0, weight=1)
        pairs_outer.grid_rowconfigure(1, weight=1)

        # Column headers
        col_hdr = ctk.CTkFrame(pairs_outer, fg_color="transparent")
        col_hdr.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))
        col_hdr.grid_columnconfigure(0, weight=1)
        col_hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            col_hdr, text="Coluna fonte (origem)", font=ctk.CTkFont(weight="bold", size=12)
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            col_hdr, text="Coluna mestre (destino)", font=ctk.CTkFont(weight="bold", size=12)
        ).grid(row=0, column=1, sticky="w", padx=(8, 0))

        self._pairs_frame = ctk.CTkScrollableFrame(pairs_outer, label_text="")
        self._pairs_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self._pairs_frame.grid_columnconfigure(0, weight=1)
        self._pairs_frame.grid_columnconfigure(1, weight=1)

        # ── Add pair button ───────────────────────────────────────────
        add_btn = ctk.CTkButton(
            self,
            text="＋  Adicionar par de colunas",
            fg_color="transparent",
            border_width=1,
            command=self._add_pair,
        )
        add_btn.grid(row=3, column=0, padx=24, pady=8, sticky="ew")

        # ── Footer ────────────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=4, column=0, padx=24, pady=(8, 20), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            footer,
            text="Cancelar",
            fg_color="transparent",
            border_width=1,
            command=self.destroy,
        ).grid(row=0, column=1, padx=(8, 0))

        ctk.CTkButton(
            footer,
            text="Salvar",
            command=self._save,
        ).grid(row=0, column=2, padx=(8, 0))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_columns(self, path: Optional[str]) -> list[str]:
        """Return the column headers of an .xlsx file, or empty list on failure."""
        if not path:
            return []
        try:
            df: pd.DataFrame = pd.read_excel(path, nrows=0, engine="openpyxl")
            return list(df.columns)
        except Exception:  # noqa: BLE001
            return []

    def _load_source_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione a planilha fonte de referência",
            filetypes=[("Planilhas Excel", "*.xlsx *.xls"), ("Todos os arquivos", "*.*")],
        )
        if not path:
            return
        cols = self._load_columns(path)
        if not cols:
            messagebox.showerror(
                "Erro", "Não foi possível ler as colunas da planilha selecionada."
            )
            return
        self._source_cols = cols
        self._src_label.configure(text=Path(path).name, text_color=("gray20", "gray90"))
        # Refresh existing pair dropdowns
        for src_var, _, _ in self._pairs:
            # nothing to refresh automatically — user sees updated list on next add
            pass

    def _add_pair(
        self,
        source_value: str = "",
        target_value: str = "",
    ) -> None:
        row_index = len(self._pairs)

        row_frame = ctk.CTkFrame(self._pairs_frame, fg_color="transparent")
        row_frame.grid(row=row_index, column=0, columnspan=3, sticky="ew", pady=3)
        row_frame.grid_columnconfigure(0, weight=1)
        row_frame.grid_columnconfigure(1, weight=1)

        src_var: ctk.StringVar = ctk.StringVar(value=source_value)
        tgt_var: ctk.StringVar = ctk.StringVar(value=target_value)

        src_combo = ctk.CTkComboBox(
            row_frame,
            variable=src_var,
            values=self._source_cols or ["(carregue uma planilha fonte)"],
        )
        src_combo.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        tgt_combo = ctk.CTkComboBox(
            row_frame,
            variable=tgt_var,
            values=self._master_cols or ["(nenhuma planilha mestre definida)"],
        )
        tgt_combo.grid(row=0, column=1, sticky="ew", padx=(0, 6))

        remove_btn = ctk.CTkButton(
            row_frame,
            text="✕",
            width=32,
            fg_color=("gray80", "gray25"),
            hover_color=("#e74c3c", "#c0392b"),
            text_color=("gray10", "gray90"),
            command=lambda f=row_frame: self._remove_pair(f),
        )
        remove_btn.grid(row=0, column=2)

        self._pairs.append((src_var, tgt_var, row_frame))

    def _remove_pair(self, frame: ctk.CTkFrame) -> None:
        self._pairs = [p for p in self._pairs if p[2] is not frame]
        frame.destroy()

    def _populate_existing(self) -> None:
        """Fill in pairs when editing an existing mapping."""
        if not self._editing:
            return
        for col_map in self._editing.columns:
            self._add_pair(col_map.source, col_map.target)

    def _save(self) -> None:
        name = self._name_var.get().strip()
        if not name:
            messagebox.showerror("Erro", "O nome do mapeamento não pode ser vazio.")
            return

        columns: list[ColumnMapping] = []
        for src_var, tgt_var, _ in self._pairs:
            src = src_var.get().strip()
            tgt = tgt_var.get().strip()
            if src and tgt:
                columns.append(ColumnMapping(source=src, target=tgt))

        if not columns:
            messagebox.showerror(
                "Erro", "Adicione ao menos um par de colunas antes de salvar."
            )
            return

        if self._editing:
            self._editing.name = name
            self._editing.columns = columns
            self.result = self._editing
        else:
            self.result = Mapping(name=name, columns=columns)

        self.destroy()
