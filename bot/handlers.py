from __future__ import annotations

import logging

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .dadata import DadataAuthError, DadataError, DadataRateLimitError
from .formatters import render_section
from .inn import extract_inn, validate_inn
from .keyboards import build_sections_keyboard
from .service import PartyLookupService

logger = logging.getLogger(__name__)


async def command_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        "Пришлите ИНН компании или ИП. Я сделаю один запрос в DaData, сохраню ответ в кеш и открою разделы по кнопкам."
    )


async def handle_text(update: Update, _: ContextTypes.DEFAULT_TYPE, service: PartyLookupService) -> None:
    if update.message is None:
        return

    text = update.message.text or ""
    inn = extract_inn(text)
    if inn is None:
        await update.message.reply_text("Нужен ИНН: 10 или 12 цифр. Можно просто вставить его сообщением.")
        return

    if not validate_inn(inn):
        await update.message.reply_text("ИНН выглядит битым: контрольные цифры не сходятся.")
        return

    try:
        payload, from_cache = await service.lookup(inn)
    except DadataAuthError:
        await update.message.reply_text(
            "DaData не пустила по ключу или тарифу. Проверьте DADATA_API_KEY и доступ к findById/party."
        )
        return
    except DadataRateLimitError:
        await update.message.reply_text("DaData режет лимит. Повторите через несколько секунд.")
        return
    except DadataError as exc:
        logger.exception("DaData error while handling INN %s", inn)
        await update.message.reply_text(f"Запрос в DaData не прошёл: {exc}")
        return

    if payload is None:
        await update.message.reply_text("По этому ИНН ничего не найдено.")
        return

    session_id = await service.create_session(inn)
    prefix = "[кеш]\n" if from_cache else ""
    await update.message.reply_text(
        prefix + render_section(payload, "main"),
        reply_markup=build_sections_keyboard(session_id),
        disable_web_page_preview=True,
    )


async def handle_callback(update: Update, _: ContextTypes.DEFAULT_TYPE, service: PartyLookupService) -> None:
    query = update.callback_query
    if query is None:
        return

    data = query.data or ""
    parts = data.split(":", 2)
    if len(parts) != 3:
        await query.answer("Некорректная кнопка.", show_alert=True)
        return

    _, session_id, section = parts
    payload = await service.get_by_session(session_id)
    if payload is None:
        await query.answer("Сессия устарела. Пришлите ИНН ещё раз.", show_alert=True)
        return

    try:
        if query.message is None:
            await query.answer("Сообщение недоступно.", show_alert=True)
            return
        await query.edit_message_text(
            render_section(payload, section),
            reply_markup=build_sections_keyboard(session_id),
            disable_web_page_preview=True,
        )
    except BadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            logger.exception("Failed to edit Telegram message")
            await query.answer("Не смог обновить сообщение.", show_alert=True)
            return
    await query.answer()


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled Telegram update error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message is not None:
        await update.effective_message.reply_text("Внутренняя ошибка. Попробуйте ещё раз через минуту.")


def register_handlers(application: Application, service: PartyLookupService) -> None:
    async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await handle_text(update, context, service)

    async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await handle_callback(update, context, service)

    application.add_handler(CommandHandler("start", command_start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_handler(CallbackQueryHandler(callback_handler, pattern=r"^s:"))
    application.add_error_handler(error_handler)
