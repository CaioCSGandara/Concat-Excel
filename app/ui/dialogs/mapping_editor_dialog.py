"""
Mapping editor dialog — allows the user to create or edit a named column mapping.

Provides independent file loaders for both source (origem) and target/master (destino)
spreadsheets, automatic row population based on column headers, and drag-and-drop
reordering/swapping of columns within the same spreadsheet side.
"""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk
import pandas as pd

from app.models.models import ColumnMapping, Mapping


class _RowItem:
    """Encapsulates widgets and variables for a single mapping row pair."""

    def __init__(
        self,
        index: int,
        frame: ctk.CTkFrame,
        row_label: ctk.CTkLabel,
        src_slot: ctk.CTkFrame,
        src_handle: ctk.CTkLabel,
        src_var: ctk.StringVar,
        src_combo: ctk.CTkComboBox,
        src_up_btn: ctk.CTkButton,
        src_down_btn: ctk.CTkButton,
        arrow_label: ctk.CTkLabel,
        tgt_slot: ctk.CTkFrame,
        tgt_handle: ctk.CTkLabel,
        tgt_var: ctk.StringVar,
        tgt_combo: ctk.CTkComboBox,
        tgt_up_btn: ctk.CTkButton,
        tgt_down_btn: ctk.CTkButton,
        del_btn: ctk.CTkButton,
    ) -> None:
        self.index = index
        self.frame = frame
        self.row_label = row_label
        self.src_slot = src_slot
        self.src_handle = src_handle
        self.src_var = src_var
        self.src_combo = src_combo
        self.src_up_btn = src_up_btn
        self.src_down_btn = src_down_btn
        self.arrow_label = arrow_label
        self.tgt_slot = tgt_slot
        self.tgt_handle = tgt_handle
        self.tgt_var = tgt_var
        self.tgt_combo = tgt_combo
        self.tgt_up_btn = tgt_up_btn
        self.tgt_down_btn = tgt_down_btn
        self.del_btn = del_btn

    def get_value(self, side: str) -> str:
        return self.src_var.get().strip() if side == "source" else self.tgt_var.get().strip()

    def set_value(self, side: str, value: str) -> None:
        if side == "source":
            self.src_var.set(value)
        else:
            self.tgt_var.set(value)

    def get_slot(self, side: str) -> ctk.CTkFrame:
        return self.src_slot if side == "source" else self.tgt_slot

    def update_options(self, side: str, options: list[str]) -> None:
        combo = self.src_combo if side == "source" else self.tgt_combo
        combo.configure(values=options)


