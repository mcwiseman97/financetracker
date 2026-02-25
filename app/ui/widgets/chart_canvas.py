"""
matplotlib FigureCanvasQTAgg wrapper with theme awareness.
Reconnects to theme_manager.theme_changed to re-render on theme switch.
"""
from __future__ import annotations
from typing import Optional, Callable

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt6.QtWidgets import QSizePolicy, QWidget


class ChartCanvas(FigureCanvasQTAgg):
    """
    Embeddable matplotlib canvas with theme support.

    Usage:
        canvas = ChartCanvas(theme_manager)
        canvas.set_draw_callback(self._draw_chart)
    """

    def __init__(
        self,
        theme_manager=None,
        width: float = 6,
        height: float = 4,
        dpi: int = 100,
        parent: Optional[QWidget] = None,
    ):
        self._theme_manager = theme_manager
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(200)

        self._draw_callback: Optional[Callable] = None

        if theme_manager:
            theme_manager.theme_changed.connect(self._on_theme_changed)
            self._apply_theme()

    def set_draw_callback(self, callback: Callable):
        """Set the function to call when (re)drawing the chart."""
        self._draw_callback = callback

    def apply_theme(self, is_dark: bool = True):
        """Apply theme colors to the figure. Called by panels on theme change."""
        self._apply_theme()

    def _apply_theme(self):
        """Apply theme-appropriate colors to the figure background."""
        if self._theme_manager:
            style = self._theme_manager.get_mpl_style()
            bg = style["figure.facecolor"]
            self.fig.patch.set_facecolor(bg)
            for ax in self.fig.get_axes():
                ax.set_facecolor(style["axes.facecolor"])

    def _on_theme_changed(self, theme_name: str):
        """Re-render when theme changes."""
        self._apply_theme()
        if self._draw_callback:
            self._draw_callback()

    def clear(self):
        """Clear all axes."""
        self.fig.clear()

    def get_axes(self, nrows: int = 1, ncols: int = 1, **kwargs):
        """Get or create axes."""
        self.fig.clear()
        if nrows == 1 and ncols == 1:
            ax = self.fig.add_subplot(111, **kwargs)
            return ax
        return self.fig.subplots(nrows, ncols, **kwargs)
