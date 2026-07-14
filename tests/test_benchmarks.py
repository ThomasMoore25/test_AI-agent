"""Тесты бенчмарков — что они вообще запускаются."""

from __future__ import annotations

from app.benchmarks import run_benchmarks


def test_run_benchmarks_returns_results() -> None:
    """run_benchmarks возвращает список результатов."""
    results = run_benchmarks()
    assert len(results) == 10
    for r in results:
        assert "name" in r
        assert "mean_ms" in r
        assert r["mean_ms"] >= 0
        assert r["min_ms"] <= r["max_ms"]


def test_benchmarks_are_fast() -> None:
    """Каждый инструмент должен работать < 100ms в среднем."""
    results = run_benchmarks()
    for r in results:
        assert r["mean_ms"] < 100, f"{r['name']} too slow: {r['mean_ms']}ms"
