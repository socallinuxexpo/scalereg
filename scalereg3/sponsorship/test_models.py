from django.test import TestCase

from .models import Item
from .models import Package


class PackageCostTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.package = Package.objects.create(name='P1',
                                             description='P1',
                                             price=10,
                                             public=True)
        cls.item1 = Item.objects.create(name='I1',
                                        description='Item 1',
                                        price=17,
                                        active=True,
                                        promo=False,
                                        package_offset=False,
                                        applies_to_all=True)
        cls.item2 = Item.objects.create(name='I2',
                                        description='Item 2',
                                        price=6,
                                        active=True,
                                        promo=False,
                                        package_offset=False,
                                        applies_to_all=True)
        cls.item3 = Item.objects.create(name='I3',
                                        description='Package offset 1',
                                        price=14,
                                        active=True,
                                        promo=False,
                                        package_offset=True,
                                        applies_to_all=True)
        cls.item4 = Item.objects.create(name='I4',
                                        description='Package offset 1',
                                        price=19,
                                        active=True,
                                        promo=False,
                                        package_offset=True,
                                        applies_to_all=True)

    def test_no_items(self):
        cost = self.package.package_cost([])
        self.assertEqual(cost, 10)

    def test_single_item(self):
        cost = self.package.package_cost([self.item1])
        self.assertEqual(cost, 27)

    def test_multiple_items(self):
        cost = self.package.package_cost([self.item1, self.item2])
        self.assertEqual(cost, 33)

    def test_with_package_offset_item(self):
        cost = self.package.package_cost([self.item3])
        self.assertEqual(cost, 14)

    def test_with_two_package_offset_items(self):
        cost = self.package.package_cost([self.item3, self.item4])
        self.assertEqual(cost, 33)

    def test_with_regular_item_and_package_offset_item(self):
        cost = self.package.package_cost([self.item2, self.item3])
        self.assertEqual(cost, 20)
