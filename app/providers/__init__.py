"""Источники курсов валют.

Сверка с заданием:
  - Основной источник: frankfurter.app (как в ТЗ).
  - Дополнительный источник: ЦБ РФ (https://www.cbr-xml-daily.ru/daily_json.js)
    для конвертаций в/из RUB, поскольку frankfurter.app (через ECB)
    не поддерживает RUB с 2022 года.
"""

from __future__ import annotations

from app.providers.cbr import fetch_rate as cbr_rate
from app.providers.frankfurter import fetch_rate as frankfurter_rate

__all__ = ["frankfurter_rate", "cbr_rate"]
