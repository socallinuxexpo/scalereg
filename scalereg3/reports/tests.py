from django.apps import apps
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone


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
