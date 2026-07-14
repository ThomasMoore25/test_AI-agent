"""Тесты fixture_manager."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.exceptions import FixtureError
from app.fixture_manager import (
    backup_fixture,
    ensure_fixture_or_raise,
    hot_reload_fixture,
    validate_fixture_schema,
)


def test_validate_fixture_ok(tmp_path: Path) -> None:
    """Валидная фикстура — 0 ошибок."""
    p = tmp_path / "ok.json"
    p.write_text(
        json.dumps(
            {
                "obligations": [
                    {
                        "id": "1",
                        "title": "X",
                        "amount": 10.0,
                        "currency": "USD",
                        "category": "subscription",
                        "next_payment_date": "2026-08-01",
                        "status": "active",
                    }
                ]
            }
        )
    )
    assert validate_fixture_schema(p) == []


def test_validate_fixture_missing_file(tmp_path: Path) -> None:
    """Несуществующий файл — 1 ошибка."""
    errors = validate_fixture_schema(tmp_path / "no.json")
    assert len(errors) == 1
    assert "not found" in errors[0]


def test_validate_fixture_bad_json(tmp_path: Path) -> None:
    """Невалидный JSON — 1 ошибка."""
    p = tmp_path / "bad.json"
    p.write_text("{not valid")
    errors = validate_fixture_schema(p)
    assert len(errors) == 1
    assert "invalid JSON" in errors[0]


def test_validate_fixture_duplicate_ids(tmp_path: Path) -> None:
    """Дубликаты ID — ошибка."""
    p = tmp_path / "dup.json"
    p.write_text(
        json.dumps(
            {
                "obligations": [
                    {
                        "id": "1",
                        "title": "A",
                        "amount": 10.0,
                        "currency": "USD",
                        "category": "subscription",
                        "next_payment_date": "2026-08-01",
                        "status": "active",
                    },
                    {
                        "id": "1",
                        "title": "B",
                        "amount": 20.0,
                        "currency": "USD",
                        "category": "subscription",
                        "next_payment_date": "2026-08-02",
                        "status": "active",
                    },
                ]
            }
        )
    )
    errors = validate_fixture_schema(p)
    assert any("duplicate" in e for e in errors)


def test_validate_fixture_bad_currency(tmp_path: Path) -> None:
    """Код валюты не 3 буквы."""
    p = tmp_path / "bad.json"
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
        )
    )
    errors = validate_fixture_schema(p)
    assert any("currency" in e for e in errors)


def test_backup_fixture_creates_copy(tmp_path: Path) -> None:
    """backup_fixture создаёт резервную копию."""
    p = tmp_path / "src.json"
    p.write_text('{"obligations": []}')
    backup = backup_fixture(p, backup_dir=tmp_path / "backups")
    assert backup.exists()
    assert backup.read_text() == '{"obligations": []}'


def test_hot_reload_fixture_returns_count() -> None:
    """hot_reload_fixture возвращает корректный count."""
    result = hot_reload_fixture()
    assert result["reloaded"] is True
    assert result["count"] >= 10
    assert result["errors"] == []


def test_ensure_fixture_or_raise_ok() -> None:
    """На валидной фикстуре не падает."""
    ensure_fixture_or_raise()  # uses default config path


def test_ensure_fixture_or_raise_raises(tmp_path: Path) -> None:
    """На невалидной фикстуре — FixtureError."""
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid")
    with pytest.raises(FixtureError):
        ensure_fixture_or_raise(bad)
