FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    USE_COLOR=False

WORKDIR /app

# Системные пакеты: ca-certificates нужен для HTTPS-запросов к GigaChat
# и frankfurter.app.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Сначала ставим зависимости (кеш слоёв)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Smoke-test при сборке: импорт всех модулей без LLM-ключа
RUN python -c "from app.agent import build_agent, SYSTEM_PROMPT; \
from app.tools import get_obligations, convert_currency; \
from app.date_utils import filter_by_date_range; \
from app.logging_callback import ReActConsoleCallback; \
assert get_obligations.invoke({'status': None, 'category': None}); \
print('Smoke OK: tools work, modules importable')"

# ENTRYPOINT: CLI (можно передать one-shot аргумент через docker compose run)
ENTRYPOINT ["python", "main.py"]
