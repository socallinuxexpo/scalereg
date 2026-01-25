from django.contrib.auth import get_user_model
from django.test import TestCase

from reg23.models import Attendee, Order, Ticket


class ReceiptTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.normal_user = get_user_model().objects.create_user('user',
                                                               is_staff=False)

        cls.ticket = Ticket.objects.create(name='FULL',
                                           description='Full Pass',
                                           price=100,
                                           public=True,
                                           cash=True,
                                           upgradable=True)
        cls.order = Order.objects.create(order_num='ORDER00001',
                                         name='Test Order',
                                         address='123 Main St',
                                         city='Anytown',
                                         state='CA',
                                         zip_code='12345',
                                         email='test@example.com',
                                         amount=100,
                                         valid=True)
        cls.attendee = Attendee.objects.create(badge_type=cls.ticket,
                                               order=cls.order,
                                               first_name='Test',
                                               last_name='User',
                                               email='attendee@example.com',
                                               zip_code='12345',
                                               valid=True)

    def test_get_request_not_logged_in(self):
        response = self.client.get('/reg23/staff/receipt/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             '/accounts/login/?next=/reg23/staff/receipt/')

    def test_get_request_normal_user(self):
        self.client.force_login(self.normal_user)
        response = self.client.get('/reg23/staff/receipt/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Receipt lookup')
        self.assertNotContains(response, 'Attendee not found')
        self.assertNotContains(response, 'Invalid attendee')

    def test_valid_attendee(self):
        self.client.force_login(self.normal_user)
        response = self.client.post('/reg23/staff/receipt/',
                                    {'attendee': self.attendee.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.attendee.full_name())
        self.assertNotContains(response, 'Attendee not found')
        self.assertNotContains(response, 'Invalid attendee')

    def test_nonexistent_attendee(self):
        self.client.force_login(self.normal_user)
        response = self.client.post('/reg23/staff/receipt/',
                                    {'attendee': 9999})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Attendee not found')

    def test_invalid_attendee(self):
        invalid_attendee = Attendee.objects.create(badge_type=self.ticket,
                                                   order=self.order,
                                                   first_name='Invalid',
                                                   last_name='User',
                                                   email='invalid@example.com',
                                                   zip_code='12345',
                                                   valid=False)
        self.client.force_login(self.normal_user)
        response = self.client.post('/reg23/staff/receipt/',
                                    {'attendee': invalid_attendee.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid attendee')

    def test_attendee_with_invalid_order(self):
        order = Order.objects.create(order_num='ORDER00002',
                                     name='Invalid Order',
                                     address='123 Main St',
                                     city='Anytown',
                                     state='CA',
                                     zip_code='12345',
                                     email='test@example.com',
                                     amount=100,
                                     valid=False)
        attendee = Attendee.objects.create(badge_type=self.ticket,
                                           order=order,
                                           first_name='Invalid',
                                           last_name='User',
                                           email='invalid@example.com',
                                           zip_code='12345',
                                           valid=True)
        self.client.force_login(self.normal_user)
        response = self.client.post('/reg23/staff/receipt/',
                                    {'attendee': attendee.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid attendee')


class StaffIndexTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.normal_user = get_user_model().objects.create_user('user',
                                                               is_staff=False)

    def test_get_request_not_logged_in(self):
        response = self.client.get('/reg23/staff/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/reg23/staff/')

    def test_get_request_normal_user(self):
        self.client.force_login(self.normal_user)
        response = self.client.get('/reg23/staff/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Staff Page')

    def test_post_request_not_logged_in(self):
        response = self.client.post('/reg23/staff/', {})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/reg23/staff/')

    def test_post_request_normal_user(self):
        self.client.force_login(self.normal_user)
        response = self.client.post('/reg23/staff/', {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Staff Page')
