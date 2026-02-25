"""
Pure dataclasses representing all domain objects.
No dependencies on UI or storage layers.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class Transaction:
    id: str
    type: str  # "expense" | "income"
    amount: float
    date: str  # ISO date string "YYYY-MM-DD"
    category_id: str
    description: str
    tags: list[str] = field(default_factory=list)
    recurring_id: Optional[str] = None
    created_at: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "amount": self.amount,
            "date": self.date,
            "category_id": self.category_id,
            "description": self.description,
            "tags": self.tags,
            "recurring_id": self.recurring_id,
            "created_at": self.created_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Transaction:
        return cls(
            id=d["id"],
            type=d["type"],
            amount=float(d["amount"]),
            date=d["date"],
            category_id=d["category_id"],
            description=d.get("description", ""),
            tags=d.get("tags", []),
            recurring_id=d.get("recurring_id"),
            created_at=d.get("created_at", ""),
            notes=d.get("notes", ""),
        )

    @property
    def date_obj(self) -> date:
        return date.fromisoformat(self.date)


@dataclass
class RecurringPayment:
    id: str
    name: str
    amount: float
    type: str  # "expense" | "income"
    category_id: str
    frequency: str  # "monthly" | "weekly" | "biweekly" | "yearly"
    start_date: str  # ISO date string
    active: bool = True
    day_of_month: Optional[int] = None
    day_of_week: Optional[int] = None  # 0=Monday
    end_date: Optional[str] = None
    last_generated_date: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "amount": self.amount,
            "type": self.type,
            "category_id": self.category_id,
            "frequency": self.frequency,
            "day_of_month": self.day_of_month,
            "day_of_week": self.day_of_week,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "active": self.active,
            "last_generated_date": self.last_generated_date,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, d: dict) -> RecurringPayment:
        return cls(
            id=d["id"],
            name=d["name"],
            amount=float(d["amount"]),
            type=d["type"],
            category_id=d["category_id"],
            frequency=d["frequency"],
            day_of_month=d.get("day_of_month"),
            day_of_week=d.get("day_of_week"),
            start_date=d["start_date"],
            end_date=d.get("end_date"),
            active=d.get("active", True),
            last_generated_date=d.get("last_generated_date"),
            tags=d.get("tags", []),
        )


@dataclass
class Category:
    id: str
    name: str
    color: str
    icon: str
    budget_limit: float
    budget_period: str  # "monthly"
    bucket: str  # "needs" | "wants" | "savings" | ""
    active: bool = True
    sort_order: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "icon": self.icon,
            "budget_limit": self.budget_limit,
            "budget_period": self.budget_period,
            "bucket": self.bucket,
            "active": self.active,
            "sort_order": self.sort_order,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Category:
        return cls(
            id=d["id"],
            name=d["name"],
            color=d.get("color", "#888888"),
            icon=d.get("icon", "tag"),
            budget_limit=float(d.get("budget_limit", 0.0)),
            budget_period=d.get("budget_period", "monthly"),
            bucket=d.get("bucket", ""),
            active=d.get("active", True),
            sort_order=d.get("sort_order", 0),
        )


@dataclass
class SavingsTransaction:
    id: str
    date: str  # ISO date string
    amount: float
    type: str  # "deposit" | "withdrawal"
    notes: str = ""
    balance_after: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date,
            "amount": self.amount,
            "type": self.type,
            "notes": self.notes,
            "balance_after": self.balance_after,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SavingsTransaction:
        return cls(
            id=d["id"],
            date=d["date"],
            amount=float(d["amount"]),
            type=d["type"],
            notes=d.get("notes", ""),
            balance_after=float(d.get("balance_after", 0.0)),
        )


@dataclass
class SavingsAccount:
    id: str
    name: str
    institution: str
    target_balance: float
    color: str
    active: bool = True
    transactions: list[SavingsTransaction] = field(default_factory=list)

    @property
    def current_balance(self) -> float:
        if self.transactions:
            return self.transactions[-1].balance_after
        return 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "institution": self.institution,
            "target_balance": self.target_balance,
            "color": self.color,
            "active": self.active,
            "transactions": [t.to_dict() for t in self.transactions],
        }

    @classmethod
    def from_dict(cls, d: dict) -> SavingsAccount:
        txns = [SavingsTransaction.from_dict(t) for t in d.get("transactions", [])]
        return cls(
            id=d["id"],
            name=d["name"],
            institution=d.get("institution", ""),
            target_balance=float(d.get("target_balance", 0.0)),
            color=d.get("color", "#2196F3"),
            active=d.get("active", True),
            transactions=txns,
        )


@dataclass
class FuturePayment:
    id: str
    title: str
    amount: float
    due_date: str  # ISO date string
    priority: str  # "low" | "medium" | "high"
    estimated: bool = False
    category_id: str = ""
    notes: str = ""
    completed: bool = False
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "amount": self.amount,
            "estimated": self.estimated,
            "due_date": self.due_date,
            "category_id": self.category_id,
            "priority": self.priority,
            "notes": self.notes,
            "completed": self.completed,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> FuturePayment:
        return cls(
            id=d["id"],
            title=d["title"],
            amount=float(d["amount"]),
            estimated=d.get("estimated", False),
            due_date=d["due_date"],
            category_id=d.get("category_id", ""),
            priority=d.get("priority", "medium"),
            notes=d.get("notes", ""),
            completed=d.get("completed", False),
            created_at=d.get("created_at", ""),
        )


@dataclass
class Settings:
    monthly_income: float = 0.0
    currency_symbol: str = "$"
    currency_locale: str = "en_US"
    theme: str = "dark"
    first_run_complete: bool = False
    date_format: str = "MM/DD/YYYY"
    week_starts_on: str = "monday"
    auto_populate_recurring: bool = True
    recurring_lookahead_days: int = 0
    needs_pct: float = 50.0
    wants_pct: float = 30.0
    savings_pct: float = 20.0
    last_opened: str = ""
    version: int = 1

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "monthly_income": self.monthly_income,
            "currency_symbol": self.currency_symbol,
            "currency_locale": self.currency_locale,
            "theme": self.theme,
            "first_run_complete": self.first_run_complete,
            "date_format": self.date_format,
            "week_starts_on": self.week_starts_on,
            "auto_populate_recurring": self.auto_populate_recurring,
            "recurring_lookahead_days": self.recurring_lookahead_days,
            "budget_buckets": {
                "needs_pct": self.needs_pct,
                "wants_pct": self.wants_pct,
                "savings_pct": self.savings_pct,
            },
            "last_opened": self.last_opened,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Settings:
        buckets = d.get("budget_buckets", {})
        return cls(
            monthly_income=float(d.get("monthly_income", 0.0)),
            currency_symbol=d.get("currency_symbol", "$"),
            currency_locale=d.get("currency_locale", "en_US"),
            theme=d.get("theme", "dark"),
            first_run_complete=d.get("first_run_complete", False),
            date_format=d.get("date_format", "MM/DD/YYYY"),
            week_starts_on=d.get("week_starts_on", "monday"),
            auto_populate_recurring=d.get("auto_populate_recurring", True),
            recurring_lookahead_days=int(d.get("recurring_lookahead_days", 0)),
            needs_pct=float(buckets.get("needs_pct", 50.0)),
            wants_pct=float(buckets.get("wants_pct", 30.0)),
            savings_pct=float(buckets.get("savings_pct", 20.0)),
            last_opened=d.get("last_opened", ""),
            version=d.get("version", 1),
        )
