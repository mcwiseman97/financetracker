"""
Currency-formatted QLineEdit.
Validates as float, formats to "1,234.56" on focus-out.
"""
from __future__ import annotations
from typing import Optional

from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLineEdit, QWidget


class AmountInput(QLineEdit):
    """QLineEdit that accepts currency amounts and formats them on focus-out."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setPlaceholderText("0.00")
        validator = QDoubleValidator(0.0, 9_999_999.99, 2, self)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.setValidator(validator)
        self.setAlignment(Qt.AlignmentFlag.AlignRight)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self._format_value()

    def _format_value(self):
        text = self.text().replace(",", "").strip()
        if not text:
            return
        try:
            value = float(text)
            self.setText(f"{value:,.2f}")
        except ValueError:
            pass

    def get_value(self) -> float:
        """Return the current value as a float (0.0 if empty/invalid)."""
        text = self.text().replace(",", "").strip()
        if not text:
            return 0.0
        try:
            return float(text)
        except ValueError:
            return 0.0

    def set_value(self, value: float):
        """Set the value and format it."""
        self.setText(f"{value:,.2f}")
