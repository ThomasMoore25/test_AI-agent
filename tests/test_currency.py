"""Тесты инструмента convert_currency.

Сверка с заданием: минимум 3 теста на оба инструмента в сумме.
Здесь — 8 на convert_currency (включая моки провайдеров).
"""

from __future__ import annotations

from unittest.mock import patch

import httpx

from app.tools.currency import _cache, _cache_put, convert_currency


def test_convert_currency_same_currency_no_api_call() -> None:
    """Конвертация USD->USD не дёргает API."""
    with (
        patch("app.tools.currency.frankfurter_rate") as mock_f,
        patch("app.tools.currency.cbr_rate") as mock_c,
    ):
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
    assert result["source"] == "identity"
    mock_f.assert_not_called()
    mock_c.assert_not_called()


def test_convert_currency_uses_cache_and_skips_api() -> None:
    """Второй вызов в пределах TTL берёт кеш, не делает сетевой запрос."""
    _cache.clear()
    _cache_put("USD", "RUB", "cbr", 90.0)

    with (
        patch("app.tools.currency.frankfurter_rate") as mock_f,
        patch("app.tools.currency.cbr_rate") as mock_c,
    ):
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
    assert result["source"] == "cbr"
    mock_f.assert_not_called()
    mock_c.assert_not_called()


def test_convert_currency_force_refresh_ignores_cache() -> None:
    """force_refresh=True -> игнорируем кеш, делаем живой запрос."""
    _cache.clear()
    _cache_put("USD", "EUR", "frankfurter", 0.5)  # устаревший кеш

    with patch("app.tools.currency.frankfurter_rate", return_value=0.9) as mock_f:
        result = convert_currency.invoke(
            {
                "amount": 10.0,
                "from_currency": "USD",
                "to_currency": "EUR",
                "force_refresh": True,
            }
        )
    assert result["ok"] is True
    assert result["rate"] == 0.9
    assert result["amount"] == 9.0
    assert result["source"] == "frankfurter"
    mock_f.assert_called_once_with("USD", "EUR")


def test_convert_currency_fallback_to_cbr_for_rub() -> None:
    """Если frankfurter падает на RUB — fallback на ЦБ РФ."""
    _cache.clear()
    err = httpx.HTTPStatusError(
        "404 Not Found",
        request=httpx.Request("GET", "https://api.frankfurter.app/latest?from=USD&to=RUB"),
        response=httpx.Response(404, json={"message": "not found"}),
    )
    with (
        patch("app.tools.currency.frankfurter_rate", side_effect=err),
        patch("app.tools.currency.cbr_rate", return_value=90.0) as mock_c,
    ):
        result = convert_currency.invoke(
            {
                "amount": 10.0,
                "from_currency": "USD",
                "to_currency": "RUB",
            }
        )
    assert result["ok"] is True
    assert result["amount"] == 900.0
    assert result["source"] == "cbr"
    mock_c.assert_called_once_with("USD", "RUB")


def test_convert_currency_all_providers_fail_returns_structured_failure() -> None:
    """При ошибке обоих провайдеров возвращается ok=false (антигаллюцинация)."""
    _cache.clear()
    err = httpx.ConnectError("boom")
    with (
        patch("app.tools.currency.frankfurter_rate", side_effect=err),
        patch("app.tools.currency.cbr_rate", side_effect=err),
    ):
        result = convert_currency.invoke(
            {
                "amount": 10.0,
                "from_currency": "USD",
                "to_currency": "RUB",
            }
        )
    assert result["ok"] is False
    assert "all currency providers failed" in result["error"]
    assert "frankfurter" in result["error"]
    assert "cbr" in result["error"]


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
    """Неподдерживаемая всеми провайдерами валюта -> ok=false.

    Пример: XYZ — нет ни в frankfurter, ни в ЦБ РФ.
    """
    _cache.clear()
    frankfurter_err = httpx.HTTPStatusError(
        "404 Not Found",
        request=httpx.Request("GET", "https://api.frankfurter.app/latest?from=XYZ&to=RUB"),
        response=httpx.Response(404, json={"message": "not found"}),
    )
    cbr_err = ValueError("CBR does not have rate for XYZ")
    with (
        patch("app.tools.currency.frankfurter_rate", side_effect=frankfurter_err),
        patch("app.tools.currency.cbr_rate", side_effect=cbr_err),
    ):
        result = convert_currency.invoke(
            {
                "amount": 100.0,
                "from_currency": "XYZ",
                "to_currency": "RUB",
            }
        )
    assert result["ok"] is False
    assert "all currency providers failed" in result["error"]


def test_convert_currency_rub_to_usd_via_cbr() -> None:
    """RUB->USD: frankfurter не поддерживает RUB, идём в CBR."""
    _cache.clear()
    err = httpx.HTTPStatusError(
        "404 Not Found",
        request=httpx.Request("GET", "https://api.frankfurter.app/latest?from=RUB&to=USD"),
        response=httpx.Response(404, json={"message": "not found"}),
    )
    with (
        patch("app.tools.currency.frankfurter_rate", side_effect=err),
        patch("app.tools.currency.cbr_rate", return_value=0.0125) as mock_c,
    ):
        result = convert_currency.invoke(
            {
                "amount": 1000.0,
                "from_currency": "RUB",
                "to_currency": "USD",
            }
        )
    assert result["ok"] is True
    assert result["amount"] == 12.5
    assert result["source"] == "cbr"
    mock_c.assert_called_once_with("RUB", "USD")
