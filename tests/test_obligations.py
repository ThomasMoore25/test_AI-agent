"""Тесты инструмента get_obligations.

Сверка с заданием: минимум 3 теста на оба инструмента в сумме.
Здесь — 4 на get_obligations.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.tools.obligations import get_obligations, _load_obligations
from app import config


def test_get_obligations_returns_all_when_no_filters() -> None:
    """Без фильтров — все записи фикстуры."""
    result = get_obligations.invoke({"status": None, "category": None})
    assert isinstance(result, list)
    assert len(result) >= 10  # ТЗ: 10-15 записей
    # Проверяем обязательные ключи
    keys = set(result[0].keys())
    assert {
        "id",
        "title",
        "amount",
        "currency",
        "category",
        "next_payment_date",
        "status",
    } <= keys


def test_get_obligations_filters_by_status() -> None:
    """Фильтр по статусу возвращает только совпадающие записи."""
    all_items = get_obligations.invoke({"status": None, "category": None})
    active = get_obligations.invoke({"status": "active", "category": None})
    assert 0 < len(active) <= len(all_items)
    assert all(o["status"] == "active" for o in active)


def test_get_obligations_filters_by_category_case_insensitive() -> None:
    """Фильтр по категории регистронезависимый."""
    subs_lower = get_obligations.invoke({"status": None, "category": "subscription"})
    subs_upper = get_obligations.invoke({"status": None, "category": "SUBSCRIPTION"})
    assert len(subs_lower) > 0
    assert len(subs_lower) == len(subs_upper)
    assert all(o["category"] == "subscription" for o in subs_lower)


def test_get_obligations_unknown_filter_returns_empty() -> None:
    """Несуществующий фильтр -> пустой список (антигаллюцинация)."""
    result = get_obligations.invoke(
        {"status": "nonexistent_status", "category": None}
    )
    assert result == []


def test_fixture_loads_and_validates(tmp_path: Path) -> None:
    """Pydantic-схема валидирует фикстуру (защита от сломанных данных)."""
    data = _load_obligations(config.OBLIGATIONS_PATH)
    assert len(data.obligations) >= 10
    # Все валюты — 3 буквы
    assert all(len(o.currency) == 3 for o in data.obligations)
    # Все суммы >= 0
    assert all(o.amount >= 0 for o in data.obligations)
