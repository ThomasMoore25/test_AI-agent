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

# --- LLM ---
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_API_KEY: str | None = os.getenv("LLM_API_KEY")
LLM_BASE_URL: str | None = os.getenv("LLM_BASE_URL")  # опц. для прокси/локальных LLM
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
    return bool(LLM_API_KEY)
