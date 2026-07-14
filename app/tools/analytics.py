"""Дополнительные инструменты аналитики.

Поверх ТЗ — для демонстрации расширяемости архитектуры.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from langchain_core.tools import tool

from app import config
from app.tools.obligations import _cached_obligations


@tool
def search_obligations(
    query: str,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """Поиск обязательств по названию (case-insensitive substring).

    Args:
        query: подстрока для поиска в поле title.
        status: опц. фильтр по статусу.

    Returns:
        Список совпадающих записей.
    """
    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    q = query.lower()
    out = [o.model_dump() for o in data.obligations if q in o.title.lower()]
    if status:
        out = [o for o in out if o["status"].lower() == status.lower()]
    return out


@tool
def filter_obligations(
    min_amount: float | None = None,
    max_amount: float | None = None,
    currency: str | None = None,
    categories: str | None = None,
    statuses: str | None = None,
) -> list[dict[str, Any]]:
    """Фильтр по сумме, валюте, нескольким категориям/статусам.

    Args:
        min_amount: минимум (включительно).
        max_amount: максимум (включительно).
        currency: код валюты.
        categories: категории через запятую (например 'subscription,software').
        statuses: статусы через запятую.

    Returns:
        Отфильтрованный список.
    """
    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    items = [o.model_dump() for o in data.obligations]

    cats = {c.strip().lower() for c in categories.split(",")} if categories else None
    sts = {s.strip().lower() for s in statuses.split(",")} if statuses else None

    out = []
    for o in items:
        if min_amount is not None and o["amount"] < min_amount:
            continue
        if max_amount is not None and o["amount"] > max_amount:
            continue
        if currency and o["currency"].upper() != currency.upper():
            continue
        if cats and o["category"].lower() not in cats:
            continue
        if sts and o["status"].lower() not in sts:
            continue
        out.append(o)
    return out


@tool
def list_obligations_paginated(
    page: int = 1,
    page_size: int = 10,
    status: str | None = None,
) -> dict[str, Any]:
    """Постраничный список обязательств.

    Args:
        page: номер страницы (1-based).
        page_size: размер страницы.
        status: опц. фильтр.

    Returns:
        Словарь: {page, page_size, total, total_pages, items}.
    """
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 10

    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    items = [o.model_dump() for o in data.obligations]
    if status:
        items = [o for o in items if o["status"].lower() == status.lower()]

    total = len(items)
    total_pages = (total + page_size - 1) // page_size or 1
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "items": items[start:end],
    }


@tool
def export_obligations_csv(
    status: str | None = None,
    category: str | None = None,
) -> str:
    """Экспорт обязательств в CSV.

    Args:
        status: опц. фильтр.
        category: опц. фильтр.

    Returns:
        CSV-строка.
    """
    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    items = [o.model_dump() for o in data.obligations]
    if status:
        items = [o for o in items if o["status"].lower() == status.lower()]
    if category:
        items = [o for o in items if o["category"].lower() == category.lower()]

    if not items:
        return ""

    fields = list(items[0].keys())
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    writer.writerows(items)
    return buf.getvalue()


@tool
def top_categories(n: int = 3, target_currency: str = "RUB") -> list[dict[str, Any]]:
    """Топ-N категорий по суммарным расходам в указанной валюте.

    Args:
        n: сколько категорий вернуть (по умолчанию 3).
        target_currency: целевая валюта для агрегации.

    Returns:
        Список {category, total, count}, отсортированный по убыванию total.
    """
    from app.date_utils import group_by_category

    if n < 1:
        n = 3
    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    items = [o.model_dump() for o in data.obligations if o.status == "active"]

    # Группируем в исходных валютах (без конвертации — её делает агент отдельно)
    grouped = group_by_category(items)
    result = [
        {"category": cat, "total": v["total"], "count": v["count"]} for cat, v in grouped.items()
    ]
    result.sort(key=lambda x: x["total"], reverse=True)
    return result[:n]
