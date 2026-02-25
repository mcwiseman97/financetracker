"""
Recurring payments panel: table of rules with active toggle and "Generate Now".
"""
from __future__ import annotations
from datetime import date
from typing import Optional

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView,
    QLabel, QMessageBox, QPushButton, QTableView, QVBoxLayout,
)

from app.core.data_manager import DataManager
from app.core.models import RecurringPayment
from app.core.recurring_engine import populate_recurring
from app.ui.panels.base_panel import BasePanel
from app.ui.dialogs.add_recurring_dialog import AddRecurringDialog


class RecurringTableModel(QAbstractTableModel):
    COLUMNS = ["Name", "Type", "Amount", "Frequency", "Day", "Category", "Next Due", "Active"]

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self._dm = data_manager
        self._rows: list[RecurringPayment] = []

    def set_rows(self, rows: list[RecurringPayment]):
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        rec = self._rows[index.row()]
        col = index.column()
        symbol = self._dm.settings.currency_symbol

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return rec.name
            if col == 1: return rec.type.capitalize()
            if col == 2: return f"{symbol}{rec.amount:,.2f}"
            if col == 3: return rec.frequency.capitalize()
            if col == 4:
                if rec.day_of_month:
                    return f"Day {rec.day_of_month}"
                return "-"
            if col == 5: return self._dm.get_category_name(rec.category_id)
            if col == 6:
                # Calculate next occurrence
                from app.core.recurring_engine import _get_dates_in_range
                today = date.today()
                start = date.fromisoformat(rec.start_date)
                dates = _get_dates_in_range(rec, today, today.replace(year=today.year + 1), start)
                return dates[0].isoformat() if dates else "-"
            if col == 7: return "Yes" if rec.active else "No"

        elif role == Qt.ItemDataRole.ForegroundRole:
            from PyQt6.QtGui import QColor
            if not rec.active:
                return QColor("#585b70")
            if col == 2:
                if rec.type == "income":
                    return QColor("#a6e3a1")
                return QColor("#f38ba8")

        elif role == Qt.ItemDataRole.UserRole:
            return rec

        return None

    def get_recurring(self, row: int) -> Optional[RecurringPayment]:
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None


class RecurringPanel(BasePanel):
    def __init__(self, data_manager: DataManager, theme_manager=None, parent=None):
        super().__init__(data_manager, theme_manager, parent)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Header
        header_row = QHBoxLayout()
        title = QLabel("Recurring Payments")
        title.setObjectName("SectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self._add_btn = QPushButton("+ Add Recurring")
        self._add_btn.setObjectName("PrimaryButton")
        self._add_btn.clicked.connect(self._add_recurring)
        header_row.addWidget(self._add_btn)

        self._edit_btn = QPushButton("Edit")
        self._edit_btn.clicked.connect(self._edit_recurring)
        header_row.addWidget(self._edit_btn)

        self._toggle_btn = QPushButton("Toggle Active")
        self._toggle_btn.clicked.connect(self._toggle_active)
        header_row.addWidget(self._toggle_btn)

        self._del_btn = QPushButton("Delete")
        self._del_btn.setObjectName("DangerButton")
        self._del_btn.clicked.connect(self._delete_recurring)
        header_row.addWidget(self._del_btn)

        self._gen_btn = QPushButton("Generate Now")
        self._gen_btn.setObjectName("SuccessButton")
        self._gen_btn.clicked.connect(self._generate_now)
        header_row.addWidget(self._gen_btn)

        layout.addLayout(header_row)

        # Info label
        info = QLabel("Recurring rules auto-generate transactions on app startup.")
        info.setObjectName("SubTitle")
        layout.addWidget(info)

        # Table
        self._model = RecurringTableModel(self._dm)
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.doubleClicked.connect(self._edit_recurring)
        layout.addWidget(self._table)

        # Summary
        self._summary_label = QLabel()
        self._summary_label.setObjectName("SubTitle")
        layout.addWidget(self._summary_label)

    def _connect_signals(self):
        self._dm.recurring_changed.connect(self.refresh)

    def refresh(self):
        rows = sorted(self._dm.recurring, key=lambda r: r.name)
        self._model.set_rows(rows)
        active = sum(1 for r in rows if r.active)
        symbol = self._dm.settings.currency_symbol
        monthly = sum(
            r.amount for r in rows if r.active and r.type == "expense" and r.frequency == "monthly"
        )
        self._summary_label.setText(
            f"{len(rows)} rules ({active} active)  |  "
            f"Monthly expenses: {symbol}{monthly:,.2f}"
        )

    def _selected_recurring(self) -> Optional[RecurringPayment]:
        indexes = self._table.selectionModel().selectedRows()
        if indexes:
            return self._model.get_recurring(indexes[0].row())
        return None

    def _add_recurring(self):
        dialog = AddRecurringDialog(self._dm, self)
        if dialog.exec():
            rec = dialog.get_recurring()
            self._dm.add_recurring(rec)

    def _edit_recurring(self):
        rec = self._selected_recurring()
        if not rec:
            return
        dialog = AddRecurringDialog(self._dm, self, recurring=rec)
        if dialog.exec():
            updated = dialog.get_recurring()
            self._dm.update_recurring(updated)

    def _toggle_active(self):
        rec = self._selected_recurring()
        if not rec:
            return
        rec.active = not rec.active
        self._dm.update_recurring(rec)

    def _delete_recurring(self):
        rec = self._selected_recurring()
        if not rec:
            return
        reply = QMessageBox.question(
            self, "Delete Recurring",
            f"Delete recurring rule: {rec.name}?\n"
            "Previously generated transactions will NOT be deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._dm.delete_recurring(rec.id)

    def _generate_now(self):
        today = date.today()
        new_txns, updates = populate_recurring(
            self._dm.recurring, self._dm.transactions, today
        )
        with self._dm.bulk_operation():
            for txn in new_txns:
                self._dm.add_transaction(txn)
            for rec_id, last_date in updates:
                rec = self._dm.get_recurring(rec_id)
                if rec:
                    rec.last_generated_date = last_date
                    self._dm.update_recurring(rec)

        QMessageBox.information(
            self, "Generated",
            f"Generated {len(new_txns)} new transaction(s).",
        )
