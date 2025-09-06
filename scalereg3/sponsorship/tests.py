import datetime

from django.test import TestCase

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
