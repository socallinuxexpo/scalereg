import datetime

from django.test import TestCase

from .models import Item
from .models import Package


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
        response = self.client.post('/sponsorship/add_items/')
        self.assertContains(response,
                            '<p>No package information.</p>',
                            count=1,
                            html=True)

    def test_bad_package(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'bad',
        })
        self.assertContains(response,
                            '<p>Package bad not found.</p>',
                            count=1,
                            html=True)

    def test_package_cost_gold(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'P1',
        })
        self.assertContains(response,
                            '<p>Your P1 gold costs $10.00.</p>',
                            count=1,
                            html=True)

    def test_package_cost_silver(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'P2',
        })
        self.assertContains(response,
                            '<p>Your P2 silver costs $5.25.</p>',
                            count=1,
                            html=True)

    def test_package_names_gold(self):
        response = self.client.post('/sponsorship/add_items/', {
            'package': 'P1',
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
