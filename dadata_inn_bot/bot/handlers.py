from __future__ import annotations

import logging
from typing import Any

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from .cache import SessionStore
from .dadata import DadataAuthError, DadataError, DadataRateLimitError
from .dadata import DadataClient
from .formatters import render_section
from .inn import extract_inn, validate_inn
from .keyboards import build_sections_keyboard

logger = logging.getLogger(__name__)


async def _lookup_party(
    store: SessionStore,
    dadata: DadataClient,
    inn: str,
) -> tuple[dict[str, Any] | None, bool]:
    cached = await store.get_party(inn)
    if cached is not None:
        return cached, True

    payload = await dadata.find_party(inn)
    if payload is not None:
        await store.set_party(inn, payload)
    return payload, False


def build_router(store: SessionStore, dadata: DadataClient) -> Router:
    router = Router(name="party_lookup")

    @router.message(CommandStart())
    async def command_start(message: Message) -> None:
        await message.answer(
            "Пришлите ИНН компании или ИП. Я сделаю один запрос в DaData, сохраню ответ в кеш и открою разделы по кнопкам."
        )

    @router.message(F.text)
    async def handle_text(message: Message) -> None:
        text = message.text or ""
        inn = extract_inn(text)
        if inn is None:
            await message.answer("Нужен ИНН: 10 или 12 цифр. Можно просто вставить его сообщением.")
            return

        if not validate_inn(inn):
            await message.answer("ИНН выглядит битым: контрольные цифры не сходятся.")
            return

        try:
            payload, from_cache = await _lookup_party(store, dadata, inn)
        except DadataAuthError:
            await message.answer("DaData не пустила по ключу или тарифу. Проверьте DADATA_API_KEY и доступ к findById/party.")
            return
        except DadataRateLimitError:
            await message.answer("DaData режет лимит. Повторите через несколько секунд.")
            return
        except DadataError as exc:
            logger.exception("DaData error while handling INN %s", inn)
            await message.answer(f"Запрос в DaData не прошёл: {exc}")
            return

        if payload is None:
            await message.answer("По этому ИНН ничего не найдено.")
            return

        session_id = await store.create_session(inn)
        prefix = "[кеш]\n" if from_cache else ""
        await message.answer(
            prefix + render_section(payload, "main"),
            reply_markup=build_sections_keyboard(session_id),
            disable_web_page_preview=True,
        )

    @router.callback_query(F.data.startswith("s:"))
    async def handle_callback(callback: CallbackQuery) -> None:
        data = callback.data or ""
        parts = data.split(":", 2)
        if len(parts) != 3:
            await callback.answer("Некорректная кнопка.", show_alert=True)
            return

        _, session_id, section = parts
        payload = await store.get_party_by_session(session_id)
        if payload is None:
            await callback.answer("Сессия устарела. Пришлите ИНН ещё раз.", show_alert=True)
            return

        try:
            if callback.message is None:
                await callback.answer("Сообщение недоступно.", show_alert=True)
                return
            await callback.message.edit_text(
                render_section(payload, section),
                reply_markup=build_sections_keyboard(session_id),
                disable_web_page_preview=True,
            )
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc).lower():
                logger.exception("Failed to edit Telegram message")
                await callback.answer("Не смог обновить сообщение.", show_alert=True)
                return
        await callback.answer()

    return router
