"""
Dialog for adding a new transaction (income or expense).
"""
from __future__ import annotations
from datetime import date
from typing import Optional

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QFormLayout, QLabel, QLineEdit, QTextEdit, QVBoxLayout,
)

from app.core.data_manager import DataManager
from app.core.models import Transaction
from app.ui.widgets.amount_input import AmountInput


class AddTransactionDialog(QDialog):
    def __init__(self, data_manager: DataManager, parent=None, transaction: Optional[Transaction] = None):
        super().__init__(parent)
        self._dm = data_manager
        self._editing = transaction
        self.setWindowTitle("Edit Transaction" if transaction else "Add Transaction")
        self.setFixedWidth(420)
        self.setModal(True)
        self._build_ui()
        if transaction:
            self._populate(transaction)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Edit Transaction" if self._editing else "Add Transaction")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        # Type
        self._type_combo = QComboBox()
        self._type_combo.addItems(["Expense", "Income"])
        form.addRow("Type:", self._type_combo)

        # Amount
        self._amount_input = AmountInput()
        form.addRow("Amount:", self._amount_input)

        # Date
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setDisplayFormat("MM/dd/yyyy")
        form.addRow("Date:", self._date_edit)

        # Category
        self._cat_combo = QComboBox()
        self._populate_categories()
        form.addRow("Category:", self._cat_combo)

        # Description
        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Brief description")
        form.addRow("Description:", self._desc_edit)

        # Notes
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

    def _populate_categories(self):
        self._cat_combo.clear()
        self._cat_ids: list[str] = []
        for cat in sorted(self._dm.categories, key=lambda c: c.name):
            if cat.active:
                self._cat_combo.addItem(cat.name)
                self._cat_ids.append(cat.id)

    def _populate(self, txn: Transaction):
        """Fill form with existing transaction data for editing."""
        self._type_combo.setCurrentText("Income" if txn.type == "income" else "Expense")
        self._amount_input.set_value(txn.amount)
        d = date.fromisoformat(txn.date)
        self._date_edit.setDate(QDate(d.year, d.month, d.day))
        # Set category
        if txn.category_id in self._cat_ids:
            self._cat_combo.setCurrentIndex(self._cat_ids.index(txn.category_id))
        self._desc_edit.setText(txn.description)
        self._notes_edit.setPlainText(txn.notes)

    def _on_accept(self):
        if self._amount_input.get_value() <= 0:
            return  # silently ignore zero amounts
        self.accept()

    def get_transaction(self) -> Transaction:
        """Build and return the transaction model from form data."""
        from datetime import datetime
        import uuid
        qdate = self._date_edit.date()
        date_str = f"{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d}"
        cat_id = self._cat_ids[self._cat_combo.currentIndex()] if self._cat_ids else ""

        if self._editing:
            txn = self._editing
            txn.type = "income" if self._type_combo.currentIndex() == 1 else "expense"
            txn.amount = self._amount_input.get_value()
            txn.date = date_str
            txn.category_id = cat_id
            txn.description = self._desc_edit.text().strip()
            txn.notes = self._notes_edit.toPlainText().strip()
            return txn
        else:
            return Transaction(
                id=f"txn_{uuid.uuid4().hex[:12]}",
                type="income" if self._type_combo.currentIndex() == 1 else "expense",
                amount=self._amount_input.get_value(),
                date=date_str,
                category_id=cat_id,
                description=self._desc_edit.text().strip(),
                created_at=datetime.now().isoformat(timespec="seconds"),
            )
