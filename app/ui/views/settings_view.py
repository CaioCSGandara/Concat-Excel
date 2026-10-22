"""
Settings view — backup directory configuration.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.models.models import AppSettings


class SettingsView(ctk.CTkFrame):
    """Configuration screen for backup directory and other app preferences."""

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
        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        ctk.CTkLabel(
            self,
            text="Configurações",
            font=ctk.CTkFont(size=26, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        ctk.CTkLabel(
            self,
            text="Preferências de backup e armazenamento.",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray65"),
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(0, 24))

        # ── Backup directory card ─────────────────────────────────────
        card = ctk.CTkFrame(self, corner_radius=14)
        card.grid(row=2, column=0, sticky="ew", pady=6)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text="💾",
            font=ctk.CTkFont(size=28),
        ).grid(row=0, column=0, rowspan=2, padx=(18, 12), pady=18)

        ctk.CTkLabel(
            card,
            text="Diretório de Backup",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="w", pady=(14, 0))

        ctk.CTkLabel(
            card,
            text="Os últimos 10 backups de cada planilha mestre são mantidos.",
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray60"),
            anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(0, 14))

        dir_frame = ctk.CTkFrame(card, fg_color="transparent")
        dir_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=18, pady=(0, 18))
        dir_frame.grid_columnconfigure(0, weight=1)

        self._backup_dir_var: ctk.StringVar = ctk.StringVar(
            value=self._settings.backup_dir or ""
        )
        dir_entry = ctk.CTkEntry(
            dir_frame,
            textvariable=self._backup_dir_var,
            placeholder_text="Caminho do diretório de backup…",
        )
        dir_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            dir_frame,
            text="Procurar…",
            width=100,
            command=self._browse_backup_dir,
        ).grid(row=0, column=1)

        ctk.CTkButton(
            dir_frame,
            text="Salvar",
            width=80,
            command=self._save_backup_dir,
        ).grid(row=0, column=2, padx=(8, 0))

        # ── Info card ─────────────────────────────────────────────────
        info_card = ctk.CTkFrame(self, corner_radius=14)
        info_card.grid(row=3, column=0, sticky="ew", pady=6)

        ctk.CTkLabel(
            info_card,
            text=(
                "ℹ️   As configurações são salvas automaticamente em  "
                "~/.concat-excel/settings.json"
            ),
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray60"),
            anchor="w",
        ).grid(padx=18, pady=14, sticky="w")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Refresh displayed values when view becomes visible."""
        self._backup_dir_var.set(self._settings.backup_dir or "")

    def _browse_backup_dir(self) -> None:
        path = filedialog.askdirectory(title="Selecione o diretório de backup")
        if path:
            self._backup_dir_var.set(path)

    def _save_backup_dir(self) -> None:
        path = self._backup_dir_var.get().strip()
        if not path:
            messagebox.showerror("Erro", "Informe um diretório válido.")
            return
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Erro", f"Não foi possível criar o diretório:\n{exc}")
            return
        self._settings.backup_dir = path
        self._on_settings_change()
        messagebox.showinfo("Salvo", f"Diretório de backup atualizado:\n{path}")
