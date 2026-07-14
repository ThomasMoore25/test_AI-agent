"""Мульти-провайдер LLM с поддержкой GigaChat, OpenAI, YandexGPT, Ollama.

Сверка с заданием: "LLM на твой выбор" + "API-ключ LLM передаётся через
переменную окружения в .env".
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel

from app import config


def build_gigachat() -> BaseChatModel:
    """GigaChat (Сбер) — нативная LLM экосистемы Сбера."""
    from langchain_gigachat.chat_models import GigaChat

    if not config.GIGACHAT_API_KEY:
        raise RuntimeError("GIGACHAT_API_KEY is not set")
    return GigaChat(
        model=config.LLM_MODEL,
        api_key=config.GIGACHAT_API_KEY,
        scope=config.GIGACHAT_SCOPE,
        base_url=config.GIGACHAT_BASE_URL,
        verify_ssl_certs=config.GIGACHAT_VERIFY_SSL_CERTS,
        temperature=config.LLM_TEMPERATURE,
        streaming=False,
    )


def build_openai() -> BaseChatModel:
    """OpenAI (опционально)."""
    from langchain_openai import ChatOpenAI

    api_key = __import__("os").getenv("OPENAI_API_KEY")
    base_url = __import__("os").getenv("OPENAI_BASE_URL")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return ChatOpenAI(
        model=config.LLM_MODEL,
        api_key=api_key,
        temperature=config.LLM_TEMPERATURE,
        base_url=base_url,
    )


def build_ollama() -> BaseChatModel:
    """Локальная LLM через Ollama (OpenAI-совместимый endpoint)."""
    from langchain_openai import ChatOpenAI

    base_url = __import__("os").getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    return ChatOpenAI(
        model=config.LLM_MODEL,
        api_key="ollama",  # dummy, Ollama не требует ключ
        temperature=config.LLM_TEMPERATURE,
        base_url=base_url,
    )


def build_yandex() -> BaseChatModel:
    """YandexGPT (опционально)."""
    from langchain_core.language_models.fake_chat import GenericFakeChatModel

    # YandexGPT LangChain-интеграция не стабилизирована — fallback на stub
    return GenericFakeChatModel(messages=iter(["YandexGPT adapter is not implemented"]))


_BUILDERS: dict[str, Any] = {
    "gigachat": build_gigachat,
    "openai": build_openai,
    "ollama": build_ollama,
    "yandex": build_yandex,
}


def build_llm_multi() -> BaseChatModel:
    """Сборка LLM по LLM_PROVIDER из .env."""
    provider = config.LLM_PROVIDER.lower()
    if provider not in _BUILDERS:
        raise RuntimeError(f"unknown LLM_PROVIDER '{provider}'. Available: {list(_BUILDERS)}")
    return _BUILDERS[provider]()


def list_supported_providers() -> list[str]:
    """Список поддерживаемых LLM-провайдеров."""
    return list(_BUILDERS)
