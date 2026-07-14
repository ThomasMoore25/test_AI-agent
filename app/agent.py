"""Сборка ReAct-агента.

Сверка с заданием:
  - Используется готовый фреймворк (LangChain + LangGraph).
  - Цикл ReAct НЕ пишется вручную.
  - Каждый шаг (Thought / Action / Observation) должен быть виден в консоли.
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from app import config
from app.tools import get_obligations, convert_currency
from app.logging_callback import ReActConsoleCallback


SYSTEM_PROMPT = """Ты — финансовый ассистент по личным подпискам и регулярным платежам.

Твоя задача: отвечать на вопросы пользователя, ВЫЗЫВАЯ ИНСТРУМЕНТЫ.
Никогда не выдумывай данные. Если инструмент вернул ошибку или пустой
список — честно сообщи об этом пользователю.

Доступные инструменты:
- get_obligations(status, category) — возвращает список обязательств
  пользователя. Каждая запись содержит: id, title, amount, currency,
  category, next_payment_date, status.
- convert_currency(amount, from_currency, to_currency, force_refresh=False)
  — конвертирует сумму через публичный API frankfurter.app. Возвращает
  {"ok": true, "amount": <число>, ...} либо {"ok": false, "error": "..."}.

Правила:
1. Для агрегации расходов по нескольким валютам всегда приводи суммы к
   единой валюте. По умолчанию (если пользователь явно не просил другую)
   используй RUB как целевую. ЕСЛИ frankfurter.app не поддерживает RUB
   (вернёт ok=false), честно сообщи пользователю, что RUB больше не
   поддерживается frankfurter.app (ECB прекратил публикацию курса RUB
   в 2022 году), и предложи альтернативу: привести суммы к USD или EUR.
2. Если convert_currency вернул ok=false — НЕ подставляй курс сам.
   Сообщи пользователю, что не удалось получить актуальный курс, и
   по возможности укажи, какие суммы не удалось конвертировать.
3. Для вопросов "в ближайшие N дней", "на этой неделе", "в этом месяце"
   фильтруй записи по next_payment_date относительно текущей даты.
   Текущая дата доступна в контексте.
4. Отвечай кратко, но с обоснованием: какие данные ты использовал,
   какие курсы применил, какие итоговые суммы получил.
5. Если данных недостаточно для ответа — так и скажи. Не угадывай.
"""


def build_llm() -> BaseChatModel:
    """Создаёт LLM-инстанс по настройкам из .env."""
    if not config.LLM_API_KEY:
        raise RuntimeError(
            "LLM_API_KEY is not set. Copy .env.example -> .env and fill it."
        )
    return ChatOpenAI(
        model=config.LLM_MODEL,
        api_key=config.LLM_API_KEY,
        temperature=config.LLM_TEMPERATURE,
        base_url=config.LLM_BASE_URL,
    )


def build_agent() -> Any:
    """Собирает ReAct-агента с двумя инструментами.

    Используется langgraph.prebuilt.create_react_agent — это полностью
    готовый цикл ReAct, мы не пишем его вручную (требование ТЗ).
    """
    llm = build_llm()
    tools = [get_obligations, convert_currency]
    agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)
    return agent


def run_agent(query: str) -> str:
    """Синхронный запуск агента с логированием шагов в консоль.

    Возвращает финальный ответ в виде строки.
    """
    agent = build_agent()
    callback = ReActConsoleCallback()
    today = __import__("datetime").date.today().isoformat()
    full_prompt = f"Текущая дата: {today}.\n\nВопрос пользователя: {query}"
    result = agent.invoke(
        {"messages": [("user", full_prompt)]},
        config={"callbacks": [callback]},
    )
    messages = result.get("messages", [])
    if not messages:
        return "(пустой ответ агента)"
    last = messages[-1]
    return getattr(last, "content", str(last))
