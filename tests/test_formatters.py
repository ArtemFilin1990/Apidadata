import unittest

from bot.formatters import _date_ms


class FormatterDateTests(unittest.TestCase):
    def test_date_ms_formats_valid_epoch_milliseconds(self):
        self.assertEqual(_date_ms(1704067200000), "01.01.2024")

    def test_date_ms_returns_original_value_for_out_of_range_timestamp(self):
        self.assertEqual(_date_ms(10**30), str(10**30))


if __name__ == "__main__":
    unittest.main()
