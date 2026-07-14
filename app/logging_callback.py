"""Callback для логирования ReAct-цикла в консоль.

Сверка с заданием:
  - Каждый шаг (Thought / Action / Observation) должен быть виден в консоли.
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult


class ReActConsoleCallback(BaseCallbackHandler):
    """Печатает ход рассуждений агента в читаемом виде."""

    def _emit(self, label: str, text: str) -> None:
        bar = "=" * 60
        print(f"\n{bar}\n[{label}]\n{text}\n{bar}", file=sys.stdout, flush=True)

    # --- LLM-level (видим Thought) ---
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        # Не печатаем сам промпт полностью (он длинный), только метку
        name = (serialized or {}).get("name", "LLM")
        self._emit("Thought / LLM call", f"model={name}")

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        try:
            text = response.generations[0][0].text
        except Exception:
            text = "(no text)"
        if text:
            self._emit("Thought", text)

    # --- Tool-level (видим Action / Observation) ---
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tool_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        name = (serialized or {}).get("name", "tool")
        self._emit("Action", f"tool={name}\ninput={input_str}")

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._emit("Observation", str(output))

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._emit("Tool error", f"{error.__class__.__name__}: {error}")
