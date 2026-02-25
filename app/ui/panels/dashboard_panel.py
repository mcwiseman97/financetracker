"""
Dashboard panel: overview stats, mini bar chart, category progress bars,
and upcoming recurring payments list.
"""
from __future__ import annotations
from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from app.core.data_manager import DataManager
from app.core.budget_engine import calculate_monthly_summary, calculate_category_statuses
from app.core.recurring_engine import get_upcoming_recurring
from app.ui.panels.base_panel import BasePanel
from app.ui.widgets.stat_card import StatCard
from app.ui.widgets.chart_canvas import ChartCanvas


class DashboardPanel(BasePanel):
    def __init__(self, data_manager: DataManager, theme_manager=None, parent=None):
        super().__init__(data_manager, theme_manager, parent)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        today = date.today()
        header_row = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("SectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()
        self._date_label = QLabel(today.strftime("%B %Y"))
        self._date_label.setObjectName("SubTitle")
        header_row.addWidget(self._date_label)
        main_layout.addLayout(header_row)

        # Stat cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self._income_card = StatCard("Monthly Income", "$0.00", "this month")
        self._expense_card = StatCard("Total Expenses", "$0.00", "this month")
        self._net_card = StatCard("Net", "$0.00", "income − expenses")
        self._savings_card = StatCard("Total Savings", "$0.00", "across all accounts")
        for card in [self._income_card, self._expense_card, self._net_card, self._savings_card]:
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            cards_row.addWidget(card)
        main_layout.addLayout(cards_row)

        # Middle row: chart + upcoming
        mid_row = QHBoxLayout()
        mid_row.setSpacing(16)

        # Bar chart: last 6 months
        chart_frame = QFrame()
        chart_frame.setObjectName("CardWidget")
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(16, 16, 16, 16)
        chart_title = QLabel("Last 6 Months")
        chart_title.setObjectName("SubTitle")
        chart_layout.addWidget(chart_title)
        self._chart = ChartCanvas(theme_manager=self._tm, width=5, height=3)
        self._chart.set_draw_callback(self._draw_chart)
        chart_layout.addWidget(self._chart)
        mid_row.addWidget(chart_frame, 2)

        # Upcoming recurring
        upcoming_frame = QFrame()
        upcoming_frame.setObjectName("CardWidget")
        upcoming_layout = QVBoxLayout(upcoming_frame)
        upcoming_layout.setContentsMargins(16, 16, 16, 12)
        upcoming_title = QLabel("Upcoming Payments (30 days)")
        upcoming_title.setObjectName("SubTitle")
        upcoming_layout.addWidget(upcoming_title)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._upcoming_widget = QWidget()
        self._upcoming_layout = QVBoxLayout(self._upcoming_widget)
        self._upcoming_layout.setContentsMargins(0, 0, 0, 0)
        self._upcoming_layout.setSpacing(6)
        self._upcoming_layout.addStretch()
        scroll.setWidget(self._upcoming_widget)
        upcoming_layout.addWidget(scroll)
        mid_row.addWidget(upcoming_frame, 1)
        main_layout.addLayout(mid_row, 1)

        # Category progress bars
        cats_frame = QFrame()
        cats_frame.setObjectName("CardWidget")
        cats_layout = QVBoxLayout(cats_frame)
        cats_layout.setContentsMargins(16, 12, 16, 12)
        cats_label = QLabel("Category Spending (this month)")
        cats_label.setObjectName("SubTitle")
        cats_layout.addWidget(cats_label)
        scroll2 = QScrollArea()
        scroll2.setWidgetResizable(True)
        scroll2.setFrameShape(QFrame.Shape.NoFrame)
        scroll2.setFixedHeight(160)
        self._cats_widget = QWidget()
        self._cats_layout = QVBoxLayout(self._cats_widget)
        self._cats_layout.setContentsMargins(0, 4, 0, 4)
        self._cats_layout.setSpacing(6)
        scroll2.setWidget(self._cats_widget)
        cats_layout.addWidget(scroll2)
        main_layout.addWidget(cats_frame)

    def _connect_signals(self):
        self._dm.transactions_changed.connect(self.refresh)
        self._dm.settings_changed.connect(self.refresh)
        self._dm.savings_changed.connect(self._refresh_savings_card)
        self._dm.recurring_changed.connect(self._refresh_upcoming)

    def refresh(self):
        today = date.today()
        summary = calculate_monthly_summary(self._dm.transactions, today.year, today.month)
        symbol = self._dm.settings.currency_symbol
        income = self._dm.settings.monthly_income or summary.total_income

        self._income_card.set_value(f"{symbol}{summary.total_income:,.2f}")
        self._expense_card.set_value(f"{symbol}{summary.total_expenses:,.2f}")

        net = summary.total_income - summary.total_expenses
        style = "positive" if net >= 0 else "negative"
        prefix = "+" if net >= 0 else ""
        self._net_card.set_value(f"{prefix}{symbol}{net:,.2f}", style)

        self._refresh_savings_card()
        self._draw_chart()
        self._refresh_upcoming()
        self._refresh_categories()

    def _refresh_savings_card(self):
        symbol = self._dm.settings.currency_symbol
        total = sum(a.current_balance for a in self._dm.savings_accounts)
        self._savings_card.set_value(f"{symbol}{total:,.2f}")

    def _draw_chart(self):
        from app.core.budget_engine import calculate_spending_by_period
        summaries = calculate_spending_by_period(self._dm.transactions, num_months=6)
        if self._tm:
            style = self._tm.get_mpl_style()
            colors = self._tm.get_chart_colors()
        else:
            style = {}
            colors = ["#cba6f7", "#89b4fa"]

        ax = self._chart.get_axes()
        for k, v in style.items():
            try:
                if k.startswith("axes."):
                    attr = k.split(".", 1)[1]
                    if hasattr(ax, f"set_{attr}"):
                        pass
            except Exception:
                pass

        import matplotlib
        for k, v in style.items():
            matplotlib.rcParams[k] = v

        months = [s.month[-5:] for s in summaries]  # "YYYY-MM" → last 5 chars
        expenses = [s.total_expenses for s in summaries]
        incomes = [s.total_income for s in summaries]

        x = range(len(months))
        width = 0.35
        ax.bar([xi - width/2 for xi in x], incomes, width, label="Income",
               color=colors[1], alpha=0.85)
        ax.bar([xi + width/2 for xi in x], expenses, width, label="Expenses",
               color=colors[5], alpha=0.85)
        ax.set_xticks(list(x))
        ax.set_xticklabels(months, fontsize=9)
        ax.legend(fontsize=9)
        ax.set_facecolor(style.get("axes.facecolor", "#24273a"))
        ax.figure.patch.set_facecolor(style.get("figure.facecolor", "#24273a"))
        ax.tick_params(colors=style.get("xtick.color", "#a6adc8"))
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(style.get("axes.edgecolor", "#45475a"))
        ax.spines["bottom"].set_color(style.get("axes.edgecolor", "#45475a"))

        self._chart.draw()

    def _refresh_upcoming(self):
        # Clear existing items
        while self._upcoming_layout.count() > 1:
            item = self._upcoming_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        upcoming = get_upcoming_recurring(self._dm.recurring, date.today(), 30)
        symbol = self._dm.settings.currency_symbol

        if not upcoming:
            empty = QLabel("No upcoming payments")
            empty.setObjectName("SubTitle")
            self._upcoming_layout.insertWidget(0, empty)
            return

        for i, (rec, due_date) in enumerate(upcoming[:10]):
            row = QHBoxLayout()
            name_label = QLabel(rec.name)
            date_label = QLabel(due_date.strftime("%b %d"))
            date_label.setObjectName("SubTitle")
            amount_label = QLabel(f"{symbol}{rec.amount:,.2f}")
            amount_label.setObjectName("AmountNegative" if rec.type == "expense" else "AmountPositive")
            row.addWidget(name_label, 1)
            row.addWidget(date_label)
            row.addWidget(amount_label)
            container = QWidget()
            container.setLayout(row)
            self._upcoming_layout.insertWidget(i, container)

    def _refresh_categories(self):
        # Clear existing
        while self._cats_layout.count():
            item = self._cats_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        today = date.today()
        statuses = calculate_category_statuses(
            self._dm.categories, self._dm.transactions, today.year, today.month
        )
        symbol = self._dm.settings.currency_symbol

        visible = [s for s in statuses if s.spent > 0 or s.budget_limit > 0][:8]
        if not visible:
            lbl = QLabel("No spending data this month")
            lbl.setObjectName("SubTitle")
            self._cats_layout.addWidget(lbl)
            return

        for status in visible:
            row = QHBoxLayout()
            row.setSpacing(8)

            name = QLabel(status.category_name)
            name.setFixedWidth(120)
            row.addWidget(name)

            bar = QProgressBar()
            bar.setRange(0, 100)
            pct = min(int(status.pct_used), 100) if status.budget_limit > 0 else 0
            bar.setValue(pct)
            if status.over_budget:
                bar.setProperty("overBudget", True)
            elif pct >= 80:
                bar.setProperty("almostOver", True)
            bar.style().unpolish(bar)
            bar.style().polish(bar)
            row.addWidget(bar, 1)

            if status.budget_limit > 0:
                amt_label = QLabel(f"{symbol}{status.spent:,.2f} / {symbol}{status.budget_limit:,.2f}")
            else:
                amt_label = QLabel(f"{symbol}{status.spent:,.2f}")
            amt_label.setObjectName("SubTitle")
            amt_label.setFixedWidth(130)
            row.addWidget(amt_label)

            container = QWidget()
            container.setLayout(row)
            self._cats_layout.addWidget(container)
