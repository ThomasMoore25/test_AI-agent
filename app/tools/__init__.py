"""Инструменты (tools) для ReAct-агента.

Сверка с заданием:
  - get_obligations(status, category)  -> список обязательств из JSON
  - convert_currency(amount, from_currency, to_currency) -> число

Доп. инструменты (поверх ТЗ):
  - search_obligations(query, status) — поиск по названию
  - filter_obligations — фильтр по сумме/валюте/нескольким категориям
  - list_obligations_paginated — постраничный список
  - export_obligations_csv — экспорт в CSV
  - top_categories — топ-N категорий по расходам
"""

from app.tools.analytics import (
    export_obligations_csv,
    filter_obligations,
    list_obligations_paginated,
    search_obligations,
    top_categories,
)
from app.tools.currency import convert_currency
from app.tools.obligations import get_obligations

__all__ = [
    "get_obligations",
    "convert_currency",
    "search_obligations",
    "filter_obligations",
    "list_obligations_paginated",
    "export_obligations_csv",
    "top_categories",
]
