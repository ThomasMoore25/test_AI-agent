"""Тесты инструмента convert_currency.

Сверка с заданием: минимум 3 теста на оба инструмента в сумме.
Здесь — 5 на convert_currency (включая мок API).
"""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import httpx
import pytest

from app.tools.currency import convert_currency, _cache_put, _cache
from app import config


def test_convert_currency_same_currency_no_api_call() -> None:
    """Конвертация USD->USD не дёргает API."""
    with patch("app.tools.currency._fetch_rate") as mock_fetch:
        result = convert_currency.invoke(
            {
                "amount": 100.0,
                "from_currency": "USD",
                "to_currency": "USD",
            }
        )
    assert result["ok"] is True
    assert result["amount"] == 100.0
    assert result["rate"] == 1.0
    mock_fetch.assert_not_called()


def test_convert_currency_uses_cache_and_skips_api() -> None:
    """Второй вызов в пределах TTL берёт кеш, не делает сетевой запрос."""
    _cache.clear()
    _cache_put("USD", "RUB", 90.0)

    with patch("app.tools.currency._fetch_rate") as mock_fetch:
        result = convert_currency.invoke(
            {
                "amount": 10.0,
                "from_currency": "USD",
                "to_currency": "RUB",
            }
        )
    assert result["ok"] is True
    assert result["amount"] == 900.0
    assert result["rate"] == 90.0
    mock_fetch.assert_not_called()


def test_convert_currency_force_refresh_ignores_cache() -> None:
    """force_refresh=True -> игнорируем кеш, делаем живой запрос."""
    _cache.clear()
    _cache_put("USD", "RUB", 90.0)  # устаревший кеш

    with patch(
        "app.tools.currency._fetch_rate", return_value=95.0
    ) as mock_fetch:
        result = convert_currency.invoke(
            {
                "amount": 10.0,
                "from_currency": "USD",
                "to_currency": "RUB",
                "force_refresh": True,
            }
        )
    assert result["ok"] is True
    assert result["rate"] == 95.0
    assert result["amount"] == 950.0
    mock_fetch.assert_called_once_with("USD", "RUB")


def test_convert_currency_api_error_returns_structured_failure() -> None:
    """При ошибке API возвращается ok=false, а не падает."""
    _cache.clear()
    err = httpx.ConnectError("boom")
    with patch("app.tools.currency._fetch_rate", side_effect=err):
        result = convert_currency.invoke(
            {
                "amount": 10.0,
                "from_currency": "USD",
                "to_currency": "RUB",
            }
        )
    assert result["ok"] is False
    assert "currency API error" in result["error"]
    assert "ConnectError" in result["error"]


def test_convert_currency_negative_amount_rejected() -> None:
    """Отрицательная сумма — отказ (антигаллюцинация)."""
    result = convert_currency.invoke(
        {
            "amount": -5.0,
            "from_currency": "USD",
            "to_currency": "RUB",
        }
    )
    assert result["ok"] is False
    assert "amount" in result["error"]


def test_convert_currency_unsupported_currency_returns_clear_error() -> None:
    """RUB не поддерживается frankfurter.app (ECB убрал RUB в 2022).

    Агент должен получить структурированную ошибку и не выдумывать курс.
    Используем мок, чтобы тест был детерминированным и не зависел от сети.
    """
    _cache.clear()
    # Имитируем ответ frankfurter для неподдерживаемой валюты
    err = httpx.HTTPStatusError(
        "404 Not Found",
        request=httpx.Request("GET", "https://api.frankfurter.app/latest?from=USD&to=RUB"),
        response=httpx.Response(404, json={"message": "not found"}),
    )
    with patch("app.tools.currency._fetch_rate", side_effect=err):
        result = convert_currency.invoke(
            {
                "amount": 100.0,
                "from_currency": "USD",
                "to_currency": "RUB",
            }
        )
    assert result["ok"] is False
    assert "currency API error" in result["error"]
    assert "404" in result["error"]
