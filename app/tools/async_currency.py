"""Async-версии инструментов (опционально, для будущих интеграций)."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app import config


async def afetch_rate_frankfurter(from_currency: str, to_currency: str) -> float:
    """Async-запрос к frankfurter.app."""
    url = f"{config.FRANKFURTER_BASE_URL}/latest"
    params = {"from": from_currency.upper(), "to": to_currency.upper()}

    async with httpx.AsyncClient(
        timeout=config.HTTP_TIMEOUT_SECONDS, follow_redirects=True
    ) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        payload = resp.json()
    rate = (payload.get("rates") or {}).get(to_currency.upper())
    if rate is None:
        raise ValueError(f"frankfurter: no rate for {from_currency}->{to_currency}")
    return float(rate)


async def afetch_rate_cbr(from_currency: str, to_currency: str) -> float:
    """Async-запрос к ЦБ РФ."""
    async with httpx.AsyncClient(
        timeout=config.HTTP_TIMEOUT_SECONDS, follow_redirects=True
    ) as client:
        resp = await client.get(config.CBR_BASE_URL)
        resp.raise_for_status()
        data = resp.json()

    valutes: dict = data.get("Valute", {})

    def rub_per_unit(code: str) -> float:
        if code == "RUB":
            return 1.0
        v = valutes.get(code)
        if v is None:
            raise ValueError(f"CBR: no rate for {code}")
        return float(v["Value"]) / float(v["Nominal"])

    return rub_per_unit(from_currency.upper()) / rub_per_unit(to_currency.upper())


async def aconvert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
) -> dict[str, Any]:
    """Async-конвертация с fallback frankfurter -> CBR."""
    if amount < 0:
        return {"ok": False, "error": "amount must be >= 0"}
    src = from_currency.upper().strip()
    dst = to_currency.upper().strip()
    if src == dst:
        return {"ok": True, "amount": float(amount), "rate": 1.0, "source": "identity"}

    try:
        rate = await afetch_rate_frankfurter(src, dst)
        return {
            "ok": True,
            "amount": round(amount * rate, 2),
            "rate": rate,
            "source": "frankfurter",
        }
    except Exception as frankfurter_err:
        if "RUB" in (src, dst):
            try:
                rate = await afetch_rate_cbr(src, dst)
                return {
                    "ok": True,
                    "amount": round(amount * rate, 2),
                    "rate": rate,
                    "source": "cbr",
                }
            except Exception as cbr_err:
                return {
                    "ok": False,
                    "error": f"all async providers failed: frankfurter: {frankfurter_err} | cbr: {cbr_err}",
                }
        return {"ok": False, "error": f"frankfurter: {frankfurter_err}"}


async def abatch_convert(
    items: list[tuple[float, str, str]],
) -> list[dict[str, Any]]:
    """Параллельная конвертация списка сумм."""
    return await asyncio.gather(*[aconvert_currency(a, f, t) for a, f, t in items])
