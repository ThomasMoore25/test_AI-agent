"""Источник курсов: frankfurter.app (требование ТЗ)."""

from __future__ import annotations

import httpx

from app import config


def fetch_rate(from_currency: str, to_currency: str) -> float:
    """Живой запрос к frankfurter.app.

    URL из ТЗ: https://api.frankfurter.app/latest?from=USD&to=RUB
    (httpx автоматически следует за 301-редиректом на api.frankfurter.dev/v1/...).

    Возвращает rate: amount_in_to = amount_in_from * rate.
    Поднимает httpx.HTTPStatusError / httpx.RequestError при сбоях,
    ValueError — если валюта не поддерживается frankfurter (например RUB).
    """
    url = f"{config.FRANKFURTER_BASE_URL}/latest"
    params = {
        "from": from_currency.upper(),
        "to": to_currency.upper(),
    }
    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        payload = resp.json()
    rates = payload.get("rates") or {}
    rate = rates.get(to_currency.upper())
    if rate is None:
        raise ValueError(
            f"frankfurter.app did not return rate for "
            f"{from_currency}->{to_currency}. "
            f"Likely currency is not supported (e.g. RUB was removed from "
            f"ECB reference rates in 2022). Response: {payload}"
        )
    return float(rate)
