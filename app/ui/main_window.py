"""
Main application window: sidebar + QStackedWidget.
Manages panel instantiation, navigation, first-run setup, and theme switching.
"""
from __future__ import annotations
from datetime import date
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox,
    QStackedWidget, QVBoxLayout, QWidget, QComboBox,
)

from app.core.data_manager import DataManager
from app.core.models import Settings
from app.core.recurring_engine import populate_recurring
from app.ui.sidebar import SidebarWidget
from app.ui.themes.theme_manager import ThemeManager


class WelcomeDialog(QDialog):
    """First-run dialog: sets monthly income and theme."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Finance Tracker")
        self.setFixedWidth(400)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Welcome!")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        desc = QLabel(
            "Let's set up your Finance Tracker.\n"
            "You can change these settings at any time."
        )
        desc.setWordWrap(True)
        desc.setObjectName("SubTitle")
        layout.addWidget(desc)

        form = QFormLayout()
        form.setSpacing(12)

        self._income_edit = QLineEdit()
        self._income_edit.setPlaceholderText("e.g. 4500.00")
        form.addRow("Monthly Income ($):", self._income_edit)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark (Catppuccin Mocha)", "Light (Catppuccin Latte)"])
        form.addRow("Theme:", self._theme_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def get_income(self) -> float:
        try:
            return float(self._income_edit.text().replace(",", "").strip() or "0")
        except ValueError:
            return 0.0

    def get_theme(self) -> str:
        return "dark" if self._theme_combo.currentIndex() == 0 else "light"


class MainWindow(QMainWindow):
    def __init__(
        self,
        data_manager: DataManager,
        theme_manager: ThemeManager,
        app_dir: Path,
        parent=None,
    ):
        super().__init__(parent)
        self._dm = data_manager
        self._tm = theme_manager
        self._app_dir = app_dir

        self.setWindowTitle("Finance Tracker")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        self._panels: list = []
        self._build_ui()
        self._connect_signals()
        self._init_data()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        self._sidebar = SidebarWidget()
        root_layout.addWidget(self._sidebar)

        # Stacked panel area
        self._stack = QStackedWidget()
        self._stack.setObjectName("PanelContainer")
        root_layout.addWidget(self._stack, 1)

        # Import and instantiate panels
        self._create_panels()

        # Select first panel
        self._sidebar.set_active(0)

    def _create_panels(self):
        """Import and create all panels, add to stack."""
        from app.ui.panels.dashboard_panel import DashboardPanel
        from app.ui.panels.transactions_panel import TransactionsPanel
        from app.ui.panels.recurring_panel import RecurringPanel
        from app.ui.panels.categories_panel import CategoriesPanel
        from app.ui.panels.graphs_panel import GraphsPanel
        from app.ui.panels.savings_panel import SavingsPanel
        from app.ui.panels.budget_panel import BudgetPanel
        from app.ui.panels.future_payments_panel import FuturePaymentsPanel

        panel_classes = [
            DashboardPanel,
            TransactionsPanel,
            RecurringPanel,
            CategoriesPanel,
            GraphsPanel,
            SavingsPanel,
            BudgetPanel,
            FuturePaymentsPanel,
        ]

        for cls in panel_classes:
            panel = cls(self._dm, self._tm)
            self._panels.append(panel)
            self._stack.addWidget(panel)

    def _connect_signals(self):
        self._sidebar.nav_item_clicked.connect(self._switch_panel)
        self._sidebar.theme_toggle_requested.connect(self._toggle_theme)
        self._tm.theme_changed.connect(self._on_theme_changed)

    def _init_data(self):
        """Load all data, run recurring engine, handle first-run."""
        self._dm.load_all()

        # First-run setup
        if not self._dm.settings.first_run_complete:
            self._run_first_run_setup()

        # Apply saved theme
        self._tm.apply_theme(self._dm.settings.theme)
        self._sidebar.update_theme_button(self._tm.is_dark)

        # Auto-populate recurring transactions
        if self._dm.settings.auto_populate_recurring:
            self._populate_recurring()

        # Refresh all panels after data load
        self._refresh_all_panels()

        # Update last_opened
        from datetime import datetime
        settings = self._dm.settings
        settings.last_opened = datetime.now().isoformat(timespec="seconds")
        self._dm.update_settings(settings)

    def _run_first_run_setup(self):
        """Bootstrap data directory and show welcome dialog."""
        data_dir = Path(__file__).parent.parent.parent / "data"
        self._dm.bootstrap_first_run(data_dir)

        dialog = WelcomeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            settings = self._dm.settings
            settings.monthly_income = dialog.get_income()
            settings.theme = dialog.get_theme()
            settings.first_run_complete = True
            self._dm.update_settings(settings)

        # Reload data after bootstrap
        self._dm.load_all()

    def _populate_recurring(self):
        """Generate any missing recurring transactions up to today."""
        today = date.today()
        lookahead = self._dm.settings.recurring_lookahead_days
        if lookahead > 0:
            from datetime import timedelta
            up_to = today + timedelta(days=lookahead)
        else:
            up_to = today

        new_txns, updates = populate_recurring(
            self._dm.recurring,
            self._dm.transactions,
            up_to,
        )

        if new_txns or updates:
            with self._dm.bulk_operation():
                for txn in new_txns:
                    self._dm.add_transaction(txn)
                # Update last_generated_date on recurring rules
                for rec_id, last_date in updates:
                    rec = self._dm.get_recurring(rec_id)
                    if rec:
                        rec.last_generated_date = last_date
                        self._dm.update_recurring(rec)

    def _refresh_all_panels(self):
        """Call refresh() on all panels."""
        for panel in self._panels:
            try:
                panel.refresh()
            except Exception:
                pass

    def _switch_panel(self, index: int):
        if 0 <= index < len(self._panels):
            self._stack.setCurrentIndex(index)
            try:
                self._panels[index].refresh()
            except Exception:
                pass

    def _toggle_theme(self):
        new_theme = self._tm.toggle_theme()
        settings = self._dm.settings
        settings.theme = new_theme
        self._dm.update_settings(settings)

    def _on_theme_changed(self, theme_name: str):
        self._sidebar.update_theme_button(theme_name == "dark")
