"""Доменные исключения."""

from __future__ import annotations


class AgentError(Exception):
    """Базовое исключение проекта."""


class ConfigurationError(AgentError):
    """Ошибка конфигурации (нет API-ключа и т.п.)."""


class FixtureError(AgentError):
    """Ошибка загрузки или валидации фикстуры."""


class CurrencyError(AgentError):
    """Все провайдеры курсов недоступны."""


class ProviderError(AgentError):
    """Ошибка конкретного провайдера курсов."""
