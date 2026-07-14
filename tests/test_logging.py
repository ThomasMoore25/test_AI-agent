"""Тесты модуля logging_setup."""

from __future__ import annotations

import logging

from app.logging_setup import get_logger, log_provider_call, log_tool_call, setup_logging


def test_setup_logging_returns_logger() -> None:
    """setup_logging возвращает корневой logger app."""
    logger = setup_logging("DEBUG")
    assert logger.name == "app"
    assert logger.level == logging.DEBUG


def test_get_logger_returns_child() -> None:
    """get_logger возвращает child-logger."""
    child = get_logger("test")
    assert child.name == "app.test"


def test_log_tool_call_does_not_raise() -> None:
    """log_tool_call не падает."""
    setup_logging("WARNING")
    log_tool_call("get_obligations", {"status": "active"}, [{"id": "1"}], ok=True)
    log_tool_call("convert_currency", {"amount": 10}, {"ok": False}, ok=False)


def test_log_provider_call_does_not_raise() -> None:
    """log_provider_call не падает."""
    setup_logging("WARNING")
    log_provider_call("frankfurter", "USD", "RUB", ok=False, error="404")
    log_provider_call("cbr", "USD", "RUB", ok=True)


def test_log_level_from_config() -> None:
    """Уровень логирования читается из config при None."""
    logger = setup_logging(None)
    assert logger.level >= logging.DEBUG
