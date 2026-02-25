"""
Base class for all panels. Provides data_manager reference and refresh() protocol.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget

from app.core.data_manager import DataManager


class BasePanel(QWidget):
    def __init__(self, data_manager: DataManager, theme_manager=None, parent=None):
        super().__init__(parent)
        self._dm = data_manager
        self._tm = theme_manager
        self._signals_connected = False

    def refresh(self):
        """Reload and redisplay data. Must be implemented by subclasses."""
        raise NotImplementedError

    def _connect_signals(self):
        """Connect data_manager signals to refresh(). Call once in __init__."""
        raise NotImplementedError
