"""Инструменты (tools) для ReAct-агента.

Сверка с заданием:
  - get_obligations(status, category)  -> список обязательств из JSON
  - convert_currency(amount, from_currency, to_currency) -> число
"""

from app.tools.currency import convert_currency
from app.tools.obligations import get_obligations

__all__ = ["get_obligations", "convert_currency"]
