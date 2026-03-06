from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from secrets import token_hex
from typing import Any, Protocol

import redis.asyncio as redis


class CacheBackend(Protocol):
    async def get_json(self, key: str) -> Any | None: ...
    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None: ...
    async def close(self) -> None: ...


class MemoryCache:
    def __init__(self) -> None:
        self._items: dict[str, tuple[float, Any]] = {}
        self._lock: asyncio.Lock | None = None

    @property
    def lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def get_json(self, key: str) -> Any | None:
        async with self.lock:
            entry = self._items.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at <= time.monotonic():
                self._items.pop(key, None)
                return None
            return value

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        async with self.lock:
            self._items[key] = (time.monotonic() + ttl_seconds, value)

    async def close(self) -> None:
        return None


class RedisCache:
    def __init__(self, url: str) -> None:
        self._redis = redis.from_url(url, encoding="utf-8", decode_responses=True)

    async def get_json(self, key: str) -> Any | None:
        raw = await self._redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        await self._redis.set(key, json.dumps(value, ensure_ascii=False), ex=ttl_seconds)

    async def close(self) -> None:
        await self._redis.aclose()


@dataclass(slots=True)
class SessionStore:
    backend: CacheBackend
    payload_ttl: int
    session_ttl: int

    def _party_key(self, inn: str) -> str:
        return f"party:{inn}"

    def _session_key(self, session_id: str) -> str:
        return f"session:{session_id}"

    async def get_party(self, inn: str) -> dict[str, Any] | None:
        value = await self.backend.get_json(self._party_key(inn))
        return value if isinstance(value, dict) else None

    async def set_party(self, inn: str, payload: dict[str, Any]) -> None:
        await self.backend.set_json(self._party_key(inn), payload, self.payload_ttl)

    async def create_session(self, inn: str) -> str:
        session_id = token_hex(6)
        await self.backend.set_json(self._session_key(session_id), {"inn": inn}, self.session_ttl)
        return session_id

    async def resolve_inn(self, session_id: str) -> str | None:
        row = await self.backend.get_json(self._session_key(session_id))
        if not isinstance(row, dict):
            return None
        inn = row.get("inn")
        if not isinstance(inn, str) or not inn:
            return None
        await self.backend.set_json(self._session_key(session_id), {"inn": inn}, self.session_ttl)
        return inn

    async def get_party_by_session(self, session_id: str) -> dict[str, Any] | None:
        inn = await self.resolve_inn(session_id)
        if inn is None:
            return None
        return await self.get_party(inn)


def create_cache(redis_url: str | None) -> CacheBackend:
    if redis_url:
        return RedisCache(redis_url)
    return MemoryCache()
