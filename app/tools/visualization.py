"""Инструменты визуализации (генерируют ASCII/Unicode графики без зависимостей)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from langchain_core.tools import tool

from app import config
from app.tools.obligations import _cached_obligations


@tool
def pie_chart_categories() -> str:
    """ASCII pie chart распределения обязательств по категориям."""
    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    items = [o.model_dump() for o in data.obligations if o.status == "active"]

    by_cat: dict[str, int] = defaultdict(int)
    for o in items:
        by_cat[o["category"]] += 1
    total = sum(by_cat.values())

    lines = [f"Распределение {total} активных обязательств по категориям:\n"]
    for cat, count in sorted(by_cat.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        bar = "█" * int(pct / 2)
        lines.append(f"  {cat:15s} {bar} {count} ({pct:.0f}%)")
    return "\n".join(lines)


@tool
def bar_chart_currencies() -> str:
    """ASCII bar chart сумм по валютам."""
    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    items = [o.model_dump() for o in data.obligations if o.status == "active"]

    by_cur: dict[str, float] = defaultdict(float)
    for o in items:
        by_cur[o["currency"]] += float(o["amount"])

    max_val = max(by_cur.values()) if by_cur else 1.0
    lines = ["Суммы по валютам:\n"]
    for cur, total in sorted(by_cur.items(), key=lambda x: -x[1]):
        bar_len = int(total / max_val * 30)
        bar = "█" * bar_len
        lines.append(f"  {cur} {bar} {total:.2f}")
    return "\n".join(lines)


@tool
def timeline_payments() -> str:
    """ASCII timeline будущих платежей."""
    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    items = sorted(
        [o.model_dump() for o in data.obligations if o.status == "active"],
        key=lambda x: x["next_payment_date"],
    )

    if not items:
        return "Нет активных обязательств."

    lines = ["Timeline платежей:\n"]
    for o in items:
        lines.append(
            f"  {o['next_payment_date']}  {o['title']:25s} {o['amount']:>8.2f} {o['currency']}"
        )
    return "\n".join(lines)


@tool
def compare_periods(
    period1_start: str, period1_end: str, period2_start: str, period2_end: str
) -> dict[str, Any]:
    """Сравнение двух периодов по количеству и сумме платежей.

    Args:
        period1_start: YYYY-MM-DD начало первого периода.
        period1_end: YYYY-MM-DD конец первого периода.
        period2_start: YYYY-MM-DD начало второго периода.
        period2_end: YYYY-MM-DD конец второго периода.

    Returns:
        Словарь с разбором по периодам.
    """
    from datetime import date

    from app.date_utils import filter_by_date_range

    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    items = [o.model_dump() for o in data.obligations]

    p1 = filter_by_date_range(
        items,
        date.fromisoformat(period1_start),
        date.fromisoformat(period1_end),
    )
    p2 = filter_by_date_range(
        items,
        date.fromisoformat(period2_start),
        date.fromisoformat(period2_end),
    )

    def total(items_list: list[dict[str, Any]]) -> dict[str, float]:
        out: dict[str, float] = defaultdict(float)
        for o in items_list:
            out[o["currency"]] += float(o["amount"])
        return dict(out)

    return {
        "period1": {
            "range": [period1_start, period1_end],
            "count": len(p1),
            "by_currency": total(p1),
        },
        "period2": {
            "range": [period2_start, period2_end],
            "count": len(p2),
            "by_currency": total(p2),
        },
        "diff_count": len(p2) - len(p1),
    }


@tool
def inflation_adjusted(amount: float, years_ago: int, target_year: int = 2026) -> dict[str, Any]:
    """Примерный расчёт с учётом инфляции (4% годовых по умолчанию).

    Args:
        amount: исходная сумма.
        years_ago: сколько лет назад была эта сумма.
        target_year: целевой год.

    Returns:
        Словарь с текущим эквивалентом.
    """
    rate = 0.04  # условная средняя инфляция
    current = amount * ((1 + rate) ** years_ago)
    return {
        "original": amount,
        "years_ago": years_ago,
        "assumed_annual_inflation": rate,
        "equivalent_today": round(current, 2),
        "target_year": target_year,
    }
