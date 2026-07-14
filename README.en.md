# Subscription Agent — AI Agent for Subscription Analytics

Test assignment for Data Scientist / ML-Engineer position. Russian version: see [README.md](README.md).

## Features

- ReAct agent on **LangChain + LangGraph** (`create_react_agent`)
- LLM: **GigaChat** (Sber) — native LLM of the Sber ecosystem
- Two main tools (per spec):
  - `get_obligations(status, category)` — read and filter JSON fixture
  - `convert_currency(amount, from_currency, to_currency, force_refresh=False)` — convert via [frankfurter.app](https://frankfurter.dev) with **CBR fallback** for RUB
- 11 additional analytics tools (search, filter, pagination, CSV/JSON/Markdown export, forecast, duplicates, summaries)
- Transparent logging of `Thought / Action / Observation` to console + optional JSONL file
- Anti-hallucination: structured errors on API failure
- Optional FastAPI REST API (`/health`, `/ask`, `/obligations`, `/convert`, `/docs`)
- Containerization: `docker compose up` with multi-stage build and healthcheck
- 30 unit + edge + integration tests, ruff + mypy configured

## Quick start

```bash
cp .env.example .env
# Fill in GIGACHAT_API_KEY (from https://developers.sber.ru/)

docker compose up --build
```

Or locally:

```bash
make install-dev
make test
python main.py "How much will I spend in next 30 days in RUB?"
```

## Repository

https://github.com/ThomasMoore25/test_AI-agent

## License

MIT — see [LICENSE](LICENSE).
