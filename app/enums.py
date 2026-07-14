"""Доменные enum'ы и типы."""

from __future__ import annotations

from enum import StrEnum


class ObligationStatus(StrEnum):
    """Статусы обязательств."""

    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class ObligationCategory(StrEnum):
    """Категории обязательств."""

    SUBSCRIPTION = "subscription"
    UTILITY = "utility"
    SOFTWARE = "software"
    MEMBERSHIP = "membership"
    DONATION = "donation"


class CurrencySource(StrEnum):
    """Источник курса валют."""

    FRANKFURTER = "frankfurter"
    CBR = "cbr"
    IDENTITY = "identity"
