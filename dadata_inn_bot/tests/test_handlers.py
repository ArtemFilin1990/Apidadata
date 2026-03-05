from __future__ import annotations

import unittest
from unittest.mock import AsyncMock

from bot.handlers import _lookup_party


class LookupPartyTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_cached_payload_without_dadata_call(self) -> None:
        cached_payload = {"value": "cached"}
        store = AsyncMock()
        store.get_party.return_value = cached_payload
        dadata = AsyncMock()

        payload, from_cache = await _lookup_party(store, dadata, "7707083893")

        self.assertEqual(payload, cached_payload)
        self.assertTrue(from_cache)
        dadata.find_party.assert_not_awaited()
        store.set_party.assert_not_awaited()

    async def test_fetches_and_caches_payload_on_cache_miss(self) -> None:
        fetched_payload = {"value": "fresh"}
        store = AsyncMock()
        store.get_party.return_value = None
        dadata = AsyncMock()
        dadata.find_party.return_value = fetched_payload

        payload, from_cache = await _lookup_party(store, dadata, "7707083893")

        self.assertEqual(payload, fetched_payload)
        self.assertFalse(from_cache)
        dadata.find_party.assert_awaited_once_with("7707083893")
        store.set_party.assert_awaited_once_with("7707083893", fetched_payload)

    async def test_does_not_cache_when_dadata_returns_none(self) -> None:
        store = AsyncMock()
        store.get_party.return_value = None
        dadata = AsyncMock()
        dadata.find_party.return_value = None

        payload, from_cache = await _lookup_party(store, dadata, "7707083893")

        self.assertIsNone(payload)
        self.assertFalse(from_cache)
        store.set_party.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
