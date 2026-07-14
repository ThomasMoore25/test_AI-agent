"""Rate limiter, circuit breaker, graceful shutdown."""

from __future__ import annotations

import signal
import threading
import time
from collections import deque
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_calls: int, window_seconds: float = 1.0) -> None:
        self.max_calls = max_calls
        self.window = window_seconds
        self._calls: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        """Попробовать взять слот. True если можно, False если превышен лимит."""
        """Попробовать взять слот. True если можно, False если превышен лимит."""
        now = time.time()
        with self._lock:
            while self._calls and now - self._calls[0] > self.window:
                self._calls.popleft()
            if len(self._calls) >= self.max_calls:
                return False
            self._calls.append(now)
            return True


class CircuitBreaker:
    """Circuit breaker для защиты от каскадных сбоев.

    States: closed (работает) -> open (сбои) -> half_open (проверка)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 30.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._failures = 0
        self._last_failure_time: float | None = None
        self._state = "closed"
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        """Текущее состояние breaker: closed / open / half_open."""
        return self._state

    def call(self, fn: Callable[[], T]) -> T:
        """Вызвать fn через breaker."""
        with self._lock:
            if self._state == "open":
                if (
                    self._last_failure_time
                    and time.time() - self._last_failure_time > self.reset_timeout
                ):
                    self._state = "half_open"
                else:
                    raise RuntimeError("circuit breaker is open")
        try:
            result = fn()
        except Exception as exc:
            with self._lock:
                self._failures += 1
                self._last_failure_time = time.time()
                if self._failures >= self.failure_threshold:
                    self._state = "open"
            raise exc
        else:
            with self._lock:
                if self._state == "half_open":
                    self._state = "closed"
                    self._failures = 0
            return result


class GracefulShutdown:
    """Обработка SIGTERM/SIGINT для graceful shutdown."""

    def __init__(self) -> None:
        self._shutdown = False
        self._handlers: list[Callable[[], None]] = []
        self._lock = threading.Lock()

    def register(self, handler: Callable[[], None]) -> None:
        """Зарегистрировать cleanup-обработчик."""
        with self._lock:
            self._handlers.append(handler)

    def is_shutting_down(self) -> bool:
        """True если получен сигнал shutdown."""
        return self._shutdown

    def install(self) -> None:
        """Установить signal handlers для SIGTERM/SIGINT."""
        """Установить signal handlers."""
        signal.signal(signal.SIGTERM, self._handle)
        signal.signal(signal.SIGINT, self._handle)

    def _handle(self, signum: int, frame: Any) -> None:
        print(f"\n[shutdown] signal {signum} received, cleaning up...", flush=True)
        self._shutdown = True
        with self._lock:
            for h in self._handlers:
                try:
                    h()
                except Exception as exc:
                    print(f"[shutdown] handler error: {exc}", flush=True)
