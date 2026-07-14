"""Тесты async-инструментов."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.tools.async_currency import abatch_convert, aconvert_currency


@pytest.mark.asyncio
async def test_aconvert_same_currency() -> None:
    """Async-конвертация USD->USD не дёргает API."""
    result = await aconvert_currency(100.0, "USD", "USD")
    assert result["ok"] is True
    assert result["amount"] == 100.0
    assert result["source"] == "identity"


@pytest.mark.asyncio
async def test_aconvert_negative_amount() -> None:
    """Отрицательная сумма — отказ."""
    result = await aconvert_currency(-5.0, "USD", "RUB")
    assert result["ok"] is False
    assert "amount" in result["error"]


@pytest.mark.asyncio
async def test_aconvert_fallback_to_cbr() -> None:
    """Fallback frankfurter -> CBR для RUB."""
    with (
        patch(
            "app.tools.async_currency.afetch_rate_frankfurter",
            new=AsyncMock(side_effect=ValueError("no RUB")),
        ),
        patch(
            "app.tools.async_currency.afetch_rate_cbr",
            new=AsyncMock(return_value=90.0),
        ),
    ):
        result = await aconvert_currency(10.0, "USD", "RUB")
    assert result["ok"] is True
    assert result["amount"] == 900.0
    assert result["source"] == "cbr"


@pytest.mark.asyncio
async def test_abatch_convert_parallel() -> None:
    """Пакетная конвертация работает."""
    items = [(100.0, "USD", "USD"), (50.0, "EUR", "EUR")]
    results = await abatch_convert(items)
    assert len(results) == 2
    assert all(r["ok"] for r in results)


@pytest.mark.asyncio
async def test_aconvert_all_providers_fail() -> None:
    """Все провайдеры упали — ok=False."""
    with (
        patch(
            "app.tools.async_currency.afetch_rate_frankfurter",
            new=AsyncMock(side_effect=ValueError("boom")),
        ),
        patch(
            "app.tools.async_currency.afetch_rate_cbr",
            new=AsyncMock(side_effect=ValueError("boom")),
        ),
    ):
        result = await aconvert_currency(10.0, "USD", "RUB")
    assert result["ok"] is False
    assert "all async providers failed" in result["error"]
