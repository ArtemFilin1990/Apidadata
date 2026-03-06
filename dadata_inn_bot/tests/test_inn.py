import unittest

from bot.inn import extract_inn, validate_inn


class InnTests(unittest.TestCase):
    def test_extract_prefers_12_digit(self):
        self.assertEqual(extract_inn("ИНН 7707083893 и 500100732259"), "500100732259")

    def test_extract_10_digit_when_no_12_digit(self):
        self.assertEqual(extract_inn("компания 7707083893"), "7707083893")

    def test_validate_known_good_values(self):
        self.assertTrue(validate_inn("7707083893"))
        self.assertTrue(validate_inn("500100732259"))

    def test_validate_bad_values(self):
        self.assertFalse(validate_inn("7707083894"))
        self.assertFalse(validate_inn("500100732250"))
        self.assertFalse(validate_inn("123"))
        self.assertFalse(validate_inn("not-an-inn"))


if __name__ == "__main__":
    unittest.main()
