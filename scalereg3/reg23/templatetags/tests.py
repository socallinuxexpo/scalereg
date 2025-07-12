from django.test import TestCase

from .reg23_filters import money


class MoneyFilterTest(TestCase):

    def test_money_filter(self):
        self.assertEqual(money("123.45"), "$123.45")
        self.assertEqual(money("123.4"), "$123.40")
        self.assertEqual(money("123"), "$123.00")
        self.assertEqual(money("0"), "$0.00")

    def test_money_filter_invalid_input(self):
        self.assertEqual(money("invalid"), "invalid")
