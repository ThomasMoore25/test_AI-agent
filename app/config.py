"""Конфигурация приложения.

Все настройки читаются из переменных окружения (.env).
Сверка с заданием:
  - LLM_API_KEY передаётся через .env (требование ТЗ)
  - путь к фикстуре и URL frankfurter.app — параметры окружения
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# .env загружается один раз при импорте модуля
load_dotenv()

# --- LLM (GigaChat от Сбера) ---
# Сверка с заданием: "LLM на твой выбор" + стажировка в Сбере → GigaChat.
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gigachat")
LLM_MODEL: str = os.getenv("LLM_MODEL", "GigaChat-Mini")
GIGACHAT_API_KEY: str | None = os.getenv("GIGACHAT_API_KEY")
GIGACHAT_SCOPE: str = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
GIGACHAT_BASE_URL: str = os.getenv(
    "GIGACHAT_BASE_URL", "https://gigachat.devices.sberbank.ru/api/v1"
)
# GigaChat использует SSL-сертификаты Минцифры РФ; в dev-режиме можно отключить
# проверку, в прод — нужно поставить сертификат в систему.
GIGACHAT_VERIFY_SSL_CERTS: bool = os.getenv(
    "GIGACHAT_VERIFY_SSL_CERTS", "False"
).lower() in ("1", "true", "yes")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0"))

# --- Источник данных об обязательствах ---
OBLIGATIONS_PATH: Path = Path(
    os.getenv(
        "OBLIGATIONS_PATH",
        str(Path(__file__).resolve().parent / "fixtures" / "obligations.json"),
    )
)

# --- frankfurter.app ---
# В ТЗ указан URL: GET https://api.frankfurter.app/latest?from=USD&to=RUB
# api.frankfurter.app (Cloudflare) редиректит 301 -> api.frankfurter.dev/v1/...
# httpx по умолчанию следует за редиректами, поэтому используем базовый URL из ТЗ.
FRANKFURTER_BASE_URL: str = os.getenv(
    "FRANKFURTER_BASE_URL", "https://api.frankfurter.app"
)
# ECB публикует курсы 1 раз в рабочий день около 16:00 CET.
# Кеш на 24 часа физически не приводит к потере актуальных данных для этого API.
# TTL вынесен в env — при желании можно поставить меньше.
CURRENCY_CACHE_TTL_SECONDS: int = int(os.getenv("CURRENCY_CACHE_TTL_SECONDS", "86400"))

# --- Валюта по умолчанию для агрегаций ---
DEFAULT_TARGET_CURRENCY: str = os.getenv("DEFAULT_TARGET_CURRENCY", "RUB")

# --- Временная зона для расчёта "сегодня / на этой неделе / в ближайшие 30 дней" ---
LOCAL_TIMEZONE: str = os.getenv("LOCAL_TIMEZONE", "Europe/Minsk")


def is_configured() -> bool:
    """Проверка, что минимально необходимые переменные заданы."""
    return bool(GIGACHAT_API_KEY)
