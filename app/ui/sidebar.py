"""
Sidebar navigation widget.
Emits nav_item_clicked(int) when a navigation button is clicked.
"""
from __future__ import annotations
from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup, QFrame, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget,
)


NAV_ITEMS = [
    ("Dashboard",         "◉"),
    ("Transactions",      "↕"),
    ("Recurring",         "↻"),
    ("Categories",        "⊞"),
    ("Graphs",            "∿"),
    ("Savings",           "◈"),
    ("Budget (50/30/20)", "◎"),
    ("Future Payments",   "◷"),
]


class SidebarWidget(QWidget):
    nav_item_clicked = pyqtSignal(int)
    theme_toggle_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("SidebarWidget")
        self._buttons: list[QPushButton] = []
        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 16)
        layout.setSpacing(2)

        # App title
        title = QLabel("Finance Tracker")
        title.setObjectName("SidebarTitle")
        layout.addWidget(title)

        subtitle = QLabel("Personal finance manager")
        subtitle.setObjectName("SidebarSubtitle")
        layout.addWidget(subtitle)

        # Divider
        divider = QFrame()
        divider.setObjectName("SidebarDivider")
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)
        layout.addSpacing(8)

        # Navigation buttons
        for i, (label, icon) in enumerate(NAV_ITEMS):
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setFlat(True)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setFixedHeight(40)
            # Capture index in lambda with default arg
            btn.clicked.connect(lambda checked, idx=i: self.nav_item_clicked.emit(idx))
            self._btn_group.addButton(btn, i)
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Divider before theme toggle
        divider2 = QFrame()
        divider2.setObjectName("SidebarDivider")
        divider2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider2)
        layout.addSpacing(4)

        # Theme toggle button
        self._theme_btn = QPushButton("☀  Switch to Light")
        self._theme_btn.setObjectName("ThemeToggleButton")
        self._theme_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._theme_btn.setFixedHeight(34)
        self._theme_btn.clicked.connect(self.theme_toggle_requested.emit)
        layout.addWidget(self._theme_btn)

    def set_active(self, index: int):
        """Programmatically activate a nav button."""
        if 0 <= index < len(self._buttons):
            self._buttons[index].setChecked(True)

    def update_theme_button(self, is_dark: bool):
        """Update theme button label after theme switch."""
        if is_dark:
            self._theme_btn.setText("☀  Switch to Light")
        else:
            self._theme_btn.setText("☾  Switch to Dark")
