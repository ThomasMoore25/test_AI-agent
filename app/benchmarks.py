"""Бенчмарки производительности инструментов."""

from __future__ import annotations

import time
from statistics import mean

from app.tools.analytics import (
    filter_obligations,
    list_obligations_paginated,
    top_categories,
)
from app.tools.exports import (
    export_markdown_report,
    export_obligations_json,
    forecast_monthly,
)
from app.tools.obligations import get_obligations
from app.tools.visualization import (
    bar_chart_currencies,
    pie_chart_categories,
    timeline_payments,
)


def _bench(name: str, fn, iterations: int = 100) -> dict:
    """Прогнать fn N раз, вернуть статистику."""
    times: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        times.append(time.perf_counter() - start)
    return {
        "name": name,
        "iterations": iterations,
        "min_ms": round(min(times) * 1000, 3),
        "max_ms": round(max(times) * 1000, 3),
        "mean_ms": round(mean(times) * 1000, 3),
    }


def run_benchmarks() -> list[dict]:
    """Запуск всех бенчмарков."""
    return [
        _bench(
            "get_obligations", lambda: get_obligations.invoke({"status": None, "category": None})
        ),
        _bench("filter_obligations", lambda: filter_obligations.invoke({"min_amount": 5})),
        _bench(
            "list_obligations_paginated",
            lambda: list_obligations_paginated.invoke({"page": 1, "page_size": 5}),
        ),
        _bench("top_categories", lambda: top_categories.invoke({"n": 3})),
        _bench("export_obligations_json", lambda: export_obligations_json.invoke({})),
        _bench("export_markdown_report", lambda: export_markdown_report.invoke({})),
        _bench("forecast_monthly", lambda: forecast_monthly.invoke({"months": 3})),
        _bench("pie_chart_categories", lambda: pie_chart_categories.invoke({})),
        _bench("bar_chart_currencies", lambda: bar_chart_currencies.invoke({})),
        _bench("timeline_payments", lambda: timeline_payments.invoke({})),
    ]


if __name__ == "__main__":
    for b in run_benchmarks():
        print(
            f"{b['name']:35s}  mean={b['mean_ms']:.3f}ms  min={b['min_ms']:.3f}ms  max={b['max_ms']:.3f}ms"
        )
