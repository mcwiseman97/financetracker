"""
Categories panel: card grid with per-category spending/budget progress.
Overspent categories get red border. Alert banner at top for over-budget items.
"""
from __future__ import annotations
from datetime import date
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox,
    QProgressBar, QPushButton, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget,
)

from app.core.budget_engine import calculate_category_statuses
from app.core.data_manager import DataManager
from app.core.models import Category
from app.ui.dialogs.add_category_dialog import AddCategoryDialog
from app.ui.panels.base_panel import BasePanel
from app.ui.widgets.alert_banner import AlertBanner


class CategoryCard(QFrame):
    """Individual category card with color swatch, name, progress bar, and amounts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CardWidget")
        self.setFixedWidth(240)
        self.setFixedHeight(130)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        header = QHBoxLayout()
        self._color_dot = QLabel("●")
        self._color_dot.setFixedWidth(20)
        header.addWidget(self._color_dot)
        self._name_label = QLabel()
        self._name_label.setObjectName("StatCardValue")
        self._name_label.setStyleSheet("font-size: 14px;")
        header.addWidget(self._name_label, 1)
        self._bucket_label = QLabel()
        self._bucket_label.setObjectName("SubTitle")
        self._bucket_label.setStyleSheet("font-size: 10px;")
        header.addWidget(self._bucket_label)
        layout.addLayout(header)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setFixedHeight(6)
        layout.addWidget(self._progress)

        amounts_row = QHBoxLayout()
        self._spent_label = QLabel()
        amounts_row.addWidget(self._spent_label)
        amounts_row.addStretch()
        self._limit_label = QLabel()
        self._limit_label.setObjectName("SubTitle")
        amounts_row.addWidget(self._limit_label)
        layout.addLayout(amounts_row)

    def update_status(self, status, symbol: str):
        self._color_dot.setStyleSheet(f"color: {status.color};")
        self._name_label.setText(status.category_name)
        bucket_display = {"needs": "Needs", "wants": "Wants", "savings": "Savings", "": "—"}
        self._bucket_label.setText(bucket_display.get(status.bucket.lower(), "—"))

        pct = min(int(status.pct_used), 100) if status.budget_limit > 0 else 0
        self._progress.setValue(pct)

        over = status.over_budget
        almost = (not over) and status.budget_limit > 0 and status.pct_used >= 80

        self._progress.setProperty("overBudget", over)
        self._progress.setProperty("almostOver", almost)
        self._progress.style().unpolish(self._progress)
        self._progress.style().polish(self._progress)

        self._spent_label.setText(f"{symbol}{status.spent:,.2f}")
        if status.budget_limit > 0:
            self._limit_label.setText(f"/ {symbol}{status.budget_limit:,.2f}")
        else:
            self._limit_label.setText("no limit")

        # Red border for over-budget
        if over:
            self.setStyleSheet(
                "#CardWidget { border: 2px solid #f38ba8; border-radius: 12px; background-color: #24273a; }"
            )
        else:
            self.setStyleSheet("")


class CategoriesPanel(BasePanel):
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
        title = QLabel("Categories")
        title.setObjectName("SectionTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self._add_btn = QPushButton("+ Add Category")
        self._add_btn.setObjectName("PrimaryButton")
        self._add_btn.clicked.connect(self._add_category)
        header_row.addWidget(self._add_btn)

        self._edit_btn = QPushButton("Edit Selected")
        self._edit_btn.clicked.connect(self._edit_category)
        header_row.addWidget(self._edit_btn)

        self._del_btn = QPushButton("Delete Selected")
        self._del_btn.setObjectName("DangerButton")
        self._del_btn.clicked.connect(self._delete_category)
        header_row.addWidget(self._del_btn)

        layout.addLayout(header_row)

        # Alert banner for over-budget categories
        self._alert = AlertBanner()
        layout.addWidget(self._alert)

        # Month label
        self._month_label = QLabel()
        self._month_label.setObjectName("SubTitle")
        layout.addWidget(self._month_label)

        # Scrollable card grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setSpacing(12)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self._grid_widget)
        layout.addWidget(scroll, 1)

        self._selected_cat_id: Optional[str] = None
        self._cards: dict[str, CategoryCard] = {}

    def _connect_signals(self):
        self._dm.transactions_changed.connect(self.refresh)
        self._dm.categories_changed.connect(self.refresh)

    def refresh(self):
        today = date.today()
        self._month_label.setText(f"Showing: {today.strftime('%B %Y')}")

        statuses = calculate_category_statuses(
            self._dm.categories, self._dm.transactions, today.year, today.month
        )
        symbol = self._dm.settings.currency_symbol

        # Clear grid
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        # Fill grid (4 columns)
        cols = 4
        for i, status in enumerate(sorted(statuses, key=lambda s: s.category_name)):
            card = CategoryCard()
            card.update_status(status, symbol)
            card.mousePressEvent = lambda e, cid=status.category_id: self._select_card(cid)
            self._grid_layout.addWidget(card, i // cols, i % cols)
            self._cards[status.category_id] = card

        # Alert for over-budget
        over_budget = [s for s in statuses if s.over_budget]
        if over_budget:
            names = ", ".join(s.category_name for s in over_budget[:3])
            self._alert.show_warning(f"Over budget: {names}")
        else:
            self._alert.hide()

        # Highlight unclassified
        unclassified = [s for s in statuses if not s.bucket and s.spent > 0]
        if unclassified:
            self._alert.show_warning(
                f"{len(unclassified)} categories have no budget bucket assigned."
            )

    def _select_card(self, cat_id: str):
        self._selected_cat_id = cat_id
        # Visual highlight: reset all, highlight selected
        for cid, card in self._cards.items():
            if cid == cat_id:
                card.setStyleSheet(
                    "#CardWidget { border: 2px solid #cba6f7; border-radius: 12px; background-color: #24273a; }"
                )
            else:
                card.setStyleSheet("")

    def _get_selected_category(self) -> Optional[Category]:
        if self._selected_cat_id:
            return self._dm.get_category(self._selected_cat_id)
        return None

    def _add_category(self):
        dialog = AddCategoryDialog(self._dm, self)
        if dialog.exec():
            cat = dialog.get_category()
            self._dm.add_category(cat)

    def _edit_category(self):
        cat = self._get_selected_category()
        if not cat:
            QMessageBox.information(self, "No Selection", "Click a category card first.")
            return
        dialog = AddCategoryDialog(self._dm, self, category=cat)
        if dialog.exec():
            updated = dialog.get_category()
            self._dm.update_category(updated)

    def _delete_category(self):
        cat = self._get_selected_category()
        if not cat:
            QMessageBox.information(self, "No Selection", "Click a category card first.")
            return
        reply = QMessageBox.question(
            self, "Delete Category",
            f"Delete category '{cat.name}'?\n"
            "Transactions with this category will still exist but show 'Unknown'.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._dm.delete_category(cat.id)
            self._selected_cat_id = None
