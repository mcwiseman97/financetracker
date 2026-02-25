"""
Central data service with Qt signals.
Pattern: mutator → modify in-memory → atomic save → emit signal.
Panels connect signals to their refresh() methods.
"""
from __future__ import annotations
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

from app.core.models import (
    Category, FuturePayment, RecurringPayment,
    SavingsAccount, SavingsTransaction, Settings, Transaction,
)
from app.core.storage import StorageManager


class DataManager(QObject):
    transactions_changed = pyqtSignal()
    categories_changed = pyqtSignal()
    recurring_changed = pyqtSignal()
    savings_changed = pyqtSignal()
    future_payments_changed = pyqtSignal()
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._storage = StorageManager()
        self._suppress_signals = False
        self._pending_signals: set[str] = set()

        # In-memory state
        self.transactions: list[Transaction] = []
        self.categories: list[Category] = []
        self.recurring: list[RecurringPayment] = []
        self.savings_accounts: list[SavingsAccount] = []
        self.future_payments: list[FuturePayment] = []
        self.settings = Settings()

    # ── Context manager for bulk operations ──────────────────────────────────

    @contextmanager
    def bulk_operation(self):
        """Suppress signals during bulk writes; emit each pending signal once on exit."""
        self._suppress_signals = True
        self._pending_signals = set()
        try:
            yield
        finally:
            self._suppress_signals = False
            for sig_name in self._pending_signals:
                getattr(self, sig_name).emit()
            self._pending_signals.clear()

    def _emit(self, signal_name: str):
        if self._suppress_signals:
            self._pending_signals.add(signal_name)
        else:
            getattr(self, signal_name).emit()

    # ── Bootstrap / first-run ────────────────────────────────────────────────

    def bootstrap_first_run(self, defaults_dir: Path):
        """Set up data directory for first-run from bundled defaults."""
        # Copy default categories
        default_cats = defaults_dir / "default_categories.json"
        self._storage.copy_default(default_cats, "categories.json")

        # Create empty files for others
        for fname, root_key in [
            ("transactions.json", "transactions"),
            ("recurring.json", "recurring"),
            ("savings.json", "accounts"),
            ("future_payments.json", "future_payments"),
        ]:
            if not self._storage.file_exists(fname):
                self._storage.save(fname, {"version": 1, root_key: []})

        # Save initial settings
        self.settings.first_run_complete = True
        self._save_settings()

    # ── Load all data ─────────────────────────────────────────────────────────

    def load_all(self):
        """Load everything from disk into memory."""
        self._load_settings()
        self._load_categories()
        self._load_transactions()
        self._load_recurring()
        self._load_savings()
        self._load_future_payments()

    def _load_settings(self):
        d = self._storage.load("settings.json")
        if d:
            self.settings = Settings.from_dict(d)
        else:
            self.settings = Settings()

    def _load_categories(self):
        d = self._storage.load("categories.json")
        self.categories = [Category.from_dict(c) for c in d.get("categories", [])]

    def _load_transactions(self):
        d = self._storage.load("transactions.json")
        self.transactions = [Transaction.from_dict(t) for t in d.get("transactions", [])]

    def _load_recurring(self):
        d = self._storage.load("recurring.json")
        self.recurring = [RecurringPayment.from_dict(r) for r in d.get("recurring", [])]

    def _load_savings(self):
        d = self._storage.load("savings.json")
        self.savings_accounts = [SavingsAccount.from_dict(a) for a in d.get("accounts", [])]

    def _load_future_payments(self):
        d = self._storage.load("future_payments.json")
        self.future_payments = [FuturePayment.from_dict(p) for p in d.get("future_payments", [])]

    # ── Save helpers ──────────────────────────────────────────────────────────

    def _save_transactions(self):
        self._storage.save("transactions.json", {
            "version": 1,
            "transactions": [t.to_dict() for t in self.transactions],
        })

    def _save_categories(self):
        self._storage.save("categories.json", {
            "version": 1,
            "categories": [c.to_dict() for c in self.categories],
        })

    def _save_recurring(self):
        self._storage.save("recurring.json", {
            "version": 1,
            "recurring": [r.to_dict() for r in self.recurring],
        })

    def _save_savings(self):
        self._storage.save("savings.json", {
            "version": 1,
            "accounts": [a.to_dict() for a in self.savings_accounts],
        })

    def _save_future_payments(self):
        self._storage.save("future_payments.json", {
            "version": 1,
            "future_payments": [p.to_dict() for p in self.future_payments],
        })

    def _save_settings(self):
        self._storage.save("settings.json", self.settings.to_dict())

    # ── Transaction CRUD ──────────────────────────────────────────────────────

    def add_transaction(self, txn: Transaction) -> Transaction:
        if not txn.id:
            txn.id = f"txn_{uuid.uuid4().hex[:12]}"
        if not txn.created_at:
            txn.created_at = datetime.now().isoformat(timespec="seconds")
        self.transactions.append(txn)
        self._save_transactions()
        self._emit("transactions_changed")
        return txn

    def update_transaction(self, txn: Transaction):
        for i, t in enumerate(self.transactions):
            if t.id == txn.id:
                self.transactions[i] = txn
                break
        self._save_transactions()
        self._emit("transactions_changed")

    def delete_transaction(self, txn_id: str):
        self.transactions = [t for t in self.transactions if t.id != txn_id]
        self._save_transactions()
        self._emit("transactions_changed")

    def get_transaction(self, txn_id: str) -> Optional[Transaction]:
        return next((t for t in self.transactions if t.id == txn_id), None)

    # ── Category CRUD ─────────────────────────────────────────────────────────

    def add_category(self, cat: Category) -> Category:
        if not cat.id:
            cat.id = f"cat_{uuid.uuid4().hex[:12]}"
        self.categories.append(cat)
        self._save_categories()
        self._emit("categories_changed")
        return cat

    def update_category(self, cat: Category):
        for i, c in enumerate(self.categories):
            if c.id == cat.id:
                self.categories[i] = cat
                break
        self._save_categories()
        self._emit("categories_changed")

    def delete_category(self, cat_id: str):
        self.categories = [c for c in self.categories if c.id != cat_id]
        self._save_categories()
        self._emit("categories_changed")

    def get_category(self, cat_id: str) -> Optional[Category]:
        return next((c for c in self.categories if c.id == cat_id), None)

    def get_category_name(self, cat_id: str) -> str:
        cat = self.get_category(cat_id)
        return cat.name if cat else "Unknown"

    # ── Recurring CRUD ────────────────────────────────────────────────────────

    def add_recurring(self, rec: RecurringPayment) -> RecurringPayment:
        if not rec.id:
            rec.id = f"rec_{uuid.uuid4().hex[:12]}"
        self.recurring.append(rec)
        self._save_recurring()
        self._emit("recurring_changed")
        return rec

    def update_recurring(self, rec: RecurringPayment):
        for i, r in enumerate(self.recurring):
            if r.id == rec.id:
                self.recurring[i] = rec
                break
        self._save_recurring()
        self._emit("recurring_changed")

    def delete_recurring(self, rec_id: str):
        self.recurring = [r for r in self.recurring if r.id != rec_id]
        self._save_recurring()
        self._emit("recurring_changed")

    def get_recurring(self, rec_id: str) -> Optional[RecurringPayment]:
        return next((r for r in self.recurring if r.id == rec_id), None)

    # ── Savings CRUD ──────────────────────────────────────────────────────────

    def add_savings_account(self, account: SavingsAccount) -> SavingsAccount:
        if not account.id:
            account.id = f"sav_{uuid.uuid4().hex[:12]}"
        self.savings_accounts.append(account)
        self._save_savings()
        self._emit("savings_changed")
        return account

    def update_savings_account(self, account: SavingsAccount):
        for i, a in enumerate(self.savings_accounts):
            if a.id == account.id:
                self.savings_accounts[i] = account
                break
        self._save_savings()
        self._emit("savings_changed")

    def delete_savings_account(self, account_id: str):
        self.savings_accounts = [a for a in self.savings_accounts if a.id != account_id]
        self._save_savings()
        self._emit("savings_changed")

    def add_savings_transaction(self, account_id: str, txn: SavingsTransaction) -> SavingsTransaction:
        if not txn.id:
            txn.id = f"savtxn_{uuid.uuid4().hex[:12]}"
        account = next((a for a in self.savings_accounts if a.id == account_id), None)
        if account:
            # Calculate balance_after
            current = account.current_balance
            if txn.type == "deposit":
                txn.balance_after = current + txn.amount
            else:
                txn.balance_after = current - txn.amount
            account.transactions.append(txn)
            self._save_savings()
            self._emit("savings_changed")
        return txn

    def delete_savings_transaction(self, account_id: str, txn_id: str):
        account = next((a for a in self.savings_accounts if a.id == account_id), None)
        if account:
            account.transactions = [t for t in account.transactions if t.id != txn_id]
            # Recalculate balances
            running = 0.0
            for t in account.transactions:
                if t.type == "deposit":
                    running += t.amount
                else:
                    running -= t.amount
                t.balance_after = running
            self._save_savings()
            self._emit("savings_changed")

    # ── Future Payments CRUD ──────────────────────────────────────────────────

    def add_future_payment(self, fp: FuturePayment) -> FuturePayment:
        if not fp.id:
            fp.id = f"fut_{uuid.uuid4().hex[:12]}"
        if not fp.created_at:
            fp.created_at = datetime.now().isoformat(timespec="seconds")
        self.future_payments.append(fp)
        self._save_future_payments()
        self._emit("future_payments_changed")
        return fp

    def update_future_payment(self, fp: FuturePayment):
        for i, p in enumerate(self.future_payments):
            if p.id == fp.id:
                self.future_payments[i] = fp
                break
        self._save_future_payments()
        self._emit("future_payments_changed")

    def delete_future_payment(self, fp_id: str):
        self.future_payments = [p for p in self.future_payments if p.id != fp_id]
        self._save_future_payments()
        self._emit("future_payments_changed")

    def complete_future_payment(self, fp_id: str):
        fp = next((p for p in self.future_payments if p.id == fp_id), None)
        if fp:
            fp.completed = True
            self._save_future_payments()
            self._emit("future_payments_changed")

    # ── Settings ──────────────────────────────────────────────────────────────

    def update_settings(self, settings: Settings):
        self.settings = settings
        self._save_settings()
        self._emit("settings_changed")

    # ── Backup ────────────────────────────────────────────────────────────────

    def backup(self) -> Path:
        return self._storage.backup()

    # ── Utility ──────────────────────────────────────────────────────────────

    def new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"
