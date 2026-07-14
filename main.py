"""CLI REPL + one-shot режим для общения с агентом.

Запуск:
    python main.py                          # интерактивный REPL
    python main.py "ваш вопрос агенту"      # one-shot режим
    python main.py --help                   # справка

Сверка с заданием:
  - Логирование Thought/Action/Observation в консоль
  - LLM_API_KEY (GIGACHAT_API_KEY) берётся из .env
"""

from __future__ import annotations

import argparse
import sys

from app import config


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="subscription-agent",
        description="AI-агент для анализа личных подписок и регулярных платежей.",
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Вопрос агенту в one-shot режиме. Без аргумента — интерактивный REPL.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Отключить цветной вывод (для логов).",
    )
    return parser


def _run_one_shot(query: str) -> int:
    """One-shot режим: один вопрос — один ответ."""
    from app.agent import run_agent

    try:
        answer = run_agent(query)
    except Exception as exc:
        print(f"[agent error] {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1
    print("\n--- ANSWER ---\n" + answer)
    return 0


def _run_repl() -> int:
    """Интерактивный REPL."""
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


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if not config.is_configured():
        print(
            "ERROR: GIGACHAT_API_KEY is not set.\n"
            "1. Зарегистрируйтесь на https://developers.sber.ru/\n"
            "2. Создайте проект и получите ключ API GigaChat.\n"
            "3. Скопируйте .env.example -> .env и впишите ключ в GIGACHAT_API_KEY.",
            file=sys.stderr,
        )
        return 2

    if args.query is not None:
        return _run_one_shot(args.query)
    return _run_repl()


if __name__ == "__main__":
    raise SystemExit(main())
