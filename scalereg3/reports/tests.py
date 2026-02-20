from datetime import timedelta
from decimal import Decimal

from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from reports.views import SCALE_EVENT_DATE


class IndexTest(TestCase):

    def test_not_logged_in(self):
        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/admin/login/?next=/reports/')

    def test_normal_user_logged_in(self):
        user = get_user_model().objects.create_user('user', is_staff=False)
        self.client.force_login(user)
        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/admin/login/?next=/reports/')

    def test_staff_user_logged_in(self):
        user = get_user_model().objects.create_user('user', is_staff=True)
        self.client.force_login(user)
        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            '<a href="sales_dashboard/">Sales Dashboard</a>')


class SalesDashboardTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        today = timezone.now()
        day = timezone.timedelta(days=1)

        order_objects = apps.get_model('reg23', 'Order').objects
        create_order_with_date = cls.create_order_with_date
        create_order_with_date(order_objects,
                               today,
                               order_num='0',
                               valid=True,
                               payment_type='cash',
                               amount=2)
        create_order_with_date(order_objects,
                               today - (8 * day),
                               order_num='1',
                               valid=True,
                               payment_type='payflow',
                               amount=3)
        create_order_with_date(order_objects,
                               today - (31 * day),
                               order_num='2',
                               valid=True,
                               payment_type='cash',
                               amount=7)

    @staticmethod
    def create_order_with_date(order_objects, date, **kwargs):
        order = order_objects.create(**kwargs)
        order.date = date
        order.save()

    def test_not_logged_in(self):
        response = self.client.get('/reports/sales_dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             '/admin/login/?next=/reports/sales_dashboard/')

    def test_normal_user_logged_in(self):
        user = get_user_model().objects.create_user('user', is_staff=False)
        self.client.force_login(user)
        response = self.client.get('/reports/sales_dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             '/admin/login/?next=/reports/sales_dashboard/')

    def test_staff_user_logged_in(self):
        user = get_user_model().objects.create_user('user', is_staff=True)
        self.client.force_login(user)
        response = self.client.get('/reports/sales_dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<tr><td>Revenue</td><td>$2.00</td><td>$5.00</td><td>$12.00</td></tr>',
            html=True)
        self.assertContains(
            response,
            '<tr><td>Payflow</td><td>0</td><td>1</td><td>1</td><td>$3.00</td></tr>',
            html=True)
        self.assertContains(
            response,
            '<tr><td>Cash</td><td>1</td><td>1</td><td>2</td><td>$9.00</td></tr>',
            html=True)


class RegDateReportTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.staff_user = get_user_model().objects.create_user('staff',
                                                              is_staff=True)

        # Create orders with different dates to test the regdate report
        order_objects = apps.get_model('reg23', 'Order').objects
        create_order_with_date = cls.create_order_with_date

        base_date = timezone.now()

        # 5 orders on day 1 - total $250
        for i in range(5):
            create_order_with_date(order_objects,
                                   base_date - timedelta(days=10),
                                   order_num=f'DAY1_{i}',
                                   valid=True,
                                   payment_type='cash',
                                   amount=Decimal('50.00'))

        # 3 orders on day 2 - total $300
        for i in range(3):
            create_order_with_date(order_objects,
                                   base_date - timedelta(days=20),
                                   order_num=f'DAY2_{i}',
                                   valid=True,
                                   payment_type='credit',
                                   amount=Decimal('100.00'))

        # 2 orders on day 3 - total $150
        for i in range(2):
            create_order_with_date(order_objects,
                                   base_date - timedelta(days=30),
                                   order_num=f'DAY3_{i}',
                                   valid=True,
                                   payment_type='cash',
                                   amount=Decimal('75.00'))

        # invalid order
        create_order_with_date(order_objects,
                               base_date - timedelta(days=15),
                               order_num='INVALID',
                               valid=False,
                               payment_type='cash',
                               amount=Decimal('200.00'))

    @staticmethod
    def create_order_with_date(order_objects, date, **kwargs):
        order = order_objects.create(**kwargs)
        order.date = date
        order.save()

    def test_authentication_required(self):
        response = self.client.get('/reports/regdate/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/admin/login/?next=/reports/regdate/')

    def test_html_view(self):
        self.client.force_login(self.staff_user)

        response = self.client.get('/reports/regdate/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Registration Date Report')
        self.assertContains(response, 'Download as CSV')
        self.assertContains(response,
                            'date,days out from scale,tickets,revenue')

    def test_csv_content_and_format(self):
        self.client.force_login(self.staff_user)

        response = self.client.get('/reports/regdate/?download=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

        content = response.content.decode('utf-8').strip().splitlines()

        # Check that the correct number of lines are returned
        # (1 header + 3 data lines)
        self.assertEqual(len(content), 4)

        # Check header
        self.assertEqual(content[0],
                         'date,days out from scale,tickets,revenue')

        # Calculate expected values for each date
        day3_date = (timezone.now() - timedelta(days=30)).date()
        day3_days_out = (SCALE_EVENT_DATE - day3_date).days

        day2_date = (timezone.now() - timedelta(days=20)).date()
        day2_days_out = (SCALE_EVENT_DATE - day2_date).days

        day1_date = (timezone.now() - timedelta(days=10)).date()
        day1_days_out = (SCALE_EVENT_DATE - day1_date).days

        # Check that the data lines contain the correct values in order
        # from oldest to newest
        self.assertEqual(content[1], f'{day3_date},{day3_days_out},2,150')
        self.assertEqual(content[2], f'{day2_date},{day2_days_out},3,300')
        self.assertEqual(content[3], f'{day1_date},{day1_days_out},5,250')

        # Check that the invalid order is not included in the report
        self.assertNotIn('200', response.content.decode('utf-8'))
