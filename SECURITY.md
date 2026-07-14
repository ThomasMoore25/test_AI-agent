# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | ✅                 |
| < 1.0   | ❌                 |

## Reporting a Vulnerability

Если вы нашли уязвимость, **не создавайте публичный issue**.

Сообщите лично: создайте private security advisory на GitHub
(Settings → Security → Security advisories → New advisory) либо
напишите на email ThomasMoore25@users.noreply.github.com.

**SLA**: ответ в течение 72 часов.

## Известные риски и митигации

| Риск | Митигация |
|------|-----------|
| Утечка `GIGACHAT_API_KEY` через коммит | `.env` в `.gitignore`; ключ передаётся только через env-var |
| Утечка GitHub-токена | Токен не хранится в remote URL; используется одноразово для push |
| MITM при запросах к frankfurter.app / cbr.ru | HTTPS с проверкой сертификатов (по умолчанию) |
| SSL-сертификаты Минцифры РФ для GigaChat | `GIGACHAT_VERIFY_SSL_CERTS=True` в прод, `False` только в dev |
| Галлюцинации LLM (выдуманные курсы) | Структурированные ошибки `{"ok": false, "error": ...}` + промпт-инструкция |

## Best practices для пользователя

1. Никогда не коммитьте `.env`.
2. Используйте отдельный API-ключ для разработки, не production.
3. Периодически ротируйте токены.
4. В прод-окружении включите `GIGACHAT_VERIFY_SSL_CERTS=True` и установите сертификат Минцифры в систему.
