import datetime
import decimal
import random

from django.test import TestCase

from .models import Item
from .models import Order
from .models import Package
from .models import PendingOrder
from .models import PromoCode
from .models import Sponsor


class IndexTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        today = datetime.date.today()
        day = datetime.timedelta(days=1)
        Package.objects.create(name='P1',
                               description='P1 gold',
                               price=10,
                               public=True,
                               start_date=today - day,
                               end_date=today + day)
        Package.objects.create(name='P2',
                               description='P2 silver',
                               price=5.25,
                               public=True)
        Package.objects.create(name='P3',
                               description='P3 unobtanium',
                               price=0,
                               public=False)
        Package.objects.create(name='P4',
                               description='P4 past',
                               price=4.00,
                               public=True,
                               end_date=today)
        Package.objects.create(name='P5',
                               description='P5 future',
                               price=6.00,
                               public=True,
                               start_date=today + day)

    def test_package_names(self):
        response = self.client.get('/sponsorship/')
        self.assertContains(
            response,
            '<input type="radio" name="package" id="package_P1" value="P1" />',
            count=1,
            html=True)
        self.assertContains(
            response,
            '<input type="radio" name="package" id="package_P2" value="P2" />',
            count=1,
            html=True)
        self.assertNotContains(
            response,
            '<input type="radio" name="package" id="package_P3" value="P3" />',
            html=True)
        self.assertNotContains(
            response,
            '<input type="radio" name="package" id="package_P4" value="P4" />',
            html=True)
        self.assertNotContains(
            response,
            '<input type="radio" name="package" id="package_P5" value="P5" />',
            html=True)

    def test_package_descriptions(self):
        response = self.client.get('/sponsorship/')
        self.assertContains(response,
                            '<td><label for="package_P1">P1 gold</label></td>',
                            count=1,
                            html=True)
        self.assertContains(
            response,
            '<td><label for="package_P2">P2 silver</label></td>',
            count=1,
            html=True)
        self.assertNotContains(
            response,
            '<td><label for="package_P3">P3 unobtanium</label></td>',
            html=True)
        self.assertNotContains(
            response,
            '<td><label for="package_P4">P4 past</label></td>',
            html=True)
        self.assertNotContains(
            response,
            '<td><label for="package_P5">P5 future</label></td>',
            html=True)

    def test_package_prices(self):
        response = self.client.get('/sponsorship/')
        self.assertContains(response,
                            '<td><label for="package_P1">$10.00</label></td>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<td><label for="package_P2">$5.25</label></td>',
                            count=1,
                            html=True)
        self.assertNotContains(
            response,
            '<td><label for="package_P3">$0.00</label></td>',
            html=True)
        self.assertNotContains(
            response,
            '<td><label for="package_P4">$4.00</label></td>',
            html=True)
        self.assertNotContains(
            response,
            '<td><label for="package_P5">$6.00</label></td>',
            html=True)


