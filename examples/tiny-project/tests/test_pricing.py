import unittest
from src.pricing import total_minor


class PricingTests(unittest.TestCase):
    def test_twenty_percent(self):
        self.assertEqual(total_minor(10000, 2000), 12000)

    def test_rejects_negative_and_non_integer(self):
        with self.assertRaises(ValueError):
            total_minor(-1, 2000)
        with self.assertRaises(TypeError):
            total_minor(True, 2000)

    def test_rounding_boundary(self):
        self.assertEqual(total_minor(1, 5000), 2)
        self.assertEqual(total_minor(0, 2000), 0)
