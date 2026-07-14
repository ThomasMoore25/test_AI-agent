"""HTTP-клиент с retry-логикой."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

import httpx

T = TypeVar("T")


def with_retry(
    fn: Callable[[], T],
    *,
    max_attempts: int = 3,
    backoff_base: float = 0.5,
    retry_on: tuple[type[Exception], ...] = (httpx.HTTPError,),
) -> T:
    """Экспоненциальный backoff для HTTP-запросов.

    Для 429 / 5xx — повторяем, для 4xx (кроме 429) — пробрасываем сразу.
    """
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except retry_on as exc:
            last_exc = exc
            # Не ретраим 4xx (кроме 429)
            if isinstance(exc, httpx.HTTPStatusError):
                status = exc.response.status_code
                if 400 <= status < 500 and status != 429:
                    raise
            if attempt < max_attempts - 1:
                time.sleep(backoff_base * (2**attempt))
    assert last_exc is not None
    raise last_exc
