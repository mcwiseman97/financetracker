"""
Dialog for adding/editing a future payment note.
"""
from __future__ import annotations
from datetime import date
from typing import Optional

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QFormLayout, QLabel, QLineEdit, QTextEdit, QVBoxLayout,
)

from app.core.data_manager import DataManager
from app.core.models import FuturePayment
from app.ui.widgets.amount_input import AmountInput


class AddFuturePaymentDialog(QDialog):
    def __init__(self, data_manager: DataManager, parent=None, payment: Optional[FuturePayment] = None):
        super().__init__(parent)
        self._dm = data_manager
        self._editing = payment
        self.setWindowTitle("Edit Future Payment" if payment else "Add Future Payment")
        self.setFixedWidth(400)
        self.setModal(True)
        self._build_ui()
        if payment:
            self._populate(payment)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Future Payment")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("e.g. Car registration")
        form.addRow("Title:", self._title_edit)

        self._amount_input = AmountInput()
        form.addRow("Amount:", self._amount_input)

        self._estimated_check = QCheckBox("Amount is estimated")
        form.addRow("", self._estimated_check)

        self._due_edit = QDateEdit()
        self._due_edit.setCalendarPopup(True)
        self._due_edit.setDate(QDate.currentDate())
        self._due_edit.setDisplayFormat("MM/dd/yyyy")
        form.addRow("Due date:", self._due_edit)

        self._priority_combo = QComboBox()
        self._priority_combo.addItems(["Low", "Medium", "High"])
        self._priority_combo.setCurrentIndex(1)  # default medium
        form.addRow("Priority:", self._priority_combo)

        self._cat_combo = QComboBox()
        self._cat_ids: list[str] = [""]
        self._cat_combo.addItem("(None)")
        for cat in sorted(self._dm.categories, key=lambda c: c.name):
            if cat.active:
                self._cat_combo.addItem(cat.name)
                self._cat_ids.append(cat.id)
        form.addRow("Category:", self._cat_combo)

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

    def _populate(self, fp: FuturePayment):
        self._title_edit.setText(fp.title)
        self._amount_input.set_value(fp.amount)
        self._estimated_check.setChecked(fp.estimated)
        d = date.fromisoformat(fp.due_date)
        self._due_edit.setDate(QDate(d.year, d.month, d.day))
        priority_map = {"low": 0, "medium": 1, "high": 2}
        self._priority_combo.setCurrentIndex(priority_map.get(fp.priority, 1))
        if fp.category_id in self._cat_ids:
            self._cat_combo.setCurrentIndex(self._cat_ids.index(fp.category_id))
        self._notes_edit.setPlainText(fp.notes)

    def _on_accept(self):
        if not self._title_edit.text().strip():
            return
        self.accept()

    def get_payment(self) -> FuturePayment:
        import uuid
        from datetime import datetime
        priority_map = {0: "low", 1: "medium", 2: "high"}
        qdate = self._due_edit.date()
        due_str = f"{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d}"
        cat_id = self._cat_ids[self._cat_combo.currentIndex()]

        if self._editing:
            fp = self._editing
            fp.title = self._title_edit.text().strip()
            fp.amount = self._amount_input.get_value()
            fp.estimated = self._estimated_check.isChecked()
            fp.due_date = due_str
            fp.priority = priority_map[self._priority_combo.currentIndex()]
            fp.category_id = cat_id
            fp.notes = self._notes_edit.toPlainText().strip()
            return fp
        else:
            return FuturePayment(
                id=f"fut_{uuid.uuid4().hex[:12]}",
                title=self._title_edit.text().strip(),
                amount=self._amount_input.get_value(),
                estimated=self._estimated_check.isChecked(),
                due_date=due_str,
                priority=priority_map[self._priority_combo.currentIndex()],
                category_id=cat_id,
                notes=self._notes_edit.toPlainText().strip(),
                created_at=datetime.now().isoformat(timespec="seconds"),
            )
