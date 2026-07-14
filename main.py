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
    from app import __version__

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
        "--version",
        action="version",
        version=f"subscription-agent {__version__}",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Отключить цветной вывод (для логов).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Подробный вывод (debug-логи).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Тихий режим (только ошибки и ответ агента).",
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
    """Интерактивный REPL с командами /help, /history, /clear."""
    from app.agent import run_agent

    history: list[str] = []
    print("=== AI-агент по подпискам. Введите вопрос (или 'exit' для выхода). ===")
    print("Команды: /help, /history, /clear, exit")
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
        if query == "/help":
            print(
                "Доступные команды:\n"
                "  /help    — эта справка\n"
                "  /history — история ваших вопросов\n"
                "  /clear   — очистить историю\n"
                "  exit     — выход\n\n"
                "Примеры вопросов:\n"
                "  - Сколько я потрачу в ближайшие 30 дней? Покажи итог в рублях.\n"
                "  - Какая категория обходится мне дороже всего?\n"
                "  - Есть ли у меня платежи на этой неделе?"
            )
            continue
        if query == "/history":
            if not history:
                print("(история пуста)")
            else:
                for i, q in enumerate(history, 1):
                    print(f"  {i}. {q}")
            continue
        if query == "/clear":
            history.clear()
            print("История очищена.")
            continue
        history.append(query)
        try:
            answer = run_agent(query)
        except Exception as exc:
            print(f"[agent error] {exc.__class__.__name__}: {exc}", file=sys.stderr)
            continue
        print("\n--- ANSWER ---\n" + answer)
    return 0


def main() -> int:
    """Точка входа CLI.

    Returns:
        Код выхода: 0 — успех, 1 — ошибка агента, 2 — ошибка конфигурации.
    """
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
