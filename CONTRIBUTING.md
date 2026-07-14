# Contributing

Спасибо за интерес к проекту! Этот документ описывает процесс внесения изменений.

## Быстрый старт для разработчика

```bash
git clone https://github.com/ThomasMoore25/test_AI-agent
cd test_AI-agent
python -m venv .venv
source .venv/bin/activate
make install-dev
cp .env.example .env
# впишите GIGACHAT_API_KEY
make test      # 30 тестов должны пройти
make lint      # ruff
make typecheck # mypy
```

## Процесс внесения изменений

1. Создайте ветку: `git checkout -b feature/my-feature`
2. Сделайте изменения. Покройте их тестами (минимум 1 тест на 1 изменение).
3. Запустите `make lint test typecheck` — всё должно быть зелёным.
4. Закоммитьте с понятным сообщением (см. стиль ниже).
5. Откройте PR в main. Опишите, что и почему.

## Стиль коммитов

```
<type>: <description>

<body, опционально>
```

Типы: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`.

Пример: `feat: add export to CSV command`.

## Стиль кода

- Python 3.11+
- ruff для линтинга и форматирования
- mypy для типов
- Документация (docstrings) на русском для всех public функций
- Длина строки — 100 символов

## Стиль тестов

- pytest, snake_case для тест-функций: `test_<что>_<когда>_<тогда>`
- Мокаем внешние API (frankfurter, cbr, GigaChat)
- Один тест — одна логическая проверка

## Code review

- PR рассматривается в течение 72 часов
- Требуется approve от maintainer
- Все CI-проверки должны быть зелёными

## Сообщения о багах

Используйте шаблон `.github/ISSUE_TEMPLATE/bug_report.md`.

## Предложения фич

Используйте шаблон `.github/ISSUE_TEMPLATE/feature_request.md`.
