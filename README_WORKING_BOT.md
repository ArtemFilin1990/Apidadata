# README_WORKING_BOT

This repository contains the working Telegram bot package aligned with the delivered `Dadata-Bot-working.zip` scope:

- Telegram bot with section-based menu
- DaData primary source
- Checko fallback source
- Polling mode for Replit
- Webhook mode for Render/Amvera
- Local persistent storage via SQLite (`.data/bot-storage.db`)

## Run

```bash
pip install -r requirements.txt
cp .env.example .env
python -m bot.main
```

Use `RUN_MODE=polling` for Replit.
