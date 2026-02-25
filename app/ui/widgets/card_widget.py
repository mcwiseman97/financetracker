"""
Rounded card widget with drop shadow effect.
Base container used throughout the UI.
"""
from __future__ import annotations
from typing import Optional

from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QVBoxLayout, QWidget
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt


class CardWidget(QFrame):
    """A rounded card frame with a subtle drop shadow."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        shadow: bool = True,
    ):
        super().__init__(parent)
        self.setObjectName("CardWidget")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        if shadow:
            effect = QGraphicsDropShadowEffect(self)
            effect.setBlurRadius(16)
            effect.setOffset(0, 2)
            effect.setColor(QColor(0, 0, 0, 60))
            self.setGraphicsEffect(effect)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(8)

    @property
    def card_layout(self) -> QVBoxLayout:
        return self._layout
