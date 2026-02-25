"""
Auto-generation of transactions from recurring payment rules.
Pure logic — no UI or Qt dependencies.
Uses python-dateutil for accurate month arithmetic.
"""
from __future__ import annotations
import calendar
import uuid
from datetime import date, timedelta
from typing import Optional

from dateutil.relativedelta import relativedelta

from app.core.models import RecurringPayment, Transaction


def _clamp_day(year: int, month: int, day: int) -> int:
    """Clamp day to last valid day of month (handles Feb 28/29, 30-day months)."""
    return min(day, calendar.monthrange(year, month)[1])


def generate_occurrences(
    rec: RecurringPayment,
    up_to: date,
    existing_dates: set[str],  # set of "YYYY-MM-DD" strings for this recurring_id
) -> list[Transaction]:
    """
    Generate all missing transactions for a recurring rule from
    last_generated_date (or start_date) up to `up_to`.
    Idempotent: skips dates already in existing_dates.
    """
    start = date.fromisoformat(rec.start_date)
    end = date.fromisoformat(rec.end_date) if rec.end_date else None
    last_gen = (
        date.fromisoformat(rec.last_generated_date)
        if rec.last_generated_date
        else start - timedelta(days=1)
    )

    # Effective generation starts one period after last_generated
    generate_from = last_gen + timedelta(days=1)
    generate_until = min(up_to, end) if end else up_to

    if generate_from > generate_until:
        return []

    occurrences = _get_dates_in_range(rec, generate_from, generate_until, start)
    transactions = []

    for occ_date in occurrences:
        date_str = occ_date.isoformat()
        if date_str in existing_dates:
            continue
        transactions.append(Transaction(
            id=f"txn_{uuid.uuid4().hex[:12]}",
            type=rec.type,
            amount=rec.amount,
            date=date_str,
            category_id=rec.category_id,
            description=rec.name,
            tags=list(rec.tags),
            recurring_id=rec.id,
            created_at=date_str + "T00:00:00",
            notes="Auto-generated from recurring rule",
        ))

    return transactions


def _get_dates_in_range(
    rec: RecurringPayment,
    from_date: date,
    to_date: date,
    start: date,
) -> list[date]:
    """Return all occurrence dates for a recurring rule within [from_date, to_date]."""
    freq = rec.frequency
    dates = []

    if freq == "monthly":
        dom = rec.day_of_month or start.day
        # Start from the first relevant month
        cursor = date(from_date.year, from_date.month, 1)
        while cursor <= to_date:
            occ_day = _clamp_day(cursor.year, cursor.month, dom)
            occ = date(cursor.year, cursor.month, occ_day)
            if from_date <= occ <= to_date and occ >= start:
                dates.append(occ)
            cursor = cursor + relativedelta(months=1)

    elif freq == "weekly":
        dow = rec.day_of_week if rec.day_of_week is not None else start.weekday()
        # Find first occurrence on or after from_date
        days_ahead = (dow - from_date.weekday()) % 7
        cursor = from_date + timedelta(days=days_ahead)
        if cursor < start:
            cursor += timedelta(weeks=1)
        while cursor <= to_date:
            if cursor >= start:
                dates.append(cursor)
            cursor += timedelta(weeks=1)

    elif freq == "biweekly":
        dow = rec.day_of_week if rec.day_of_week is not None else start.weekday()
        days_ahead = (dow - from_date.weekday()) % 7
        cursor = from_date + timedelta(days=days_ahead)
        if cursor < start:
            cursor += timedelta(weeks=2)
        while cursor <= to_date:
            if cursor >= start:
                dates.append(cursor)
            cursor += timedelta(weeks=2)

    elif freq == "yearly":
        month = start.month
        dom = rec.day_of_month or start.day
        cursor_year = from_date.year
        while True:
            occ_day = _clamp_day(cursor_year, month, dom)
            occ = date(cursor_year, month, occ_day)
            if occ > to_date:
                break
            if from_date <= occ and occ >= start:
                dates.append(occ)
            cursor_year += 1

    return sorted(dates)


def populate_recurring(
    recurring_rules: list[RecurringPayment],
    existing_transactions: list[Transaction],
    up_to: date,
) -> tuple[list[Transaction], list[str]]:
    """
    Main entry point: generate all missing recurring transactions.

    Returns:
        (new_transactions, updated_last_generated_dates_map)
        Where updated_last_generated_dates_map is list of (rec_id, last_date_str) tuples.
    """
    # Build index: recurring_id → set of existing dates
    existing_by_rec: dict[str, set[str]] = {}
    for txn in existing_transactions:
        if txn.recurring_id:
            existing_by_rec.setdefault(txn.recurring_id, set()).add(txn.date)

    all_new: list[Transaction] = []
    updates: list[tuple[str, str]] = []  # (rec_id, last_generated_date)

    for rec in recurring_rules:
        if not rec.active:
            continue
        existing_dates = existing_by_rec.get(rec.id, set())
        new_txns = generate_occurrences(rec, up_to, existing_dates)
        if new_txns:
            all_new.extend(new_txns)
            last_date = max(t.date for t in new_txns)
            updates.append((rec.id, last_date))

    return all_new, updates


def get_upcoming_recurring(
    recurring_rules: list[RecurringPayment],
    from_date: date,
    days_ahead: int = 30,
) -> list[tuple[RecurringPayment, date]]:
    """
    Return list of (rule, next_due_date) for upcoming recurring payments
    within the next `days_ahead` days.
    """
    to_date = from_date + timedelta(days=days_ahead)
    result = []
    for rec in recurring_rules:
        if not rec.active:
            continue
        dates = _get_dates_in_range(rec, from_date, to_date, date.fromisoformat(rec.start_date))
        for d in dates[:1]:  # just the next occurrence
            result.append((rec, d))
    result.sort(key=lambda x: x[1])
    return result
