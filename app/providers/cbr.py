"""Источник курсов: ЦБ РФ (доп. источник для RUB)."""

from __future__ import annotations

import httpx

from app.http_client import with_retry

CBR_BASE_URL = "https://www.cbr-xml-daily.ru/daily_json.js"
CBR_TIMEOUT = 10.0


def _fetch_daily() -> dict:
    """GET daily_json.js с retry."""

    def _do() -> dict:
        with httpx.Client(timeout=CBR_TIMEOUT, follow_redirects=True) as client:
            resp = client.get(CBR_BASE_URL)
            resp.raise_for_status()
            return resp.json()

    return with_retry(_do)


def fetch_rate(from_currency: str, to_currency: str) -> float:
    """Конвертация через ЦБ РФ с retry."""
    src = from_currency.upper()
    dst = to_currency.upper()
    data = _fetch_daily()
    valutes: dict = data.get("Valute", {})

    def rub_per_unit(code: str) -> float:
        if code == "RUB":
            return 1.0
        v = valutes.get(code)
        if v is None:
            raise ValueError(
                f"CBR does not have rate for {code}. Available: {sorted(valutes.keys())[:20]}..."
            )
        return float(v["Value"]) / float(v["Nominal"])

    rate_src_to_rub = rub_per_unit(src)
    rate_dst_to_rub = rub_per_unit(dst)
    return rate_src_to_rub / rate_dst_to_rub
