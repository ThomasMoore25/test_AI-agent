"""CLI REPL для общения с агентом.

Запуск:
    python main.py

Сверка с заданием:
  - Логирование Thought/Action/Observation в консоль
  - LLM_API_KEY берётся из .env
"""

from __future__ import annotations

import sys

from app import config


def main() -> int:
    if not config.is_configured():
        print(
            "ERROR: LLM_API_KEY is not set.\n"
            "Copy .env.example -> .env and fill in your API key.",
            file=sys.stderr,
        )
        return 2

    # Импорт после проверки ключа — чтобы модуль запускался без установленных
    # langchain-зависимостей при отсутствии конфигурации (для диагностики).
    from app.agent import run_agent

    print("=== AI-агент по подпискам. Введите вопрос (или 'exit' для выхода). ===")
    while True:
        try:
            query = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query:
            continue
        if query.lower() in {"exit", "quit", ":q", "q"}:
            break
        try:
            answer = run_agent(query)
        except Exception as exc:
            print(f"[agent error] {exc.__class__.__name__}: {exc}", file=sys.stderr)
            continue
        print("\n--- ANSWER ---\n" + answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
