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

load_dotenv()


def _get_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("1", "true", "yes", "on")


def _get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def _get_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


# --- LLM (GigaChat от Сбера) ---
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gigachat")
LLM_MODEL: str = os.getenv("LLM_MODEL", "GigaChat-Mini")
GIGACHAT_API_KEY: str | None = os.getenv("GIGACHAT_API_KEY")
GIGACHAT_SCOPE: str = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
GIGACHAT_BASE_URL: str = os.getenv(
    "GIGACHAT_BASE_URL", "https://gigachat.devices.sberbank.ru/api/v1"
)
GIGACHAT_VERIFY_SSL_CERTS: bool = _get_bool("GIGACHAT_VERIFY_SSL_CERTS", False)
LLM_TEMPERATURE: float = _get_float("LLM_TEMPERATURE", 0.0)
LLM_MAX_TOKENS: int | None = _get_int("LLM_MAX_TOKENS", 0) or None

# --- Источник данных ---
OBLIGATIONS_PATH: Path = Path(
    os.getenv(
        "OBLIGATIONS_PATH",
        str(Path(__file__).resolve().parent / "fixtures" / "obligations.json"),
    )
)

# --- frankfurter.app ---
FRANKFURTER_BASE_URL: str = os.getenv("FRANKFURTER_BASE_URL", "https://api.frankfurter.app")
CURRENCY_CACHE_TTL_SECONDS: int = _get_int("CURRENCY_CACHE_TTL_SECONDS", 86400)
HTTP_TIMEOUT_SECONDS: float = _get_float("HTTP_TIMEOUT_SECONDS", 10.0)
HTTP_MAX_RETRIES: int = _get_int("HTTP_MAX_RETRIES", 3)

# --- ЦБ РФ fallback ---
CBR_BASE_URL: str = os.getenv("CBR_BASE_URL", "https://www.cbr-xml-daily.ru/daily_json.js")

# --- Бизнес-настройки ---
DEFAULT_TARGET_CURRENCY: str = os.getenv("DEFAULT_TARGET_CURRENCY", "RUB")
LOCAL_TIMEZONE: str = os.getenv("LOCAL_TIMEZONE", "Europe/Minsk")

# --- Логирование ---
TRACE_LOG_PATH: str | None = os.getenv("TRACE_LOG_PATH") or None
USE_COLOR: bool = _get_bool("USE_COLOR", True)
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()


def is_configured() -> bool:
    """Проверка, что минимально необходимые переменные заданы."""
    return bool(GIGACHAT_API_KEY)
