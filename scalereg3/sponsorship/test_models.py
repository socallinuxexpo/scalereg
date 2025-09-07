import decimal

from django.test import TestCase

from .models import Item
from .models import Package
from .models import PromoCode
from .models import Sponsor


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
        cost = self.package.package_cost([], None)
        self.assertEqual(cost, 10)

    def test_single_item(self):
        cost = self.package.package_cost([self.item1], None)
        self.assertEqual(cost, 27)

    def test_multiple_items(self):
        cost = self.package.package_cost([self.item1, self.item2], None)
        self.assertEqual(cost, 33)

    def test_with_package_offset_item(self):
        cost = self.package.package_cost([self.item3], None)
        self.assertEqual(cost, 14)

    def test_with_two_package_offset_items(self):
        cost = self.package.package_cost([self.item3, self.item4], None)
        self.assertEqual(cost, 33)

    def test_with_regular_item_and_package_offset_item(self):
        cost = self.package.package_cost([self.item2, self.item3], None)
        self.assertEqual(cost, 20)


class SponsorTicketCostTest(TestCase):

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
        cls.promo_package = PromoCode.objects.create(
            name='DISC50',
            description='50% off package',
            price_modifier=decimal.Decimal('0.50'),
            active=True,
            applies_to_all=False)
        cls.promo_package.applies_to.add(cls.package)
        cls.promo_item = PromoCode.objects.create(
            name='ITEM25',
            description='25% off promo items',
            price_modifier=decimal.Decimal('0.75'),
            active=True,
            applies_to_all=True)
        cls.item_promo_eligible = Item.objects.create(
            name='IPE',
            description='Item Promo Eligible',
            price=20,
            active=True,
            promo=True,
            package_offset=False,
            applies_to_all=True)

        cls.sponsor = Sponsor.objects.create(package=cls.package,
                                             first_name='John',
                                             last_name='Doe',
                                             org='Example Org',
                                             email='john.doe@example.com',
                                             zip_code='12345')

    def test_cost_no_items(self):
        self.assertEqual(self.sponsor.package_cost(), 10)
        # Make sure there are no side effects in the previous call.
        self.assertEqual(self.sponsor.package_cost(), 10)

    def test_cost_with_items(self):
        self.sponsor.ordered_items.add(self.item1, self.item2)
        self.assertEqual(self.sponsor.package_cost(), 33)
        # Make sure there are no side effects in the previous call.
        self.assertEqual(self.sponsor.package_cost(), 33)

    def test_cost_with_package_offset_item(self):
        item_offset = Item.objects.create(name='IO1',
                                          description='Offset Item',
                                          price=50,
                                          active=True,
                                          promo=False,
                                          package_offset=True,
                                          applies_to_all=True)
        self.sponsor.ordered_items.add(item_offset)
        self.assertEqual(self.sponsor.package_cost(), 50)
        # Make sure there are no side effects in the previous call.
        self.assertEqual(self.sponsor.package_cost(), 50)

    def test_cost_with_package_promo(self):
        self.sponsor.promo = self.promo_package
        self.sponsor.save()
        self.assertEqual(self.sponsor.package_cost(), 5)  # 10 * 0.5 = 5

    def test_cost_with_item_promo(self):
        self.sponsor.promo = self.promo_item
        self.sponsor.ordered_items.add(self.item_promo_eligible)
        self.sponsor.save()
        # package price (10 * 0.75 = 7.50) + item price (20 * 0.75 = 15) = 22.50
        self.assertEqual(self.sponsor.package_cost(), decimal.Decimal('22.50'))

    def test_cost_with_package_and_item_promo_eligible(self):
        self.sponsor.promo = self.promo_item
        self.sponsor.ordered_items.add(self.item1, self.item_promo_eligible)
        self.sponsor.save()
        # package price (10 * 0.75 = 7.50) + item1 (17) +
        # item_promo_eligible (20 * 0.75 = 15) = 39.50
        self.assertEqual(self.sponsor.package_cost(), decimal.Decimal('39.50'))

    def test_cost_with_package_offset_and_item_promo(self):
        self.sponsor.promo = self.promo_item
        item_offset = Item.objects.create(name='IO1',
                                          description='Offset Item',
                                          price=50,
                                          active=True,
                                          promo=False,
                                          package_offset=True,
                                          applies_to_all=True)
        self.sponsor.ordered_items.add(item_offset, self.item_promo_eligible)
        self.sponsor.save()
        # package offset item (50) + item_promo_eligible (20 * 0.75 = 15) = 65
        self.assertEqual(self.sponsor.package_cost(), 65)

    def test_cost_with_package_promo_and_item_promo_eligible(self):
        self.sponsor.promo = self.promo_package
        self.sponsor.ordered_items.add(self.item_promo_eligible)
        self.sponsor.save()
        # package price (10 * 0.5 = 5) + item_promo_eligible (20 * 0.5 = 10) = 15
        self.assertEqual(self.sponsor.package_cost(), decimal.Decimal('15.00'))

    def test_cost_with_package_promo_and_item_not_promo_eligible(self):
        self.sponsor.promo = self.promo_package
        self.sponsor.ordered_items.add(self.item1)
        self.sponsor.save()
        # package price (10 * 0.5 = 5) + item1 (17) = 22
        self.assertEqual(self.sponsor.package_cost(), 22)
