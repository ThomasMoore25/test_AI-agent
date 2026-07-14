"""Утилиты для работы с датами.

Сверка с заданием: User Story #1 — 'Сколько я потрачу в ближайшие 30 дней?'
User Story #3 — 'Есть ли у меня платежи на этой неделе?'
Агент должен учитывать текущую дату при фильтрации next_payment_date.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable, Sequence


def filter_by_date_range(
    items: Iterable[dict],
    start: date,
    end: date,
    date_field: str = "next_payment_date",
) -> list[dict]:
    """Фильтрует записи по полю date_field (ISO YYYY-MM-DD) включительно [start, end]."""
    out = []
    for item in items:
        raw = item.get(date_field)
        if not raw:
            continue
        try:
            d = datetime.fromisoformat(raw).date()
        except ValueError:
            continue
        if start <= d <= end:
            out.append(item)
    return out


def next_n_days(n: int, today: date | None = None) -> tuple[date, date]:
    """Возвращает (today, today + n дней)."""
    today = today or date.today()
    return today, today + timedelta(days=n)


def this_week(today: date | None = None) -> tuple[date, date]:
    """Возвращает диапазон текущей недели (понедельник — воскресенье)."""
    today = today or date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def group_by_category(
    items: Sequence[dict],
    target_currency_amount: dict[str, float] | None = None,
    default_currency: str = "RUB",
) -> dict[str, dict[str, float]]:
    """Группирует записи по category.

    Если target_currency_amount передан (dict {id: amount_in_target_currency}),
    использует его для агрегации; иначе — берёт исходный amount в исходной валюте.
    """
    out: dict[str, dict[str, float]] = {}
    for item in items:
        cat = item.get("category", "unknown")
        if cat not in out:
            out[cat] = {"count": 0, "total": 0.0}
        out[cat]["count"] += 1
        if target_currency_amount and item.get("id") in target_currency_amount:
            out[cat]["total"] += target_currency_amount[item["id"]]
        else:
            out[cat]["total"] += float(item.get("amount", 0))
    return out
