"""
Transactions panel: QTableView with filter bar and Add/Edit/Delete.
"""
from __future__ import annotations
from datetime import date
from typing import Optional

from PyQt6.QtCore import (
    QAbstractTableModel, QDate, QModelIndex, Qt, pyqtSignal,
)
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QDateEdit, QHBoxLayout,
    QHeaderView, QLabel, QMessageBox, QPushButton,
    QTableView, QVBoxLayout,
)

from app.core.data_manager import DataManager
from app.core.models import Transaction
from app.ui.panels.base_panel import BasePanel
from app.ui.dialogs.add_transaction_dialog import AddTransactionDialog


class TransactionTableModel(QAbstractTableModel):
    COLUMNS = ["Date", "Type", "Description", "Category", "Amount", "Notes"]

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self._dm = data_manager
        self._rows: list[Transaction] = []

    def set_rows(self, rows: list[Transaction]):
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
        txn = self._rows[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return txn.date
            elif col == 1:
                return txn.type.capitalize()
            elif col == 2:
                return txn.description
            elif col == 3:
                return self._dm.get_category_name(txn.category_id)
            elif col == 4:
                symbol = self._dm.settings.currency_symbol
                if txn.type == "income":
                    return f"+{symbol}{txn.amount:,.2f}"
                return f"-{symbol}{txn.amount:,.2f}"
            elif col == 5:
                return txn.notes

        elif role == Qt.ItemDataRole.ForegroundRole:
            from PyQt6.QtGui import QColor
            if col == 4:
                if txn.type == "income":
                    return QColor("#a6e3a1")
                return QColor("#f38ba8")

        elif role == Qt.ItemDataRole.UserRole:
            return txn

        return None

    def get_transaction(self, row: int) -> Optional[Transaction]:
        if 0 <= row < len(self._rows):
            return self._rows[row]
        return None


class TransactionsPanel(BasePanel):
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
        title = QLabel("Transactions")
        title.setObjectName("SectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self._add_btn = QPushButton("+ Add Transaction")
        self._add_btn.setObjectName("PrimaryButton")
        self._add_btn.clicked.connect(self._add_transaction)
        header_row.addWidget(self._add_btn)

        self._edit_btn = QPushButton("Edit")
        self._edit_btn.clicked.connect(self._edit_transaction)
        header_row.addWidget(self._edit_btn)

        self._del_btn = QPushButton("Delete")
        self._del_btn.setObjectName("DangerButton")
        self._del_btn.clicked.connect(self._delete_transaction)
        header_row.addWidget(self._del_btn)

        layout.addLayout(header_row)

        # Filter bar
        filter_row = QHBoxLayout()

        filter_row.addWidget(QLabel("Month:"))
        self._month_combo = QComboBox()
        self._month_combo.setMinimumWidth(120)
        self._populate_month_filter()
        self._month_combo.currentIndexChanged.connect(self._apply_filters)
        filter_row.addWidget(self._month_combo)

        filter_row.addSpacing(12)
        filter_row.addWidget(QLabel("Category:"))
        self._cat_filter = QComboBox()
        self._cat_filter.setMinimumWidth(140)
        self._cat_filter.currentIndexChanged.connect(self._apply_filters)
        filter_row.addWidget(self._cat_filter)

        filter_row.addSpacing(12)
        filter_row.addWidget(QLabel("Type:"))
        self._type_filter = QComboBox()
        self._type_filter.addItems(["All", "Expense", "Income"])
        self._type_filter.currentIndexChanged.connect(self._apply_filters)
        filter_row.addWidget(self._type_filter)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Table
        self._model = TransactionTableModel(self._dm)
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setShowGrid(True)
        self._table.doubleClicked.connect(self._edit_transaction)
        layout.addWidget(self._table)

        # Summary row
        self._summary_label = QLabel()
        self._summary_label.setObjectName("SubTitle")
        layout.addWidget(self._summary_label)

    def _populate_month_filter(self):
        self._month_combo.blockSignals(True)
        self._month_combo.clear()
        self._month_combo.addItem("All months", None)
        today = date.today()
        for i in range(24):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            label = date(y, m, 1).strftime("%B %Y")
            self._month_combo.addItem(label, f"{y:04d}-{m:02d}")
        self._month_combo.blockSignals(False)

    def _connect_signals(self):
        self._dm.transactions_changed.connect(self.refresh)
        self._dm.categories_changed.connect(self._refresh_category_filter)

    def refresh(self):
        self._refresh_category_filter()
        self._apply_filters()

    def _refresh_category_filter(self):
        self._cat_filter.blockSignals(True)
        current = self._cat_filter.currentData()
        self._cat_filter.clear()
        self._cat_filter.addItem("All categories", None)
        for cat in sorted(self._dm.categories, key=lambda c: c.name):
            if cat.active:
                self._cat_filter.addItem(cat.name, cat.id)
        # Restore selection
        for i in range(self._cat_filter.count()):
            if self._cat_filter.itemData(i) == current:
                self._cat_filter.setCurrentIndex(i)
                break
        self._cat_filter.blockSignals(False)

    def _apply_filters(self):
        month_filter = self._month_combo.currentData()
        cat_filter = self._cat_filter.currentData()
        type_filter = self._type_filter.currentText().lower()

        rows = self._dm.transactions
        if month_filter:
            rows = [t for t in rows if t.date.startswith(month_filter)]
        if cat_filter:
            rows = [t for t in rows if t.category_id == cat_filter]
        if type_filter != "all":
            rows = [t for t in rows if t.type == type_filter]

        rows = sorted(rows, key=lambda t: t.date, reverse=True)
        self._model.set_rows(rows)

        # Update summary
        symbol = self._dm.settings.currency_symbol
        total_in = sum(t.amount for t in rows if t.type == "income")
        total_out = sum(t.amount for t in rows if t.type == "expense")
        self._summary_label.setText(
            f"{len(rows)} transactions  |  "
            f"Income: {symbol}{total_in:,.2f}  |  "
            f"Expenses: {symbol}{total_out:,.2f}  |  "
            f"Net: {symbol}{total_in - total_out:,.2f}"
        )

    def _selected_transaction(self) -> Optional[Transaction]:
        indexes = self._table.selectionModel().selectedRows()
        if indexes:
            return self._model.get_transaction(indexes[0].row())
        return None

    def _add_transaction(self):
        dialog = AddTransactionDialog(self._dm, self)
        if dialog.exec():
            txn = dialog.get_transaction()
            self._dm.add_transaction(txn)

    def _edit_transaction(self):
        txn = self._selected_transaction()
        if not txn:
            return
        dialog = AddTransactionDialog(self._dm, self, transaction=txn)
        if dialog.exec():
            updated = dialog.get_transaction()
            self._dm.update_transaction(updated)

    def _delete_transaction(self):
        txn = self._selected_transaction()
        if not txn:
            return
        reply = QMessageBox.question(
            self, "Delete Transaction",
            f"Delete transaction: {txn.description} ({txn.date})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._dm.delete_transaction(txn.id)
