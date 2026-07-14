# Multi-stage build: builder + runtime
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime stage
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    USE_COLOR=False

WORKDIR /app

# Системные пакеты
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем установленные пакеты из builder
COPY --from=builder /install /usr/local

# Копируем код
COPY . .

# Smoke-test при сборке
RUN python -c "from app.agent import build_agent, SYSTEM_PROMPT; \
from app.tools import get_obligations, convert_currency; \
from app.date_utils import filter_by_date_range; \
from app.logging_callback import ReActConsoleCallback; \
assert get_obligations.invoke({'status': None, 'category': None}); \
print('Smoke OK')"

# Healthcheck: проверяем, что Python может импортировать приложение
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from app import config; import sys; sys.exit(0 if True else 1)"

ENTRYPOINT ["python", "main.py"]
