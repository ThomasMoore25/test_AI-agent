"""Общие pytest fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


@pytest.fixture()
def sample_obligation() -> dict[str, Any]:
    """Один пример обязательства для тестов."""
    return {
        "id": "test-001",
        "title": "TestService",
        "amount": 9.99,
        "currency": "USD",
        "category": "subscription",
        "next_payment_date": "2026-08-01",
        "status": "active",
    }


@pytest.fixture()
def empty_cache() -> None:
    """Очищенный кеш курсов перед тестом."""
    from app.tools.currency import _cache

    _cache.clear()
    yield
    _cache.clear()


@pytest.fixture()
def tmp_fixture_file(tmp_path: Path, sample_obligation: dict[str, Any]) -> Path:
    """Временный JSON-файл с фикстурой."""
    import json

    p = tmp_path / "test_obligations.json"
    p.write_text(
        json.dumps({"obligations": [sample_obligation]}, ensure_ascii=False),
        encoding="utf-8",
    )
    return p
