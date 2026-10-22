"""
Mappings view — CRUD interface for named column mappings.
"""
from __future__ import annotations

from collections.abc import Callable
from tkinter import messagebox

import customtkinter as ctk

from app.models.models import AppSettings, Mapping
from app.ui.dialogs.mapping_editor_dialog import MappingEditorDialog


class MappingsView(ctk.CTkFrame):
    """Lists all saved mappings with options to create, edit, and delete."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        settings: AppSettings,
        on_settings_change: Callable[[], None],
    ) -> None:
        super().__init__(parent, fg_color="transparent")

        self._settings = settings
        self._on_settings_change = on_settings_change

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_ui()
        self._render_list()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ── Header ────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Mapeamentos",
            font=ctk.CTkFont(size=26, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="Crie e gerencie mapeamentos de colunas reutilizáveis.",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray65"),
            anchor="w",
        ).grid(row=1, column=0, sticky="w")

        ctk.CTkButton(
            header,
            text="＋  Novo Mapeamento",
            command=self._create_mapping,
        ).grid(row=0, column=1, rowspan=2, padx=(12, 0))

        # ── Scrollable list ───────────────────────────────────────────
        self._list_frame = ctk.CTkScrollableFrame(self, label_text="")
        self._list_frame.grid(row=1, column=0, sticky="nsew")
        self._list_frame.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # List rendering
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Called when this view becomes visible."""
        self._render_list()

    def _render_list(self) -> None:
        # Clear existing widgets
        for widget in self._list_frame.winfo_children():
            widget.destroy()

        if not self._settings.mappings:
            ctk.CTkLabel(
                self._list_frame,
                text="Nenhum mapeamento criado ainda.\nClique em '＋ Novo Mapeamento' para começar.",
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray60"),
                justify="center",
            ).grid(row=0, column=0, pady=60)
            return

        for idx, mapping in enumerate(self._settings.mappings):
            self._make_mapping_row(idx, mapping)

    def _make_mapping_row(self, idx: int, mapping: Mapping) -> None:
        row = ctk.CTkFrame(self._list_frame, corner_radius=10)
        row.grid(row=idx, column=0, sticky="ew", pady=5)
        row.grid_columnconfigure(0, weight=1)

        # Info
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=0, sticky="ew", padx=16, pady=10)
        info.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            info,
            text=f"🔗  {mapping.name}",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        n_cols = len(mapping.columns)
        detail = f"{n_cols} par(es) de coluna" + ("s" if n_cols != 1 else "")
        ctk.CTkLabel(
            info,
            text=detail,
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray60"),
            anchor="w",
        ).grid(row=1, column=0, sticky="w")

        # Action buttons
        btn_frame = ctk.CTkFrame(row, fg_color="transparent")
        btn_frame.grid(row=0, column=1, padx=(8, 12), pady=10)

        ctk.CTkButton(
            btn_frame,
            text="✏  Editar",
            width=90,
            command=lambda m=mapping: self._edit_mapping(m),
        ).grid(row=0, column=0, padx=4)

        ctk.CTkButton(
            btn_frame,
            text="🗑  Excluir",
            width=90,
            fg_color=("#e74c3c", "#c0392b"),
            hover_color=("#c0392b", "#a93226"),
            command=lambda m=mapping: self._delete_mapping(m),
        ).grid(row=0, column=1, padx=4)

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    def _create_mapping(self) -> None:
        dialog = MappingEditorDialog(
            parent=self.winfo_toplevel(),
            master_sheet_path=self._settings.master_sheet_path,
        )
        self.wait_window(dialog)
        if dialog.result:
            self._settings.mappings.append(dialog.result)
            self._on_settings_change()
            self._render_list()

    def _edit_mapping(self, mapping: Mapping) -> None:
        dialog = MappingEditorDialog(
            parent=self.winfo_toplevel(),
            master_sheet_path=self._settings.master_sheet_path,
            mapping=mapping,
        )
        self.wait_window(dialog)
        if dialog.result:
            self._on_settings_change()
            self._render_list()

    def _delete_mapping(self, mapping: Mapping) -> None:
        confirmed = messagebox.askyesno(
            "Confirmar exclusão",
            f"Tem certeza que deseja excluir o mapeamento '{mapping.name}'?",
        )
        if confirmed:
            self._settings.mappings = [
                m for m in self._settings.mappings if m.id != mapping.id
            ]
            self._on_settings_change()
            self._render_list()
