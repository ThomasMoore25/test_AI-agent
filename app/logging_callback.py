"""Callback для логирования ReAct-цикла в консоль и в файл.

Сверка с заданием:
  - Каждый шаг (Thought / Action / Observation) должен быть виден в консоли.
Дополнительно (поверх ТЗ):
  - Полный трейс пишется в JSONL-файл для последующего аудита/отладки.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


class ReActConsoleCallback(BaseCallbackHandler):
    """Печатает ход рассуждений агента в читаемом виде + пишет в JSONL."""

    def __init__(
        self,
        log_file: Path | None = None,
        use_color: bool = True,
    ) -> None:
        self.log_file = log_file
        self.use_color = use_color and sys.stdout.isatty()
        self._trace: list[dict[str, Any]] = []
        self._run_start: float = time.time()

    # --- Цветовые коды (минимальный набор) ---
    _COLORS = {
        "thought": "\033[36m",  # cyan
        "action": "\033[33m",  # yellow
        "observation": "\033[32m",  # green
        "error": "\033[31m",  # red
        "reset": "\033[0m",
    }

    def _color(self, kind: str, text: str) -> str:
        if not self.use_color:
            return text
        return f"{self._COLORS.get(kind, '')}{text}{self._COLORS['reset']}"

    def _emit(self, label: str, text: str, color: str = "") -> None:
        bar = "=" * 60
        header = self._color(color, f"[{label}]")
        print(f"\n{bar}\n{header}\n{text}\n{bar}", file=sys.stdout, flush=True)
        # Сохраняем в трейс
        self._trace.append(
            {
                "ts": time.time() - self._run_start,
                "type": label.lower(),
                "content": text,
            }
        )

    def flush_to_file(self) -> None:
        """Дописать накопленный трейс в JSONL-файл."""
        if not self.log_file:
            return
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "started_at": self._run_start,
                        "events": self._trace,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    # --- LLM-level (видим Thought) ---
    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """LangChain callback: on_llm_start."""
        name = (serialized or {}).get("name", "LLM")
        self._emit("Thought / LLM call", f"model={name}", "thought")

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """LangChain callback: on_llm_end."""
        try:
            text = response.generations[0][0].text
        except Exception:
            text = "(no text)"
        if text:
            self._emit("Thought", text, "thought")

    # --- Tool-level (видим Action / Observation) ---
    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tool_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """LangChain callback: on_tool_start."""
        name = (serialized or {}).get("name", "tool")
        self._emit("Action", f"tool={name}\ninput={input_str}", "action")

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """LangChain callback: on_tool_end."""
        self._emit("Observation", str(output), "observation")

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """LangChain callback: on_tool_error."""
        self._emit(
            "Tool error",
            f"{error.__class__.__name__}: {error}",
            "error",
        )
