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
        os.environ["TELEGRAM_WEBHOOK_SECRET"] = "x" * 16
        os.environ["WEBHOOK_PATH"] = "/telegram/webhook"

    def test_settings_success(self):
        self._set_minimal_env()
        os.environ["WEBHOOK_BASE_URL"] = "https://example.com"

        settings = config.get_settings()

        self.assertEqual(settings.webhook_base_url, "https://example.com")
        self.assertEqual(settings.webhook_path, "/telegram/webhook")
        self.assertEqual(settings.port, 80)

    def test_invalid_webhook_scheme(self):
        self._set_minimal_env()
        os.environ["WEBHOOK_BASE_URL"] = "http://example.com"

        with self.assertRaisesRegex(RuntimeError, "https://"):
            config.get_settings()

    def test_invalid_short_secret(self):
        os.environ["BOT_TOKEN"] = "token"
        os.environ["DADATA_API_KEY"] = "key"
        os.environ["WEBHOOK_BASE_URL"] = "https://example.com"
        os.environ["TELEGRAM_WEBHOOK_SECRET"] = "short"

        with self.assertRaisesRegex(RuntimeError, "at least 16"):
            config.get_settings()


if __name__ == "__main__":
    unittest.main()
