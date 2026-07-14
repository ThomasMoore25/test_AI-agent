# Makefile — частые команды для разработки
# Использование: make <target>

.PHONY: help install install-dev test test-cov lint format typecheck run run-docker clean

PYTHON ?= python
PIP ?= $(PYTHON) -m pip

help:  ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Установить runtime-зависимости
	$(PIP) install -r requirements.txt

install-dev:  ## Установить dev-зависимости (тесты + линтеры)
	$(PIP) install -r requirements-dev.txt

test:  ## Запустить юнит-тесты
	$(PYTHON) -m pytest -v

test-cov:  ## Запустить тесты с покрытием
	$(PYTHON) -m pytest --cov=app --cov-report=term-missing

lint:  ## Линтинг кода (ruff)
	$(PYTHON) -m ruff check app/ tests/ main.py

format:  ## Форматирование кода (ruff format + fix)
	$(PYTHON) -m ruff check --fix app/ tests/ main.py
	$(PYTHON) -m ruff format app/ tests/ main.py

typecheck:  ## Проверка типов (mypy)
	$(PYTHON) -m mypy app/

run:  ## Запустить агент локально (REPL)
	$(PYTHON) main.py

run-docker:  ## Запустить агент в Docker
	docker compose up --build

clean:  ## Удалить кеши Python/pytest/ruff
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache .mypy_cache
	rm -f .coverage coverage.xml trace.jsonl
