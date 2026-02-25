"""
Dialog for adding/editing a recurring payment rule.
"""
from __future__ import annotations
from datetime import date
from typing import Optional

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QFormLayout, QLabel, QLineEdit, QSpinBox, QVBoxLayout,
)

from app.core.data_manager import DataManager
from app.core.models import RecurringPayment
from app.ui.widgets.amount_input import AmountInput


class AddRecurringDialog(QDialog):
    def __init__(self, data_manager: DataManager, parent=None, recurring: Optional[RecurringPayment] = None):
        super().__init__(parent)
        self._dm = data_manager
        self._editing = recurring
        self.setWindowTitle("Edit Recurring" if recurring else "Add Recurring Payment")
        self.setFixedWidth(420)
        self.setModal(True)
        self._build_ui()
        if recurring:
            self._populate(recurring)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Recurring Payment")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        # Name
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. Netflix, Rent")
        form.addRow("Name:", self._name_edit)

        # Type
        self._type_combo = QComboBox()
        self._type_combo.addItems(["Expense", "Income"])
        form.addRow("Type:", self._type_combo)

        # Amount
        self._amount_input = AmountInput()
        form.addRow("Amount:", self._amount_input)

        # Frequency
        self._freq_combo = QComboBox()
        self._freq_combo.addItems(["Monthly", "Weekly", "Biweekly", "Yearly"])
        self._freq_combo.currentIndexChanged.connect(self._on_freq_changed)
        form.addRow("Frequency:", self._freq_combo)

        # Day of month
        self._dom_spin = QSpinBox()
        self._dom_spin.setRange(1, 31)
        self._dom_spin.setValue(1)
        form.addRow("Day of month:", self._dom_spin)
        self._dom_row_label = form.labelForField(self._dom_spin)

        # Category
        self._cat_combo = QComboBox()
        self._populate_categories()
        form.addRow("Category:", self._cat_combo)

        # Start date
        self._start_edit = QDateEdit()
        self._start_edit.setCalendarPopup(True)
        self._start_edit.setDate(QDate.currentDate())
        self._start_edit.setDisplayFormat("MM/dd/yyyy")
        form.addRow("Start date:", self._start_edit)

        # Active
        self._active_check = QCheckBox("Active")
        self._active_check.setChecked(True)
        form.addRow("", self._active_check)

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

    def _on_freq_changed(self, index: int):
        freq = ["monthly", "weekly", "biweekly", "yearly"][index]
        self._dom_spin.setEnabled(freq in ("monthly", "yearly"))

    def _populate(self, rec: RecurringPayment):
        self._name_edit.setText(rec.name)
        self._type_combo.setCurrentText("Income" if rec.type == "income" else "Expense")
        self._amount_input.set_value(rec.amount)
        freq_map = {"monthly": 0, "weekly": 1, "biweekly": 2, "yearly": 3}
        self._freq_combo.setCurrentIndex(freq_map.get(rec.frequency, 0))
        if rec.day_of_month:
            self._dom_spin.setValue(rec.day_of_month)
        if rec.category_id in self._cat_ids:
            self._cat_combo.setCurrentIndex(self._cat_ids.index(rec.category_id))
        d = date.fromisoformat(rec.start_date)
        self._start_edit.setDate(QDate(d.year, d.month, d.day))
        self._active_check.setChecked(rec.active)

    def _on_accept(self):
        if not self._name_edit.text().strip():
            return
        if self._amount_input.get_value() <= 0:
            return
        self.accept()

    def get_recurring(self) -> RecurringPayment:
        import uuid
        freq_map = {0: "monthly", 1: "weekly", 2: "biweekly", 3: "yearly"}
        freq = freq_map[self._freq_combo.currentIndex()]
        qdate = self._start_edit.date()
        start_str = f"{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d}"
        cat_id = self._cat_ids[self._cat_combo.currentIndex()] if self._cat_ids else ""

        if self._editing:
            rec = self._editing
            rec.name = self._name_edit.text().strip()
            rec.type = "income" if self._type_combo.currentIndex() == 1 else "expense"
            rec.amount = self._amount_input.get_value()
            rec.frequency = freq
            rec.day_of_month = self._dom_spin.value() if freq in ("monthly", "yearly") else None
            rec.category_id = cat_id
            rec.start_date = start_str
            rec.active = self._active_check.isChecked()
            return rec
        else:
            return RecurringPayment(
                id=f"rec_{uuid.uuid4().hex[:12]}",
                name=self._name_edit.text().strip(),
                type="income" if self._type_combo.currentIndex() == 1 else "expense",
                amount=self._amount_input.get_value(),
                category_id=cat_id,
                frequency=freq,
                day_of_month=self._dom_spin.value() if freq in ("monthly", "yearly") else None,
                start_date=start_str,
                active=self._active_check.isChecked(),
            )
