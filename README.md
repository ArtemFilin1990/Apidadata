# Telegram-бот проверки контрагента по ИНН на DaData

Это каркас под прод, без внешних источников кроме DaData:

- один запрос `findById/party` на ИНН;
- кеш ответа по ИНН;
- inline-разделы без повторных вызовов API;
- webhook с `secret_token` через python-telegram-bot;
- деплой через Docker на Amvera.

## Что умеет

После ввода ИНН бот:

1. валидирует формат и контрольные цифры;
2. проверяет кеш;
3. при промахе делает `POST /suggestions/api/4_1/rs/findById/party`;
4. сохраняет результат в кеш;
5. показывает карточку и inline-кнопки:
   - Карточка
   - Оборот
   - Долги
   - Штрафы
   - Суды
   - Риски
   - Лица
   - Контакты
   - Лицензии

## Важная оговорка по кнопке «Суды»

Раздел `Суды` в этом проекте показывает только те судебные решения, которые DaData вернула в признаках недостоверности по адресу, руководителям или учредителям. Это не полный реестр арбитражных дел.

## До запуска

1. Перевыпустите токен бота в `@BotFather`. Если токен уже светился в URL, считать его действующим нельзя.
2. Заполните `.env` на основе `.env.example`.
3. Убедитесь, что на тарифе DaData доступен `findById/party` и нужные расширенные поля.

## Переменные окружения

Обязательные:

- `BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET (минимум 16 символов)`
- `WEBHOOK_BASE_URL`
- `DADATA_API_KEY`

Опциональные:

- `WEBHOOK_PATH=/telegram/webhook`
- `CACHE_TTL_SECONDS=21600`
- `SESSION_TTL_SECONDS=7200`
- `DADATA_RPS_LIMIT=8`
- `DADATA_MAX_CONNECTIONS=10`
- `REQUEST_TIMEOUT_SECONDS=10`
- `REDIS_URL=`
- `PORT=80`
- `DROP_PENDING_UPDATES=false`

Если `REDIS_URL` не задан, бот использует память процесса. Для прода лучше Redis, иначе после рестарта кеш и активные сессии пропадут.

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m bot.main
```

Для локальной проверки webhook нужен внешний HTTPS URL, например через туннель или обратный прокси.

## Docker

```bash
docker build -t dadata-inn-bot .
docker run --env-file .env -p 80:80 dadata-inn-bot
```

## Деплой на Amvera

В проекте уже есть `Dockerfile` и `amvera.yml`.

### Вариант 1: использовать текущий git-репозиторий

```bash
git status
git add .
git commit -m "Prepare deploy"
git remote add amvera https://git.amvera.ru/<username>/<project-name>
git push amvera master
```

### Вариант 2: использовать выделенный репозиторий Amvera

```bash
git clone https://git.amvera.ru/<username>/<project-name>
cd <project-name>
# Скопируйте сюда файлы проекта (Dockerfile, requirements.txt, amvera.yml, папку bot/)
git add .
git commit -m "Initial deploy"
git remote add amvera https://git.amvera.ru/<username>/<project-name>
git push amvera master
```

После push Amvera автоматически запускает сборку и деплой.

Дальше:

1. Добавить секреты из `.env.example` во вкладке переменных окружения.
2. Убедиться, что публичный URL проекта совпадает с `WEBHOOK_BASE_URL`.
3. Проверить в логах успешную установку webhook и отправить /start боту для smoke-теста.
4. Если процесс слушает `localhost`, заменить host на `0.0.0.0` (в этом проекте уже используется `0.0.0.0`).
5. При проблемах смотреть build/runtime-логи в Amvera (логи могут появляться с задержкой).

Если деплой на Amvera падает на старте из-за конфигурации (`WEBHOOK_BASE_URL`, секрет вебхука, структура архива), см. подробный чеклист: [DEPLOYMENT_TROUBLESHOOTING.md](DEPLOYMENT_TROUBLESHOOTING.md).

## Что стоит докрутить после запуска

- Redis как обязательный backend для кеша.
- метрики и алерты по 429/5xx;
- отдельный мониторинг остатка лимита DaData через `api/v2/stat/daily`;
- журнал запросов без хранения персональных данных дольше необходимого;
- fallback-команду администратора для чтения `getWebhookInfo` после ротации токена.

## Структура проекта

```text
bot/
  config.py      # env и настройки
  cache.py       # memory/redis кеш и сессии
  dadata.py      # клиент DaData + rate limit + retries
  formatters.py  # сборка карточек и секций
  handlers.py    # Telegram handlers
  inn.py         # извлечение и проверка ИНН
  keyboards.py   # inline-кнопки
  main.py        # python-telegram-bot webhook app
```