class IndexTestWithPromo(TestCase):

    @classmethod
    def setUpTestData(cls):
        today = datetime.date.today()
        day = datetime.timedelta(days=1)
        Package.objects.create(name='PK1',
                               description='PK1 gold',
                               price=10,
                               public=True,
                               start_date=today - day,
                               end_date=today + day)
        package2_silver = Package.objects.create(name='PK2',
                                                 description='PK2 silver',
                                                 price=5.25,
                                                 public=True)
        PromoCode.objects.create(name='P1',
                                 description='P1 all',
                                 price_modifier=0.5,
                                 active=True,
                                 applies_to_all=True)
        PromoCode.objects.create(name='P2',
                                 description='P2 inactive',
                                 price_modifier=0.5,
                                 active=False,
                                 applies_to_all=True)
        PromoCode.objects.create(name='P3',
                                 description='P3 past',
                                 price_modifier=0.5,
                                 active=True,
                                 end_date=today,
                                 applies_to_all=True)
        PromoCode.objects.create(name='P4',
                                 description='P4 future',
                                 price_modifier=0.5,
                                 active=True,
                                 start_date=today + day,
                                 applies_to_all=True)
        promo5_silver_only = PromoCode.objects.create(
            name='P5',
            description='P5 silver only',
            price_modifier=0.7,
            active=True,
            applies_to_all=False)
        promo5_silver_only.applies_to.add(package2_silver)

    def test_package_prices_with_promo(self):
        response = self.client.post('/sponsorship/', {'promo': 'P1'})
        self.assertContains(response,
                            '<label for="package_PK1">$5.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="package_PK2">$2.62</label>',
                            count=1,
                            html=True)

    def test_package_prices_with_promo_lowercase(self):
        response = self.client.post('/sponsorship/', {'promo': 'p1'})
        self.assertContains(response,
                            '<label for="package_PK1">$5.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="package_PK2">$2.62</label>',
                            count=1,
                            html=True)

    def test_package_prices_with_inactive_promo(self):
        response = self.client.post('/sponsorship/', {'promo': 'P2'})
        self.assertContains(response,
                            '<label for="package_PK1">$10.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="package_PK2">$5.25</label>',
                            count=1,
                            html=True)

    def test_package_prices_with_past_promo(self):
        response = self.client.post('/sponsorship/', {'promo': 'P3'})
        self.assertContains(response,
                            '<label for="package_PK1">$10.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="package_PK2">$5.25</label>',
                            count=1,
                            html=True)

    def test_package_prices_with_future_promo(self):
        response = self.client.post('/sponsorship/', {'promo': 'P4'})
        self.assertContains(response,
                            '<label for="package_PK1">$10.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="package_PK2">$5.25</label>',
                            count=1,
                            html=True)

    def test_package_prices_with_silver_only_promo(self):
        response = self.client.post('/sponsorship/', {'promo': 'P5'})
        self.assertContains(response,
                            '<label for="package_PK1">$10.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="package_PK2">$3.68</label>',
                            count=1,
                            html=True)

    def test_package_prices_with_no_such_promo(self):
        response = self.client.post('/sponsorship/', {'promo': 'NOSUCH'})
        self.assertContains(response,
                            '<label for="package_PK1">$10.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="package_PK2">$5.25</label>',
                            count=1,
                            html=True)

    def test_package_prices_with_preset_promo(self):
        response = self.client.get('/sponsorship/?promo=P1')
        self.assertContains(response,
                            '<label for="package_PK1">$5.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="package_PK2">$2.62</label>',
                            count=1,
                            html=True)

    def test_package_prices_with_preset_promo_lowercase(self):
        response = self.client.get('/sponsorship/?promo=p1')
        self.assertContains(response,
                            '<label for="package_PK1">$5.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="package_PK2">$2.62</label>',
                            count=1,
                            html=True)

    def test_package_prices_with_preset_no_such_promo(self):
        response = self.client.get('/sponsorship/?promo=NOSUCH')
        self.assertContains(response,
                            '<label for="package_PK1">$10.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="package_PK2">$5.25</label>',
                            count=1,
                            html=True)


class ItemsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        package1_gold = Package.objects.create(name='P1',
                                               description='P1 gold',
                                               price=10,
                                               public=True)
        Package.objects.create(name='P2',
                               description='P2 silver',
                               price=5.25,
                               public=True)
        Item.objects.create(name='I1',
                            description='For all item',
                            price=17,
                            active=True,
                            promo=False,
                            package_offset=False,
                            applies_to_all=True)
        item2_gold_only = Item.objects.create(name='I2',
                                              description='Full only item',
                                              price=16,
                                              active=True,
                                              promo=False,
                                              package_offset=False,
                                              applies_to_all=False)
        item2_gold_only.applies_to.add(package1_gold)
        Item.objects.create(name='I3',
                            description='Inactive item',
                            price=15,
                            active=False,
                            promo=False,
                            package_offset=False,
                            applies_to_all=True)

    def test_get_request(self):
        response = self.client.get('/sponsorship/add_items/')
        self.assertRedirects(response, '/sponsorship/')

    def test_no_info(self):
        response = self.client.post('/sponsorship/add_items/')
        self.assertContains(response,
                            '<p>No package information.</p>',
                            count=1,
                            html=True)

    def test_no_package(self):
        response = self.client.post('/sponsorship/add_items/', {'promo': ''})
        self.assertContains(response,
                            '<p>No package information.</p>',
                            count=1,
                            html=True)

    def test_bad_package(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'bad',
            'promo': ''
        })
        self.assertContains(response,
                            '<p>Package bad not found.</p>',
                            count=1,
                            html=True)

    def test_package_cost_gold(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'P1',
            'promo': ''
        })
        self.assertContains(response,
                            '<p>Your P1 gold costs $10.00.</p>',
                            count=1,
                            html=True)

    def test_package_cost_silver(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'P2',
            'promo': ''
        })
        self.assertContains(response,
                            '<p>Your P2 silver costs $5.25.</p>',
                            count=1,
                            html=True)

    def test_package_names_gold(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'P1',
            'promo': ''
        })
        self.assertContains(
            response,
            '<input type="checkbox" name="item0" id="item_I1" value="I1" />',
            count=1,
            html=True)
        self.assertContains(
            response,
            '<input type="checkbox" name="item1" id="item_I2" value="I2" />',
            count=1,
            html=True)
        self.assertNotContains(
            response,
            '<input type="checkbox" name="item2" id="item_I3" value="I3" />',
            html=True)

    def test_package_names_silver(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'P2',
            'promo': ''
        })
        self.assertContains(
            response,
            '<input type="checkbox" name="item0" id="item_I1" value="I1" />',
            count=1,
            html=True)
        self.assertNotContains(
            response,
            '<input type="checkbox" name="item1" id="item_I2" value="I2" />',
            html=True)
        self.assertNotContains(
            response,
            '<input type="checkbox" name="item1" id="item_I3" value="I3" />',
            html=True)

    def test_package_descriptions_gold(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'P1',
            'promo': ''
        })
        self.assertContains(response,
                            '<label for="item_I1">For all item</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="item_I2">Full only item</label>',
                            count=1,
                            html=True)
        self.assertNotContains(response,
                               '<label for="item_I3">Inactive item</label>',
                               html=True)

    def test_package_descriptions_silver(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'P2',
            'promo': ''
        })
        self.assertContains(response,
                            '<label for="item_I1">For all item</label>',
                            count=1,
                            html=True)
        self.assertNotContains(response,
                               '<label for="item_I2">Full only item</label>',
                               html=True)
        self.assertNotContains(response,
                               '<label for="item_I3">Inactive item</label>',
                               html=True)

    def test_package_prices_gold(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'P1',
            'promo': ''
        })
        self.assertContains(response,
                            '<label for="item_I1">$17.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="item_I2">$16.00</label>',
                            count=1,
                            html=True)
        self.assertNotContains(response,
                               '<label for="item_I3">$15.00</label>',
                               html=True)

    def test_package_prices_silver(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'P2',
            'promo': ''
        })
        self.assertContains(response,
                            '<label for="item_I1">$17.00</label>',
                            count=1,
                            html=True)
        self.assertNotContains(response,
                               '<label for="item_I2">$16.00</label>',
                               html=True)
        self.assertNotContains(response,
                               '<label for="item_I3">$15.00</label>',
                               html=True)


class ItemsTestWithPromo(TestCase):

    @classmethod
    def setUpTestData(cls):
        Package.objects.create(name='PK1',
                               description='PK1 gold',
                               price=10,
                               public=True)
        package2_silver = Package.objects.create(name='PK2',
                                                 description='PK2 silver',
                                                 price=5.25,
                                                 public=True)
        Item.objects.create(name='I1',
                            description='Applies to promo',
                            price=17,
                            active=True,
                            promo=True,
                            package_offset=False,
                            applies_to_all=True)
        Item.objects.create(name='I2',
                            description='Does not apply to promo',
                            price=16.11,
                            active=True,
                            promo=False,
                            package_offset=False,
                            applies_to_all=True)
        promo1_silver_only = PromoCode.objects.create(
            name='P1',
            description='P1 silver only',
            price_modifier=0.5,
            active=True,
            applies_to_all=False)
        promo1_silver_only.applies_to.add(package2_silver)

    def test_gold_package_with_promo(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'PK1',
            'promo': 'P1'
        })
        self.assertContains(response,
                            '<p>Your PK1 gold costs $10.00.</p>',
                            count=1,
                            html=True)
        self.assertContains(
            response,
            '<input type="checkbox" name="item0" id="item_I1" value="I1" />',
            count=1,
            html=True)
        self.assertContains(
            response,
            '<input type="checkbox" name="item1" id="item_I2" value="I2" />',
            count=1,
            html=True)
        self.assertContains(response,
                            '<label for="item_I1">$8.50</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="item_I2">$16.11</label>',
                            count=1,
                            html=True)

    def test_gold_package_with_promo_lowercase(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'PK1',
            'promo': 'p1'
        })
        self.assertContains(response,
                            '<p>Your PK1 gold costs $10.00.</p>',
                            count=1,
                            html=True)
        self.assertContains(
            response,
            '<input type="checkbox" name="item0" id="item_I1" value="I1" />',
            count=1,
            html=True)
        self.assertContains(
            response,
            '<input type="checkbox" name="item1" id="item_I2" value="I2" />',
            count=1,
            html=True)
        self.assertContains(response,
                            '<label for="item_I1">$8.50</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="item_I2">$16.11</label>',
                            count=1,
                            html=True)

    def test_gold_package_with_no_such_promo(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'PK1',
            'promo': 'BAD'
        })
        self.assertContains(response,
                            '<p>Your PK1 gold costs $10.00.</p>',
                            count=1,
                            html=True)
        self.assertContains(
            response,
            '<input type="checkbox" name="item0" id="item_I1" value="I1" />',
            count=1,
            html=True)
        self.assertContains(
            response,
            '<input type="checkbox" name="item1" id="item_I2" value="I2" />',
            count=1,
            html=True)
        self.assertContains(response,
                            '<label for="item_I1">$17.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="item_I2">$16.11</label>',
                            count=1,
                            html=True)

    def test_silver_package_with_promo(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'PK2',
            'promo': 'P1'
        })
        self.assertContains(response,
                            '<p>Your PK2 silver costs $2.62.</p>',
                            count=1,
                            html=True)
        self.assertContains(
            response,
            '<input type="checkbox" name="item0" id="item_I1" value="I1" />',
            count=1,
            html=True)
        self.assertContains(
            response,
            '<input type="checkbox" name="item1" id="item_I2" value="I2" />',
            count=1,
            html=True)
        self.assertContains(response,
                            '<label for="item_I1">$8.50</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="item_I2">$16.11</label>',
                            count=1,
                            html=True)

    def test_silver_package_with_no_such_promo(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'PK2',
            'promo': 'BAD'
        })
        self.assertContains(response,
                            '<p>Your PK2 silver costs $5.25.</p>',
                            count=1,
                            html=True)
        self.assertContains(
            response,
            '<input type="checkbox" name="item0" id="item_I1" value="I1" />',
            count=1,
            html=True)
        self.assertContains(
            response,
            '<input type="checkbox" name="item1" id="item_I2" value="I2" />',
            count=1,
            html=True)
        self.assertContains(response,
                            '<label for="item_I1">$17.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="item_I2">$16.11</label>',
                            count=1,
                            html=True)


class SponsorTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        today = datetime.date.today()
        day = datetime.timedelta(days=1)
        cls.package = Package.objects.create(name='P1',
                                             description='P1 gold',
                                             price=10,
                                             public=True,
                                             start_date=today - day,
                                             end_date=today + day)
        Package.objects.create(name='P2',
                               description='P2 silver',
                               price=5.25,
                               public=True)
        cls.item1 = Item.objects.create(name='I1',
                                        description='The item',
                                        price=6.77,
                                        active=True,
                                        promo=False,
                                        package_offset=False,
                                        applies_to_all=True)
        cls.item2 = Item.objects.create(name='I2',
                                        description='The offset item',
                                        price=99.99,
                                        active=True,
                                        promo=False,
                                        package_offset=True,
                                        applies_to_all=True)

    def check_first_sponsor(self, sponsor):
        self.assertEqual(sponsor.first_name, 'First')
        self.assertEqual(sponsor.last_name, 'Last')
        self.assertEqual(sponsor.email, 'a@a.com')
        self.assertEqual(sponsor.zip_code, '12345')
        self.assertEqual(sponsor.org, 'Org')

    def test_get_request(self):
        response = self.client.get('/sponsorship/add_sponsor/')
        self.assertRedirects(response, '/sponsorship/')

    def test_no_info(self):
        response = self.client.post('/sponsorship/add_sponsor/')
        self.assertContains(response,
                            '<p>No package information.</p>',
                            count=1,
                            html=True)

    def test_no_package(self):
        response = self.client.post(
            '/sponsorship/add_sponsor/', {'promo': ''},
            HTTP_REFERER='https://example.com/sponsorship/add_items/')
        self.assertContains(response,
                            '<p>No package information.</p>',
                            count=1,
                            html=True)

    def test_no_promo(self):
        response = self.client.post(
            '/sponsorship/add_sponsor/', {'package': 'P1'},
            HTTP_REFERER='https://example.com/sponsorship/add_items/')
        self.assertContains(response,
                            '<p>No promo information.</p>',
                            count=1,
                            html=True)

    def test_no_referrer(self):
        response = self.client.post('/sponsorship/add_sponsor/', {
            'package': 'P1',
            'promo': ''
        })
        self.assertContains(response,
                            '<p>Invalid referrer.</p>',
                            count=1,
                            html=True)

    def test_invalid_referrer(self):
        response = self.client.post(
            '/sponsorship/add_sponsor/', {
                'package': 'P1',
                'promo': ''
            },
            HTTP_REFERER='https://example.com/sponsorship/invalid/')
        self.assertContains(response,
                            '<p>Invalid referrer.</p>',
                            count=1,
                            html=True)

    def test_bad_package(self):
        response = self.client.post(
            '/sponsorship/add_sponsor/', {
                'package': 'bad',
                'promo': ''
            },
            HTTP_REFERER='https://example.com/sponsorship/add_items/')
        self.assertContains(response,
                            '<p>Package bad not found.</p>',
                            count=1,
                            html=True)

    def test_package_empty_promo(self):
        response = self.client.post(
            '/sponsorship/add_sponsor/', {
                'package': 'P1',
                'promo': ''
            },
            HTTP_REFERER='https://example.com/sponsorship/add_items/')
        self.assertContains(response,
                            '<p>Your P1 gold costs $10.00.</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>Your total is $10.00.</p>',
                            count=1,
                            html=True)
        self.assertNotContains(response, 'You are using promo code')
        self.assertNotContains(response, 'additional items')

    def test_package_empty_promo_and_item(self):
        response = self.client.post(
            '/sponsorship/add_sponsor/', {
                'package': 'P1',
                'promo': '',
                'item0': 'I1'
            },
            HTTP_REFERER='https://example.com/sponsorship/add_items/')
        self.assertContains(response,
                            '<p>Your P1 gold costs $10.00.</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '* The item ($6.77)<br />',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>Your total is $16.77.</p>',
                            count=1,
                            html=True)
        self.assertNotContains(response, 'You are using promo code')

    def test_package_empty_promo_and_offset_item(self):
        response = self.client.post(
            '/sponsorship/add_sponsor/', {
                'package': 'P1',
                'promo': '',
                'item0': 'I2'
            },
            HTTP_REFERER='https://example.com/sponsorship/add_items/')
        self.assertContains(response,
                            '<p>Your P1 gold costs $10.00.</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '* The offset item ($99.99)<br />',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>Your total is $99.99.</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            'The offset item waives the package price of',
                            count=1,
                            html=False)
        self.assertNotContains(response, 'You are using promo code')

    def test_validate_missing_form_data(self):
        self.client.get('/sponsorship/')
        response = self.client.post(
            '/sponsorship/add_sponsor/', {
                'package': 'P1',
                'promo': ''
            },
            HTTP_REFERER='https://example.com/sponsorship/add_sponsor/')
        self.assertContains(response, 'This field is required.')
        self.assertEqual(Sponsor.objects.count(), 0)

    def test_validate_missing_cookie(self):
        response = self.client.post(
            '/sponsorship/add_sponsor/', {
                'package': 'P1',
                'promo': '',
                'first_name': 'First',
                'last_name': 'Last',
                'email': 'a@a.com',
                'zip_code': '12345',
                'org': 'Org',
                'agreed': True,
            },
            HTTP_REFERER='https://example.com/sponsorship/add_sponsor/')
        self.assertContains(response,
                            'Please do not register multiple sponsors')
        self.assertEqual(Sponsor.objects.count(), 0)

    def test_validate_double_post(self):
        self.client.get('/sponsorship/')
        response = self.client.post(
            '/sponsorship/add_sponsor/', {
                'package': 'P1',
                'promo': '',
                'first_name': 'First',
                'last_name': 'Last',
                'email': 'a@a.com',
                'zip_code': '12345',
                'org': 'Org',
                'agreed': True,
            },
            HTTP_REFERER='https://example.com/sponsorship/add_sponsor/')
        self.assertRedirects(response, '/sponsorship/payment/')
        response = self.client.post(
            '/sponsorship/add_sponsor/', {
                'package': 'P1',
                'promo': '',
                'first_name': 'First',
                'last_name': 'Last',
                'email': 'a@a.com',
                'zip_code': '54321',
                'org': 'Org',
                'agreed': True,
            },
            HTTP_REFERER='https://example.com/sponsorship/add_sponsor/')
        self.assertContains(response, 'Already added sponsor')
        self.assertIn('sponsor', self.client.session.keys())
        self.assertEqual(self.client.session.get('sponsor'), 1)
        self.assertEqual(Sponsor.objects.count(), 1)
        self.check_first_sponsor(Sponsor.objects.get(id=1))

    def test_validate_form_data(self):
        self.client.get('/sponsorship/')
        response = self.client.post(
            '/sponsorship/add_sponsor/', {
                'package': 'P1',
                'promo': '',
                'first_name': 'First',
                'last_name': 'Last',
                'email': 'a@a.com',
                'zip_code': '12345',
                'org': 'Org',
                'agreed': True,
            },
            HTTP_REFERER='https://example.com/sponsorship/add_sponsor/')
        self.assertRedirects(response, '/sponsorship/payment/')
        self.assertIn('sponsor', self.client.session.keys())
        self.assertEqual(self.client.session.get('sponsor'), 1)
        self.assertEqual(Sponsor.objects.count(), 1)
        self.check_first_sponsor(Sponsor.objects.get(id=1))

    def test_validate_form_data_with_trailing_spaces(self):
        self.client.get('/sponsorship/')
        response = self.client.post(
            '/sponsorship/add_sponsor/', {
                'package': 'P1',
                'promo': '',
                'first_name': 'First ',
                'last_name': 'Last ',
                'email': 'a@a.com ',
                'zip_code': '12345 ',
                'org': 'Org ',
                'agreed': True,
            },
            HTTP_REFERER='https://example.com/sponsorship/add_sponsor/')
        self.assertRedirects(response, '/sponsorship/payment/')
        self.assertIn('sponsor', self.client.session.keys())
        self.assertEqual(self.client.session.get('sponsor'), 1)
        self.assertEqual(Sponsor.objects.count(), 1)
        self.check_first_sponsor(Sponsor.objects.get(id=1))

    def test_validate_form_data_including_items(self):
        self.client.get('/sponsorship/')
        response = self.client.post(
            '/sponsorship/add_sponsor/', {
                'package': 'P1',
                'promo': '',
                'first_name': 'First',
                'last_name': 'Last',
                'email': 'a@a.com',
                'zip_code': '12345',
                'org': 'Org',
                'agreed': True,
                'item0': 'I1'
            },
            HTTP_REFERER='https://example.com/sponsorship/add_sponsor/')
        self.assertRedirects(response, '/sponsorship/payment/')
        self.assertIn('sponsor', self.client.session.keys())
        self.assertEqual(self.client.session.get('sponsor'), 1)
        self.assertEqual(Sponsor.objects.count(), 1)
        sponsor = Sponsor.objects.get(id=1)
        self.check_first_sponsor(sponsor)
        self.assertEqual(sponsor.ordered_items.count(), 1)
        self.assertEqual(sponsor.ordered_items.first().name, 'I1')

    def test_validate_form_data_with_non_existent_item(self):
        self.client.get('/sponsorship/')
        response = self.client.post(
            '/sponsorship/add_sponsor/', {
                'package': 'P1',
                'promo': '',
                'first_name': 'First',
                'last_name': 'Last',
                'email': 'a@a.com',
                'zip_code': '12345',
                'org': 'Org',
                'agreed': True,
                'item0': 'NON_EXISTENT_ITEM',
                'item1': 'I1'
            },
            HTTP_REFERER='https://example.com/sponsorship/add_sponsor/')
        self.assertRedirects(response, '/sponsorship/payment/')
        self.assertIn('sponsor', self.client.session.keys())
        self.assertEqual(self.client.session.get('sponsor'), 1)
        self.assertEqual(Sponsor.objects.count(), 1)
        sponsor = Sponsor.objects.get(id=1)
        self.check_first_sponsor(sponsor)
        self.assertEqual(sponsor.ordered_items.count(), 1)
        self.assertEqual(sponsor.ordered_items.first().name, 'I1')
        # Check that the total cost does not include the non-existent item.
        # Original package (10) + item1 (6.77) = 16.77
        self.assertEqual(sponsor.package_cost(), decimal.Decimal('16.77'))


class PaymentTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        p = Package.objects.create(name='PK1',
                                   description='PK1 gold',
                                   price=100,
                                   public=True)
        promo = PromoCode.objects.create(name='PROMO',
                                         description='P all',
                                         price_modifier=0.5,
                                         active=True,
                                         applies_to_all=True)
        Sponsor.objects.create(first_name='First',
                               last_name='Last',
                               email='a@a.com',
                               zip_code='12345',
                               org='Org1',
                               package=p)
        Sponsor.objects.create(first_name='Second',
                               last_name='Last',
                               email='b@a.com',
                               zip_code='54321',
                               org='Org2',
                               package=p,
                               valid=True)
        Sponsor.objects.create(first_name='Third',
                               last_name='Person',
                               email='c@a.com',
                               zip_code='99999',
                               org='Org3',
                               package=p,
                               promo=promo)

    def test_post_request(self):
        response = self.client.post('/sponsorship/payment/')
        self.assertRedirects(response, '/sponsorship/')
        self.assertEqual(PendingOrder.objects.count(), 0)

    def test_get_request_no_session(self):
        response = self.client.get('/sponsorship/payment/')
        self.assertRedirects(response, '/sponsorship/')
        self.assertEqual(PendingOrder.objects.count(), 0)

    def test_get_request_with_invalid_sponsor_data_type(self):
        session = self.client.session
        session['sponsor'] = 'bad'
        session.save()
        response = self.client.get('/sponsorship/payment/')
        self.assertRedirects(response, '/sponsorship/')
        self.assertEqual(PendingOrder.objects.count(), 0)

    def test_get_request_with_unpaid_sponsor(self):
        random.seed(0)
        session = self.client.session
        session['sponsor'] = 1
        session.save()
        response = self.client.get('/sponsorship/payment/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sponsorship - Payment')
        self.assertContains(response, 'First Last')
        self.assertContains(response, '$100.00')
        self.assertNotContains(response, 'cannot generate order ID')
        self.assertEqual(PendingOrder.objects.count(), 1)
        pending_order = PendingOrder.objects.all()[0]
        self.assertEqual(pending_order.order_num, 'Y0CQ65ZT4W')
        self.assertEqual(pending_order.sponsor.id, 1)

    def test_get_request_with_unpaid_promo_sponsor(self):
        random.seed(0)
        session = self.client.session
        session['sponsor'] = 3
        session.save()
        response = self.client.get('/sponsorship/payment/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sponsorship - Payment')
        self.assertContains(response, 'Third Person')
        self.assertContains(response, '$50.00')
        self.assertNotContains(response, 'cannot generate order ID')
        self.assertEqual(PendingOrder.objects.count(), 1)
        pending_order = PendingOrder.objects.all()[0]
        self.assertEqual(pending_order.order_num, 'Y0CQ65ZT4W')
        self.assertEqual(pending_order.sponsor.id, 3)

    def test_get_request_with_unpaid_sponsor_and_existing_order(self):
        random.seed(0)
        PendingOrder.objects.create(order_num='Y0CQ65ZT4W',
                                    sponsor=Sponsor.objects.get(id=3))
        session = self.client.session
        session['sponsor'] = 1
        session.save()
        response = self.client.get('/sponsorship/payment/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sponsorship - Payment')
        self.assertContains(response, 'First Last')
        self.assertContains(response, '$100.00')
        self.assertNotContains(response, 'cannot generate order ID')
        self.assertEqual(PendingOrder.objects.count(), 2)
        pending_order = PendingOrder.objects.get(sponsor_id=1)
        self.assertEqual(pending_order.order_num, 'N6ISIGQ8JT')
        self.assertEqual(pending_order.sponsor.id, 1)

    def test_get_request_with_paid_sponsor(self):
        session = self.client.session
        session['sponsor'] = 2
        session.save()
        response = self.client.get('/sponsorship/payment/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No sponsor to pay for.')
        self.assertEqual(PendingOrder.objects.count(), 0)

    def test_get_request_with_no_such_sponsor(self):
        session = self.client.session
        session['sponsor'] = 999
        session.save()
        response = self.client.get('/sponsorship/payment/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No sponsor to pay for.')
        self.assertEqual(PendingOrder.objects.count(), 0)


class SaleTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        p = Package.objects.create(name='PK1',
                                   description='PK1 gold',
                                   price=decimal.Decimal(100),
                                   public=True)
        Sponsor.objects.create(first_name='First',
                               last_name='Last',
                               email='a@a.com',
                               zip_code='12345',
                               org='Org1',
                               package=p,
                               valid=False)
        Sponsor.objects.create(first_name='Second',
                               last_name='Last',
                               email='b@a.com',
                               zip_code='54321',
                               org='Org2',
                               package=p,
                               valid=True)

        PendingOrder.objects.create(order_num='1234567890',
                                    sponsor=Sponsor.objects.get(id=1))
        PendingOrder.objects.create(order_num='ALREADYPAID',
                                    sponsor=Sponsor.objects.get(id=2))

        cls.post_data = {
            'NAME': 'First Last',
            'ADDRESS': '123 Main St',
            'CITY': 'Anytown',
            'STATE': 'CA',
            'ZIP': '12345',
            'COUNTRY': 'USA',
            'PHONE': '555-555-5555',
            'EMAIL': 'a@a.com',
            'AMOUNT': '100.00',
            'AUTHCODE': '123456',
            'PNREF': 'A1B2C3D4E5F6',
            'RESULT': '0',
            'RESPMSG': 'Approved',
            'USER1': '1234567890',
        }

    def test_get_request(self):
        response = self.client.get('/sponsorship/sale/')
        self.assertEqual(response.status_code, 405)

    def test_post_request_success(self):
        response = self.client.post('/sponsorship/sale/', self.post_data)
        self.assertContains(response, 'success', status_code=200)
        self.assertEqual(Order.objects.count(), 1)
        sponsor = Sponsor.objects.get(id=1)
        self.assertTrue(sponsor.valid)
        self.assertTrue(sponsor.order)
        order = Order.objects.first()
        self.assertEqual(order.already_paid_sponsor, False)

    def test_post_request_missing_data(self):
        response = self.client.post('/sponsorship/sale/')
        self.assertContains(response, 'required vars missing', status_code=500)
        self.assertEqual(Order.objects.count(), 0)

        for key in self.post_data:
            if key == 'COUNTRY':
                continue
            post_data = self.post_data.copy()
            del post_data[key]
            response = self.client.post('/sponsorship/sale/', post_data)
            self.assertContains(response,
                                'required vars missing',
                                status_code=500)
            self.assertEqual(Order.objects.count(), 0)

    def test_post_request_bad_result(self):
        post_data = self.post_data.copy()
        post_data['RESULT'] = '1'
        response = self.client.post('/sponsorship/sale/', post_data)
        self.assertContains(response,
                            'transaction did not succeed',
                            status_code=500)
        self.assertEqual(Order.objects.count(), 0)

    def test_post_request_bad_response_message(self):
        post_data = self.post_data.copy()
        post_data['RESPMSG'] = 'BAD'
        response = self.client.post('/sponsorship/sale/', post_data)
        self.assertContains(response, 'transaction declined', status_code=500)
        self.assertEqual(Order.objects.count(), 0)

    def test_post_request_order_already_exists(self):
        Order.objects.create(order_num='1234567890',
                             amount=decimal.Decimal(100),
                             sponsor=Sponsor.objects.get(id=1))
        response = self.client.post('/sponsorship/sale/', self.post_data)
        self.assertContains(response, 'order already exists', status_code=500)
        self.assertEqual(Order.objects.count(), 1)

    def test_post_request_missing_pending_order(self):
        post_data = self.post_data.copy()
        post_data['USER1'] = 'BAD'
        response = self.client.post('/sponsorship/sale/', post_data)
        self.assertContains(response,
                            'cannot get pending order',
                            status_code=500)
        self.assertEqual(Order.objects.count(), 0)

    def test_post_request_pending_order_no_amount(self):
        post_data = self.post_data.copy()
        post_data['AMOUNT'] = '0.00'
        response = self.client.post('/sponsorship/sale/', post_data)
        self.assertContains(response,
                            'incorrect payment amount: got 0',
                            status_code=500)
        self.assertEqual(Order.objects.count(), 0)

    def test_post_request_pending_order_wrong_amount(self):
        post_data = self.post_data.copy()
        post_data['AMOUNT'] = '150.00'
        response = self.client.post('/sponsorship/sale/', post_data)
        self.assertContains(response,
                            'incorrect payment amount: expected 100, got 150',
                            status_code=500)
        self.assertEqual(Order.objects.count(), 0)

    def test_post_request_already_paid_sponsor(self):
        post_data = self.post_data.copy()
        post_data['USER1'] = 'ALREADYPAID'
        post_data['EMAIL'] = 'b@a.com'
        post_data['NAME'] = 'Second Last'
        post_data['AMOUNT'] = '100.00'
        response = self.client.post('/sponsorship/sale/', post_data)
        self.assertContains(response, 'success', status_code=200)
        self.assertEqual(Order.objects.count(), 1)
        sponsor = Sponsor.objects.get(id=2)
        self.assertTrue(sponsor.valid)
        order = Order.objects.first()
        self.assertEqual(order.already_paid_sponsor, True)
        self.assertEqual(order.sponsor, sponsor)


class FailedPaymentTest(TestCase):

    def test_get_request(self):
        response = self.client.get('/sponsorship/failed_payment/')
        self.assertContains(response, 'Sponsorship Payment Failed')

    def test_post_request(self):
        response = self.client.post('/sponsorship/failed_payment/')
        self.assertContains(response, 'Sponsorship Payment Failed')
