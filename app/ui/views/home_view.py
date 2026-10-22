"""
Home view — the main workflow screen.

Allows the user to:
  1. Set / change the master sheet (persistent).
  2. Select a source sheet for the current session.
  3. Choose a column mapping.
  4. Run the import with live progress and log output.
"""
from __future__ import annotations

import queue
import threading
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk

from app.core.backup_manager import BackupManager
from app.core.importer import ImportResult, Importer
from app.models.models import AppSettings, Mapping


class HomeView(ctk.CTkFrame):
    """Main import workflow view."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        settings: AppSettings,
        on_settings_change: Callable[[], None],
    ) -> None:
        super().__init__(parent, fg_color="transparent")

        self._settings = settings
        self._on_settings_change = on_settings_change
        self._source_path: Optional[str] = None
        self._selected_mapping: Optional[Mapping] = None
        self._importer = Importer()
        self._progress_queue: queue.Queue[tuple[float, str] | tuple[str, ImportResult]] = (
            queue.Queue()
        )

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._build_ui()
        self._refresh_mapping_dropdown()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ── Page title ────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="Importação de Dados",
            font=ctk.CTkFont(size=26, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        ctk.CTkLabel(
            self,
            text="Configure as planilhas e o mapeamento, depois clique em Importar.",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray65"),
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(0, 18))

        # ── Cards row ─────────────────────────────────────────────────
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.grid(row=2, column=0, sticky="ew")
        cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self._master_card = self._make_file_card(
            cards_frame,
            col=0,
            icon="🗂️",
            title="Planilha Mestre",
            subtitle="Persistente — lembrada entre sessões",
            btn_text="Selecionar…",
            btn_command=self._select_master,
        )
        self._master_path_label = self._make_path_label(self._master_card)
        self._refresh_master_label()

        self._source_card = self._make_file_card(
            cards_frame,
            col=1,
            icon="📄",
            title="Planilha Fonte",
            subtitle="Selecionada por sessão",
            btn_text="Selecionar…",
            btn_command=self._select_source,
        )
        self._source_path_label = self._make_path_label(self._source_card)
        self._source_path_label.configure(text="Nenhuma selecionada")

        mapping_card = self._make_file_card(
            cards_frame,
            col=2,
            icon="🔗",
            title="Mapeamento",
            subtitle="Escolha um mapeamento salvo",
            btn_text=None,
            btn_command=None,
        )

        self._mapping_var: ctk.StringVar = ctk.StringVar(value="")
        self._mapping_combo = ctk.CTkComboBox(
            mapping_card,
            variable=self._mapping_var,
            values=[],
            command=self._on_mapping_selected,
            state="readonly",
            width=200,
        )
        self._mapping_combo.pack(pady=(8, 0))

        # ── Import button ─────────────────────────────────────────────
        self._import_btn = ctk.CTkButton(
            self,
            text="⬇  Iniciar Importação",
            height=48,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=12,
            command=self._start_import,
            state="disabled",
        )
        self._import_btn.grid(row=3, column=0, pady=20, ipadx=10)

        # ── Progress section ──────────────────────────────────────────
        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 4))
        progress_frame.grid_columnconfigure(0, weight=1)
        progress_frame.grid_rowconfigure(1, weight=1)

        self.grid_rowconfigure(4, weight=1)

        self._progress_bar = ctk.CTkProgressBar(progress_frame)
        self._progress_bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        self._progress_bar.set(0)

        self._progress_label = ctk.CTkLabel(
            progress_frame,
            text="Aguardando…",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65"),
            anchor="w",
        )
        self._progress_label.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 4))

        self._log_box = ctk.CTkTextbox(
            progress_frame,
            font=ctk.CTkFont(family="Courier", size=12),
            state="disabled",
            wrap="word",
        )
        self._log_box.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        progress_frame.grid_rowconfigure(2, weight=1)

    # ------------------------------------------------------------------
    # Card builder helpers
    # ------------------------------------------------------------------

    def _make_file_card(
        self,
        parent: ctk.CTkFrame,
        col: int,
        icon: str,
        title: str,
        subtitle: str,
        btn_text: Optional[str],
        btn_command: Optional[Callable[[], None]],
    ) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, corner_radius=14)
        card.grid(row=0, column=col, padx=6, pady=4, sticky="nsew")

        ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=28)).pack(pady=(18, 0))
        ctk.CTkLabel(
            card, text=title, font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(4, 0))
        ctk.CTkLabel(
            card,
            text=subtitle,
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray60"),
        ).pack()

        if btn_text and btn_command:
            ctk.CTkButton(card, text=btn_text, command=btn_command, width=140).pack(
                pady=(10, 18)
            )
        return card

    def _make_path_label(self, card: ctk.CTkFrame) -> ctk.CTkLabel:
        label = ctk.CTkLabel(
            card,
            text="Nenhuma selecionada",
            text_color=("gray45", "gray60"),
            font=ctk.CTkFont(size=11),
            wraplength=180,
        )
        label.pack(pady=(4, 18))
        return label

    # ------------------------------------------------------------------
    # File selection
    # ------------------------------------------------------------------

    def _select_master(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione a planilha mestre",
            filetypes=[("Planilhas Excel", "*.xlsx *.xls"), ("Todos os arquivos", "*.*")],
        )
        if not path:
            return
        self._settings.master_sheet_path = path
        self._on_settings_change()
        self._refresh_master_label()
        self._update_import_btn_state()

    def _select_source(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione a planilha fonte",
            filetypes=[("Planilhas Excel", "*.xlsx *.xls"), ("Todos os arquivos", "*.*")],
        )
        if not path:
            return
        self._source_path = path
        self._source_path_label.configure(
            text=Path(path).name, text_color=("gray20", "gray90")
        )
        self._update_import_btn_state()

    # ------------------------------------------------------------------
    # Mapping dropdown
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Called when this view becomes visible — refreshes dynamic content."""
        self._refresh_mapping_dropdown()

    def _refresh_mapping_dropdown(self) -> None:
        names = [m.name for m in self._settings.mappings]
        self._mapping_combo.configure(values=names if names else ["(nenhum mapeamento)"])
        if not names:
            self._mapping_var.set("")
            self._selected_mapping = None
        elif self._selected_mapping and self._selected_mapping.name in names:
            self._mapping_var.set(self._selected_mapping.name)
        else:
            self._mapping_var.set(names[0])
            self._on_mapping_selected(names[0])
        self._update_import_btn_state()

    def _on_mapping_selected(self, value: str) -> None:
        self._selected_mapping = next(
            (m for m in self._settings.mappings if m.name == value), None
        )
        self._update_import_btn_state()

    # ------------------------------------------------------------------
    # Import workflow
    # ------------------------------------------------------------------

    def _update_import_btn_state(self) -> None:
        ready = (
            bool(self._settings.master_sheet_path)
            and bool(self._source_path)
            and self._selected_mapping is not None
        )
        self._import_btn.configure(state="normal" if ready else "disabled")

    def _refresh_master_label(self) -> None:
        path = self._settings.master_sheet_path
        if path:
            self._master_path_label.configure(
                text=Path(path).name, text_color=("gray20", "gray90")
            )
        else:
            self._master_path_label.configure(
                text="Nenhuma selecionada", text_color=("gray45", "gray60")
            )

    def _start_import(self) -> None:
        # Validate backup dir
        backup_dir = self._settings.backup_dir
        if not backup_dir:
            messagebox.showerror(
                "Configuração incompleta",
                "Configure o diretório de backup em Configurações antes de importar.",
            )
            return

        self._import_btn.configure(state="disabled")
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")
        self._progress_bar.set(0)
        self._progress_label.configure(text="Iniciando…")

        thread = threading.Thread(target=self._run_import_thread, daemon=True)
        thread.start()
        self._poll_progress()

    def _run_import_thread(self) -> None:
        try:
            # ── Backup ────────────────────────────────────────────────
            self._progress_queue.put((0.01, "💾 Criando backup da planilha mestre…"))
            bm = BackupManager(self._settings.backup_dir)  # type: ignore[arg-type]
            bm.create_backup(self._settings.master_sheet_path)  # type: ignore[arg-type]
            self._progress_queue.put((0.04, "✅ Backup criado com sucesso."))

            # ── Import ────────────────────────────────────────────────
            result = self._importer.import_data(
                master_path=self._settings.master_sheet_path,  # type: ignore[arg-type]
                source_path=self._source_path,  # type: ignore[arg-type]
                mapping=self._selected_mapping,  # type: ignore[arg-type]
                progress_callback=lambda p, m: self._progress_queue.put((p, m)),
            )
            self._progress_queue.put(("done", result))

        except Exception as exc:  # noqa: BLE001
            from app.core.importer import ImportResult as IR

            msg = f"❌ Falha no backup: {exc}"
            self._progress_queue.put((-1.0, msg))
            self._progress_queue.put(
                ("done", IR(success=False, error_message=str(exc), log_entries=[msg]))
            )

    def _poll_progress(self) -> None:
        try:
            while True:
                item = self._progress_queue.get_nowait()
                first = item[0]
                if first == "done":
                    self._handle_done(item[1])  # type: ignore[arg-type]
                    return
                progress: float = float(first)  # type: ignore[arg-type]
                msg: str = str(item[1])
                if progress >= 0:
                    self._progress_bar.set(progress)
                self._progress_label.configure(text=msg)
                self._append_log(msg)
        except queue.Empty:
            pass
        self.after(80, self._poll_progress)

    def _handle_done(self, result: ImportResult) -> None:
        self._progress_bar.set(1.0 if result.success else 0.0)
        if result.success:
            self._progress_label.configure(
                text=f"✅ {result.rows_imported} importada(s), {result.rows_skipped} ignorada(s)."
            )
            messagebox.showinfo(
                "Importação concluída",
                f"{result.rows_imported} linha(s) importada(s) com sucesso.\n"
                f"{result.rows_skipped} duplicata(s) ignorada(s).",
            )
            # Reset source sheet for next session
            self._source_path = None
            self._source_path_label.configure(
                text="Nenhuma selecionada", text_color=("gray45", "gray60")
            )
        else:
            self._progress_label.configure(
                text=f"❌ Erro: {result.error_message}"
            )
            messagebox.showerror(
                "Erro na importação",
                result.error_message or "Erro desconhecido. Verifique o log.",
            )
        self._import_btn.configure(state="normal")
        self._update_import_btn_state()

    def _append_log(self, message: str) -> None:
        self._log_box.configure(state="normal")
        self._log_box.insert("end", message + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")