class MappingEditorDialog(ctk.CTkToplevel):
    """Modal dialog for creating or editing a :class:`Mapping`."""

    def __init__(
        self,
        parent: ctk.CTk | ctk.CTkToplevel,
        master_sheet_path: Optional[str] = None,
        mapping: Optional[Mapping] = None,
    ) -> None:
        super().__init__(parent)

        self._editing: Optional[Mapping] = mapping
        self.result: Optional[Mapping] = None

        # Column name lists loaded from reference files
        self._source_cols: list[str] = []
        self._target_cols: list[str] = []

        # Internal row models
        self._rows: list[_RowItem] = []

        # Drag-and-drop state
        self._dragging: bool = False
        self._drag_side: Optional[str] = None
        self._drag_start_idx: Optional[int] = None
        self._drag_hover_idx: Optional[int] = None
        self._drag_badge: Optional[tk.Toplevel] = None

        self._build_ui()
        self._populate_existing()

        # If a master sheet path was passed and no existing mapping, we can optionally load it
        if master_sheet_path and not mapping:
            cols = self._read_columns(master_sheet_path)
            if cols:
                self._target_cols = cols
                self._target_file_label.configure(
                    text=f"{Path(master_sheet_path).name} ({len(cols)} colunas)",
                    text_color=("gray20", "gray85"),
                )
                self._apply_file_columns("target", cols)

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
        self.geometry("860x700")
        self.resizable(True, True)
        self.minsize(740, 560)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Header (Name) ─────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(20, 10), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="Nome do mapeamento",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self._name_var: ctk.StringVar = ctk.StringVar(
            value=self._editing.name if self._editing else ""
        )
        ctk.CTkEntry(
            header,
            textvariable=self._name_var,
            placeholder_text="Ex.: Relatório Diário Financeiro",
            height=36,
        ).grid(row=0, column=1, padx=(12, 0), sticky="ew")

        # ── Independent File Pickers Section ──────────────────────────
        pickers_card = ctk.CTkFrame(self, corner_radius=10)
        pickers_card.grid(row=1, column=0, padx=24, pady=(0, 12), sticky="ew")
        pickers_card.grid_columnconfigure(0, weight=1)
        pickers_card.grid_columnconfigure(1, weight=1)

        # Left picker: Origem (Fonte)
        src_box = ctk.CTkFrame(pickers_card, fg_color="transparent")
        src_box.grid(row=0, column=0, padx=16, pady=12, sticky="nsew")
        src_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            src_box,
            text="📄  Planilha de Origem (Fonte)",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._source_file_label = ctk.CTkLabel(
            src_box,
            text="Nenhum arquivo carregado",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60"),
            anchor="w",
        )
        self._source_file_label.grid(row=1, column=0, sticky="w", pady=(2, 6))

        ctk.CTkButton(
            src_box,
            text="Selecionar Planilha de Origem…",
            height=32,
            command=lambda: self._load_file("source"),
        ).grid(row=2, column=0, sticky="w")

        # Right picker: Destino (Mestre)
        tgt_box = ctk.CTkFrame(pickers_card, fg_color="transparent")
        tgt_box.grid(row=0, column=1, padx=16, pady=12, sticky="nsew")
        tgt_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tgt_box,
            text="🎯  Planilha de Destino (Mestre)",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._target_file_label = ctk.CTkLabel(
            tgt_box,
            text="Nenhum arquivo carregado",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60"),
            anchor="w",
        )
        self._target_file_label.grid(row=1, column=0, sticky="w", pady=(2, 6))

        ctk.CTkButton(
            tgt_box,
            text="Selecionar Planilha de Destino…",
            height=32,
            command=lambda: self._load_file("target"),
        ).grid(row=2, column=0, sticky="w")

        # ── Pairs Container ───────────────────────────────────────────
        pairs_container = ctk.CTkFrame(self)
        pairs_container.grid(row=2, column=0, padx=24, pady=4, sticky="nsew")
        pairs_container.grid_columnconfigure(0, weight=1)
        pairs_container.grid_rowconfigure(1, weight=1)

        # Table Header
        col_hdr = ctk.CTkFrame(pairs_container, fg_color="transparent")
        col_hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        col_hdr.grid_columnconfigure(1, weight=1)
        col_hdr.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            col_hdr,
            text="#",
            width=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("gray50", "gray60"),
        ).grid(row=0, column=0, padx=(0, 4))

        ctk.CTkLabel(
            col_hdr,
            text="Coluna Origem (Fonte)  •  Arraste ⠿ para trocar",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="w", padx=6)

        ctk.CTkLabel(
            col_hdr,
            text="➔",
            width=24,
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60"),
        ).grid(row=0, column=2, padx=4)

        ctk.CTkLabel(
            col_hdr,
            text="Coluna Destino (Mestre)  •  Arraste ⠿ para trocar",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).grid(row=0, column=3, sticky="w", padx=6)

        ctk.CTkLabel(
            col_hdr,
            text="",
            width=28,
        ).grid(row=0, column=4, padx=(4, 0))

        # Scrollable pairs frame
        self._pairs_frame = ctk.CTkScrollableFrame(pairs_container, label_text="")
        self._pairs_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._pairs_frame.grid_columnconfigure(0, weight=1)

        # ── Action Buttons under table ────────────────────────────────
        actions_bar = ctk.CTkFrame(self, fg_color="transparent")
        actions_bar.grid(row=3, column=0, padx=24, pady=6, sticky="ew")
        actions_bar.grid_columnconfigure(0, weight=1)

        self._counter_label = ctk.CTkLabel(
            actions_bar,
            text="0 pares de mapeamento",
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray65"),
            anchor="w",
        )
        self._counter_label.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            actions_bar,
            text="＋  Adicionar Linha de Mapeamento",
            width=230,
            height=30,
            fg_color="transparent",
            border_width=1,
            command=lambda: self._add_row(),
        ).grid(row=0, column=1, sticky="e")

        # ── Footer ────────────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=4, column=0, padx=24, pady=(6, 18), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            footer,
            text="Cancelar",
            width=100,
            height=34,
            fg_color="transparent",
            border_width=1,
            command=self.destroy,
        ).grid(row=0, column=1, padx=(8, 0))

        ctk.CTkButton(
            footer,
            text="Salvar Mapeamento",
            width=160,
            height=34,
            command=self._save,
        ).grid(row=0, column=2, padx=(8, 0))

    # ------------------------------------------------------------------
    # File Reading & Column Population
    # ------------------------------------------------------------------

    def _read_columns(self, path: Optional[str]) -> list[str]:
        """Return the list of column headers from an Excel file."""
        if not path:
            return []
        try:
            df: pd.DataFrame = pd.read_excel(path, nrows=0, engine="openpyxl")
            return [str(col).strip() for col in df.columns]
        except Exception:
            try:
                df = pd.read_excel(path, nrows=0)
                return [str(col).strip() for col in df.columns]
            except Exception:
                return []

    def _load_file(self, side: str) -> None:
        title = (
            "Selecione a planilha de origem (fonte)"
            if side == "source"
            else "Selecione a planilha de destino (mestre)"
        )
        path = filedialog.askopenfilename(
            title=title,
            filetypes=[("Planilhas Excel", "*.xlsx *.xls"), ("Todos os arquivos", "*.*")],
        )
        if not path:
            return

        cols = self._read_columns(path)
        if not cols:
            messagebox.showerror(
                "Erro ao ler arquivo",
                f"Não foi possível ler as colunas da planilha selecionada:\n{Path(path).name}",
            )
            return

        filename = Path(path).name
        if side == "source":
            self._source_cols = cols
            self._source_file_label.configure(
                text=f"{filename} ({len(cols)} colunas)",
                text_color=("gray15", "gray85"),
            )
        else:
            self._target_cols = cols
            self._target_file_label.configure(
                text=f"{filename} ({len(cols)} colunas)",
                text_color=("gray15", "gray85"),
            )

        self._apply_file_columns(side, cols)

    def _apply_file_columns(self, side: str, columns: list[str]) -> None:
        """
        Populate the specified side with column headers.

        - If only one side is loaded, matching positions on the other side stay empty.
        - If the new list has more items than existing rows, new rows are created.
        - If fewer, excess rows on this side are cleared to empty.
        - Trailing rows where both source and target are empty are removed.
        """
        target_count = max(len(self._rows), len(columns))

        # Expand rows up to target_count
        while len(self._rows) < target_count:
            self._add_row(reindex=False)

        options = [""] + columns

        # Assign values for the loaded side
        for i in range(target_count):
            row = self._rows[i]
            row.update_options(side, options)
            if i < len(columns):
                row.set_value(side, columns[i])
            else:
                row.set_value(side, "")

        # Also update options for any existing rows
        for row in self._rows:
            row.update_options(side, options)

        # Trim trailing fully empty rows
        while (
            len(self._rows) > 0
            and not self._rows[-1].src_var.get().strip()
            and not self._rows[-1].tgt_var.get().strip()
        ):
            self._remove_row(len(self._rows) - 1, reindex=False)

        self._reindex_rows()
        self._update_counter()

    # ------------------------------------------------------------------
    # Row Construction & Management
    # ------------------------------------------------------------------

    def _add_row(
        self,
        source_value: str = "",
        target_value: str = "",
        reindex: bool = True,
    ) -> _RowItem:
        row_idx = len(self._rows)

        row_frame = ctk.CTkFrame(self._pairs_frame, corner_radius=6, fg_color="transparent")
        row_frame.grid(row=row_idx, column=0, sticky="ew", pady=3, padx=2)
        row_frame.grid_columnconfigure(1, weight=1)
        row_frame.grid_columnconfigure(3, weight=1)

        # 1. Row number label
        row_lbl = ctk.CTkLabel(
            row_frame,
            text=f"#{row_idx + 1}",
            width=30,
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
        )
        row_lbl.grid(row=0, column=0, padx=(0, 4))

        # 2. Source Slot Frame
        src_slot = ctk.CTkFrame(
            row_frame,
            corner_radius=6,
            border_width=1,
            border_color=("gray75", "gray30"),
        )
        src_slot.grid(row=0, column=1, sticky="ew", padx=(2, 4))
        src_slot.grid_columnconfigure(2, weight=1)

        src_handle = ctk.CTkLabel(
            src_slot,
            text="⠿",
            cursor="fleur",
            width=22,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=("gray40", "gray65"),
        )
        src_handle.grid(row=0, column=0, padx=(4, 2), sticky="ns")

        # Quick swap buttons (Source)
        src_btns_frame = ctk.CTkFrame(src_slot, fg_color="transparent")
        src_btns_frame.grid(row=0, column=1, padx=(0, 4))

        src_up_btn = ctk.CTkButton(
            src_btns_frame,
            text="▲",
            width=18,
            height=14,
            font=("Segoe UI", 8),
            fg_color="transparent",
            hover_color=("gray80", "gray25"),
            text_color=("gray25", "gray75"),
            command=lambda: self._quick_move("source", row_idx, -1),
        )
        src_up_btn.pack(side="top", pady=1)

        src_down_btn = ctk.CTkButton(
            src_btns_frame,
            text="▼",
            width=18,
            height=14,
            font=("Segoe UI", 8),
            fg_color="transparent",
            hover_color=("gray80", "gray25"),
            text_color=("gray25", "gray75"),
            command=lambda: self._quick_move("source", row_idx, 1),
        )
        src_down_btn.pack(side="bottom", pady=1)

        src_var = ctk.StringVar(value=source_value)
        src_options = [""] + self._source_cols
        src_combo = ctk.CTkComboBox(
            src_slot,
            variable=src_var,
            values=src_options,
            height=28,
            command=lambda _: self._update_counter(),
        )
        src_combo.grid(row=0, column=2, sticky="ew", padx=(2, 6), pady=4)

        # 3. Arrow indicator
        arrow_lbl = ctk.CTkLabel(
            row_frame,
            text="➔",
            width=24,
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60"),
        )
        arrow_lbl.grid(row=0, column=2, padx=4)

        # 4. Target Slot Frame
        tgt_slot = ctk.CTkFrame(
            row_frame,
            corner_radius=6,
            border_width=1,
            border_color=("gray75", "gray30"),
        )
        tgt_slot.grid(row=0, column=3, sticky="ew", padx=(4, 2))
        tgt_slot.grid_columnconfigure(0, weight=1)

        tgt_var = ctk.StringVar(value=target_value)
        tgt_options = [""] + self._target_cols
        tgt_combo = ctk.CTkComboBox(
            tgt_slot,
            variable=tgt_var,
            values=tgt_options,
            height=28,
            command=lambda _: self._update_counter(),
        )
        tgt_combo.grid(row=0, column=0, sticky="ew", padx=(6, 2), pady=4)

        # Quick swap buttons (Target)
        tgt_btns_frame = ctk.CTkFrame(tgt_slot, fg_color="transparent")
        tgt_btns_frame.grid(row=0, column=1, padx=(4, 0))

        tgt_up_btn = ctk.CTkButton(
            tgt_btns_frame,
            text="▲",
            width=18,
            height=14,
            font=("Segoe UI", 8),
            fg_color="transparent",
            hover_color=("gray80", "gray25"),
            text_color=("gray25", "gray75"),
            command=lambda: self._quick_move("target", row_idx, -1),
        )
        tgt_up_btn.pack(side="top", pady=1)

        tgt_down_btn = ctk.CTkButton(
            tgt_btns_frame,
            text="▼",
            width=18,
            height=14,
            font=("Segoe UI", 8),
            fg_color="transparent",
            hover_color=("gray80", "gray25"),
            text_color=("gray25", "gray75"),
            command=lambda: self._quick_move("target", row_idx, 1),
        )
        tgt_down_btn.pack(side="bottom", pady=1)

        tgt_handle = ctk.CTkLabel(
            tgt_slot,
            text="⠿",
            cursor="fleur",
            width=22,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=("gray40", "gray65"),
        )
        tgt_handle.grid(row=0, column=2, padx=(2, 4), sticky="ns")

        # 5. Delete row button
        del_btn = ctk.CTkButton(
            row_frame,
            text="✕",
            width=26,
            height=26,
            fg_color="transparent",
            hover_color=("#e74c3c", "#c0392b"),
            text_color=("gray40", "gray70"),
            command=lambda: self._remove_row_by_frame(row_frame),
        )
        del_btn.grid(row=0, column=4, padx=(4, 0))

        item = _RowItem(
            index=row_idx,
            frame=row_frame,
            row_label=row_lbl,
            src_slot=src_slot,
            src_handle=src_handle,
            src_var=src_var,
            src_combo=src_combo,
            src_up_btn=src_up_btn,
            src_down_btn=src_down_btn,
            arrow_label=arrow_lbl,
            tgt_slot=tgt_slot,
            tgt_handle=tgt_handle,
            tgt_var=tgt_var,
            tgt_combo=tgt_combo,
            tgt_up_btn=tgt_up_btn,
            tgt_down_btn=tgt_down_btn,
            del_btn=del_btn,
        )

        # Bind Drag and Drop mouse events to handles and slots
        self._bind_drag_events(item)

        self._rows.append(item)

        if reindex:
            self._reindex_rows()
            self._update_counter()

        return item

    def _bind_drag_events(self, item: _RowItem) -> None:
        """Bind drag-and-drop mouse events to the handles and slot frames."""
        # Source drag
        for widget in (item.src_handle, item.src_slot):
            widget.bind(
                "<ButtonPress-1>",
                lambda e, it=item: self._start_drag("source", it.index, e),
            )
            widget.bind(
                "<B1-Motion>",
                lambda e: self._on_drag_motion("source", e),
            )
            widget.bind(
                "<ButtonRelease-1>",
                lambda e: self._end_drag("source", e),
            )

        # Target drag
        for widget in (item.tgt_handle, item.tgt_slot):
            widget.bind(
                "<ButtonPress-1>",
                lambda e, it=item: self._start_drag("target", it.index, e),
            )
            widget.bind(
                "<B1-Motion>",
                lambda e: self._on_drag_motion("target", e),
            )
            widget.bind(
                "<ButtonRelease-1>",
                lambda e: self._end_drag("target", e),
            )

    def _remove_row_by_frame(self, frame: ctk.CTkFrame) -> None:
        idx = next((i for i, r in enumerate(self._rows) if r.frame is frame), None)
        if idx is not None:
            self._remove_row(idx)

    def _remove_row(self, idx: int, reindex: bool = True) -> None:
        if 0 <= idx < len(self._rows):
            row = self._rows.pop(idx)
            row.frame.destroy()
            if reindex:
                self._reindex_rows()
                self._update_counter()

    def _reindex_rows(self) -> None:
        """Update row positions in the grid and update button commands."""
        for i, row in enumerate(self._rows):
            row.index = i
            row.row_label.configure(text=f"#{i + 1}")
            row.frame.grid(row=i, column=0, sticky="ew", pady=3, padx=2)

            # Update quick move button handlers to point to current index
            row.src_up_btn.configure(command=lambda idx=i: self._quick_move("source", idx, -1))
            row.src_down_btn.configure(command=lambda idx=i: self._quick_move("source", idx, 1))
            row.tgt_up_btn.configure(command=lambda idx=i: self._quick_move("target", idx, -1))
            row.tgt_down_btn.configure(command=lambda idx=i: self._quick_move("target", idx, 1))

    def _quick_move(self, side: str, row_idx: int, direction: int) -> None:
        """Swap row with adjacent row (direction: -1 for up, +1 for down)."""
        target_idx = row_idx + direction
        if 0 <= target_idx < len(self._rows):
            self._swap_values(side, row_idx, target_idx)

    # ------------------------------------------------------------------
    # Drag and Drop Implementation
    # ------------------------------------------------------------------

    def _start_drag(self, side: str, row_idx: int, event: tk.Event) -> None:
        """Initialize drag session for the given side and row index."""
        if self._dragging or row_idx >= len(self._rows):
            return

        self._dragging = True
        self._drag_side = side
        self._drag_start_idx = row_idx
        self._drag_hover_idx = None

        val = self._rows[row_idx].get_value(side)

        # Highlight dragged slot
        dragged_slot = self._rows[row_idx].get_slot(side)
        dragged_slot.configure(border_color="#3B8ED0", border_width=2)

        # Create floating badge following cursor
        try:
            self._drag_badge = tk.Toplevel(self)
            self._drag_badge.overrideredirect(True)
            self._drag_badge.attributes("-topmost", True)
            badge_frame = tk.Frame(
                self._drag_badge,
                bg="#1f538d",
                padx=8,
                pady=4,
                highlightbackground="#3b8ed0",
                highlightthickness=1,
            )
            badge_frame.pack()
            badge_text = f"⠿ {val}" if val else "⠿ (vazio)"
            lbl = tk.Label(
                badge_frame,
                text=badge_text,
                bg="#1f538d",
                fg="white",
                font=("Segoe UI", 9, "bold"),
            )
            lbl.pack()
            self._drag_badge.geometry(f"+{event.x_root + 15}+{event.y_root + 10}")
        except Exception:
            self._drag_badge = None

    def _on_drag_motion(self, side: str, event: tk.Event) -> None:
        """Track mouse motion during drag and highlight candidate drop slot."""
        if not self._dragging or self._drag_side != side:
            return

        # Move floating badge
        if self._drag_badge:
            try:
                self._drag_badge.geometry(f"+{event.x_root + 15}+{event.y_root + 10}")
            except Exception:
                pass

        # Auto-scroll when near top or bottom of scrollable frame canvas
        try:
            canvas = self._pairs_frame._parent_canvas
            cy = canvas.winfo_rooty()
            ch = canvas.winfo_height()
            if event.y_root < cy + 30:
                canvas.yview_scroll(-1, "units")
            elif event.y_root > cy + ch - 30:
                canvas.yview_scroll(1, "units")
        except Exception:
            pass

        # Identify slot under cursor on the SAME side
        hovered_idx: Optional[int] = None
        for idx, row in enumerate(self._rows):
            slot = row.get_slot(side)
            try:
                sx = slot.winfo_rootx()
                sy = slot.winfo_rooty()
                sw = slot.winfo_width()
                sh = slot.winfo_height()
            except Exception:
                continue

            # Check vertical proximity
            if (sy - 3) <= event.y_root <= (sy + sh + 3):
                # Check horizontal bounds: must be over THIS side only
                if (sx - 15) <= event.x_root <= (sx + sw + 15):
                    hovered_idx = idx
                    break

        if hovered_idx != self._drag_hover_idx:
            # Reset previous hover highlight if not the dragged start
            if (
                self._drag_hover_idx is not None
                and self._drag_hover_idx != self._drag_start_idx
                and self._drag_hover_idx < len(self._rows)
            ):
                prev_slot = self._rows[self._drag_hover_idx].get_slot(side)
                prev_slot.configure(border_color=("gray75", "gray30"), border_width=1)

            # Apply highlight to newly hovered slot
            if (
                hovered_idx is not None
                and hovered_idx != self._drag_start_idx
                and hovered_idx < len(self._rows)
            ):
                new_slot = self._rows[hovered_idx].get_slot(side)
                new_slot.configure(border_color="#2FA572", border_width=2)

            self._drag_hover_idx = hovered_idx

    def _end_drag(self, side: str, event: tk.Event) -> None:
        """Conclude drag session, swap items if dropped on valid slot, and clean up."""
        if not self._dragging or self._drag_side != side:
            return

        # Destroy badge
        if self._drag_badge:
            try:
                self._drag_badge.destroy()
            except Exception:
                pass
            self._drag_badge = None

        # Reset all slot borders
        for row in self._rows:
            slot = row.get_slot(side)
            slot.configure(border_color=("gray75", "gray30"), border_width=1)

        # Perform swap if drop target is valid and distinct
        if (
            self._drag_start_idx is not None
            and self._drag_hover_idx is not None
            and self._drag_start_idx != self._drag_hover_idx
        ):
            self._swap_values(side, self._drag_start_idx, self._drag_hover_idx)

        self._dragging = False
        self._drag_side = None
        self._drag_start_idx = None
        self._drag_hover_idx = None

    def _swap_values(self, side: str, idx_a: int, idx_b: int) -> None:
        """Swap values between two rows on the specified side."""
        if 0 <= idx_a < len(self._rows) and 0 <= idx_b < len(self._rows):
            row_a = self._rows[idx_a]
            row_b = self._rows[idx_b]

            val_a = row_a.get_value(side)
            val_b = row_b.get_value(side)

            row_a.set_value(side, val_b)
            row_b.set_value(side, val_a)

            self._update_counter()

    # ------------------------------------------------------------------
    # Existing Mapping Population & Saving
    # ------------------------------------------------------------------

    def _populate_existing(self) -> None:
        """Fill in pairs when editing an existing mapping."""
        if not self._editing:
            return

        for col_map in self._editing.columns:
            self._add_row(col_map.source, col_map.target, reindex=False)

        self._reindex_rows()
        self._update_counter()

    def _update_counter(self) -> None:
        """Update the counter label with total rows and completed pairs."""
        total = len(self._rows)
        completed = sum(
            1
            for r in self._rows
            if r.src_var.get().strip() and r.tgt_var.get().strip()
        )
        self._counter_label.configure(
            text=f"{total} linha(s)  •  {completed} par(es) completo(s) para importação"
        )

    def _save(self) -> None:
        name = self._name_var.get().strip()
        if not name:
            messagebox.showerror("Erro", "O nome do mapeamento não pode ser vazio.")
            return

        columns: list[ColumnMapping] = []
        for row in self._rows:
            src = row.src_var.get().strip()
            tgt = row.tgt_var.get().strip()
            if src and tgt:
                columns.append(ColumnMapping(source=src, target=tgt))

        if not columns:
            messagebox.showerror(
                "Erro", "Adicione ao menos um par de colunas completo antes de salvar."
            )
            return

        if self._editing:
            self._editing.name = name
            self._editing.columns = columns
            self.result = self._editing
        else:
            self.result = Mapping(name=name, columns=columns)

        self.destroy()
