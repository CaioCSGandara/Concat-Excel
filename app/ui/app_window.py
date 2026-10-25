"""
Main application window for Concatenador de Dados.

Implements a sidebar-navigation layout with three views:
  - Home (import workflow)
  - Mappings (CRUD)
  - Settings
"""
from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from typing import Union

import customtkinter as ctk

from app.config.settings_manager import SettingsManager
from app.models.models import AppSettings
from app.ui.views.home_view import HomeView
from app.ui.views.mappings_view import MappingsView
from app.ui.views.settings_view import SettingsView

# Type alias for the union of concrete view types
AnyView = Union[HomeView, MappingsView, SettingsView]


class AppWindow(ctk.CTk):
    """Root application window."""

    _WINDOW_TITLE: str = "Concatenador de Dados"
    _WINDOW_SIZE: str = "1180x720"
    _WINDOW_MIN: tuple[int, int] = (960, 600)

    def __init__(self) -> None:
        super().__init__()

        self._settings_manager: SettingsManager = SettingsManager()
        self._settings: AppSettings = self._settings_manager.load()

        # Apply persisted theme before any widget is created
        ctk.set_appearance_mode(self._settings.theme)
        ctk.set_default_color_theme("blue")

        self._setup_window()
        self._build_layout()
        self._show_view("home")

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        self.title(self._WINDOW_TITLE)
        self.geometry(self._WINDOW_SIZE)
        self.minsize(*self._WINDOW_MIN)

        # ── Ícone da janela e barra de tarefas ─────────────────────────
        if getattr(sys, "frozen", False):
            # Executando como .exe gerado pelo PyInstaller
            base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        else:
            # Executando em desenvolvimento
            base_path = Path(__file__).parent.parent.parent  # raiz do projeto

        icon_path = base_path / "assets" / "icon.ico"
        png_path = base_path / "assets" / "icon.png"

        # No Windows, self.iconbitmap carrega nativamente as 7 camadas do .ico
        # (16px para titlebar, 24px/32px para taskbar, 48px para Alt+Tab).
        # Não chamamos self.wm_iconphoto por cima, pois o Tkinter sobrescreveria
        # o .ico nativo com um redimensionamento grosseiro de imagem.
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass
        elif png_path.exists():
            try:
                self._icon_photo = tk.PhotoImage(file=str(png_path))
                self.wm_iconphoto(True, self._icon_photo)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=265, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(8, weight=1)  # spacer

        # ── Logo ──────────────────────────────────────────────────────
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=16, pady=(28, 8), sticky="ew")

        # Resolve asset path
        if getattr(sys, "frozen", False):
            base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        else:
            base_path = Path(__file__).parent.parent.parent

        png_path = base_path / "assets" / "icon.png"
        has_logo = False
        if png_path.exists():
            try:
                from PIL import Image

                pil_img = Image.open(png_path)
                self._sidebar_logo_img = ctk.CTkImage(
                    light_image=pil_img, dark_image=pil_img, size=(34, 34)
                )
                ctk.CTkLabel(
                    logo_frame, text="", image=self._sidebar_logo_img
                ).pack(side="left", padx=(0, 8))
                has_logo = True
            except Exception:
                pass

        if not has_logo:
            ctk.CTkLabel(
                logo_frame,
                text="⬇",
                font=ctk.CTkFont(size=30),
            ).pack(side="left", padx=(0, 8))

        title_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_frame,
            text="Concatenador de Dados",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_frame,
            text="Importador de planilhas",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray60"),
            anchor="w",
        ).pack(anchor="w")

        # ── Separator ─────────────────────────────────────────────────
        ctk.CTkFrame(sidebar, height=1, fg_color=("gray80", "gray25")).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(8, 12)
        )

        # ── Navigation buttons ────────────────────────────────────────
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        nav_items: list[tuple[str, str, str]] = [
            ("home", "🏠", "Início"),
            ("mappings", "🔗", "Mapeamentos"),
            ("settings", "⚙️", "Configurações"),
        ]

        for grid_row, (key, icon, label) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(
                sidebar,
                text=f"  {icon}  {label}",
                anchor="w",
                height=42,
                corner_radius=8,
                fg_color="transparent",
                hover_color=("gray85", "gray27"),
                text_color=("gray10", "gray90"),
                font=ctk.CTkFont(size=13),
                command=lambda k=key: self._show_view(k),
            )
            btn.grid(row=grid_row, column=0, padx=12, pady=3, sticky="ew")
            self._nav_buttons[key] = btn

        # ── Spacer ────────────────────────────────────────────────────
        # (row 8 is the weight-1 spacer via grid_rowconfigure above)

        # ── Theme toggle ──────────────────────────────────────────────
        ctk.CTkFrame(sidebar, height=1, fg_color=("gray80", "gray25")).grid(
            row=9, column=0, sticky="ew", padx=16, pady=(0, 8)
        )

        theme_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        theme_frame.grid(row=10, column=0, padx=16, pady=(0, 20), sticky="ew")
        theme_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            theme_frame,
            text="Modo Escuro",
            font=ctk.CTkFont(size=12),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._theme_switch = ctk.CTkSwitch(
            theme_frame,
            text="",
            command=self._on_theme_toggle,
            onvalue="dark",
            offvalue="light",
        )
        self._theme_switch.grid(row=0, column=1)
        if self._settings.theme == "dark":
            self._theme_switch.select()

    def _build_content_area(self) -> None:
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid(row=0, column=1, sticky="nsew", padx=28, pady=28)
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        self._views: dict[str, AnyView] = {}
        self._current_view_key: str = ""

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _show_view(self, key: str) -> None:
        if key == self._current_view_key:
            return

        # Update nav button appearance
        for k, btn in self._nav_buttons.items():
            btn.configure(
                fg_color=("gray78", "gray28") if k == key else "transparent"
            )

        # Hide previous view
        if self._current_view_key and self._current_view_key in self._views:
            self._views[self._current_view_key].grid_remove()

        # Create view lazily
        if key not in self._views:
            self._views[key] = self._create_view(key)
            self._views[key].grid(row=0, column=0, sticky="nsew")
        else:
            self._views[key].grid()
            # Refresh dynamic content
            view = self._views[key]
            if hasattr(view, "refresh"):
                view.refresh()  # type: ignore[union-attr]

        self._current_view_key = key

    def _create_view(self, key: str) -> AnyView:
        kwargs: dict = {
            "parent": self._content,
            "settings": self._settings,
            "on_settings_change": self._persist_settings,
        }
        match key:
            case "home":
                return HomeView(**kwargs)
            case "mappings":
                return MappingsView(**kwargs)
            case "settings":
                return SettingsView(**kwargs)
            case _:
                raise ValueError(f"Unknown view key: {key!r}")

    # ------------------------------------------------------------------
    # Settings persistence
    # ------------------------------------------------------------------

    def _persist_settings(self) -> None:
        """Save current settings to disk. Called by child views on changes."""
        self._settings_manager.save(self._settings)

    def _on_theme_toggle(self) -> None:
        theme: str = self._theme_switch.get()
        ctk.set_appearance_mode(theme)
        self._settings.theme = theme
        self._persist_settings()
