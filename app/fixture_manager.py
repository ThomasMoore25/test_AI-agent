"""Валидация и hot-reload фикстуры."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from app import config
from app.exceptions import FixtureError


def validate_fixture_schema(path: Path) -> list[str]:
    """Проверка структуры фикстуры.

    Returns:
        Список ошибок (пустой = ОК).
    """
    errors: list[str] = []
    if not path.exists():
        return [f"file not found: {path}"]

    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"]

    if not isinstance(data, dict):
        return ["top-level must be object"]
    if "obligations" not in data:
        return ["missing 'obligations' key"]
    if not isinstance(data["obligations"], list):
        return ["'obligations' must be array"]

    required_fields = {
        "id",
        "title",
        "amount",
        "currency",
        "category",
        "next_payment_date",
        "status",
    }
    seen_ids: set[str] = set()
    for i, item in enumerate(data["obligations"]):
        if not isinstance(item, dict):
            errors.append(f"item[{i}] not an object")
            continue
        missing = required_fields - set(item.keys())
        if missing:
            errors.append(f"item[{i}] missing fields: {missing}")
            continue
        if item["id"] in seen_ids:
            errors.append(f"item[{i}] duplicate id: {item['id']}")
        seen_ids.add(item["id"])
        if not isinstance(item["amount"], (int, float)) or item["amount"] < 0:
            errors.append(f"item[{i}] bad amount: {item['amount']}")
        if not (isinstance(item["currency"], str) and len(item["currency"]) == 3):
            errors.append(f"item[{i}] bad currency: {item['currency']}")
    return errors


def backup_fixture(path: Path, backup_dir: Path | None = None) -> Path:
    """Создать резервную копию фикстуры."""
    backup_dir = backup_dir or path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    from datetime import datetime

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{path.stem}_{ts}.json"
    shutil.copy2(path, backup_path)
    return backup_path


def hot_reload_fixture(path: Path | None = None) -> dict[str, Any]:
    """Принудительная перезагрузка фикстуры (сбрасывает lru_cache)."""
    from app.tools.obligations import _cached_obligations

    _cached_obligations.cache_clear()
    target = str(path or config.OBLIGATIONS_PATH)
    data = _cached_obligations(target)
    return {
        "reloaded": True,
        "path": target,
        "count": len(data.obligations),
        "errors": validate_fixture_schema(Path(target)),
    }


def ensure_fixture_or_raise(path: Path | None = None) -> None:
    """Validate fixture, raise FixtureError если есть проблемы."""
    target = path or config.OBLIGATIONS_PATH
    errors = validate_fixture_schema(target)
    if errors:
        raise FixtureError(f"fixture validation failed: {errors}")
