import tempfile
import unittest

from bot.cache import SqliteCache, create_cache


class SqliteCacheTests(unittest.IsolatedAsyncioTestCase):
    async def test_sqlite_cache_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SqliteCache(f"{temp_dir}/cache.db")
            await cache.set_json("k", {"v": 1}, ttl_seconds=60)
            self.assertEqual(await cache.get_json("k"), {"v": 1})
            await cache.close()

    async def test_create_cache_sqlite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            backend = create_cache("sqlite", None, f"{temp_dir}/cache.db")
            await backend.set_json("k", {"v": 2}, ttl_seconds=60)
            self.assertEqual(await backend.get_json("k"), {"v": 2})
            await backend.close()


if __name__ == "__main__":
    unittest.main()
