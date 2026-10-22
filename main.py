"""
Entry point for the Concat Excel application.

Run with:
    python main.py
"""
from app.ui.app_window import AppWindow


def main() -> None:
    """Initialise and start the application event loop."""
    app = AppWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
