# Dadata + Checko Telegram Bot (Render/Replit ready)

Production-oriented Telegram bot for counterparty checks by INN.

## What works now

- DaData `findById/party` lookup by INN (single API call per uncached INN).
- Optional fallback to Checko (`/company`, `/entrepreneur`, `/person`) when DaData returns no data.
- Reply + inline menu sections: `Реквизиты`, `Финансы`, `Налоги`, `Проверки`, `Арбитраж`, `Риски`, `Лица`, `Контакты`, `Лицензии`.
- Runtime modes:
  - `webhook` (Render/Amvera)
  - `polling` (Replit/local)
- Storage backends:
  - `memory`
  - `redis`
  - `sqlite` (default; file `.data/bot-storage.db`)

## DaData Max / Clean API notes

- This bot uses **DaData Suggestions API** (`findById/party`) for subscription traffic.
- **Clean API methods are pay-per-request and not included in subscription tariff plans**.
- If you enable Clean API in future revisions, keep it strictly server-side (`X-Secret`), with explicit feature flags and budget monitoring.

## Quick start (local/Replit)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

For Replit/local polling mode set in `.env`:

```env
RUN_MODE=polling
STORAGE_BACKEND=sqlite
```

Then start:

```bash
python -m bot.main
```

## Render webhook deploy

1. Set `RUN_MODE=webhook`.
2. Provide:
   - `WEBHOOK_BASE_URL=https://<your-service>.onrender.com`
   - `TELEGRAM_WEBHOOK_SECRET` (>=16 chars)
3. Ensure service listens on `0.0.0.0:$PORT`.
4. Deploy via existing `Dockerfile`.

## Required environment variables

Always required:

- `BOT_TOKEN`
- `DADATA_API_KEY`
- `RUN_MODE` (`webhook|polling`)

Webhook-only required:

- `WEBHOOK_BASE_URL`
- `TELEGRAM_WEBHOOK_SECRET`

Optional:

- `STORAGE_BACKEND=memory|redis|sqlite`
- `REDIS_URL` (required when `STORAGE_BACKEND=redis`)
- `SQLITE_PATH` (default `.data/bot-storage.db`)
- `CHECKO_API_KEY`
- `CHECKO_BASE_URL`
- `CACHE_TTL_SECONDS`, `SESSION_TTL_SECONDS`, `DADATA_RPS_LIMIT`, `DADATA_MAX_CONNECTIONS`, `REQUEST_TIMEOUT_SECONDS`

## Safety and caveats

- Never commit tokens/keys.
- If both DaData and Checko return empty: user gets a clear “not found” response.
- For organization checks, INN validation is strict (control digits).
- Fallback data from Checko is normalized to bot section format; some extended section fields may stay empty when source data does not provide them.
