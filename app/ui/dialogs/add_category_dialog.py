"""
Dialog for adding/editing a spending category.
"""
from __future__ import annotations
from typing import Optional

from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QVBoxLayout, QColorDialog,
)
from PyQt6.QtGui import QColor

from app.core.data_manager import DataManager
from app.core.models import Category


class AddCategoryDialog(QDialog):
    def __init__(self, data_manager: DataManager, parent=None, category: Optional[Category] = None):
        super().__init__(parent)
        self._dm = data_manager
        self._editing = category
        self._color = category.color if category else "#cba6f7"
        self.setWindowTitle("Edit Category" if category else "Add Category")
        self.setFixedWidth(400)
        self.setModal(True)
        self._build_ui()
        if category:
            self._populate(category)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Edit Category" if self._editing else "Add Category")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        # Name
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. Groceries")
        form.addRow("Name:", self._name_edit)

        # Color
        color_row = QHBoxLayout()
        self._color_preview = QPushButton()
        self._color_preview.setFixedSize(32, 32)
        self._color_preview.clicked.connect(self._pick_color)
        self._update_color_preview()
        color_row.addWidget(self._color_preview)
        color_row.addStretch()
        form.addRow("Color:", color_row)

        # Budget limit
        self._budget_spin = QDoubleSpinBox()
        self._budget_spin.setRange(0, 99999.99)
        self._budget_spin.setDecimals(2)
        self._budget_spin.setPrefix("$ ")
        self._budget_spin.setValue(0.0)
        form.addRow("Monthly budget:", self._budget_spin)

        # Bucket
        self._bucket_combo = QComboBox()
        self._bucket_combo.addItems(["Needs", "Wants", "Savings", "Unclassified"])
        form.addRow("Budget bucket:", self._bucket_combo)

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

    def _update_color_preview(self):
        self._color_preview.setStyleSheet(
            f"background-color: {self._color}; border-radius: 6px; border: none;"
        )

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._color), self, "Choose Category Color")
        if color.isValid():
            self._color = color.name()
            self._update_color_preview()

    def _populate(self, cat: Category):
        self._name_edit.setText(cat.name)
        self._budget_spin.setValue(cat.budget_limit)
        bucket_map = {"needs": 0, "wants": 1, "savings": 2, "": 3}
        self._bucket_combo.setCurrentIndex(bucket_map.get(cat.bucket.lower(), 3))
        self._active_check.setChecked(cat.active)

    def _on_accept(self):
        if not self._name_edit.text().strip():
            return
        self.accept()

    def get_category(self) -> Category:
        import uuid
        bucket_map = {0: "needs", 1: "wants", 2: "savings", 3: ""}
        bucket = bucket_map[self._bucket_combo.currentIndex()]

        if self._editing:
            cat = self._editing
            cat.name = self._name_edit.text().strip()
            cat.color = self._color
            cat.budget_limit = self._budget_spin.value()
            cat.bucket = bucket
            cat.active = self._active_check.isChecked()
            return cat
        else:
            return Category(
                id=f"cat_{uuid.uuid4().hex[:12]}",
                name=self._name_edit.text().strip(),
                color=self._color,
                icon="tag",
                budget_limit=self._budget_spin.value(),
                budget_period="monthly",
                bucket=bucket,
                active=self._active_check.isChecked(),
                sort_order=len(self._dm.categories),
            )
