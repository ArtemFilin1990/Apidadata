from __future__ import annotations

import logging
import sys

from dotenv import load_dotenv
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, Defaults

from .cache import SessionStore, create_cache
from .checko import CheckoClient
from .config import get_settings
from .dadata import DadataClient
from .handlers import register_handlers
from .service import PartyLookupService


def main() -> None:
    load_dotenv()
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    cache_backend = create_cache(settings.storage_backend, settings.redis_url, settings.sqlite_path)
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
    checko_client = (
        CheckoClient(
            api_key=settings.checko_api_key,
            base_url=settings.checko_base_url,
            timeout_seconds=settings.request_timeout_seconds,
        )
        if settings.checko_api_key
        else None
    )

    service = PartyLookupService(store=store, dadata=dadata_client, checko=checko_client)

    async def post_shutdown(bot: object) -> None:
        _ = bot
        await dadata_client.close()
        if checko_client is not None:
            await checko_client.close()
        await cache_backend.close()

    application = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .defaults(Defaults(parse_mode=ParseMode.HTML))
        .post_shutdown(post_shutdown)
        .build()
    )
    register_handlers(application, service)

    if settings.run_mode == "polling":
        application.run_polling(
            drop_pending_updates=settings.drop_pending_updates,
            allowed_updates=["message", "callback_query"],
        )
        return

    application.run_webhook(
        listen=settings.host,
        port=settings.port,
        url_path=settings.webhook_path.lstrip("/"),
        webhook_url=f"{settings.webhook_base_url}{settings.webhook_path}",
        drop_pending_updates=settings.drop_pending_updates,
        secret_token=settings.webhook_secret,
        allowed_updates=["message", "callback_query"],
    )


if __name__ == "__main__":
    main()
