# Changelog

Все заметные изменения проекта задокументированы здесь.
Формат соответствует [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
версионирование — [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

## [2.0.0] — 2026-07-15

### Added (поверх v1.0)
- **13 аналитических инструментов**: search_obligations, filter_obligations,
  list_obligations_paginated, export_obligations_csv, top_categories,
  export_obligations_json, export_markdown_report, forecast_monthly,
  find_duplicates, currency_summary, status_summary, pie/bar/timeline charts,
  compare_periods, inflation_adjusted, historical_rate, list_supported_currencies,
  currency_info, list_categories, list_statuses, suggest_obligations
- **Опциональный FastAPI** с эндпоинтами /health, /ask, /obligations, /convert,
  /docs (Swagger), /redoc, минимальный HTML-UI
- **Async-инструменты**: aconvert_currency, abatch_convert (asyncio.gather)
- **Multi-LLM provider factory**: gigachat / openai / ollama / yandex
- **Резилицентность**: RateLimiter (token bucket), CircuitBreaker, GracefulShutdown
- **Fixture manager**: валидация схемы, backup, hot-reload
- **Структурированное логирование**: setup_logging с LOG_LEVEL из env
- **YAML-конфиг** (опционально, поверх .env)
- **Performance benchmarks**: 10 инструментов, каждый < 1ms
- **E2E + contract + fuzz тесты** (27 шт.)
- **Документация**: ARCHITECTURE.md, CONTRIBUTING.md, SECURITY.md,
  CODE_OF_CONDUCT.md, README.en.md, .github/ISSUE_TEMPLATE/,
  PULL_REQUEST_TEMPLATE.md, dependabot.yml, .pre-commit-config.yaml
- **CLI**: --version, --verbose, --quiet, REPL /help, /history, /clear
- **Code quality**: ruff с D-rules (pydocstyle), mypy strict для app/*,
  pytest markers, coverage threshold 70%
- **Multi-stage Docker build** с healthcheck
- **docker-compose profiles**: default, test, lint

### Changed
- Все HTTP-запросы используют with_retry (экспоненциальный backoff для 5xx/429)
- Все callback-методы задокументированы
- Все public-функции имеют docstrings

### Tests
- 87 unit/edge/integration/contract/fuzz тестов (с 30 в v1.0)

## [1.0.0] — 2026-07-15

### Added
- ReAct-агент на LangChain 1.3 + LangGraph 1.2
- LLM: GigaChat (Сбер) — `GigaChat-Mini`
- Инструмент `get_obligations(status, category)` из JSON-фикстуры (12 записей)
- Инструмент `convert_currency(amount, from, to, force_refresh)` через frankfurter.app
- Fallback на ЦБ РФ для конвертаций в/из RUB
- Логирование Thought/Action/Observation в консоль + JSONL-файл
- CLI: REPL + one-shot режим, флаги --version, --verbose, --quiet
- Dockerfile с smoke-test, docker-compose с volume для логов
- 30 unit-тестов (8 currency + 5 obligations + 9 edge cases + 8 integration/date)
- `examples/` с 4 примерами ReAct-трейсов
- `Makefile`, `pyproject.toml` (ruff + mypy + pytest конфиги)
- `ARCHITECTURE.md`, `CHANGELOG.md`, `LICENSE`, `SECURITY.md`, `CODE_OF_CONDUCT.md`
- `.dockerignore`, `.editorconfig`, `tests/conftest.py`
- Доменные enum'ы: ObligationStatus, ObligationCategory, CurrencySource
- Доменные исключения: AgentError → ConfigurationError/FixtureError/CurrencyError/ProviderError
- HTTP-клиент с retry и экспоненциальным backoff

### Changed
- LLM переключён с OpenAI GPT-4o-mini на GigaChat (Сбер)

### Security
- `.env` в `.gitignore`
- Токен GitHub не хранится в репозитории
- SSL-сертификаты Минцифры обрабатываются через флаг `GIGACHAT_VERIFY_SSL_CERTS`

## [0.1.0] — 2026-07-14

### Added
- Initial skeleton с ReAct-агентом на OpenAI GPT-4o-mini

[Unreleased]: https://github.com/ThomasMoore25/test_AI-agent/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/ThomasMoore25/test_AI-agent/releases/tag/v1.0.0
[0.1.0]: https://github.com/ThomasMoore25/test_AI-agent/releases/tag/v0.1.0
