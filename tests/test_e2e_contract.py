"""E2E и contract-тесты инструментов."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from app.tools import (
    convert_currency,
    export_obligations_json,
    filter_obligations,
    get_obligations,
    top_categories,
)
from app.tools.currency import _cache

# ===== E2E сценарий: User Story #1 без реального LLM =====


def test_e2e_user_story_1_filter_and_convert() -> None:
    """Полный сценарий: получить обязательства, отфильтровать, конвертировать."""
    # 1. Получаем все обязательства
    all_items = get_obligations.invoke({"status": None, "category": None})
    assert len(all_items) == 12

    # 2. Фильтруем активные
    active = [o for o in all_items if o["status"] == "active"]
    assert len(active) == 11

    # 3. Конвертируем одну USD-запись в RUB (с моком CBR)
    _cache.clear()
    usd_item = next(o for o in active if o["currency"] == "USD")
    with (
        patch("app.tools.currency.frankfurter_rate", side_effect=ValueError("no RUB")),
        patch("app.tools.currency.cbr_rate", return_value=80.0),
    ):
        result = convert_currency.invoke(
            {
                "amount": usd_item["amount"],
                "from_currency": "USD",
                "to_currency": "RUB",
            }
        )
    assert result["ok"] is True
    assert result["source"] == "cbr"
    assert result["amount"] == round(usd_item["amount"] * 80.0, 2)


# ===== Contract test: схема ответа get_obligations =====


def test_contract_get_obligations_schema() -> None:
    """Каждая запись содержит все обязательные поля корректных типов."""
    items = get_obligations.invoke({"status": None, "category": None})
    for item in items:
        assert set(item.keys()) == {
            "id",
            "title",
            "amount",
            "currency",
            "category",
            "next_payment_date",
            "status",
        }
        assert isinstance(item["id"], str)
        assert isinstance(item["title"], str)
        assert isinstance(item["amount"], (int, float))
        assert isinstance(item["currency"], str)
        assert len(item["currency"]) == 3
        assert isinstance(item["category"], str)
        assert isinstance(item["next_payment_date"], str)
        assert isinstance(item["status"], str)


def test_contract_convert_currency_schema() -> None:
    """Ответ convert_currency соответствует контракту."""
    _cache.clear()
    result = convert_currency.invoke({"amount": 10.0, "from_currency": "USD", "to_currency": "USD"})
    assert result["ok"] is True
    assert "amount" in result
    assert "from" in result
    assert "to" in result
    assert "rate" in result
    assert "source" in result


def test_contract_filter_obligations_schema() -> None:
    """filter_obligations возвращает список словарей."""
    items = filter_obligations.invoke({"min_amount": 0})
    assert isinstance(items, list)
    for o in items:
        assert isinstance(o, dict)


def test_contract_top_categories_schema() -> None:
    """top_categories возвращает отсортированный список."""
    result = top_categories.invoke({"n": 3})
    assert isinstance(result, list)
    assert len(result) <= 3
    for r in result:
        assert "category" in r
        assert "total" in r
        assert "count" in r
    totals = [r["total"] for r in result]
    assert totals == sorted(totals, reverse=True)


def test_contract_export_json_valid() -> None:
    """export_obligations_json возвращает валидный JSON."""
    raw = export_obligations_json.invoke({})
    data = json.loads(raw)
    assert "obligations" in data
    assert isinstance(data["obligations"], list)


# ===== Fuzz тесты =====


@pytest.mark.parametrize("amount", [0, 0.01, 1, 100, 1_000_000, 1e15])
def test_fuzz_convert_amounts(amount: float) -> None:
    """Конвертация одинаковой валюты работает для разных сумм."""
    _cache.clear()
    result = convert_currency.invoke(
        {"amount": amount, "from_currency": "USD", "to_currency": "USD"}
    )
    assert result["ok"] is True
    assert result["amount"] == amount


@pytest.mark.parametrize("currency", ["USD", "EUR", "RUB", "GBP", "JPY", "usd", "Usd"])
def test_fuzz_same_currency(currency: str) -> None:
    """Конвертация X->X работает для разных валют."""
    _cache.clear()
    result = convert_currency.invoke(
        {"amount": 10.0, "from_currency": currency, "to_currency": currency}
    )
    assert result["ok"] is True


@pytest.mark.parametrize(
    "query",
    ["netflix", "Netflix", "NETFLIX", "net", "NET", "Н", "a", ""],
)
def test_fuzz_search_queries(query: str) -> None:
    """Поиск по названию работает для разных запросов."""
    from app.tools.analytics import search_obligations

    result = search_obligations.invoke({"query": query})
    assert isinstance(result, list)
