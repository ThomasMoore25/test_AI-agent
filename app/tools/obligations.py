"""Инструмент get_obligations.

Сверка с заданием:
  - Возвращает список финансовых обязательств пользователя.
  - Данные читаются из локального JSON-файла.
  - Параметры status и category фильтруют возвращаемый список.
  - Схема записи содержит: id, title, amount, currency, category,
    next_payment_date, status.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app import config


class Obligation(BaseModel):
    """Схема одной записи об обязательстве."""

    id: str
    title: str
    amount: float = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    category: str
    next_payment_date: str  # ISO YYYY-MM-DD
    status: str


class ObligationList(BaseModel):
    """Обёртка-контейнер фикстуры."""

    obligations: list[Obligation]


def _load_obligations(path: Path) -> ObligationList:
    """Чтение и валидация JSON-фикстуры.

    Валидация через Pydantic гарантирует, что некорректная запись
    будет выявлена на старте, а не попадёт в ответ агента.
    """
    if not path.exists():
        raise FileNotFoundError(f"Obligations fixture not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        raw: dict[str, Any] = json.load(f)
    return ObligationList.model_validate(raw)


@lru_cache(maxsize=1)
def _cached_obligations(path: str) -> ObligationList:
    """Кеш чтения файла на время жизни процесса.

    path передаётся строкой, чтобы корректно работало хеширование lru_cache.
    """
    return _load_obligations(Path(path))


def _filter(
    items: list[Obligation],
    status: str | None = None,
    category: str | None = None,
) -> list[Obligation]:
    result = items
    if status is not None and status != "":
        result = [o for o in result if o.status.lower() == status.lower()]
    if category is not None and category != "":
        result = [o for o in result if o.category.lower() == category.lower()]
    return result


@tool
def get_obligations(
    status: str | None = None,
    category: str | None = None,
) -> list[dict[str, Any]]:
    """Возвращает список финансовых обязательств пользователя.

    Данные читаются из локального JSON-файла (фикстура).
    Параметры status и category фильтруют возвращаемый список
    (регистронезависимое сравнение). Если фильтр не задан —
    возвращаются все записи.

    Аргументы:
        status:   фильтр по статусу ('active', 'paused', 'cancelled').
        category: фильтр по категории ('subscription', 'utility',
                  'software', 'membership', 'donation').

    Возвращает:
        Список словарей с ключами:
        id, title, amount, currency, category, next_payment_date, status.
        Если ничего не найдено — пустой список.
    """
    data = _cached_obligations(str(config.OBLIGATIONS_PATH))
    filtered = _filter(data.obligations, status=status, category=category)
    return [o.model_dump() for o in filtered]
