from __future__ import annotations

import logging
import sys

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv

from .cache import SessionStore, create_cache
from .config import get_settings
from .dadata import DadataClient
from .handlers import build_router
from .service import PartyLookupService


async def healthcheck(_: web.Request) -> web.Response:
    return web.json_response({"ok": True})


def main() -> None:
    load_dotenv()
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    cache_backend = create_cache(settings.redis_url)
    store = SessionStore(
        backend=cache_backend,
        payload_ttl=settings.cache_ttl_seconds,
        session_ttl=settings.session_ttl_seconds,
    )
    dadata_client = DadataClient(
        api_key=settings.dadata_api_key,
        timeout_seconds=settings.request_timeout_seconds,
        rps_limit=settings.dadata_rps_limit,
        max_connections=settings.max_connections,
    )
    service = PartyLookupService(store=store, dadata=dadata_client)

    dp = Dispatcher()
    dp.include_router(build_router(service))

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    async def on_startup(bot: Bot) -> None:
        await bot.set_webhook(
            url=f"{settings.webhook_base_url}{settings.webhook_path}",
            secret_token=settings.webhook_secret,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=settings.drop_pending_updates,
        )
        logging.getLogger(__name__).info(
            "Webhook configured at %s%s",
            settings.webhook_base_url,
            settings.webhook_path,
        )

    async def on_shutdown(_: Bot) -> None:
        await dadata_client.close()
        await cache_backend.close()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    app.router.add_get("/health", healthcheck)

    request_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret,
    )
    request_handler.register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
