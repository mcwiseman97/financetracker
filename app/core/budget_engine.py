"""
Pure calculation functions for budget analysis.
No UI or Qt dependencies. All functions are unit-testable.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class CategoryBudgetStatus:
    category_id: str
    category_name: str
    color: str
    bucket: str
    budget_limit: float
    spent: float
    remaining: float
    pct_used: float
    over_budget: bool


@dataclass
class BucketSummary:
    name: str          # "Needs" | "Wants" | "Savings"
    target_pct: float
    target_amount: float
    actual_amount: float
    delta: float       # positive = under budget
    pct_used: float


@dataclass
class BudgetAnalysis:
    monthly_income: float
    buckets: list[BucketSummary] = field(default_factory=list)
    category_statuses: list[CategoryBudgetStatus] = field(default_factory=list)
    income_set: bool = True
    unclassified_spend: float = 0.0


@dataclass
class MonthlySpendingSummary:
    month: str  # "YYYY-MM"
    total_income: float
    total_expenses: float
    net: float
    by_category: dict[str, float]  # category_id → amount


def calculate_category_statuses(
    categories,
    transactions,
    year: int,
    month: int,
) -> list[CategoryBudgetStatus]:
    """Calculate budget status per category for the given month."""
    # Sum spending per category for the month
    spent_by_cat: dict[str, float] = {}
    month_str = f"{year:04d}-{month:02d}"
    for txn in transactions:
        if txn.type == "expense" and txn.date.startswith(month_str):
            spent_by_cat[txn.category_id] = spent_by_cat.get(txn.category_id, 0.0) + txn.amount

    statuses = []
    for cat in categories:
        if not cat.active:
            continue
        spent = spent_by_cat.get(cat.id, 0.0)
        limit = cat.budget_limit
        if limit > 0:
            pct = (spent / limit) * 100
            remaining = limit - spent
        else:
            pct = 0.0
            remaining = 0.0
        statuses.append(CategoryBudgetStatus(
            category_id=cat.id,
            category_name=cat.name,
            color=cat.color,
            bucket=cat.bucket,
            budget_limit=limit,
            spent=spent,
            remaining=remaining,
            pct_used=pct,
            over_budget=(limit > 0 and spent > limit),
        ))

    statuses.sort(key=lambda s: s.spent, reverse=True)
    return statuses


def calculate_budget_analysis(
    categories,
    transactions,
    savings_accounts,
    settings,
    year: int,
    month: int,
) -> BudgetAnalysis:
    """
    Calculate 50/30/20 bucket analysis for the given month.
    - Needs/wants actuals come from transactions bucketed by category
    - Savings actuals = savings account deposits this month
    """
    income = settings.monthly_income
    income_set = income > 0

    month_str = f"{year:04d}-{month:02d}"

    # Build category lookup
    cat_by_id = {c.id: c for c in categories}

    # Sum spending by bucket
    bucket_spend: dict[str, float] = {"needs": 0.0, "wants": 0.0, "savings": 0.0}
    unclassified = 0.0

    for txn in transactions:
        if txn.type == "expense" and txn.date.startswith(month_str):
            cat = cat_by_id.get(txn.category_id)
            bucket = cat.bucket if cat else ""
            if bucket in bucket_spend:
                bucket_spend[bucket] += txn.amount
            else:
                unclassified += txn.amount

    # Add savings account deposits this month
    for account in savings_accounts:
        for st in account.transactions:
            if st.type == "deposit" and st.date.startswith(month_str):
                bucket_spend["savings"] += st.amount

    # Build bucket summaries
    buckets = []
    bucket_defs = [
        ("Needs", "needs", settings.needs_pct),
        ("Wants", "wants", settings.wants_pct),
        ("Savings", "savings", settings.savings_pct),
    ]
    for display_name, key, pct in bucket_defs:
        target = income * (pct / 100) if income_set else 0.0
        actual = bucket_spend[key]
        delta = target - actual
        pct_used = (actual / target * 100) if target > 0 else 0.0
        buckets.append(BucketSummary(
            name=display_name,
            target_pct=pct,
            target_amount=target,
            actual_amount=actual,
            delta=delta,
            pct_used=pct_used,
        ))

    cat_statuses = calculate_category_statuses(categories, transactions, year, month)

    return BudgetAnalysis(
        monthly_income=income,
        buckets=buckets,
        category_statuses=cat_statuses,
        income_set=income_set,
        unclassified_spend=unclassified,
    )


def calculate_monthly_summary(
    transactions,
    year: int,
    month: int,
) -> MonthlySpendingSummary:
    """Calculate income/expense totals for a specific month."""
    month_str = f"{year:04d}-{month:02d}"
    total_income = 0.0
    total_expenses = 0.0
    by_category: dict[str, float] = {}

    for txn in transactions:
        if not txn.date.startswith(month_str):
            continue
        if txn.type == "income":
            total_income += txn.amount
        elif txn.type == "expense":
            total_expenses += txn.amount
            by_category[txn.category_id] = by_category.get(txn.category_id, 0.0) + txn.amount

    return MonthlySpendingSummary(
        month=month_str,
        total_income=total_income,
        total_expenses=total_expenses,
        net=total_income - total_expenses,
        by_category=by_category,
    )


def calculate_spending_by_period(
    transactions,
    num_months: int = 6,
    end_date: Optional[date] = None,
) -> list[MonthlySpendingSummary]:
    """Return monthly summaries for the past `num_months` months."""
    if end_date is None:
        end_date = date.today()

    summaries = []
    year, month = end_date.year, end_date.month

    for _ in range(num_months):
        summaries.append(calculate_monthly_summary(transactions, year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1

    return list(reversed(summaries))


def calculate_spending_by_category(
    transactions,
    year: int,
    month: int,
) -> dict[str, float]:
    """Return spending per category for a month."""
    month_str = f"{year:04d}-{month:02d}"
    result: dict[str, float] = {}
    for txn in transactions:
        if txn.type == "expense" and txn.date.startswith(month_str):
            result[txn.category_id] = result.get(txn.category_id, 0.0) + txn.amount
    return result
