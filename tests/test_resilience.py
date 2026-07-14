"""Тесты resilience: rate limiter, circuit breaker."""

from __future__ import annotations

import time

import pytest

from app.resilience import CircuitBreaker, RateLimiter


def test_rate_limiter_allows_up_to_max() -> None:
    """RateLimiter пропускает до max_calls за window."""
    rl = RateLimiter(max_calls=3, window_seconds=1.0)
    assert rl.acquire() is True
    assert rl.acquire() is True
    assert rl.acquire() is True
    assert rl.acquire() is False


def test_rate_limiter_refills_after_window() -> None:
    """После window секунды слот освобождается."""
    rl = RateLimiter(max_calls=1, window_seconds=0.1)
    assert rl.acquire() is True
    assert rl.acquire() is False
    time.sleep(0.15)
    assert rl.acquire() is True


def test_circuit_breaker_starts_closed() -> None:
    """Изначальное состояние — closed."""
    cb = CircuitBreaker(failure_threshold=3)
    assert cb.state == "closed"


def test_circuit_breaker_opens_after_threshold() -> None:
    """После N ошибок — open."""
    cb = CircuitBreaker(failure_threshold=3, reset_timeout=10)

    def _fail() -> None:
        raise ValueError("boom")

    for _ in range(3):
        with pytest.raises(ValueError):
            cb.call(_fail)
    assert cb.state == "open"


def test_circuit_breaker_blocks_when_open() -> None:
    """В open состоянии — RuntimeError."""
    cb = CircuitBreaker(failure_threshold=1, reset_timeout=10)
    with pytest.raises(ValueError):
        cb.call(lambda: (_ for _ in ()).throw(ValueError("x")))
    with pytest.raises(RuntimeError, match="circuit breaker is open"):
        cb.call(lambda: "ok")


def test_circuit_breaker_half_open_after_timeout() -> None:
    """После reset_timeout — half_open, успешный вызов -> closed."""
    cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.05)
    with pytest.raises(ValueError):
        cb.call(lambda: (_ for _ in ()).throw(ValueError("x")))
    assert cb.state == "open"
    time.sleep(0.06)
    assert cb.call(lambda: "ok") == "ok"
    assert cb.state == "closed"
