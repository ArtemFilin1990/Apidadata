from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .cache import SessionStore
from .dadata import DadataClient


@dataclass(slots=True)
class PartyLookupService:
    store: SessionStore
    dadata: DadataClient

    async def lookup(self, inn: str) -> tuple[dict[str, Any] | None, bool]:
        cached = await self.store.get_party(inn)
        if cached is not None:
            return cached, True

        payload = await self.dadata.find_party(inn)
        if payload is not None:
            await self.store.set_party(inn, payload)
        return payload, False

    async def create_session(self, inn: str) -> str:
        return await self.store.create_session(inn)

    async def get_by_session(self, session_id: str) -> dict[str, Any] | None:
        return await self.store.get_party_by_session(session_id)
