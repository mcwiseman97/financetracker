"""
Dashboard metric stat card with label, value, and optional subtext.
"""
from __future__ import annotations
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QLabel, QVBoxLayout, QWidget,
)
from PyQt6.QtGui import QColor


class StatCard(QFrame):
    """A card displaying a single metric with label/value/subtext."""

    def __init__(
        self,
        label: str = "",
        value: str = "",
        subtext: str = "",
        value_style: str = "",  # "positive" | "negative" | ""
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setObjectName("StatCard")

        effect = QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(16)
        effect.setOffset(0, 2)
        effect.setColor(QColor(0, 0, 0, 50))
        self.setGraphicsEffect(effect)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self._label = QLabel(label)
        self._label.setObjectName("StatCardLabel")
        layout.addWidget(self._label)

        self._value = QLabel(value)
        self._value.setObjectName("StatCardValue")
        layout.addWidget(self._value)

        self._subtext = QLabel(subtext)
        self._subtext.setObjectName("StatCardSubtext")
        layout.addWidget(self._subtext)

        if value_style == "positive":
            self._value.setObjectName("AmountPositive")
        elif value_style == "negative":
            self._value.setObjectName("AmountNegative")

    def set_label(self, text: str):
        self._label.setText(text)

    def set_value(self, text: str, style: str = ""):
        self._value.setText(text)
        if style == "positive":
            self._value.setObjectName("AmountPositive")
        elif style == "negative":
            self._value.setObjectName("AmountNegative")
        else:
            self._value.setObjectName("StatCardValue")
        # Force style refresh
        self._value.style().unpolish(self._value)
        self._value.style().polish(self._value)

    def set_subtext(self, text: str):
        self._subtext.setText(text)
