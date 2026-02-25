# Finance Tracker

A personal finance desktop application for Linux built with Python and PyQt6. Tracks transactions, recurring payments, category budgets, savings goals, and provides spending analysis — all stored locally in JSON files.

![Theme: Catppuccin Mocha (dark) and Latte (light)](https://img.shields.io/badge/theme-Catppuccin-cba6f7?style=flat-square)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-89b4fa?style=flat-square)
![PyQt6](https://img.shields.io/badge/PyQt-6-a6e3a1?style=flat-square)

## Features

- **Dashboard** — monthly stat cards, 6-month income/expense bar chart, category progress bars, upcoming recurring payments
- **Transactions** — add/edit/delete with filters by month, category, and type
- **Recurring Payments** — define rules (monthly/weekly/biweekly/yearly) that auto-generate transactions on startup
- **Categories** — card grid with per-category budget limits, overspend alerts, and Needs/Wants/Savings bucket assignment
- **Graphs** — monthly bar chart, category pie, income vs expense, and trend line — with PNG export
- **Savings Accounts** — track balances with deposit/withdrawal history and progress toward a target
- **Budget (50/30/20)** — bucket analysis against your monthly income with a live pie chart
- **Future Payments** — notepad for upcoming bills with priority levels, overdue highlighting, and one-click convert to transaction
- **Themes** — Catppuccin Mocha (dark) and Catppuccin Latte (light), toggled from the sidebar

## Screenshots

> First launch shows a Welcome dialog to set your monthly income and preferred theme.

## Requirements

- Python 3.10+
- PyQt6
- matplotlib
- python-dateutil
- babel

### Arch / CachyOS

```bash
sudo pacman -S python-pyqt6 python-matplotlib python-dateutil python-babel
```

### Other distros / venv

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

Data is stored in `~/.local/share/financetracker/`. A backup ZIP can be triggered from the data manager at any time.

## Project Structure

```
financetracker/
├── main.py
├── requirements.txt
├── data/
│   └── default_categories.json   # bootstrapped on first run
└── app/
    ├── core/
    │   ├── models.py              # dataclasses (Transaction, Category, …)
    │   ├── storage.py             # atomic JSON I/O
    │   ├── data_manager.py        # CRUD + Qt signals
    │   ├── budget_engine.py       # 50/30/20 & category calculations
    │   └── recurring_engine.py    # auto-generate transactions from rules
    └── ui/
        ├── main_window.py
        ├── sidebar.py
        ├── panels/                # one file per section
        ├── widgets/               # CardWidget, StatCard, ChartCanvas, …
        ├── dialogs/               # add/edit dialogs for all entity types
        └── themes/
            ├── dark.qss           # Catppuccin Mocha
            ├── light.qss          # Catppuccin Latte
            └── theme_manager.py
```

## Data Storage

All data lives in `~/.local/share/financetracker/` as plain JSON files:

| File | Contents |
|---|---|
| `transactions.json` | All income and expense transactions |
| `recurring.json` | Recurring payment rules |
| `categories.json` | Categories with budget limits and bucket assignments |
| `savings.json` | Savings accounts and their transaction history |
| `future_payments.json` | Upcoming payment notes |
| `settings.json` | Monthly income, theme, budget percentages |
