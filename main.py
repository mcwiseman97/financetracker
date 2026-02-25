#!/usr/bin/env python3
"""
Finance Tracker — Personal Finance Desktop Application
Entry point: bootstraps Qt application, data manager, and main window.
"""
import sys
from pathlib import Path

# Ensure the project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFontDatabase, QFont
    from PyQt6.QtCore import Qt

    app = QApplication(sys.argv)
    app.setApplicationName("Finance Tracker")
    app.setOrganizationName("FinanceTracker")

    # Load bundled Inter font if available
    fonts_dir = Path(__file__).parent / "app" / "fonts"
    if fonts_dir.exists():
        for font_file in fonts_dir.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(font_file))

    # Set fallback font
    font = QFont("Inter")
    font.setStyleHint(QFont.StyleHint.SansSerif)
    font.setPointSize(10)
    app.setFont(font)

    # Initialize core services
    from app.core.data_manager import DataManager
    from app.ui.themes.theme_manager import ThemeManager

    data_manager = DataManager()
    theme_manager = ThemeManager()

    # Check for first-run (before loading data)
    storage_dir = data_manager._storage.DATA_DIR
    is_first_run = not (storage_dir / "settings.json").exists()

    if is_first_run:
        # Bootstrap first run: apply dark theme temporarily for welcome dialog
        theme_manager.apply_theme("dark")

    # Create and show main window
    from app.ui.main_window import MainWindow
    app_dir = Path(__file__).parent

    window = MainWindow(data_manager, theme_manager, app_dir)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
