import random

from django.contrib.auth import get_user_model
from django.test import TestCase

from reg23.models import Attendee
from reg23.models import Order
from reg23.models import Ticket


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


class CashPaymentTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.normal_user = get_user_model().objects.create_user('user',
                                                               is_staff=False)
        cls.ticket = Ticket.objects.create(name='CASH',
                                           description='Cash Pass',
                                           price=50,
                                           public=True,
                                           cash=True,
                                           upgradable=True)
        cls.non_cash_ticket = Ticket.objects.create(name='FULL',
                                                    description='Full Pass',
                                                    price=100,
                                                    public=True,
                                                    cash=False,
                                                    upgradable=True)

    def check_basic_strings(self, response):
        self.assertContains(response, 'Cash Payment')
        self.assertContains(response, 'First Name')
        self.assertContains(response, 'CASH - Cash Pass - $50.00')
        self.assertNotContains(response, 'Full Pass')

    def test_get_request_not_logged_in(self):
        response = self.client.get('/reg23/staff/cash_payment/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, '/accounts/login/?next=/reg23/staff/cash_payment/')

    def test_get_request_normal_user(self):
        self.client.force_login(self.normal_user)
        response = self.client.get('/reg23/staff/cash_payment/')
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)

    def test_post_request_not_logged_in(self):
        response = self.client.post(
            '/reg23/staff/cash_payment/', {
                'TICKET': 'CASH',
                'first_name': 'John',
                'last_name': 'Doe',
                'title': 'Engineer',
                'org': 'ACME',
                'email': 'john@example.com',
                'zip_code': '12345',
            })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, '/accounts/login/?next=/reg23/staff/cash_payment/')

    def test_valid_data(self):
        random.seed(0)
        self.assertEqual(Attendee.objects.count(), 0)
        self.assertEqual(Order.objects.count(), 0)
        self.client.force_login(self.normal_user)
        response = self.client.post(
            '/reg23/staff/cash_payment/', {
                'TICKET': 'CASH',
                'first_name': 'John',
                'last_name': 'Doe',
                'title': 'Engineer',
                'org': 'ACME',
                'email': 'john@example.com',
                'zip_code': '12345',
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Attendee.objects.count(), 1)
        self.assertEqual(Order.objects.count(), 1)
        attendee = Attendee.objects.get(id=1)
        self.assertEqual(attendee.badge_type, self.ticket)
        self.assertTrue(attendee.order)
        self.assertTrue(attendee.order.valid)
        self.assertEqual(attendee.order.payment_type, 'cash')
        self.assertEqual(attendee.order.amount, 50)
        self.assertTrue(attendee.valid)
        self.assertTrue(attendee.checked_in)
        self.assertEqual(attendee.first_name, 'John')
        self.assertEqual(attendee.last_name, 'Doe')
        self.assertEqual(attendee.email, 'john@example.com')
        self.assertEqual(attendee.zip_code, '12345')
        self.check_basic_strings(response)
        self.assertContains(response,
                            'Attendee John Doe successfully registered!')
        self.assertNotContains(response, 'Error:')

    def test_missing_ticket(self):
        self.client.force_login(self.normal_user)
        response = self.client.post(
            '/reg23/staff/cash_payment/', {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com',
                'zip_code': '12345',
            })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No TICKET information.')

    def test_invalid_ticket(self):
        self.client.force_login(self.normal_user)
        response = self.client.post(
            '/reg23/staff/cash_payment/', {
                'TICKET': 'NONE',
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com',
                'zip_code': '12345',
            })
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'Error: Cannot find ticket type')

    def test_non_cash_ticket(self):
        self.client.force_login(self.normal_user)
        response = self.client.post(
            '/reg23/staff/cash_payment/', {
                'TICKET': 'FULL',
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com',
                'zip_code': '12345',
            })
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'Error: Cannot find ticket type')

    def test_invalid_form(self):
        self.client.force_login(self.normal_user)
        response = self.client.post(
            '/reg23/staff/cash_payment/', {
                'TICKET': 'CASH',
                'first_name': 'John',
                'email': 'john@example.com',
                'zip_code': '12345',
            })
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'This field is required.')


