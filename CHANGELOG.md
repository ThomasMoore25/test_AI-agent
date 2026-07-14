# Changelog

Все заметные изменения проекта задокументированы здесь.
Формат соответствует [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
версионирование — [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

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
