"""Источник курсов: ЦБ РФ (доп. источник для RUB).

frankfurter.app (через ECB) не поддерживает RUB с 2022 года.
ЦБ РФ публикует курсы основных валют к RUB ежедневно.
API: https://www.cbr-xml-daily.ru/daily_json.js
Формат: {"Valute": {"USD": {"Value": 90.5, "Nominal": 1}, ...}}
"""

from __future__ import annotations

import httpx

CBR_BASE_URL = "https://www.cbr-xml-daily.ru/daily_json.js"
CBR_TIMEOUT = 10.0


def _fetch_daily() -> dict:
    """GET daily_json.js и парсинг JSON."""
    with httpx.Client(timeout=CBR_TIMEOUT, follow_redirects=True) as client:
        resp = client.get(CBR_BASE_URL)
        resp.raise_for_status()
        return resp.json()


def fetch_rate(from_currency: str, to_currency: str) -> float:
    """Конвертация через ЦБ РФ.

    Поддерживает пары (X->RUB), (RUB->X), (X->Y) через RUB как промежуточную.
    Курсы ЦБ РФ даются как "1 единица валюты = Value рублей RUB".
    Для RUB->X: обратный курс.
    Для X->Y: X->RUB->Y.

    Поднимает httpx.HTTPError при сетевой ошибке,
    ValueError — если валюта не найдена в ответе ЦБ РФ.
    """
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
        # Nominal: например для JPY Nominal=100, Value=67.5 —
        # значит 100 JPY = 67.5 RUB, т.е. 1 JPY = 0.675 RUB
        return float(v["Value"]) / float(v["Nominal"])

    rate_src_to_rub = rub_per_unit(src)
    rate_dst_to_rub = rub_per_unit(dst)
    # X -> Y: rate = rub_per_unit(X) / rub_per_unit(Y)
    return rate_src_to_rub / rate_dst_to_rub
