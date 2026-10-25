"""
Entry point for the Concatenador de Dados application.

Run with:
    python main.py
    (or pythonw main.py to run without console)
"""
from __future__ import annotations

import ctypes
import sys

from app.ui.app_window import AppWindow


def _setup_windows_app_id() -> None:
    """
    Set an explicit AppUserModelID on Windows.

    This ensures Windows treats the process as an individual application on the
    taskbar rather than grouping it under the generic python.exe, allowing the
    custom window icon to appear on the taskbar.
    """
    if sys.platform == "win32":
        # Incrementing the version identifier clears any stale Windows Shell taskbar icon cache
        app_id = "concat_excel.concatenador_dados.2.0"
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            pass


def main() -> None:
    """Initialise and start the application event loop."""
    _setup_windows_app_id()
    app = AppWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
