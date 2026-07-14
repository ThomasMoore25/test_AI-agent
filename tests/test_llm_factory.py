"""Тесты llm_factory."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.llm_factory import build_llm_multi, list_supported_providers


def test_list_supported_providers() -> None:
    """Список провайдеров содержит ожидаемые."""
    providers = list_supported_providers()
    assert "gigachat" in providers
    assert "openai" in providers
    assert "ollama" in providers
    assert "yandex" in providers


def test_build_unknown_provider_raises() -> None:
    """Неизвестный провайдер -> RuntimeError."""
    with patch("app.config.LLM_PROVIDER", "unknown"):
        with pytest.raises(RuntimeError, match="unknown LLM_PROVIDER"):
            build_llm_multi()


def test_build_gigachat_without_key_raises() -> None:
    """GigaChat без ключа -> RuntimeError."""
    with patch("app.config.LLM_PROVIDER", "gigachat"), patch("app.config.GIGACHAT_API_KEY", None):
        with pytest.raises(RuntimeError, match="GIGACHAT_API_KEY"):
            build_llm_multi()
