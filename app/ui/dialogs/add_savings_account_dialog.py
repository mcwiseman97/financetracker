"""
Dialog for adding/editing a savings account.
"""
from __future__ import annotations
from typing import Optional

from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QColorDialog,
)
from PyQt6.QtGui import QColor

from app.core.models import SavingsAccount


class AddSavingsAccountDialog(QDialog):
    def __init__(self, parent=None, account: Optional[SavingsAccount] = None):
        super().__init__(parent)
        self._editing = account
        self._color = account.color if account else "#2196F3"
        self.setWindowTitle("Edit Account" if account else "Add Savings Account")
        self.setFixedWidth(380)
        self.setModal(True)
        self._build_ui()
        if account:
            self._populate(account)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Savings Account")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. Emergency Fund")
        form.addRow("Account name:", self._name_edit)

        self._institution_edit = QLineEdit()
        self._institution_edit.setPlaceholderText("e.g. Online Bank")
        form.addRow("Institution:", self._institution_edit)

        self._target_spin = QDoubleSpinBox()
        self._target_spin.setRange(0, 9_999_999.99)
        self._target_spin.setDecimals(2)
        self._target_spin.setPrefix("$ ")
        form.addRow("Target balance:", self._target_spin)

        color_row = QHBoxLayout()
        self._color_preview = QPushButton()
        self._color_preview.setFixedSize(32, 32)
        self._color_preview.clicked.connect(self._pick_color)
        self._update_color_preview()
        color_row.addWidget(self._color_preview)
        color_row.addStretch()
        form.addRow("Color:", color_row)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _update_color_preview(self):
        self._color_preview.setStyleSheet(
            f"background-color: {self._color}; border-radius: 6px; border: none;"
        )

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._color), self, "Choose Account Color")
        if color.isValid():
            self._color = color.name()
            self._update_color_preview()

    def _populate(self, account: SavingsAccount):
        self._name_edit.setText(account.name)
        self._institution_edit.setText(account.institution)
        self._target_spin.setValue(account.target_balance)

    def _on_accept(self):
        if not self._name_edit.text().strip():
            return
        self.accept()

    def get_account(self) -> SavingsAccount:
        import uuid
        if self._editing:
            acc = self._editing
            acc.name = self._name_edit.text().strip()
            acc.institution = self._institution_edit.text().strip()
            acc.target_balance = self._target_spin.value()
            acc.color = self._color
            return acc
        else:
            return SavingsAccount(
                id=f"sav_{uuid.uuid4().hex[:12]}",
                name=self._name_edit.text().strip(),
                institution=self._institution_edit.text().strip(),
                target_balance=self._target_spin.value(),
                color=self._color,
            )
