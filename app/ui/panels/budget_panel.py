"""
Budget (50/30/20) panel: three large bucket cards, breakdown table, and pie chart.
"""
from __future__ import annotations
from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QScrollArea, QSplitter, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from app.core.budget_engine import calculate_budget_analysis
from app.core.data_manager import DataManager
from app.ui.panels.base_panel import BasePanel
from app.ui.widgets.chart_canvas import ChartCanvas


class IncomeSettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Budget Settings")
        self.setFixedWidth(360)
        self._settings = settings
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Budget Settings")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self._income_spin = QDoubleSpinBox()
        self._income_spin.setRange(0, 9_999_999.99)
        self._income_spin.setDecimals(2)
        self._income_spin.setPrefix("$ ")
        self._income_spin.setValue(self._settings.monthly_income)
        form.addRow("Monthly income:", self._income_spin)

        self._needs_spin = QDoubleSpinBox()
        self._needs_spin.setRange(0, 100)
        self._needs_spin.setDecimals(1)
        self._needs_spin.setSuffix(" %")
        self._needs_spin.setValue(self._settings.needs_pct)
        form.addRow("Needs %:", self._needs_spin)

        self._wants_spin = QDoubleSpinBox()
        self._wants_spin.setRange(0, 100)
        self._wants_spin.setDecimals(1)
        self._wants_spin.setSuffix(" %")
        self._wants_spin.setValue(self._settings.wants_pct)
        form.addRow("Wants %:", self._wants_spin)

        self._savings_spin = QDoubleSpinBox()
        self._savings_spin.setRange(0, 100)
        self._savings_spin.setDecimals(1)
        self._savings_spin.setSuffix(" %")
        self._savings_spin.setValue(self._settings.savings_pct)
        form.addRow("Savings %:", self._savings_spin)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self):
        return {
            "monthly_income": self._income_spin.value(),
            "needs_pct": self._needs_spin.value(),
            "wants_pct": self._wants_spin.value(),
            "savings_pct": self._savings_spin.value(),
        }


