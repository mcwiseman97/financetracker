"""
Graphs panel: QTabWidget with 4 chart types + date range picker + Export PNG.
"""
from __future__ import annotations
from datetime import date
from typing import Optional

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QFileDialog, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from app.core.budget_engine import (
    calculate_spending_by_period, calculate_spending_by_category,
    calculate_monthly_summary,
)
from app.core.data_manager import DataManager
from app.ui.panels.base_panel import BasePanel
from app.ui.widgets.chart_canvas import ChartCanvas


class GraphsPanel(BasePanel):
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
        title = QLabel("Graphs & Analytics")
        title.setObjectName("SectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        # Months picker
        header_row.addWidget(QLabel("Last:"))
        self._months_combo = QComboBox()
        self._months_combo.addItems(["3 months", "6 months", "12 months"])
        self._months_combo.setCurrentIndex(1)
        self._months_combo.currentIndexChanged.connect(self.refresh)
        header_row.addWidget(self._months_combo)

        self._export_btn = QPushButton("Export PNG")
        self._export_btn.clicked.connect(self._export_png)
        header_row.addWidget(self._export_btn)

        layout.addLayout(header_row)

        # Tabs
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs, 1)

        # Monthly bar chart
        self._monthly_canvas = ChartCanvas(theme_manager=self._tm, width=8, height=5)
        self._monthly_canvas.set_draw_callback(self._draw_monthly_bar)
        self._tabs.addTab(self._monthly_canvas, "Monthly Bar")

        # Category pie
        self._pie_canvas = ChartCanvas(theme_manager=self._tm, width=6, height=5)
        self._pie_canvas.set_draw_callback(self._draw_category_pie)
        self._tabs.addTab(self._pie_canvas, "Category Pie")

        # Income vs Expense
        self._ive_canvas = ChartCanvas(theme_manager=self._tm, width=8, height=5)
        self._ive_canvas.set_draw_callback(self._draw_income_vs_expense)
        self._tabs.addTab(self._ive_canvas, "Income vs Expense")

        # Trend line
        self._trend_canvas = ChartCanvas(theme_manager=self._tm, width=8, height=5)
        self._trend_canvas.set_draw_callback(self._draw_trend)
        self._tabs.addTab(self._trend_canvas, "Trend Line")

        self._tabs.currentChanged.connect(self._on_tab_changed)

    def _connect_signals(self):
        self._dm.transactions_changed.connect(self.refresh)

    def _get_num_months(self) -> int:
        return [3, 6, 12][self._months_combo.currentIndex()]

    def refresh(self):
        tab = self._tabs.currentIndex()
        draw_fns = [
            self._draw_monthly_bar,
            self._draw_category_pie,
            self._draw_income_vs_expense,
            self._draw_trend,
        ]
        if 0 <= tab < len(draw_fns):
            draw_fns[tab]()

    def _on_tab_changed(self, index: int):
        self.refresh()

    def _get_style(self):
        if self._tm:
            return self._tm.get_mpl_style(), self._tm.get_chart_colors()
        return {}, ["#cba6f7", "#89b4fa", "#a6e3a1", "#fab387", "#f9e2af", "#f38ba8"]

    def _apply_ax_style(self, ax, style: dict):
        bg = style.get("axes.facecolor", "#24273a")
        fig_bg = style.get("figure.facecolor", "#24273a")
        ax.set_facecolor(bg)
        ax.figure.patch.set_facecolor(fig_bg)
        ax.tick_params(colors=style.get("xtick.color", "#a6adc8"), labelsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for spine in ["left", "bottom"]:
            ax.spines[spine].set_color(style.get("axes.edgecolor", "#45475a"))
        ax.xaxis.label.set_color(style.get("axes.labelcolor", "#a6adc8"))
        ax.yaxis.label.set_color(style.get("axes.labelcolor", "#a6adc8"))
        ax.title.set_color(style.get("text.color", "#cdd6f4"))

    def _draw_monthly_bar(self):
        style, colors = self._get_style()
        n = self._get_num_months()
        summaries = calculate_spending_by_period(self._dm.transactions, n)

        ax = self._monthly_canvas.get_axes()
        months = [s.month for s in summaries]
        expenses = [s.total_expenses for s in summaries]
        incomes = [s.total_income for s in summaries]

        x = range(len(months))
        width = 0.35
        ax.bar([xi - width/2 for xi in x], incomes, width, label="Income",
               color=colors[1], alpha=0.85)
        ax.bar([xi + width/2 for xi in x], expenses, width, label="Expenses",
               color=colors[5], alpha=0.85)
        ax.set_xticks(list(x))
        ax.set_xticklabels(months, rotation=30, ha="right", fontsize=9)
        ax.set_ylabel("Amount")
        ax.set_title("Monthly Income vs Expenses")
        ax.legend(fontsize=9)
        self._apply_ax_style(ax, style)
        self._monthly_canvas.draw()

    def _draw_category_pie(self):
        style, colors = self._get_style()
        today = date.today()
        by_cat = calculate_spending_by_category(
            self._dm.transactions, today.year, today.month
        )
        # Map IDs to names
        cat_by_id = {c.id: c for c in self._dm.categories}
        named = {}
        for cat_id, amount in by_cat.items():
            name = cat_by_id[cat_id].name if cat_id in cat_by_id else "Unknown"
            named[name] = named.get(name, 0) + amount

        ax = self._pie_canvas.get_axes()
        if not named:
            ax.text(0.5, 0.5, "No expense data this month",
                    ha="center", va="center",
                    color=style.get("text.color", "#cdd6f4"), fontsize=12)
            ax.axis("off")
        else:
            labels = list(named.keys())
            values = list(named.values())
            ax.pie(
                values, labels=labels, colors=colors[:len(labels)],
                autopct="%1.1f%%", startangle=90,
                textprops={"color": style.get("text.color", "#cdd6f4"), "fontsize": 9},
            )
            ax.set_title(f"Spending by Category — {today.strftime('%B %Y')}")
        ax.figure.patch.set_facecolor(style.get("figure.facecolor", "#24273a"))
        ax.title.set_color(style.get("text.color", "#cdd6f4"))
        self._pie_canvas.draw()

    def _draw_income_vs_expense(self):
        style, colors = self._get_style()
        n = self._get_num_months()
        summaries = calculate_spending_by_period(self._dm.transactions, n)

        ax = self._ive_canvas.get_axes()
        months = [s.month for s in summaries]
        net = [s.total_income - s.total_expenses for s in summaries]
        bar_colors = [colors[1] if v >= 0 else colors[5] for v in net]

        ax.bar(months, net, color=bar_colors, alpha=0.85)
        ax.axhline(0, color=style.get("axes.edgecolor", "#45475a"), linewidth=0.8)
        ax.set_xlabel("Month")
        ax.set_ylabel("Net (Income − Expenses)")
        ax.set_title("Net Cash Flow")
        ax.set_xticklabels(months, rotation=30, ha="right", fontsize=9)
        self._apply_ax_style(ax, style)
        self._ive_canvas.draw()

    def _draw_trend(self):
        style, colors = self._get_style()
        n = self._get_num_months()
        summaries = calculate_spending_by_period(self._dm.transactions, n)

        ax = self._trend_canvas.get_axes()
        months = [s.month for s in summaries]
        expenses = [s.total_expenses for s in summaries]
        incomes = [s.total_income for s in summaries]

        ax.plot(months, incomes, marker="o", color=colors[1], label="Income",
                linewidth=2, markersize=5)
        ax.plot(months, expenses, marker="o", color=colors[5], label="Expenses",
                linewidth=2, markersize=5)
        ax.fill_between(months, expenses, alpha=0.1, color=colors[5])
        ax.set_xlabel("Month")
        ax.set_ylabel("Amount")
        ax.set_title("Income & Expense Trend")
        ax.legend(fontsize=9)
        ax.set_xticklabels(months, rotation=30, ha="right", fontsize=9)
        self._apply_ax_style(ax, style)
        self._trend_canvas.draw()

    def _export_png(self):
        tab = self._tabs.currentIndex()
        canvases = [self._monthly_canvas, self._pie_canvas, self._ive_canvas, self._trend_canvas]
        if 0 <= tab < len(canvases):
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Chart", "", "PNG Images (*.png)"
            )
            if path:
                canvases[tab].fig.savefig(path, dpi=150, bbox_inches="tight")
