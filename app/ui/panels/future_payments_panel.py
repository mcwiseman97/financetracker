"""
Future payments panel: sortable list by due_date/priority with color coding.
"Mark Complete" optionally converts to transaction.
"""
from __future__ import annotations
from datetime import date
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QDialogButtonBox,
    QHBoxLayout, QHeaderView, QLabel, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from app.core.data_manager import DataManager
from app.core.models import FuturePayment, Transaction
from app.ui.panels.base_panel import BasePanel
from app.ui.dialogs.add_future_payment_dialog import AddFuturePaymentDialog
from app.ui.dialogs.add_transaction_dialog import AddTransactionDialog


PRIORITY_COLORS = {
    "high": "#f38ba8",
    "medium": "#f9e2af",
    "low": "#a6adc8",
}


class FuturePaymentsPanel(BasePanel):
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
        title = QLabel("Future Payments")
        title.setObjectName("SectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self._add_btn = QPushButton("+ Add Payment")
        self._add_btn.setObjectName("PrimaryButton")
        self._add_btn.clicked.connect(self._add_payment)
        header_row.addWidget(self._add_btn)

        self._edit_btn = QPushButton("Edit")
        self._edit_btn.clicked.connect(self._edit_payment)
        header_row.addWidget(self._edit_btn)

        self._complete_btn = QPushButton("Mark Complete")
        self._complete_btn.setObjectName("SuccessButton")
        self._complete_btn.clicked.connect(self._mark_complete)
        header_row.addWidget(self._complete_btn)

        self._del_btn = QPushButton("Delete")
        self._del_btn.setObjectName("DangerButton")
        self._del_btn.clicked.connect(self._delete_payment)
        header_row.addWidget(self._del_btn)

        layout.addLayout(header_row)

        # Filter
        filter_row = QHBoxLayout()
        self._show_completed = QCheckBox("Show completed")
        self._show_completed.stateChanged.connect(self.refresh)
        filter_row.addWidget(self._show_completed)
        filter_row.addStretch()

        # Sort info
        sort_info = QLabel("Click column headers to sort")
        sort_info.setObjectName("SubTitle")
        filter_row.addWidget(sort_info)
        layout.addLayout(filter_row)

        # Table
        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["Title", "Due Date", "Amount", "Priority", "Category", "Status"]
        )
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.setSortingEnabled(True)
        self._table.doubleClicked.connect(self._edit_payment)
        layout.addWidget(self._table, 1)

        # Summary
        self._summary_label = QLabel()
        self._summary_label.setObjectName("SubTitle")
        layout.addWidget(self._summary_label)

    def _connect_signals(self):
        self._dm.future_payments_changed.connect(self.refresh)

    def refresh(self):
        show_completed = self._show_completed.isChecked()
        payments = self._dm.future_payments
        if not show_completed:
            payments = [p for p in payments if not p.completed]

        # Sort by due_date ascending (incomplete first, then complete)
        payments = sorted(payments, key=lambda p: (p.completed, p.due_date))

        symbol = self._dm.settings.currency_symbol
        today = date.today()

        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)

        for fp in payments:
            row = self._table.rowCount()
            self._table.insertRow(row)

            # Title
            title_item = QTableWidgetItem(fp.title)
            if fp.completed:
                title_item.setForeground(QColor("#585b70"))
            self._table.setItem(row, 0, title_item)

            # Due date with overdue highlight
            due = date.fromisoformat(fp.due_date)
            due_item = QTableWidgetItem(fp.due_date)
            if not fp.completed:
                if due < today:
                    due_item.setForeground(QColor("#f38ba8"))
                elif (due - today).days <= 7:
                    due_item.setForeground(QColor("#f9e2af"))
            self._table.setItem(row, 1, due_item)

            # Amount
            est_str = "~" if fp.estimated else ""
            amt_item = QTableWidgetItem(f"{est_str}{symbol}{fp.amount:,.2f}")
            self._table.setItem(row, 2, amt_item)

            # Priority
            prio_item = QTableWidgetItem(fp.priority.capitalize())
            prio_color = PRIORITY_COLORS.get(fp.priority, "#a6adc8")
            prio_item.setForeground(QColor(prio_color))
            self._table.setItem(row, 3, prio_item)

            # Category
            cat_name = self._dm.get_category_name(fp.category_id) if fp.category_id else "—"
            self._table.setItem(row, 4, QTableWidgetItem(cat_name))

            # Status
            if fp.completed:
                status = "✓ Done"
            elif due < today:
                status = "⚠ Overdue"
            else:
                days_left = (due - today).days
                status = f"{days_left}d left"
            status_item = QTableWidgetItem(status)
            self._table.setItem(row, 5, status_item)

            # Store FP id
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, fp.id)

        self._table.setSortingEnabled(True)

        # Summary
        pending = [p for p in self._dm.future_payments if not p.completed]
        overdue = [p for p in pending if date.fromisoformat(p.due_date) < today]
        total_pending = sum(p.amount for p in pending)
        self._summary_label.setText(
            f"{len(pending)} pending  |  "
            f"{len(overdue)} overdue  |  "
            f"Total upcoming: {symbol}{total_pending:,.2f}"
        )

    def _selected_payment(self) -> Optional[FuturePayment]:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        fp_id = self._table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        return next((p for p in self._dm.future_payments if p.id == fp_id), None)

    def _add_payment(self):
        dialog = AddFuturePaymentDialog(self._dm, self)
        if dialog.exec():
            fp = dialog.get_payment()
            self._dm.add_future_payment(fp)

    def _edit_payment(self):
        fp = self._selected_payment()
        if not fp:
            return
        dialog = AddFuturePaymentDialog(self._dm, self, payment=fp)
        if dialog.exec():
            updated = dialog.get_payment()
            self._dm.update_future_payment(updated)

    def _mark_complete(self):
        fp = self._selected_payment()
        if not fp:
            return
        # Ask if user wants to convert to transaction
        reply = QMessageBox.question(
            self, "Mark Complete",
            f"Mark '{fp.title}' as complete?\n\n"
            "Would you also like to log this as a transaction?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Cancel:
            return

        if reply == QMessageBox.StandardButton.Yes:
            # Pre-fill transaction dialog
            import uuid
            from datetime import datetime
            from app.core.models import Transaction
            txn = Transaction(
                id=f"txn_{uuid.uuid4().hex[:12]}",
                type="expense",
                amount=fp.amount,
                date=date.today().isoformat(),
                category_id=fp.category_id,
                description=fp.title,
                notes=f"From future payment: {fp.title}",
                created_at=datetime.now().isoformat(timespec="seconds"),
            )
            dialog = AddTransactionDialog(self._dm, self, transaction=txn)
            if dialog.exec():
                new_txn = dialog.get_transaction()
                self._dm.add_transaction(new_txn)

        self._dm.complete_future_payment(fp.id)

    def _delete_payment(self):
        fp = self._selected_payment()
        if not fp:
            return
        reply = QMessageBox.question(
            self, "Delete Payment",
            f"Delete '{fp.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._dm.delete_future_payment(fp.id)
