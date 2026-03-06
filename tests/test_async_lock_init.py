import unittest

from bot.cache import MemoryCache
from bot.dadata import SlidingWindowRateLimiter


class AsyncLockInitializationTests(unittest.IsolatedAsyncioTestCase):
    async def test_memory_cache_lock_is_lazy(self):
        cache = MemoryCache()
        self.assertIsNone(cache._lock)

        await cache.set_json("k", {"v": 1}, ttl_seconds=60)

        self.assertIsNotNone(cache._lock)
        self.assertEqual(await cache.get_json("k"), {"v": 1})

    async def test_rate_limiter_lock_is_lazy(self):
        limiter = SlidingWindowRateLimiter(max_calls=1)
        self.assertIsNone(limiter._lock)

        await limiter.acquire()

        self.assertIsNotNone(limiter._lock)


if __name__ == "__main__":
    unittest.main()
