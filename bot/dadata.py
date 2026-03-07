from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class DadataError(Exception):
    pass


class DadataAuthError(DadataError):
    pass


class DadataRateLimitError(DadataError):
    pass


class SlidingWindowRateLimiter:
    def __init__(self, max_calls: int, period_seconds: float = 1.0) -> None:
        self._max_calls = max_calls
        self._period = period_seconds
        self._timestamps: deque[float] = deque()
        self._lock: asyncio.Lock | None = None

    async def acquire(self) -> None:
        if self._lock is None:
            self._lock = asyncio.Lock()

        while True:
            async with self._lock:
                now = time.monotonic()
                while self._timestamps and now - self._timestamps[0] >= self._period:
                    self._timestamps.popleft()

                if len(self._timestamps) < self._max_calls:
                    self._timestamps.append(now)
                    return

                wait_for = self._period - (now - self._timestamps[0])
            await asyncio.sleep(max(wait_for, 0.01))


@dataclass(slots=True)
class DadataClient:
    api_key: str
    timeout_seconds: float
    rps_limit: int
    max_connections: int
    _client: httpx.AsyncClient = field(init=False, repr=False)
    _limiter: SlidingWindowRateLimiter = field(init=False, repr=False)

    def __post_init__(self) -> None:
        limits = httpx.Limits(
            max_keepalive_connections=min(self.max_connections, 5),
            max_connections=self.max_connections,
        )
        self._client = httpx.AsyncClient(
            base_url="https://suggestions.dadata.ru",
            headers={
                "Authorization": f"Token {self.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=self.timeout_seconds,
            limits=limits,
        )
        self._limiter = SlidingWindowRateLimiter(self.rps_limit)

    async def close(self) -> None:
        await self._client.aclose()

    async def find_party(self, inn: str) -> dict[str, Any] | None:
        last_error: Exception | None = None

        for attempt in range(1, 4):
            await self._limiter.acquire()
            try:
                response = await self._client.post(
                    "/suggestions/api/4_1/rs/findById/party",
                    json={"query": inn},
                )
            except httpx.HTTPError as exc:
                last_error = exc
                logger.warning("DaData request transport error on attempt %s: %s", attempt, exc)
                if attempt < 3:
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                    continue
                raise DadataError("DaData is unavailable") from exc

            if response.status_code in {401, 403}:
                raise DadataAuthError("Invalid DaData credentials or missing access")

            if response.status_code in {429, 500, 502, 503, 504}:
                last_error = DadataRateLimitError(f"DaData temporary error: {response.status_code}")
                logger.warning(
                    "DaData temporary status %s on attempt %s: %s",
                    response.status_code,
                    attempt,
                    response.text,
                )
                if attempt < 3:
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                    continue
                if response.status_code == 429:
                    raise DadataRateLimitError("DaData rate limit exceeded")
                raise DadataError(f"DaData temporary error: {response.status_code}")

            if response.status_code >= 400:
                raise DadataError(f"DaData returned {response.status_code}: {response.text}")

            payload = response.json()
            suggestions = payload.get("suggestions") or []
            if not suggestions:
                return None
            first = suggestions[0]
            if not isinstance(first, dict):
                return None
            first.setdefault("_source", "dadata")
            return first

        if last_error is not None:
            raise DadataError("DaData request failed") from last_error
        return None
