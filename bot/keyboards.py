from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def build_sections_keyboard(session_id: str) -> InlineKeyboardMarkup:
    def button(text: str, section: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=text, callback_data=f"s:{session_id}:{section}")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [button("Карточка", "main"), button("Оборот", "revenue")],
            [button("Долги", "debt"), button("Штрафы", "penalty")],
            [button("Суды", "court"), button("Риски", "risks")],
            [button("Лица", "people"), button("Контакты", "contacts")],
            [button("Лицензии", "licenses")],
        ]
    )
