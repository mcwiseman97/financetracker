"""
Dismissible alert banner widget.
Shows warning/error/success messages at the top of panels.
"""
from __future__ import annotations
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QWidget,
)


class AlertBanner(QWidget):
    """A dismissible horizontal alert bar."""

    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._build_ui()
        self.hide()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        self._icon = QLabel("⚠")
        self._icon.setFixedWidth(20)
        layout.addWidget(self._icon)

        self._message = QLabel()
        self._message.setWordWrap(True)
        layout.addWidget(self._message, 1)

        dismiss_btn = QPushButton("✕")
        dismiss_btn.setFixedSize(24, 24)
        dismiss_btn.setFlat(True)
        dismiss_btn.clicked.connect(self.hide)
        layout.addWidget(dismiss_btn)

    def show_message(self, message: str, level: str = WARNING):
        """Show the banner with a message."""
        self._message.setText(message)
        if level == self.ERROR:
            self.setObjectName("AlertBannerError")
            self._icon.setText("✕")
        elif level == self.SUCCESS:
            self.setObjectName("AlertBannerSuccess")
            self._icon.setText("✓")
        else:
            self.setObjectName("AlertBanner")
            self._icon.setText("⚠")
        # Force style refresh
        self.style().unpolish(self)
        self.style().polish(self)
        self.show()

    def show_warning(self, message: str):
        self.show_message(message, self.WARNING)

    def show_error(self, message: str):
        self.show_message(message, self.ERROR)

    def show_success(self, message: str):
        self.show_message(message, self.SUCCESS)
