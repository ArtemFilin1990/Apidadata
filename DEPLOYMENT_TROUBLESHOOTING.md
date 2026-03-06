# Deployment troubleshooting (Amvera)

## Симптом: приложение падает при старте с ошибкой

```text
RuntimeError: WEBHOOK_BASE_URL must start with https://
```

Причина: в `WEBHOOK_BASE_URL` передано пустое значение, `http://...` или неполный URL без корректного HTTPS-схемы.

### Как исправить

1. В Amvera откройте **Environment variables**.
2. Проверьте, что `WEBHOOK_BASE_URL` задан полностью и начинается с `https://`.

Пример:

```env
WEBHOOK_BASE_URL=https://api.example.ru
```

3. Проверьте `WEBHOOK_PATH` — должен начинаться с `/` (по умолчанию `/telegram/webhook`).
4. Проверьте `TELEGRAM_WEBHOOK_SECRET` — минимум 16 символов.
5. Проверьте обязательные переменные:
   - `BOT_TOKEN`
   - `DADATA_API_KEY`
   - `WEBHOOK_BASE_URL`
   - `TELEGRAM_WEBHOOK_SECRET`

> Примечание: в текущей версии репозитория используется только `DADATA_API_KEY`. Если в вашей форк-версии добавлен `DADATA_SECRET_KEY`, задайте и его.

## Структура репозитория при деплое из архива

Код должен лежать в корне проекта Amvera. Внутри рабочей директории должны быть `Dockerfile`, `requirements.txt`, `amvera.yml`, папка `bot/` и остальные файлы проекта.

Неправильно:

```text
/app/Apidadata-main/Dockerfile
```

Правильно:

```text
/app/Dockerfile
/app/requirements.txt
/app/amvera.yml
/app/bot/...
```

Если архив разворачивается с дополнительной верхней папкой, перепакуйте архив так, чтобы файлы проекта были сразу в корне.

## Пересоздание webhook после исправления ENV

После исправления переменных:

1. Удалите старый webhook:

```text
https://api.telegram.org/bot<TOKEN>/deleteWebhook
```

2. Дайте приложению перезапуститься.
3. Проверьте, что приложение отвечает на `GET /health`.
4. Убедитесь, что в логах есть успешная установка webhook без ошибок валидации.

## Быстрая самопроверка перед деплоем

1. Скопируйте `.env.example` в `.env`.
2. Заполните обязательные значения.
3. Запустите локально:

```bash
python -m bot.main
```

4. Если старт не удался — проверьте текст исключения: он укажет, какая переменная заполнена неверно.
