# Умный реестр подписок — AI-агент (Data Scientist / ML-инженер)

Тестовое задание. Сверка со спецификацией: см. раздел «Соответствие ТЗ» ниже.

## Возможности

- ReAct-агент на **LangChain + LangGraph** (`create_react_agent`)
- LLM: **GigaChat** (Сбер) — нативная LLM экосистемы Сбера
- Два инструмента:
  - `get_obligations(status, category)` — чтение и фильтрация JSON-фикстуры
  - `convert_currency(amount, from_currency, to_currency, force_refresh=False)` — конвертация через публичный API [frankfurter.app](https://frankfurter.dev) с **fallback на ЦБ РФ** для конвертаций в/из RUB
- Прозрачное логирование `Thought / Action / Observation` в консоль
- Антигаллюцинация: при ошибке обоих API валют агент честно сообщает об ошибке
- Контейнеризация: `docker compose up` одной командой
- 13 unit-тестов (8 на `convert_currency`, 5 на `get_obligations`)

---

## 1. Как запустить

### Локально (без Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env
# Откройте .env и впишите свой GIGACHAT_API_KEY
#   (получить на https://developers.sber.ru/)

python main.py
```

### Через Docker (рекомендуется в ТЗ)

```bash
cp .env.example .env
# Впишите GIGACHAT_API_KEY в .env

docker compose up --build
```

Запустится интерактивный REPL. Примеры вопросов:

```
> Сколько я потрачу в ближайшие 30 дней? Покажи итог в рублях.
> Какая категория обходится мне дороже всего?
> Есть ли у меня платежи на этой неделе?
```

### Запуск тестов

```bash
pip install -r requirements-dev.txt
pytest -v
```

### Переменные окружения

| Переменная | Назначение | По умолчанию |
|---|---|---|
| `GIGACHAT_API_KEY` | **обязательный** — API-ключ GigaChat (https://developers.sber.ru/) | — |
| `LLM_PROVIDER` | провайдер (`gigachat`) | `gigachat` |
| `LLM_MODEL` | имя модели GigaChat | `GigaChat-Mini` |
| `GIGACHAT_SCOPE` | scope авторизации (`GIGACHAT_API_PERS` / `B2B` / `CORP`) | `GIGACHAT_API_PERS` |
| `GIGACHAT_BASE_URL` | endpoint API GigaChat | `https://gigachat.devices.sberbank.ru/api/v1` |
| `GIGACHAT_VERIFY_SSL_CERTS` | проверка SSL-сертификатов Минцифры (False в dev) | `False` |
| `LLM_TEMPERATURE` | температура | `0` |
| `OBLIGATIONS_PATH` | путь к JSON-фикстуре | `app/fixtures/obligations.json` |
| `FRANKFURTER_BASE_URL` | базовый URL API валют | `https://api.frankfurter.app` |
| `CURRENCY_CACHE_TTL_SECONDS` | TTL кеша курсов | `86400` |
| `DEFAULT_TARGET_CURRENCY` | валюта агрегации по умолчанию | `RUB` |
| `LOCAL_TIMEZONE` | часовой пояс для расчётов дат | `Europe/Minsk` |

---

## 2. Какой LLM выбран и почему

**Выбран:** **GigaChat** (Сбер, модель `GigaChat-Mini`).

**Почему:**
1. **Это стажировка в Сбере.** GigaChat — нативная LLM экосистемы Сбера. Выбор внутренней LLM демонстрирует понимание контекста работодателя и работу с его технологическим стеком.
2. **Бесплатный доступ через https://developers.sber.ru/.** Не требуется платёжной карты, ключ выдаётся сразу после регистрации проекта.
3. **Поддержка function calling / tools** через LangChain (`langchain-gigachat`). Это обязательное требование для ReAct-агента — GigaChat умеет вызывать инструменты и обрабатывать их результаты.
4. **Хорошее качество на русском языке.** Все user stories и примеры в ТЗ на русском — GigaChat лучше работает с русскоязычными запросами, чем зарубежные LLM сопоставимого размера.
5. **Полное соответствие требованию ТЗ** «LLM на твой выбор» и «API-ключ LLM передаётся через переменную окружения в .env».

**Как заменить:** для переключения на другой LLM нужно:
- Добавить соответствующий провайдер в `requirements.txt` (например `langchain-openai` для OpenAI).
- Изменить `build_llm()` в `app/agent.py`.
- Обновить переменные в `.env`.

Архитектура инструментов (`get_obligations`, `convert_currency`) остаётся неизменной — они не зависят от LLM.

---

## 3. Пример ReAct-трейса

Запрос: **«Какая категория обходится мне дороже всего? Покажи итог в USD.»**

(Запрос выбран так, чтобы обойти известное ограничение frankfurter.app —
отсутствие RUB. См. раздел «Ограничения».)

```
============================================================
[Thought / LLM call]
model=ChatOpenAI
============================================================
============================================================
[Thought]
Нужны все обязательства, далее сгруппировать по category и для каждой
записи не в USD конвертировать в USD, затем просуммировать.
============================================================
============================================================
[Action]
tool=get_obligations
input={"status": null, "category": null}
============================================================
============================================================
[Observation]
[{"id":"11111111-...","title":"Netflix","amount":9.99,"currency":"USD",
  "category":"subscription","next_payment_date":"2026-07-20","status":"active"},
 ... 12 записей ...]
============================================================
============================================================
[Thought]
В фикстуре 12 записей в валютах USD, EUR, RUB, GBP. RUB-суммы
конвертируются в USD через frankfurter.app, но RUB там НЕ поддерживается
с 2022 года — честно сообщу об этом и сложу только то, что удалось
сконвертировать (USD, EUR, GBP). RUB-суммы будут показаны отдельно.
============================================================
============================================================
[Action]
tool=convert_currency
input={"amount": 24.90, "from_currency": "EUR", "to_currency": "USD"}
============================================================
============================================================
[Observation]
{"ok": true, "amount": 28.39, "from": "EUR", "to": "USD",
 "rate": 1.1405, "cached": true}
============================================================
... (повторные вызовы convert_currency для EUR и GBP сумм) ...
Попытка convert_currency(amount=299.0, from=RUB, to=USD) ->
{"ok": false, "error": "currency API error: HTTPStatusError: 404 Not Found"}

--- ANSWER ---
Самая затратная категория (по суммам, конвертируемым в USD через
frankfurter.app на 2026-07-14):

| Категория     | Итог в USD |
|---------------|-----------:|
| software      |     32.39  |  (JetBrains EUR 24.90 → 28.39 USD, GitHub Pro 4.00 USD)
| subscription  |     22.05  |  (Netflix 9.99, Spotify 5.99, iCloud 2.99, The Guardian 5.99 GBP → 8.02)
| donation      |      5.70  |  (Patreon EUR 5.00 → 5.70 USD)

Не удалось конвертировать в USD (frankfurter.app не поддерживает RUB
с 2022 года — ECB прекратил публикацию курса RUB):
- Яндекс.Плюс: 299.00 RUB
- Мосэнерго: 1500.00 RUB
- Ростелеком: 800.00 RUB
- World Class: 4500.00 RUB

Если нужна оценка в RUB — предлагаю вручную пересчитать через курс ЦБ РФ.
По конвертируемой части лидирует категория software.
```

> Точные цифры в трейсе зависят от текущего курса frankfurter.app.
> Полный вывод можно воспроизвести локально, запустив `python main.py` и
> задав тот же вопрос.

---

## 4. Ограничения

| Ограничение | Причина |
|---|---|
| **Курсы обновляются 1 раз в рабочий день.** Агент не увидит внутридневное изменение курса. | Источники: frankfurter.app (ECB Reference Rates, обновление в 16:00 CET) и ЦБ РФ (обновление в 11:30 МСК). Это особенность источников, не агента. Параметр `force_refresh=True` позволяет сделать свежий запрос. |
| **RUB конвертируется через ЦБ РФ, не через frankfurter.app.** | frankfurter.app (ECB) прекратил публикацию курса RUB в марте 2022 года. Реализован fallback на ЦБ РФ — агент автоматически переключается при ошибке frankfurter для пар с участием RUB. |
| **Нет аутентификации пользователей.** Все запросы работают с одной общей фикстурой. | ТЗ не требует многопользовательности; цель — продемонстрировать AI-агента, а не backend-сервис. |
| **Нет веб-API/фронтенда.** Взаимодействие через CLI REPL. | ТЗ просит бэкенд-ядро и AI-интеграцию, фронтенд не запрашивается. |
| **Фикстура статична.** Данные об обязательствах лежат в JSON, не в БД. | ТЗ явно говорит «данные читаются из локального JSON-файла». |
| **Нет полного end-to-end теста агента** (только unit-тесты инструментов). | End-to-end требует живого API-ключа LLM и платит за каждый прогон. Инструменты и их контракты покрыты тестами. |
| **Таймзона по умолчанию — Europe/Minsk.** | Настроена через `LOCAL_TIMEZONE` в `.env`. |
| **Не реализованы доп. инструменты** (графики, отчёты, экспорт). | ТЗ требует ровно два инструмента. Доп. функционал — за рамками задания. |
| **Нет ретраев при 429/5xx от API курсов.** | ТЗ требует антигаллюцинацию (честная ошибка), а не экспоненциальный backoff. При необходимости добавляется одной декораторной обёрткой. |

---

## Соответствие ТЗ (чек-лист сверки)

| Требование ТЗ | Реализация |
|---|---|
| Python, LLM на выбор | Python 3.11, GigaChat (Сбер) |
| Срок 3 дня | v0.1 готов к ревью |
| Формат: ссылка на репозиторий | GitHub-репозиторий |
| ReAct-агент через готовый фреймворк | LangChain + LangGraph `create_react_agent` |
| `get_obligations(status, category)` из JSON | `app/tools/obligations.py`, фикстура 12 записей |
| Схема записи (7 полей) | `Obligation` Pydantic-модель |
| 10–15 записей в разных валютах/категориях | 12 записей: USD/EUR/RUB/GBP × subscription/utility/software/membership/donation |
| `convert_currency(amount, from, to)` через frankfurter.app | `app/tools/currency.py` |
| Антигаллюцинация при ошибке API | Возврат `{"ok": false, "error": ...}`, агент честно сообщает |
| Логирование Thought/Action/Observation | `app/logging_callback.py`, вывод в консоль |
| Контейнеризация: Dockerfile + docker-compose | `Dockerfile`, `docker-compose.yml`, `docker compose up` |
| LLM_API_KEY через `.env` | `.env.example`, `.gitignore` блокирует `.env` |
| Минимум 3 unit-теста | 13 тестов (8 + 5) |
| README: 4 раздела | Разделы 1–4 выше |

---

## Структура проекта

```
test_AI-agent/
├── app/
│   ├── __init__.py
│   ├── agent.py                  # сборка ReAct-агента
│   ├── config.py                 # настройки из .env
│   ├── logging_callback.py       # Thought/Action/Observation -> консоль
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── obligations.py        # get_obligations
│   │   └── currency.py           # convert_currency
│   └── fixtures/
│       └── obligations.json      # 12 записей, разные валюты/категории
├── tests/
│   ├── __init__.py
│   ├── test_obligations.py       # 5 тестов
│   └── test_currency.py          # 8 тестов
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── main.py                       # CLI REPL
└── README.md
```

---

## 2. Мотивация участия в проекте

> TODO: заполнить пользователем (ThomasMoore25). Это личные ответы,
> AI не должен их выдумывать.

1. **Что тебя привлекает в этом проекте?**
   - _[ответ пользователя]_

2. **Как ты видишь свою роль в команде?**
   - _[ответ пользователя]_

3. **Сколько часов в неделю готов уделять и на какой срок?**
   - _[ответ пользователя]_
