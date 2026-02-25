"""
Savings panel: account cards with balance/progress and transaction history.
"""
from __future__ import annotations
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSplitter, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.core.data_manager import DataManager
from app.core.models import SavingsAccount
from app.ui.panels.base_panel import BasePanel
from app.ui.dialogs.add_savings_account_dialog import AddSavingsAccountDialog
from app.ui.dialogs.savings_transaction_dialog import SavingsTransactionDialog


class SavingsAccountCard(QFrame):
    """Card showing account name, balance, progress bar, and action buttons."""

    def __init__(self, account: SavingsAccount, symbol: str, parent=None):
        super().__init__(parent)
        self.setObjectName("CardWidget")
        self._account = account
        self.setFixedWidth(260)
        self._build(symbol)

    def _build(self, symbol: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Color dot + name
        header = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {self._account.color}; font-size: 16px;")
        dot.setFixedWidth(20)
        header.addWidget(dot)
        name = QLabel(self._account.name)
        name.setObjectName("StatCardValue")
        name.setStyleSheet("font-size: 14px;")
        header.addWidget(name, 1)
        layout.addLayout(header)

        institution = QLabel(self._account.institution or "—")
        institution.setObjectName("SubTitle")
        layout.addWidget(institution)

        # Balance
        balance_label = QLabel(f"{symbol}{self._account.current_balance:,.2f}")
        balance_label.setObjectName("AmountPositive")
        balance_label.setStyleSheet("font-size: 20px;")
        layout.addWidget(balance_label)

        # Progress bar (toward target)
        if self._account.target_balance > 0:
            pct = min(int((self._account.current_balance / self._account.target_balance) * 100), 100)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(pct)
            bar.setFixedHeight(6)
            layout.addWidget(bar)
            target_label = QLabel(f"Target: {symbol}{self._account.target_balance:,.2f} ({pct}%)")
            target_label.setObjectName("SubTitle")
            target_label.setStyleSheet("font-size: 11px;")
            layout.addWidget(target_label)

    @property
    def account_id(self) -> str:
        return self._account.id


class SavingsPanel(BasePanel):
    def __init__(self, data_manager: DataManager, theme_manager=None, parent=None):
        super().__init__(data_manager, theme_manager, parent)
        self._selected_account_id: Optional[str] = None
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Header
        header_row = QHBoxLayout()
        title = QLabel("Savings Accounts")
        title.setObjectName("SectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self._add_account_btn = QPushButton("+ New Account")
        self._add_account_btn.setObjectName("PrimaryButton")
        self._add_account_btn.clicked.connect(self._add_account)
        header_row.addWidget(self._add_account_btn)

        self._edit_account_btn = QPushButton("Edit Account")
        self._edit_account_btn.clicked.connect(self._edit_account)
        header_row.addWidget(self._edit_account_btn)

        self._del_account_btn = QPushButton("Delete Account")
        self._del_account_btn.setObjectName("DangerButton")
        self._del_account_btn.clicked.connect(self._delete_account)
        header_row.addWidget(self._del_account_btn)

        layout.addLayout(header_row)

        # Splitter: accounts row on top, transaction history below
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Accounts scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setFixedHeight(200)
        self._accounts_widget = QWidget()
        self._accounts_layout = QHBoxLayout(self._accounts_widget)
        self._accounts_layout.setContentsMargins(0, 0, 0, 0)
        self._accounts_layout.setSpacing(12)
        self._accounts_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self._accounts_widget)
        splitter.addWidget(scroll)

        # Transaction history
        history_frame = QFrame()
        history_frame.setObjectName("CardWidget")
        history_layout = QVBoxLayout(history_frame)
        history_layout.setContentsMargins(16, 12, 16, 12)
        history_layout.setSpacing(8)

        history_header = QHBoxLayout()
        self._history_title = QLabel("Select an account to view history")
        self._history_title.setObjectName("SubTitle")
        history_header.addWidget(self._history_title)
        history_header.addStretch()

        self._deposit_btn = QPushButton("+ Deposit")
        self._deposit_btn.setObjectName("SuccessButton")
        self._deposit_btn.clicked.connect(self._add_deposit)
        self._deposit_btn.setEnabled(False)
        history_header.addWidget(self._deposit_btn)

        self._withdraw_btn = QPushButton("- Withdraw")
        self._withdraw_btn.setObjectName("DangerButton")
        self._withdraw_btn.clicked.connect(self._add_withdrawal)
        self._withdraw_btn.setEnabled(False)
        history_header.addWidget(self._withdraw_btn)

        self._del_txn_btn = QPushButton("Delete Entry")
        self._del_txn_btn.clicked.connect(self._delete_transaction)
        self._del_txn_btn.setEnabled(False)
        history_header.addWidget(self._del_txn_btn)

        history_layout.addLayout(history_header)

        self._history_table = QTableWidget(0, 4)
        self._history_table.setHorizontalHeaderLabels(["Date", "Type", "Amount", "Balance After"])
        self._history_table.setAlternatingRowColors(True)
        self._history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._history_table.verticalHeader().setVisible(False)
        self._history_table.horizontalHeader().setStretchLastSection(True)
        history_layout.addWidget(self._history_table)

        splitter.addWidget(history_frame)
        layout.addWidget(splitter, 1)

        # Summary
        self._summary_label = QLabel()
        self._summary_label.setObjectName("SubTitle")
        layout.addWidget(self._summary_label)

    def _connect_signals(self):
        self._dm.savings_changed.connect(self.refresh)

    def refresh(self):
        # Clear account cards
        while self._accounts_layout.count():
            item = self._accounts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        symbol = self._dm.settings.currency_symbol
        accounts = [a for a in self._dm.savings_accounts if a.active]

        for account in accounts:
            card = SavingsAccountCard(account, symbol)
            card.mousePressEvent = lambda e, aid=account.id: self._select_account(aid)
            self._accounts_layout.addWidget(card)

        self._accounts_layout.addStretch()

        # Summary
        total = sum(a.current_balance for a in accounts)
        total_target = sum(a.target_balance for a in accounts if a.target_balance > 0)
        self._summary_label.setText(
            f"{len(accounts)} accounts  |  "
            f"Total balance: {symbol}{total:,.2f}  |  "
            f"Total target: {symbol}{total_target:,.2f}"
        )

        # Refresh history if account selected
        if self._selected_account_id:
            self._refresh_history()

    def _select_account(self, account_id: str):
        self._selected_account_id = account_id
        self._deposit_btn.setEnabled(True)
        self._withdraw_btn.setEnabled(True)
        self._del_txn_btn.setEnabled(True)
        self._refresh_history()

    def _refresh_history(self):
        account = next(
            (a for a in self._dm.savings_accounts if a.id == self._selected_account_id), None
        )
        if not account:
            return

        self._history_title.setText(f"Transaction History — {account.name}")
        symbol = self._dm.settings.currency_symbol

        self._history_table.setRowCount(0)
        for txn in reversed(account.transactions):
            row = self._history_table.rowCount()
            self._history_table.insertRow(row)
            self._history_table.setItem(row, 0, QTableWidgetItem(txn.date))
            type_item = QTableWidgetItem(txn.type.capitalize())
            from PyQt6.QtGui import QColor
            if txn.type == "deposit":
                type_item.setForeground(QColor("#a6e3a1"))
            else:
                type_item.setForeground(QColor("#f38ba8"))
            self._history_table.setItem(row, 1, type_item)
            self._history_table.setItem(row, 2, QTableWidgetItem(f"{symbol}{txn.amount:,.2f}"))
            self._history_table.setItem(row, 3, QTableWidgetItem(f"{symbol}{txn.balance_after:,.2f}"))
            # Store txn id in row
            self._history_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, txn.id)

    def _add_deposit(self):
        self._add_savings_transaction("deposit")

    def _add_withdrawal(self):
        self._add_savings_transaction("withdrawal")

    def _add_savings_transaction(self, txn_type: str):
        account = next(
            (a for a in self._dm.savings_accounts if a.id == self._selected_account_id), None
        )
        if not account:
            return
        dialog = SavingsTransactionDialog(account.name, self)
        # Pre-select type
        if txn_type == "withdrawal":
            dialog._type_combo.setCurrentIndex(1)
        if dialog.exec():
            txn = dialog.get_transaction()
            self._dm.add_savings_transaction(account.id, txn)

    def _delete_transaction(self):
        rows = self._history_table.selectionModel().selectedRows()
        if not rows:
            return
        row = rows[0].row()
        txn_id = self._history_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not txn_id or not self._selected_account_id:
            return
        reply = QMessageBox.question(
            self, "Delete Entry",
            "Delete this savings transaction? Balances will be recalculated.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._dm.delete_savings_transaction(self._selected_account_id, txn_id)

    def _add_account(self):
        dialog = AddSavingsAccountDialog(self)
        if dialog.exec():
            account = dialog.get_account()
            self._dm.add_savings_account(account)

    def _edit_account(self):
        if not self._selected_account_id:
            QMessageBox.information(self, "No Selection", "Click an account card first.")
            return
        account = next(
            (a for a in self._dm.savings_accounts if a.id == self._selected_account_id), None
        )
        if account:
            dialog = AddSavingsAccountDialog(self, account=account)
            if dialog.exec():
                updated = dialog.get_account()
                self._dm.update_savings_account(updated)

    def _delete_account(self):
        if not self._selected_account_id:
            QMessageBox.information(self, "No Selection", "Click an account card first.")
            return
        account = next(
            (a for a in self._dm.savings_accounts if a.id == self._selected_account_id), None
        )
        if not account:
            return
        reply = QMessageBox.question(
            self, "Delete Account",
            f"Delete savings account '{account.name}'? All transaction history will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._dm.delete_savings_account(account.id)
            self._selected_account_id = None
            self._deposit_btn.setEnabled(False)
            self._withdraw_btn.setEnabled(False)
            self._del_txn_btn.setEnabled(False)
