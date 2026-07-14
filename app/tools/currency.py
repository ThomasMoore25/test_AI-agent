"""Инструмент convert_currency.

Сверка с заданием:
  - Конвертирует сумму через публичный API frankfurter.app
  - GET https://api.frankfurter.dev/v1/latest?base=USD&symbols=RUB
  - Принимает amount, from_currency, to_currency и возвращает число.

Дополнительно (поверх ТЗ):
  - Кеш курсов на TTL из .env (по умолчанию 24 часа). Обоснование:
    frankfurter.app использует курсы ECB, которые обновляются 1 раз в
    рабочий день — 24-часовой кеш не приводит к потере актуальности.
  - Параметр force_refresh: при True кеш игнорируется и делается живой
    запрос к API (на случай, если агент подозревает устаревание).
  - При ошибке API возвращается структурированное сообщение об ошибке
    (антигаллюцинация: агент не должен выдумывать курс).
"""

from __future__ import annotations

import time
from typing import Any, Optional

import httpx
from langchain_core.tools import tool

from app import config


# Кеш: ключ (from_currency, to_currency) -> (rate, fetched_at_epoch)
_cache: dict[tuple[str, str], tuple[float, float]] = {}


def _cache_get(from_currency: str, to_currency: str) -> Optional[float]:
    key = (from_currency.upper(), to_currency.upper())
    entry = _cache.get(key)
    if entry is None:
        return None
    rate, fetched_at = entry
    if time.time() - fetched_at > config.CURRENCY_CACHE_TTL_SECONDS:
        return None
    return rate


def _cache_put(from_currency: str, to_currency: str, rate: float) -> None:
    key = (from_currency.upper(), to_currency.upper())
    _cache[key] = (rate, time.time())


def _fetch_rate(from_currency: str, to_currency: str) -> float:
    """Живой запрос к frankfurter.app.

    Использует URL из ТЗ: https://api.frankfurter.app/latest?from=USD&to=RUB
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
        # Так frankfurter отвечает для неподдерживаемых валют (например RUB):
        # GET /latest?from=USD&to=RUB -> 404 {"message":"not found"}
        # Если же валюта просто отсутствует в rates — это тоже информативная ошибка.
        raise ValueError(
            f"frankfurter.app did not return rate for "
            f"{from_currency}->{to_currency}. "
            f"Likely currency is not supported (e.g. RUB was removed from "
            f"ECB reference rates in 2022). Response: {payload}"
        )
    return float(rate)


@tool
def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Конвертирует сумму из одной валюты в другую через frankfurter.app.

    Используется публичный API курсов Европейского центрального банка
    (обновляется 1 раз в рабочий день). Результаты кешируются на TTL
    из .env (по умолчанию 24 часа).

    Аргументы:
        amount:         сумма для конвертации (>= 0).
        from_currency:  ISO-код исходной валюты (например 'USD').
        to_currency:    ISO-код целевой валюты (например 'RUB').
        force_refresh:  если True — игнорировать кеш и сделать свежий
                        запрос к API (по умолчанию False).

    Возвращает:
        Словарь:
          {"ok": True, "amount": <float>, "from": ..., "to": ..., "rate": <float>}
        При ошибке:
          {"ok": False, "error": "<сообщение>"}
        Агент ДОЛЖЕН честно сообщить пользователю об ошибке, а не
        выдумывать курс.
    """
    if amount < 0:
        return {"ok": False, "error": "amount must be >= 0"}
    src = from_currency.upper().strip()
    dst = to_currency.upper().strip()
    if len(src) != 3 or len(dst) != 3:
        return {"ok": False, "error": "currency codes must be 3-letter ISO"}

    if src == dst:
        return {
            "ok": True,
            "amount": float(amount),
            "from": src,
            "to": dst,
            "rate": 1.0,
            "cached": False,
        }

    rate: Optional[float] = None
    if not force_refresh:
        rate = _cache_get(src, dst)

    if rate is None:
        try:
            rate = _fetch_rate(src, dst)
        except (httpx.HTTPError, ValueError) as exc:
            return {
                "ok": False,
                "error": f"currency API error: {exc.__class__.__name__}: {exc}",
            }
        _cache_put(src, dst, rate)

    converted = float(amount) * rate
    return {
        "ok": True,
        "amount": round(converted, 2),
        "from": src,
        "to": dst,
        "rate": rate,
        "cached": force_refresh is False,
    }
