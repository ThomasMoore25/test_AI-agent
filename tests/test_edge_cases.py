"""Дополнительные edge-case тесты на ошибки фикстуры."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.exceptions import FixtureError
from app.tools.obligations import _load_obligations


def test_load_obligations_missing_file(tmp_path: Path) -> None:
    """Несуществующий путь -> FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        _load_obligations(tmp_path / "nonexistent.json")


def test_load_obligations_invalid_json(tmp_path: Path) -> None:
    """Невалидный JSON -> json.JSONDecodeError."""
    p = tmp_path / "bad.json"
    p.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        _load_obligations(p)


def test_load_obligations_missing_field(tmp_path: Path) -> None:
    """Запись без обязательного поля -> ValidationError."""
    p = tmp_path / "incomplete.json"
    p.write_text(
        json.dumps(
            {
                "obligations": [
                    {"id": "1", "title": "X"}  # нет amount, currency, и т.д.
                ]
            }
        ),
        encoding="utf-8",
    )
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        _load_obligations(p)


def test_load_obligations_negative_amount(tmp_path: Path) -> None:
    """Отрицательная сумма -> ValidationError (Field ge=0)."""
    p = tmp_path / "neg.json"
    p.write_text(
        json.dumps(
            {
                "obligations": [
                    {
                        "id": "1",
                        "title": "X",
                        "amount": -10.0,
                        "currency": "USD",
                        "category": "subscription",
                        "next_payment_date": "2026-08-01",
                        "status": "active",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        _load_obligations(p)


def test_load_obligations_bad_currency_code(tmp_path: Path) -> None:
    """Код валюты не 3 буквы -> ValidationError."""
    p = tmp_path / "bad_cur.json"
    p.write_text(
        json.dumps(
            {
                "obligations": [
                    {
                        "id": "1",
                        "title": "X",
                        "amount": 10.0,
                        "currency": "DOLLAR",
                        "category": "subscription",
                        "next_payment_date": "2026-08-01",
                        "status": "active",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        _load_obligations(p)


def test_exception_hierarchy() -> None:
    """Проверка иерархии доменных исключений."""
    from app.exceptions import (
        AgentError,
        ConfigurationError,
        CurrencyError,
        ProviderError,
    )

    assert issubclass(ConfigurationError, AgentError)
    assert issubclass(FixtureError, AgentError)
    assert issubclass(CurrencyError, AgentError)
    assert issubclass(ProviderError, AgentError)


def test_enums_string_values() -> None:
    """StrEnum значения корректно сериализуются в строки."""
    from app.enums import CurrencySource, ObligationCategory, ObligationStatus

    assert ObligationStatus.ACTIVE == "active"
    assert ObligationCategory.SOFTWARE == "software"
    assert CurrencySource.CBR == "cbr"


def test_http_retry_succeeds_after_failure() -> None:
    """with_retry возвращает результат после 1 неудачи."""
    import httpx

    from app.http_client import with_retry

    calls = {"n": 0}

    def _flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise httpx.ConnectError("boom")
        return "ok"

    # monkeypatch sleep чтобы тест был быстрым
    import app.http_client

    orig_sleep = app.http_client.time.sleep
    app.http_client.time.sleep = lambda _x: None
    try:
        result = with_retry(_flaky, max_attempts=3, backoff_base=0.001)
    finally:
        app.http_client.time.sleep = orig_sleep
    assert result == "ok"
    assert calls["n"] == 2


def test_http_retry_no_4xx_retry() -> None:
    """with_retry НЕ повторяет 4xx (кроме 429)."""
    import httpx

    from app.http_client import with_retry

    calls = {"n": 0}

    def _404() -> None:
        calls["n"] += 1
        raise httpx.HTTPStatusError(
            "404",
            request=httpx.Request("GET", "http://x"),
            response=httpx.Response(404),
        )

    with pytest.raises(httpx.HTTPStatusError):
        with_retry(_404, max_attempts=3, backoff_base=0.001)
    assert calls["n"] == 1  # без ретраев