class CheckInTest(TestCase):

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
        cls.order = Order.objects.create(order_num='ORDER12345',
                                         name='Test Order',
                                         address='123 Main St',
                                         city='Anytown',
                                         state='CA',
                                         zip_code='12345',
                                         email='test@example.com',
                                         amount=100,
                                         payment_type='payflow',
                                         payflow_pnref='PNREF001',
                                         valid=True)
        cls.attendee = Attendee.objects.create(badge_type=cls.ticket,
                                               order=cls.order,
                                               first_name='Alice',
                                               last_name='Smith',
                                               email='alice@example.com',
                                               zip_code='98765',
                                               valid=True)
        cls.invalid_attendee = Attendee.objects.create(
            badge_type=cls.ticket,
            order=None,
            first_name='Carol',
            last_name='Invalid',
            email='invalid@example.com',
            zip_code='99999',
            valid=False)

    def check_basic_strings(self, response):
        self.assertContains(response, 'Attendee Check In')
        self.assertContains(response, 'Express Check In Code')
        self.assertContains(response, 'Last Name')

    def check_attendee_found(self, response, attendee):
        self.assertContains(response, 'Search results for:')
        self.assertContains(response, attendee.full_name())
        self.assertNotContains(response, 'Attendee not found.')
        self.assertNotContains(response, 'Invalid')
        self.assertNotContains(response, 'Already Checked In')

    def check_attendee_not_found(self, response, attendee):
        self.assertContains(response, 'Search results for:')
        self.assertContains(response, 'Attendee not found.')
        self.assertNotContains(response, attendee.full_name())
        self.assertNotContains(response, 'Invalid')
        self.assertNotContains(response, 'Already Checked In')

    def check_attendee_invalid(self, response, attendee):
        self.assertContains(response, 'Search results for:')
        self.assertContains(response, attendee.full_name())
        self.assertContains(response, 'Invalid')
        self.assertNotContains(response, 'Attendee not found.')
        self.assertNotContains(response, 'Already Checked In')

    def check_attendee_already_checked_in(self, response, attendee):
        self.assertContains(response, 'Search results for:')
        self.assertContains(response, attendee.full_name())
        self.assertContains(response, 'Already Checked In')
        self.assertNotContains(response, 'Attendee not found.')
        self.assertNotContains(response, 'Invalid')

    def test_get_request_not_logged_in(self):
        response = self.client.get('/reg23/staff/check_in/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             '/accounts/login/?next=/reg23/staff/check_in/')

    def test_get_request_normal_user(self):
        self.client.force_login(self.normal_user)
        response = self.client.get('/reg23/staff/check_in/')
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)

    def test_post_request_not_logged_in(self):
        response = self.client.post(
            '/reg23/staff/check_in/', {
                'express': self.attendee.checkin_code(),
                'last_name': '',
                'payflow': '',
                'zip_code': '',
            })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             '/accounts/login/?next=/reg23/staff/check_in/')

    def test_express(self):
        self.client.force_login(self.normal_user)
        response = self.client.post(
            '/reg23/staff/check_in/', {
                'express': self.attendee.checkin_code(),
                'last_name': '',
                'payflow': '',
                'zip_code': '',
            })
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(
            response, f'Express Check In Code: {self.attendee.checkin_code()}')
        self.check_attendee_found(response, self.attendee)

    def test_express_not_found(self):
        self.client.force_login(self.normal_user)
        response = self.client.post('/reg23/staff/check_in/', {
            'express': '0000bad',
            'last_name': '',
            'payflow': '',
            'zip_code': '',
        })
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'Express Check In Code: 0000bad')
        self.check_attendee_not_found(response, self.attendee)

    def test_express_not_invalid(self):
        self.client.force_login(self.normal_user)
        response = self.client.post(
            '/reg23/staff/check_in/', {
                'express': self.invalid_attendee.checkin_code(),
                'last_name': '',
                'payflow': '',
                'zip_code': '',
            })
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(
            response,
            f'Express Check In Code: {self.invalid_attendee.checkin_code()}')
        self.check_attendee_invalid(response, self.invalid_attendee)

    def test_payflow(self):
        self.client.force_login(self.normal_user)
        response = self.client.post(
            '/reg23/staff/check_in/', {
                'express': '',
                'last_name': '',
                'payflow': 'PNREF001',
                'zip_code': '',
            })
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'Paypal Payflow Confirmation: PNREF001')
        self.check_attendee_found(response, self.attendee)

    def test_payflow_not_found(self):
        self.client.force_login(self.normal_user)
        response = self.client.post('/reg23/staff/check_in/', {
            'express': '',
            'last_name': '',
            'payflow': 'nosuch',
            'zip_code': '',
        })
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'Paypal Payflow Confirmation: nosuch')
        self.check_attendee_not_found(response, self.attendee)

    def test_last_name(self):
        self.client.force_login(self.normal_user)
        response = self.client.post('/reg23/staff/check_in/', {
            'express': '',
            'last_name': 'smi',
            'payflow': '',
            'zip_code': '',
        })
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'Last Name: smi')
        self.check_attendee_found(response, self.attendee)

    def test_last_name_not_found(self):
        self.client.force_login(self.normal_user)
        response = self.client.post('/reg23/staff/check_in/', {
            'express': '',
            'last_name': 'nosuch',
            'payflow': '',
            'zip_code': '',
        })
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'Last Name: nosuch')
        self.check_attendee_not_found(response, self.attendee)

    def test_last_name_invalid(self):
        self.client.force_login(self.normal_user)
        response = self.client.post('/reg23/staff/check_in/', {
            'express': '',
            'last_name': 'invalid',
            'payflow': '',
            'zip_code': '',
        })
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'Last Name: invalid')
        self.check_attendee_invalid(response, self.invalid_attendee)

    def test_zip_code(self):
        self.client.force_login(self.normal_user)
        response = self.client.post('/reg23/staff/check_in/', {
            'express': '',
            'last_name': '',
            'payflow': '',
            'zip_code': '98765',
        })
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'Zip Code: 98765')
        self.check_attendee_found(response, self.attendee)

    def test_zip_code_not_found(self):
        self.client.force_login(self.normal_user)
        response = self.client.post('/reg23/staff/check_in/', {
            'express': '',
            'last_name': '',
            'payflow': '',
            'zip_code': 'nosuch',
        })
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'Zip Code: nosuch')
        self.check_attendee_not_found(response, self.attendee)

    def test_zip_code_invalid(self):
        self.client.force_login(self.normal_user)
        response = self.client.post('/reg23/staff/check_in/', {
            'express': '',
            'last_name': '',
            'payflow': '',
            'zip_code': '99999',
        })
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(response, 'Zip Code: 99999')
        self.check_attendee_invalid(response, self.invalid_attendee)

    def test_empty_data(self):
        self.client.force_login(self.normal_user)
        response = self.client.post('/reg23/staff/check_in/', {
            'express': '',
            'last_name': '',
            'payflow': '',
            'zip_code': '',
        })
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.check_attendee_not_found(response, self.attendee)

    def test_multiple_results(self):
        attendee = Attendee.objects.create(badge_type=self.ticket,
                                           order=self.order,
                                           first_name='Bob',
                                           last_name='Smith',
                                           email='bob@example.com',
                                           zip_code='11111',
                                           valid=True)
        self.client.force_login(self.normal_user)
        response = self.client.post('/reg23/staff/check_in/', {
            'express': '',
            'last_name': 'Smith',
            'payflow': '',
            'zip_code': '',
        })
        self.assertEqual(response.status_code, 200)
        self.check_attendee_found(response, self.attendee)
        self.check_attendee_found(response, attendee)

    def test_already_checked_in_attendee(self):
        self.client.force_login(self.normal_user)
        self.attendee.checked_in = True
        self.attendee.save()
        response = self.client.post(
            '/reg23/staff/check_in/', {
                'express': self.attendee.checkin_code(),
                'last_name': '',
                'payflow': '',
                'zip_code': '',
            })
        self.assertEqual(response.status_code, 200)
        self.check_basic_strings(response)
        self.assertContains(
            response, f'Express Check In Code: {self.attendee.checkin_code()}')
        self.check_attendee_already_checked_in(response, self.attendee)
