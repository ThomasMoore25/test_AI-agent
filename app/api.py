"""Опциональный FastAPI-эндпоинт для доступа к агенту по HTTP.

Запуск:
    uvicorn app.api:app --host 0.0.0.0 --port 8000

Сверка с ТЗ: ТЗ не требует веб-API, но наличие опционального REST-эндпоинта
повышает гибкость и может быть использовано для интеграции.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app import __version__, config
from app.tools import convert_currency, get_obligations

app = FastAPI(
    title="Умный реестр подписок — AI-агент",
    description="REST API для аналитики личных подписок и регулярных платежей.",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS для веб-интеграций
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    """Запрос к агенту."""

    query: str


class AskResponse(BaseModel):
    """Ответ агента."""

    answer: str
    trace_available: bool


@app.get("/health")
def health() -> dict[str, Any]:
    """Healthcheck для Docker и балансировщиков."""
    return {
        "status": "ok",
        "version": __version__,
        "llm_configured": config.is_configured(),
    }


@app.get("/version")
def version() -> dict[str, str]:
    """Версия приложения."""
    return {"version": __version__}


@app.get("/obligations")
def list_obligations(
    status: str | None = None, category: str | None = None
) -> list[dict[str, Any]]:
    """Список обязательств с фильтрами."""
    return get_obligations.invoke({"status": status, "category": category})


@app.get("/convert")
def convert(
    amount: float,
    from_currency: str,
    to_currency: str,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Конвертация валюты."""
    return convert_currency.invoke(
        {
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "force_refresh": force_refresh,
        }
    )


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    """Вопрос агенту (требует GIGACHAT_API_KEY)."""
    if not config.is_configured():
        raise HTTPException(status_code=503, detail="LLM not configured (GIGACHAT_API_KEY missing)")
    from app.agent import run_agent

    try:
        answer = run_agent(req.query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"{exc.__class__.__name__}: {exc}") from exc
    return AskResponse(answer=answer, trace_available=bool(config.TRACE_LOG_PATH))


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Минимальная HTML-страница для ручного тестирования."""
    return """
    <!doctype html>
    <html lang="ru">
    <head><meta charset="utf-8"><title>Subscription Agent</title></head>
    <body>
      <h1>Subscription Agent API</h1>
      <ul>
        <li><a href="/docs">Swagger UI</a></li>
        <li><a href="/redoc">ReDoc</a></li>
        <li><a href="/health">/health</a></li>
        <li><a href="/obligations">/obligations</a></li>
        <li><a href="/convert?amount=10&from_currency=USD&to_currency=RUB">/convert</a></li>
      </ul>
      <h2>Ask agent</h2>
      <form id="f">
        <textarea name="query" rows="3" cols="60"></textarea><br>
        <button type="submit">Send</button>
      </form>
      <pre id="out"></pre>
      <script>
        document.getElementById('f').onsubmit = async (e) => {
          e.preventDefault();
          const q = e.target.query.value;
          const r = await fetch('/ask', {method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({query: q})});
          const data = await r.json();
          document.getElementById('out').textContent = JSON.stringify(data, null, 2);
        };
      </script>
    </body>
    </html>
    """
