"""Инструмент convert_currency.

Сверка с заданием:
  - Конвертирует сумму через публичный API frankfurter.app (основной источник).
  - Доп. источник: ЦБ РФ для конвертаций с участием RUB
    (frankfurter.app не поддерживает RUB с 2022 года).
  - Принимает amount, from_currency, to_currency и возвращает число.

Дополнительно (поверх ТЗ):
  - Кеш курсов на TTL из .env (по умолчанию 24 часа). Обоснование:
    frankfurter.app использует курсы ECB, которые обновляются 1 раз в
    рабочий день; ЦБ РФ также обновляет курсы 1 раз в рабочий день.
  - Параметр force_refresh: при True кеш игнорируется и делается живой
    запрос к API.
  - При ошибке обоих источников возвращается структурированное сообщение
    об ошибке (антигаллюцинация: агент не должен выдумывать курс).
"""

from __future__ import annotations

import time
from typing import Any

from langchain_core.tools import tool

from app import config
from app.providers import cbr_rate, frankfurter_rate

# Кеш: ключ (from_currency, to_currency, source) -> (rate, fetched_at_epoch)
_cache: dict[tuple[str, str, str], tuple[float, float]] = {}


def _cache_get(src: str, dst: str, source: str) -> float | None:
    key = (src.upper(), dst.upper(), source)
    entry = _cache.get(key)
    if entry is None:
        return None
    rate, fetched_at = entry
    if time.time() - fetched_at > config.CURRENCY_CACHE_TTL_SECONDS:
        return None
    return rate


def _cache_put(src: str, dst: str, source: str, rate: float) -> None:
    key = (src.upper(), dst.upper(), source)
    _cache[key] = (rate, time.time())


def _try_providers(src: str, dst: str) -> tuple[float | None, str | None, str | None]:
    """Пробует провайдеров по очереди. Возвращает (rate, source, error)."""
    # 1. Тот же источник = frankfurter (ТЗ)
    try:
        rate = frankfurter_rate(src, dst)
        return rate, "frankfurter", None
    except Exception as exc:
        frankfurter_err = f"{exc.__class__.__name__}: {exc}"

    # 2. Fallback: ЦБ РФ для пар с RUB
    if "RUB" in (src, dst):
        try:
            rate = cbr_rate(src, dst)
            return rate, "cbr", None
        except Exception as exc:
            cbr_err = f"{exc.__class__.__name__}: {exc}"
            return None, None, f"frankfurter: {frankfurter_err} | cbr: {cbr_err}"

    return None, None, f"frankfurter: {frankfurter_err}"


@tool
def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Конвертирует сумму из одной валюты в другую.

    Основной источник курса — frankfurter.app (ECB reference rates).
    Для конвертаций с участием RUB используется доп. источник — ЦБ РФ,
    т.к. frankfurter.app не поддерживает RUB с 2022 года.

    Аргументы:
        amount:         сумма для конвертации (>= 0).
        from_currency:  ISO-код исходной валюты (например 'USD').
        to_currency:    ISO-код целевой валюты (например 'RUB').
        force_refresh:  если True — игнорировать кеш и сделать свежий
                        запрос к API (по умолчанию False).

    Возвращает:
        Словарь:
          {"ok": True, "amount": <float>, "from": ..., "to": ...,
           "rate": <float>, "source": "frankfurter"|"cbr"}
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
            "source": "identity",
        }

    # Сначала кеш (для любого провайдера)
    for source in ("frankfurter", "cbr"):
        cached = _cache_get(src, dst, source)
        if cached is not None and not force_refresh:
            return {
                "ok": True,
                "amount": round(float(amount) * cached, 2),
                "from": src,
                "to": dst,
                "rate": cached,
                "source": source,
            }

    rate, source, err = _try_providers(src, dst)
    if rate is None:
        return {
            "ok": False,
            "error": f"all currency providers failed: {err}",
        }

    assert source is not None
    _cache_put(src, dst, source, rate)
    return {
        "ok": True,
        "amount": round(float(amount) * rate, 2),
        "from": src,
        "to": dst,
        "rate": rate,
        "source": source,
    }
