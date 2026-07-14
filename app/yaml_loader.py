"""Опциональная YAML-конфигурация (поверх .env).

Файл config.yaml (если есть) загружается ПЕРЕД env-vars, и env-vars
перекрывают значения из YAML.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_yaml_config(path: Path | str = "config.yaml") -> dict[str, Any]:
    """Загрузить YAML-конфиг, если он есть.

    Args:
        path: путь к config.yaml.

    Returns:
        Словарь настроек (пустой, если файла нет).
    """
    p = Path(path)
    if not p.exists():
        return {}
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return {}
    with p.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


def apply_yaml_to_env(yaml_data: dict[str, Any]) -> None:
    """Применить YAML-настройки к os.environ, не перекрывая существующие.

    Это позволяет .env перекрывать config.yaml, как и должно быть.
    """
    import os

    for key, value in yaml_data.items():
        if value is None:
            continue
        env_key = str(key).upper()
        if env_key not in os.environ:
            os.environ[env_key] = str(value)
