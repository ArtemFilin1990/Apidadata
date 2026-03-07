import unittest

from bot.service import PartyLookupService


class StubStore:
    def __init__(self):
        self.data = {}

    async def get_party(self, inn):
        return self.data.get(inn)

    async def set_party(self, inn, payload):
        self.data[inn] = payload

    async def create_session(self, inn):
        return "sid"

    async def get_party_by_session(self, session_id):
        return self.data.get("7707083893")


class StubDaData:
    async def find_party(self, inn):
        _ = inn
        return None


class StubChecko:
    async def find_party(self, inn):
        return {"_source": "checko", "data": {"inn": inn}}


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_checko_fallback_used_when_dadata_empty(self):
        service = PartyLookupService(store=StubStore(), dadata=StubDaData(), checko=StubChecko())
        payload, from_cache = await service.lookup("7707083893")

        self.assertFalse(from_cache)
        self.assertEqual(payload.get("_source"), "checko")


if __name__ == "__main__":
    unittest.main()
