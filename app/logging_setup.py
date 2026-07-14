"""Structured logging через stdlib logging с возможностью подключения structlog.

Сверка с заданием: ТЗ требует логирование Thought/Action/Observation в консоль.
Это модульная надстройка над ReActConsoleCallback, предоставляющая
стандартный logging-интерфейс для остальных компонентов приложения.
"""

from __future__ import annotations

import logging
import sys

from app import config

_CONFIGURED = False


def setup_logging(level: str | None = None) -> logging.Logger:
    """Глобальная настройка logging.

    Args:
        level: уровень логирования (DEBUG/INFO/WARNING/ERROR). Если None — из config.

    Returns:
        Корневой logger приложения.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return logging.getLogger("app")
    _CONFIGURED = True

    lvl = (level or config.LOG_LEVEL).upper()
    numeric = getattr(logging, lvl, logging.INFO)

    logger = logging.getLogger("app")
    logger.setLevel(numeric)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(numeric)
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)

    if config.TRACE_LOG_PATH:
        from pathlib import Path

        trace_path = Path(config.TRACE_LOG_PATH)
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(trace_path.with_suffix(".log"))
        file_handler.setLevel(numeric)
        file_handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "app") -> logging.Logger:
    """Получить child-logger."""
    if not _CONFIGURED:
        setup_logging()
    return logging.getLogger(f"app.{name}")


def log_tool_call(tool_name: str, input_data: dict, output: object, ok: bool = True) -> None:
    """Логирование вызова инструмента."""
    logger = get_logger("tools")
    status = "OK" if ok else "FAIL"
    logger.info(
        "tool_call status=%s tool=%s input=%s output_len=%d",
        status,
        tool_name,
        str(input_data)[:200],
        len(str(output)),
    )


def log_provider_call(provider: str, from_cur: str, to_cur: str, ok: bool, error: str = "") -> None:
    """Логирование вызова провайдера курсов."""
    logger = get_logger("providers")
    if ok:
        logger.info("provider=%s %s->%s OK", provider, from_cur, to_cur)
    else:
        logger.warning("provider=%s %s->%s FAIL: %s", provider, from_cur, to_cur, error)
