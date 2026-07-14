"""Исторические курсы и справочники валют."""

from __future__ import annotations

from datetime import date
from typing import Any

import httpx
from langchain_core.tools import tool

from app import config
from app.http_client import with_retry


@tool
def historical_rate(from_currency: str, to_currency: str, on_date: str) -> dict[str, Any]:
    """Исторический курс frankfurter.app на указанную дату.

    Args:
        from_currency: исходная валюта.
        to_currency: целевая валюта.
        on_date: дата в формате YYYY-MM-DD.

    Returns:
        Словарь с курсом и датой.
    """
    try:
        date.fromisoformat(on_date)
    except ValueError as exc:
        return {"ok": False, "error": f"invalid date: {exc}"}

    url = f"{config.FRANKFURTER_BASE_URL}/{on_date}"
    params = {"from": from_currency.upper(), "to": to_currency.upper()}

    def _do() -> dict[str, Any]:
        with httpx.Client(timeout=config.HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    try:
        payload = with_retry(_do)
    except Exception as exc:
        return {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}

    rate = (payload.get("rates") or {}).get(to_currency.upper())
    if rate is None:
        return {"ok": False, "error": f"no rate for {from_currency}->{to_currency} on {on_date}"}
    return {
        "ok": True,
        "rate": float(rate),
        "from": from_currency.upper(),
        "to": to_currency.upper(),
        "date": payload.get("date", on_date),
    }


@tool
def list_supported_currencies() -> dict[str, str]:
    """Список валют, поддерживаемых frankfurter.app."""
    url = f"{config.FRANKFURTER_BASE_URL}/currencies"

    def _do() -> dict[str, str]:
        with httpx.Client(timeout=config.HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.json()

    try:
        return with_retry(_do)
    except Exception as exc:
        return {"error": f"{exc.__class__.__name__}: {exc}"}


@tool
def currency_info(code: str) -> dict[str, Any]:
    """Информация о валюте: название, поддерживается ли frankfurter, есть ли в ЦБ РФ.

    Args:
        code: 3-буквенный код валюты.
    """
    code = code.upper().strip()
    out: dict[str, Any] = {"code": code}

    try:
        supported = list_supported_currencies.invoke({})
        if isinstance(supported, dict) and code in supported:
            out["name"] = supported[code]
            out["frankfurter_supported"] = True
        else:
            out["frankfurter_supported"] = False
    except Exception:
        out["frankfurter_supported"] = "unknown"

    out["cbr_supported"] = code == "RUB" or None  # быстрый ответ без запроса
    return out


@tool
def list_categories() -> list[str]:
    """Список всех категорий в фикстуре."""
    from app.tools.obligations import _cached_obligations

    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    return sorted({o.category for o in data.obligations})


@tool
def list_statuses() -> list[str]:
    """Список всех статусов в фикстуре."""
    from app.tools.obligations import _cached_obligations

    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    return sorted({o.status for o in data.obligations})


@tool
def suggest_obligations(prefix: str) -> list[dict[str, Any]]:
    """Автодополнение по названию (prefix match).

    Args:
        prefix: префикс для поиска.
    """
    from app.tools.obligations import _cached_obligations

    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    p = prefix.lower()
    return [o.model_dump() for o in data.obligations if o.title.lower().startswith(p)]
