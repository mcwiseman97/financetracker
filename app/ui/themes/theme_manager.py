"""
Theme management: loads QSS files and applies to QApplication.
Emits theme_changed signal so charts and widgets can re-render.
"""
from __future__ import annotations
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication


class ThemeManager(QObject):
    theme_changed = pyqtSignal(str)  # emits "dark" or "light"

    _THEMES_DIR = Path(__file__).parent

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_theme = "dark"

    @property
    def current_theme(self) -> str:
        return self._current_theme

    @property
    def is_dark(self) -> bool:
        return self._current_theme == "dark"

    def apply_theme(self, theme_name: str):
        """Load and apply QSS stylesheet to the application."""
        qss_file = self._THEMES_DIR / f"{theme_name}.qss"
        if not qss_file.exists():
            # Fallback to dark
            qss_file = self._THEMES_DIR / "dark.qss"
            theme_name = "dark"

        try:
            qss = qss_file.read_text(encoding="utf-8")
            app = QApplication.instance()
            if app:
                app.setStyleSheet(qss)
            self._current_theme = theme_name
            self.theme_changed.emit(theme_name)
        except OSError:
            pass

    def toggle_theme(self):
        """Switch between dark and light themes."""
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self.apply_theme(new_theme)
        return new_theme

    # ── Matplotlib colors ─────────────────────────────────────────────────

    def get_mpl_style(self) -> dict:
        """Return matplotlib rcParams dict matching the current theme."""
        if self._current_theme == "dark":
            return {
                "figure.facecolor": "#24273a",
                "axes.facecolor": "#24273a",
                "axes.edgecolor": "#45475a",
                "axes.labelcolor": "#a6adc8",
                "text.color": "#cdd6f4",
                "xtick.color": "#a6adc8",
                "ytick.color": "#a6adc8",
                "grid.color": "#313244",
                "grid.alpha": 0.5,
                "axes.spines.top": False,
                "axes.spines.right": False,
            }
        else:
            return {
                "figure.facecolor": "#e6e9ef",
                "axes.facecolor": "#e6e9ef",
                "axes.edgecolor": "#bcc0cc",
                "axes.labelcolor": "#6c6f85",
                "text.color": "#4c4f69",
                "xtick.color": "#6c6f85",
                "ytick.color": "#6c6f85",
                "grid.color": "#ccd0da",
                "grid.alpha": 0.5,
                "axes.spines.top": False,
                "axes.spines.right": False,
            }

    def get_chart_colors(self) -> list[str]:
        """Return a palette of chart colors for the current theme."""
        if self._current_theme == "dark":
            return [
                "#cba6f7",  # mauve
                "#89b4fa",  # blue
                "#a6e3a1",  # green
                "#fab387",  # peach
                "#f9e2af",  # yellow
                "#f38ba8",  # red
                "#74c7ec",  # sapphire
                "#94e2d5",  # teal
                "#f5c2e7",  # pink
                "#b4befe",  # lavender
            ]
        else:
            return [
                "#8839ef",  # mauve
                "#1e66f5",  # blue
                "#40a02b",  # green
                "#fe640b",  # peach
                "#df8e1d",  # yellow
                "#d20f39",  # red
                "#209fb5",  # sapphire
                "#179299",  # teal
                "#ea76cb",  # pink
                "#7287fd",  # lavender
            ]
