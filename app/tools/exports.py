"""Дополнительные экспорт-инструменты."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date
from typing import Any

from langchain_core.tools import tool

from app import config
from app.tools.obligations import _cached_obligations


@tool
def export_obligations_json(
    status: str | None = None,
    category: str | None = None,
) -> str:
    """Экспорт обязательств в JSON-строку.

    Args:
        status: опц. фильтр.
        category: опц. фильтр.

    Returns:
        JSON-строка.
    """
    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    items = [o.model_dump() for o in data.obligations]
    if status:
        items = [o for o in items if o["status"].lower() == status.lower()]
    if category:
        items = [o for o in items if o["category"].lower() == category.lower()]
    return json.dumps({"obligations": items}, ensure_ascii=False, indent=2)


@tool
def export_markdown_report(target_currency: str = "RUB") -> str:
    """Markdown-отчёт по всем обязательствам с группировкой по категориям.

    Args:
        target_currency: валюта для итогов (только в шапке, без конвертации).

    Returns:
        Markdown-строка.
    """
    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    items = [o.model_dump() for o in data.obligations if o.status == "active"]

    lines: list[str] = []
    lines.append("# Отчёт по подпискам")
    lines.append("")
    lines.append(f"**Дата:** {date.today().isoformat()}")
    lines.append(f"**Целевая валюта:** {target_currency}")
    lines.append(f"**Всего активных:** {len(items)}")
    lines.append("")

    # Группировка по категориям
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for o in items:
        by_cat.setdefault(o["category"], []).append(o)

    for cat in sorted(by_cat.keys()):
        lines.append(f"## {cat.title()}")
        lines.append("")
        lines.append("| Название | Сумма | Валюта | Дата |")
        lines.append("|----------|------:|--------|------|")
        for o in sorted(by_cat[cat], key=lambda x: x["next_payment_date"]):
            lines.append(
                f"| {o['title']} | {o['amount']:.2f} | {o['currency']} | {o['next_payment_date']} |"
            )
        lines.append("")

    return "\n".join(lines)


@tool
def forecast_monthly(months: int = 3) -> list[dict[str, Any]]:
    """Прогноз расходов по месяцам на основе next_payment_date.

    Args:
        months: на сколько месяцев вперёд прогнозировать.

    Returns:
        Список {month, count, items: [{title, amount, currency}]}.
    """
    if months < 1 or months > 12:
        months = 3

    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    items = [o.model_dump() for o in data.obligations if o.status == "active"]

    today = date.today()
    out: list[dict[str, Any]] = []
    for i in range(months):
        # Первый день i-го месяца вперёд
        if today.month + i <= 12:
            m = today.month + i
            y = today.year
        else:
            m = (today.month + i - 1) % 12 + 1
            y = today.year + (today.month + i - 1) // 12
        month_label = f"{y:04d}-{m:02d}"
        month_items = []
        for o in items:
            d = o["next_payment_date"][:7]  # YYYY-MM
            if d == month_label:
                month_items.append(
                    {"title": o["title"], "amount": o["amount"], "currency": o["currency"]}
                )
        out.append(
            {
                "month": month_label,
                "count": len(month_items),
                "items": month_items,
            }
        )
    return out


@tool
def find_duplicates() -> list[dict[str, Any]]:
    """Поиск дублирующихся подписок (одинаковый title, разные id).

    Returns:
        Список групп дубликатов.
    """
    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    items = [o.model_dump() for o in data.obligations]

    by_title: dict[str, list[dict[str, Any]]] = {}
    for o in items:
        key = o["title"].lower().strip()
        by_title.setdefault(key, []).append(o)

    return [{"title": title, "items": group} for title, group in by_title.items() if len(group) > 1]


@tool
def currency_summary() -> dict[str, dict[str, float]]:
    """Сводка по валютам: сколько платежей и на какую сумму в каждой валюте.

    Returns:
        Словарь {currency: {count, total_amount}}.
    """
    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    items = [o.model_dump() for o in data.obligations if o.status == "active"]

    out: dict[str, dict[str, float]] = {}
    for o in items:
        cur = o["currency"]
        if cur not in out:
            out[cur] = {"count": 0, "total_amount": 0.0}
        out[cur]["count"] += 1
        out[cur]["total_amount"] += float(o["amount"])
    return out


@tool
def status_summary() -> dict[str, int]:
    """Сводка по статусам обязательств.

    Returns:
        Словарь {status: count}.
    """
    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    items = [o.model_dump() for o in data.obligations]
    counter: Counter[str] = Counter(o["status"] for o in items)
    return dict(counter)
