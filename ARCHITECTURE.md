# Архитектура

## Обзор

Проект реализует ReAct-агента для аналитики личных подписок и регулярных платежей.

```
                ┌──────────────────────────┐
                │  User (CLI / one-shot)   │
                └──────────┬───────────────┘
                           │
                           ▼
                ┌──────────────────────────┐
                │      main.py (CLI)       │
                └──────────┬───────────────┘
                           │
                           ▼
                ┌──────────────────────────┐
                │      app/agent.py        │
                │  (ReAct через LangGraph) │
                └──┬────────────────────┬──┘
                   │                    │
                   ▼                    ▼
        ┌──────────────────┐  ┌──────────────────┐
        │  get_obligations │  │ convert_currency │
        │  (from JSON)     │  │  (multi-source)  │
        └────────┬─────────┘  └──┬────────────┬──┘
                 │               │            │
                 ▼               ▼            ▼
        ┌──────────────────┐  ┌──────────┐ ┌──────────┐
        │ obligations.json │  │frankfurter│ │  cbr.ru  │
        │  (12 records)    │  │   .app   │ │ (fallback│
        └──────────────────┘  └──────────┘ │  для RUB)│
                                          └──────────┘
```

## Компоненты

### CLI (`main.py`)
- REPL или one-shot режим
- argparse с --version, --verbose, --quiet
- Обработка ошибок без LLM-ключа

### Агент (`app/agent.py`)
- `build_llm()` — создание GigaChat-инстанса
- `build_agent()` — сборка ReAct через `langgraph.prebuilt.create_react_agent`
- `run_agent()` — синхронный запуск с callback
- SYSTEM_PROMPT — ролевая инструкция с антигаллюцинацией

### Инструменты (`app/tools/`)
- `get_obligations(status, category)` — чтение JSON + Pydantic-валидация
- `convert_currency(amount, from, to, force_refresh)` — оркестрация провайдеров

### Провайдеры курсов (`app/providers/`)
- `frankfurter.py` — основной источник (ТЗ)
- `cbr.py` — fallback для пар с RUB

### Утилиты
- `app/config.py` — все настройки из .env
- `app/date_utils.py` — фильтры по датам, группировка
- `app/enums.py` — StrEnum для статусов, категорий, источников
- `app/exceptions.py` — доменные исключения
- `app/http_client.py` — with_retry для HTTP-запросов
- `app/logging_callback.py` — Thought/Action/Observation в консоль + JSONL

## Ключевые архитектурные решения

1. **Готовый ReAct, не свой цикл** — требование ТЗ.
2. **Fallback на ЦБ РФ для RUB** — frankfurter.app не поддерживает RUB с 2022.
3. **Антигаллюцинация** — структурированные ошибки `{"ok": false, ...}`.
4. **Pydantic-валидация фикстуры** — некорректные данные ловим на старте.
5. **Кеширование курсов** — TTL 24h (ECB обновляет 1 раз в рабочий день).
6. **Retry с backoff** — для 5xx и 429, не для 4xx.

## Что не сделано (намеренно)

- Веб-API — ТЗ не требует.
- Многопользовательский режим — ТЗ не требует.
- БД — ТЗ просит JSON.
- Свой ReAct-цикл — ТЗ просит готовый фреймворк.
