from django.contrib.auth import get_user_model
from django.test import TestCase

from reg23.models import Attendee
from reg23.models import Order
from reg23.models import Ticket


class ScannerTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.normal_user = get_user_model().objects.create_user('user',
                                                               is_staff=False)

        cls.ticket = Ticket.objects.create(name='FULL',
                                           description='Full Pass',
                                           ticket_type='full',
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
                                               valid=True,
                                               checked_in=True)
        cls.get_data = {'RESULT': '19~Test~User', 'SIZE': 'ML'}

    def check_basic_strings(self, response):
        self.assertContains(response, 'No selected size')

    def test_get_request_not_logged_in(self):
        response = self.client.get('/reg23/scanner/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/reg23/scanner/')

    def test_post_request_not_logged_in(self):
        response = self.client.post('/reg23/scanner/', {})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/accounts/login/?next=/reg23/scanner/')

    def test_post_request_normal_user(self):
        self.client.force_login(self.normal_user)
        self.client.force_login(self.normal_user)
        response = self.client.post('/reg23/scanner/', {})
        self.assertEqual(response.status_code, 405)

    def test_get_request_normal_user(self):
        self.client.force_login(self.normal_user)
        response = self.client.get('/reg23/scanner/')
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'color: red')
        self.assertNotContains(response, 'Invalid')
        self.assertNotContains(response, 'Attendee not checked in')
        self.assertNotContains(response, 'Badge already scanned: ')
        self.assertNotContains(response, 'Scanned 1')

    def test_get_request_valid_result(self):
        self.client.force_login(self.normal_user)
        response = self.client.get('/reg23/scanner/', self.get_data)
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'color: green')
        self.assertContains(response, 'Scanned 1')
        self.assertNotContains(response, 'Invalid')
        self.assertNotContains(response, 'Attendee not checked in')
        self.assertNotContains(response, 'Badge already scanned:')

    def test_get_request_no_result(self):
        self.client.force_login(self.normal_user)
        get_data = {'SIZE': 'ML'}
        response = self.client.get('/reg23/scanner/', get_data)
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'color: red')
        self.assertNotContains(response, 'Invalid')
        self.assertNotContains(response, 'Attendee not checked in')
        self.assertNotContains(response, 'Badge already scanned: ')
        self.assertNotContains(response, 'Scanned 1')

    def test_get_request_no_size(self):
        self.client.force_login(self.normal_user)
        get_data = {'RESULT': '19~Test~User'}
        response = self.client.get('/reg23/scanner/', get_data)
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'color: red')
        self.assertNotContains(response, 'Invalid')
        self.assertNotContains(response, 'Attendee not checked in')
        self.assertNotContains(response, 'Badge already scanned: ')
        self.assertNotContains(response, 'Scanned 1')

    def test_get_request_empty_result(self):
        self.client.force_login(self.normal_user)
        get_data = {'RESULT': '', 'SIZE': 'ML'}
        response = self.client.get('/reg23/scanner/', get_data)
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'color: red')
        self.assertContains(response, 'Invalid barcode')
        self.assertNotContains(response, 'Attendee not checked in')
        self.assertNotContains(response, 'Badge already scanned: ')
        self.assertNotContains(response, 'Scanned 1')

    def test_get_request_empty_id(self):
        self.client.force_login(self.normal_user)
        get_data = {'RESULT': '~Test~User', 'SIZE': 'ML'}
        response = self.client.get('/reg23/scanner/', get_data)
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'color: red')
        self.assertContains(response, 'Invalid barcode')
        self.assertNotContains(response, 'Attendee not checked in')
        self.assertNotContains(response, 'Badge already scanned: ')
        self.assertNotContains(response, 'Scanned 1')

    def test_get_request_invalid_id(self):
        self.client.force_login(self.normal_user)
        get_data = {'RESULT': '9991~Test~User', 'SIZE': 'ML'}
        response = self.client.get('/reg23/scanner/', get_data)
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'color: red')
        self.assertContains(response, 'Invalid barcode')
        self.assertNotContains(response, 'Attendee not checked in')
        self.assertNotContains(response, 'Badge already scanned: ')
        self.assertNotContains(response, 'Scanned 1')

    def test_get_request_invalid_parity_bad(self):
        self.client.force_login(self.normal_user)
        get_data = {'RESULT': '12~Test~User', 'SIZE': 'ML'}
        response = self.client.get('/reg23/scanner/', get_data)
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'color: red')
        self.assertContains(response, 'Invalid parity bit')
        self.assertNotContains(response, 'Attendee not checked in')
        self.assertNotContains(response, 'Badge already scanned:')
        self.assertNotContains(response, 'Scanned 1')

    def test_get_request_attendee_not_valid(self):
        self.attendee.valid = False
        self.attendee.save()
        self.client.force_login(self.normal_user)
        response = self.client.get('/reg23/scanner/', self.get_data)
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'color: red')
        self.assertContains(response, 'Invalid attendee')
        self.assertNotContains(response, 'Attendee not checked in')
        self.assertNotContains(response, 'Badge already scanned:')
        self.assertNotContains(response, 'Scanned 1')

    def test_get_request_attendee_no_order(self):
        self.attendee.order = None
        self.attendee.save()
        self.client.force_login(self.normal_user)
        response = self.client.get('/reg23/scanner/', self.get_data)
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'color: red')
        self.assertContains(response, 'Invalid attendee')
        self.assertNotContains(response, 'Attendee not checked in')
        self.assertNotContains(response, 'Badge already scanned:')
        self.assertNotContains(response, 'Scanned 1')

    def test_get_request_attendee_not_checked_in(self):
        self.attendee.checked_in = False
        self.attendee.save()
        self.client.force_login(self.normal_user)
        response = self.client.get('/reg23/scanner/', self.get_data)
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'color: red')
        self.assertContains(response, 'Attendee not checked in')
        self.assertNotContains(response, 'Invalid')
        self.assertNotContains(response, 'Badge already scanned:')
        self.assertNotContains(response, 'Scanned 1')

    def test_get_request_badge_already_scanned(self):
        self.attendee.tshirt = 'MXL'
        self.attendee.save()
        self.client.force_login(self.normal_user)
        response = self.client.get('/reg23/scanner/', self.get_data)
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'color: orange')
        self.assertContains(response, 'Badge already scanned: 1')
        self.assertNotContains(response, 'Invalid')
        self.assertNotContains(response, 'Scanned 1')
