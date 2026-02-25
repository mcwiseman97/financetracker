"""
Dialog for adding a deposit or withdrawal to a savings account.
"""
from __future__ import annotations
from datetime import date

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QFormLayout, QLabel, QTextEdit, QVBoxLayout,
)

from app.core.models import SavingsTransaction
from app.ui.widgets.amount_input import AmountInput


class SavingsTransactionDialog(QDialog):
    def __init__(self, account_name: str, parent=None):
        super().__init__(parent)
        self._account_name = account_name
        self.setWindowTitle(f"Transaction — {account_name}")
        self.setFixedWidth(380)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Add Transaction")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self._type_combo = QComboBox()
        self._type_combo.addItems(["Deposit", "Withdrawal"])
        form.addRow("Type:", self._type_combo)

        self._amount_input = AmountInput()
        form.addRow("Amount:", self._amount_input)

        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setDisplayFormat("MM/dd/yyyy")
        form.addRow("Date:", self._date_edit)

        self._notes_edit = QTextEdit()
        self._notes_edit.setFixedHeight(60)
        self._notes_edit.setPlaceholderText("Optional notes...")
        form.addRow("Notes:", self._notes_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        if self._amount_input.get_value() <= 0:
            return
        self.accept()

    def get_transaction(self) -> SavingsTransaction:
        import uuid
        qdate = self._date_edit.date()
        date_str = f"{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d}"
        return SavingsTransaction(
            id=f"savtxn_{uuid.uuid4().hex[:12]}",
            date=date_str,
            amount=self._amount_input.get_value(),
            type="deposit" if self._type_combo.currentIndex() == 0 else "withdrawal",
            notes=self._notes_edit.toPlainText().strip(),
        )
