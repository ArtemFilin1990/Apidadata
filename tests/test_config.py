import os
import unittest

from bot import config


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self._saved_env = os.environ.copy()
        config.get_settings.cache_clear()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._saved_env)
        config.get_settings.cache_clear()

    def _set_minimal_env(self):
        os.environ["BOT_TOKEN"] = "token"
        os.environ["DADATA_API_KEY"] = "key"

    def test_settings_success_webhook(self):
        self._set_minimal_env()
        os.environ["RUN_MODE"] = "webhook"
        os.environ["WEBHOOK_BASE_URL"] = "https://example.com"
        os.environ["TELEGRAM_WEBHOOK_SECRET"] = "x" * 16
        os.environ["WEBHOOK_PATH"] = "/telegram/webhook"

        settings = config.get_settings()

        self.assertEqual(settings.webhook_base_url, "https://example.com")
        self.assertEqual(settings.webhook_path, "/telegram/webhook")
        self.assertEqual(settings.port, 80)

    def test_settings_success_polling_without_webhook_env(self):
        self._set_minimal_env()
        os.environ["RUN_MODE"] = "polling"

        settings = config.get_settings()

        self.assertEqual(settings.run_mode, "polling")
        self.assertIsNone(settings.webhook_base_url)
        self.assertIsNone(settings.webhook_secret)


    def test_default_storage_backend_is_sqlite(self):
        self._set_minimal_env()
        os.environ["RUN_MODE"] = "polling"

        settings = config.get_settings()

        self.assertEqual(settings.storage_backend, "sqlite")

    def test_redis_backend_requires_redis_url(self):
        self._set_minimal_env()
        os.environ["RUN_MODE"] = "polling"
        os.environ["STORAGE_BACKEND"] = "redis"

        with self.assertRaisesRegex(RuntimeError, "REDIS_URL"):
            config.get_settings()

    def test_invalid_webhook_scheme(self):
        self._set_minimal_env()
        os.environ["RUN_MODE"] = "webhook"
        os.environ["WEBHOOK_BASE_URL"] = "http://example.com"
        os.environ["TELEGRAM_WEBHOOK_SECRET"] = "x" * 16

        with self.assertRaisesRegex(RuntimeError, "https://"):
            config.get_settings()

    def test_invalid_short_secret(self):
        self._set_minimal_env()
        os.environ["RUN_MODE"] = "webhook"
        os.environ["WEBHOOK_BASE_URL"] = "https://example.com"
        os.environ["TELEGRAM_WEBHOOK_SECRET"] = "short"

        with self.assertRaisesRegex(RuntimeError, "at least 16"):
            config.get_settings()


if __name__ == "__main__":
    unittest.main()