class BucketCard(QFrame):
    """Large card for a single 50/30/20 bucket."""

    OBJECT_NAMES = {"Needs": "BucketNeeds", "Wants": "BucketWants", "Savings": "BucketSavings"}

    def __init__(self, bucket_name: str, parent=None):
        super().__init__(parent)
        self.setObjectName("BudgetCard")
        self.setProperty("class", self.OBJECT_NAMES.get(bucket_name, ""))
        self._build(bucket_name)

    def _build(self, name: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        self._title = QLabel(name)
        self._title.setObjectName("SectionTitle")
        layout.addWidget(self._title)

        self._pct_label = QLabel("0%")
        self._pct_label.setObjectName("SubTitle")
        layout.addWidget(self._pct_label)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setFixedHeight(10)
        layout.addWidget(self._progress)

        details = QHBoxLayout()
        self._actual_label = QLabel("$0.00")
        self._actual_label.setObjectName("StatCardValue")
        self._actual_label.setStyleSheet("font-size: 24px;")
        details.addWidget(self._actual_label)
        details.addStretch()
        self._target_label = QLabel("/ $0.00")
        self._target_label.setObjectName("SubTitle")
        details.addWidget(self._target_label)
        layout.addLayout(details)

        self._delta_label = QLabel()
        layout.addWidget(self._delta_label)

    def update(self, bucket_summary, symbol: str):
        self._pct_label.setText(f"Target: {bucket_summary.target_pct:.0f}% of income")
        pct = min(int(bucket_summary.pct_used), 100)
        self._progress.setValue(pct)
        over = bucket_summary.actual_amount > bucket_summary.target_amount and bucket_summary.target_amount > 0
        self._progress.setProperty("overBudget", over)
        self._progress.style().unpolish(self._progress)
        self._progress.style().polish(self._progress)

        self._actual_label.setText(f"{symbol}{bucket_summary.actual_amount:,.2f}")
        self._target_label.setText(f"/ {symbol}{bucket_summary.target_amount:,.2f}")

        delta = bucket_summary.delta
        if delta >= 0:
            self._delta_label.setText(f"▼ {symbol}{delta:,.2f} remaining")
            self._delta_label.setObjectName("AmountPositive")
        else:
            self._delta_label.setText(f"▲ {symbol}{abs(delta):,.2f} over budget")
            self._delta_label.setObjectName("AmountNegative")
        self._delta_label.style().unpolish(self._delta_label)
        self._delta_label.style().polish(self._delta_label)


class BudgetPanel(BasePanel):
    def __init__(self, data_manager: DataManager, theme_manager=None, parent=None):
        super().__init__(data_manager, theme_manager, parent)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_row = QHBoxLayout()
        title = QLabel("Budget Analysis (50/30/20)")
        title.setObjectName("SectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self._settings_btn = QPushButton("⚙ Settings")
        self._settings_btn.clicked.connect(self._edit_settings)
        header_row.addWidget(self._settings_btn)

        layout.addLayout(header_row)

        # Income banner
        self._income_label = QLabel()
        self._income_label.setObjectName("SubTitle")
        layout.addWidget(self._income_label)

        # Three bucket cards
        buckets_row = QHBoxLayout()
        buckets_row.setSpacing(16)
        self._needs_card = BucketCard("Needs")
        self._wants_card = BucketCard("Wants")
        self._savings_card = BucketCard("Savings")
        for card in [self._needs_card, self._wants_card, self._savings_card]:
            buckets_row.addWidget(card)
        layout.addLayout(buckets_row)

        # Splitter: breakdown table + pie chart
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Category breakdown table
        breakdown_frame = QFrame()
        breakdown_frame.setObjectName("CardWidget")
        breakdown_layout = QVBoxLayout(breakdown_frame)
        breakdown_layout.setContentsMargins(16, 12, 16, 12)
        breakdown_layout.setSpacing(8)
        breakdown_title = QLabel("Category Breakdown")
        breakdown_title.setObjectName("SubTitle")
        breakdown_layout.addWidget(breakdown_title)
        self._breakdown_table = QTableWidget(0, 4)
        self._breakdown_table.setHorizontalHeaderLabels(["Category", "Bucket", "Spent", "Budget"])
        self._breakdown_table.setAlternatingRowColors(True)
        self._breakdown_table.verticalHeader().setVisible(False)
        self._breakdown_table.setEditTriggers(
            self._breakdown_table.EditTrigger.NoEditTriggers
        )
        self._breakdown_table.horizontalHeader().setStretchLastSection(True)
        breakdown_layout.addWidget(self._breakdown_table)
        splitter.addWidget(breakdown_frame)

        # Pie chart
        chart_frame = QFrame()
        chart_frame.setObjectName("CardWidget")
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(16, 12, 16, 12)
        chart_title = QLabel("Bucket Distribution")
        chart_title.setObjectName("SubTitle")
        chart_layout.addWidget(chart_title)
        self._pie_canvas = ChartCanvas(theme_manager=self._tm, width=4, height=4)
        self._pie_canvas.set_draw_callback(self._draw_pie)
        chart_layout.addWidget(self._pie_canvas)
        splitter.addWidget(chart_frame)

        splitter.setSizes([600, 400])
        layout.addWidget(splitter, 1)

    def _connect_signals(self):
        self._dm.transactions_changed.connect(self.refresh)
        self._dm.savings_changed.connect(self.refresh)
        self._dm.settings_changed.connect(self.refresh)

    def refresh(self):
        today = date.today()
        analysis = calculate_budget_analysis(
            self._dm.categories,
            self._dm.transactions,
            self._dm.savings_accounts,
            self._dm.settings,
            today.year,
            today.month,
        )
        symbol = self._dm.settings.currency_symbol

        if not analysis.income_set:
            self._income_label.setText(
                "⚠  Monthly income is not set. Click 'Settings' to set it."
            )
        else:
            self._income_label.setText(
                f"Monthly income: {symbol}{analysis.monthly_income:,.2f}  |  "
                f"Month: {today.strftime('%B %Y')}"
            )

        bucket_map = {"Needs": 0, "Wants": 1, "Savings": 2}
        bucket_cards = [self._needs_card, self._wants_card, self._savings_card]
        for bucket in analysis.buckets:
            idx = bucket_map.get(bucket.name, 0)
            bucket_cards[idx].update(bucket, symbol)

        # Breakdown table
        self._breakdown_table.setRowCount(0)
        for status in analysis.category_statuses:
            if status.spent == 0 and status.budget_limit == 0:
                continue
            row = self._breakdown_table.rowCount()
            self._breakdown_table.insertRow(row)
            self._breakdown_table.setItem(row, 0, QTableWidgetItem(status.category_name))
            bucket_display = {"needs": "Needs", "wants": "Wants", "savings": "Savings", "": "—"}
            bucket_item = QTableWidgetItem(bucket_display.get(status.bucket.lower(), "—"))
            if not status.bucket:
                from PyQt6.QtGui import QColor
                bucket_item.setForeground(QColor("#f9e2af"))
            self._breakdown_table.setItem(row, 1, bucket_item)
            spent_item = QTableWidgetItem(f"{symbol}{status.spent:,.2f}")
            if status.over_budget:
                from PyQt6.QtGui import QColor
                spent_item.setForeground(QColor("#f38ba8"))
            self._breakdown_table.setItem(row, 2, spent_item)
            if status.budget_limit > 0:
                self._breakdown_table.setItem(row, 3, QTableWidgetItem(f"{symbol}{status.budget_limit:,.2f}"))
            else:
                self._breakdown_table.setItem(row, 3, QTableWidgetItem("—"))

        self._draw_pie()

    def _draw_pie(self):
        style = self._tm.get_mpl_style() if self._tm else {}
        colors = (
            ["#89b4fa", "#fab387", "#a6e3a1"]
            if (self._tm and self._tm.is_dark)
            else ["#1e66f5", "#fe640b", "#40a02b"]
        )

        today = date.today()
        analysis = calculate_budget_analysis(
            self._dm.categories,
            self._dm.transactions,
            self._dm.savings_accounts,
            self._dm.settings,
            today.year,
            today.month,
        )

        ax = self._pie_canvas.get_axes()
        labels = [b.name for b in analysis.buckets]
        values = [b.actual_amount for b in analysis.buckets]

        if sum(values) == 0:
            ax.text(0.5, 0.5, "No data yet",
                    ha="center", va="center",
                    color=style.get("text.color", "#cdd6f4"), fontsize=12)
            ax.axis("off")
        else:
            ax.pie(
                values, labels=labels, colors=colors,
                autopct="%1.1f%%", startangle=90,
                textprops={"color": style.get("text.color", "#cdd6f4"), "fontsize": 10},
            )
        ax.figure.patch.set_facecolor(style.get("figure.facecolor", "#24273a"))
        self._pie_canvas.draw()

    def _edit_settings(self):
        dialog = IncomeSettingsDialog(self._dm.settings, self)
        if dialog.exec():
            values = dialog.get_values()
            settings = self._dm.settings
            settings.monthly_income = values["monthly_income"]
            settings.needs_pct = values["needs_pct"]
            settings.wants_pct = values["wants_pct"]
            settings.savings_pct = values["savings_pct"]
            self._dm.update_settings(settings)
