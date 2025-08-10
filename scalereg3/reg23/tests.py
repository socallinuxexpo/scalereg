import datetime

from django.test import TestCase

from .models import Attendee
from .models import Item
from .models import PromoCode
from .models import Ticket


class RootRedirectTest(TestCase):

    def test_root_redirect(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/reg23/')


class IndexTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        today = datetime.date.today()
        day = datetime.timedelta(days=1)
        Ticket.objects.create(name='T1',
                              description='T1 full',
                              ticket_type='full',
                              price=10,
                              public=True,
                              cash=False,
                              upgradable=False,
                              start_date=today - day,
                              end_date=today + day)
        Ticket.objects.create(name='T2',
                              description='T2 expo',
                              ticket_type='expo',
                              price=5.25,
                              public=True,
                              cash=False,
                              upgradable=False)
        Ticket.objects.create(name='T3',
                              description='T3 press',
                              ticket_type='press',
                              price=0,
                              public=False,
                              cash=False,
                              upgradable=False)
        Ticket.objects.create(name='T4',
                              description='T4 past',
                              ticket_type='expo',
                              price=4.00,
                              public=True,
                              cash=False,
                              upgradable=False,
                              end_date=today)
        Ticket.objects.create(name='T5',
                              description='T5 future',
                              ticket_type='expo',
                              price=6.00,
                              public=True,
                              cash=False,
                              upgradable=False,
                              start_date=today + day)

    def test_ticket_names(self):
        response = self.client.get('/reg23/')
        self.assertContains(
            response,
            '<input type="radio" name="ticket" id="ticket_T1" value="T1" />',
            count=1,
            html=True)
        self.assertContains(
            response,
            '<input type="radio" name="ticket" id="ticket_T2" value="T2" />',
            count=1,
            html=True)
        self.assertNotContains(
            response,
            '<input type="radio" name="ticket" id="ticket_T3" value="T3" />',
            html=True)
        self.assertNotContains(
            response,
            '<input type="radio" name="ticket" id="ticket_T4" value="T4" />',
            html=True)
        self.assertNotContains(
            response,
            '<input type="radio" name="ticket" id="ticket_T5" value="T5" />',
            html=True)

    def test_ticket_descriptions(self):
        response = self.client.get('/reg23/')
        self.assertContains(response,
                            '<td><label for="ticket_T1">T1 full</label></td>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<td><label for="ticket_T2">T2 expo</label></td>',
                            count=1,
                            html=True)
        self.assertNotContains(
            response,
            '<td><label for="ticket_T3">T3 press</label></td>',
            html=True)
        self.assertNotContains(
            response,
            '<td><label for="ticket_T4">T4 past</label></td>',
            html=True)
        self.assertNotContains(
            response,
            '<td><label for="ticket_T5">T5 future</label></td>',
            html=True)

    def test_ticket_prices(self):
        response = self.client.get('/reg23/')
        self.assertContains(response,
                            '<td><label for="ticket_T1">$10.00</label></td>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<td><label for="ticket_T2">$5.25</label></td>',
                            count=1,
                            html=True)
        self.assertNotContains(response,
                               '<td><label for="ticket_T3">$0.00</label></td>',
                               html=True)
        self.assertNotContains(response,
                               '<td><label for="ticket_T4">$4.00</label></td>',
                               html=True)
        self.assertNotContains(response,
                               '<td><label for="ticket_T5">$6.00</label></td>',
                               html=True)


class IndexTestWithPromo(TestCase):

    @classmethod
    def setUpTestData(cls):
        today = datetime.date.today()
        day = datetime.timedelta(days=1)
        Ticket.objects.create(name='T1',
                              description='T1 full',
                              ticket_type='full',
                              price=10,
                              public=True,
                              cash=False,
                              upgradable=False,
                              start_date=today - day,
                              end_date=today + day)
        ticket2_expo = Ticket.objects.create(name='T2',
                                             description='T2 expo',
                                             ticket_type='expo',
                                             price=5.25,
                                             public=True,
                                             cash=False,
                                             upgradable=False)
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
        promo5_expo_only = PromoCode.objects.create(name='P5',
                                                    description='P5 expo only',
                                                    price_modifier=0.7,
                                                    active=True,
                                                    applies_to_all=False)
        promo5_expo_only.applies_to.add(ticket2_expo)

    def test_ticket_prices_with_promo(self):
        response = self.client.post('/reg23/', {'promo': 'P1'})
        self.assertContains(response,
                            '<label for="ticket_T1">$5.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="ticket_T2">$2.62</label>',
                            count=1,
                            html=True)

    def test_ticket_prices_with_promo_lowercase(self):
        response = self.client.post('/reg23/', {'promo': 'p1'})
        self.assertContains(response,
                            '<label for="ticket_T1">$5.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="ticket_T2">$2.62</label>',
                            count=1,
                            html=True)

    def test_ticket_prices_with_inactive_promo(self):
        response = self.client.post('/reg23/', {'promo': 'P2'})
        self.assertContains(response,
                            '<label for="ticket_T1">$10.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="ticket_T2">$5.25</label>',
                            count=1,
                            html=True)

    def test_ticket_prices_with_past_promo(self):
        response = self.client.post('/reg23/', {'promo': 'P3'})
        self.assertContains(response,
                            '<label for="ticket_T1">$10.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="ticket_T2">$5.25</label>',
                            count=1,
                            html=True)

    def test_ticket_prices_with_future_promo(self):
        response = self.client.post('/reg23/', {'promo': 'P4'})
        self.assertContains(response,
                            '<label for="ticket_T1">$10.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="ticket_T2">$5.25</label>',
                            count=1,
                            html=True)

    def test_ticket_prices_with_expo_only_promo(self):
        response = self.client.post('/reg23/', {'promo': 'P5'})
        self.assertContains(response,
                            '<label for="ticket_T1">$10.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="ticket_T2">$3.67</label>',
                            count=1,
                            html=True)

    def test_ticket_prices_with_no_such_promo(self):
        response = self.client.post('/reg23/', {'promo': 'NOSUCH'})
        self.assertContains(response,
                            '<label for="ticket_T1">$10.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="ticket_T2">$5.25</label>',
                            count=1,
                            html=True)

    def test_ticket_prices_with_preset_promo(self):
        response = self.client.get('/reg23/?promo=P1')
        self.assertContains(response,
                            '<label for="ticket_T1">$5.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="ticket_T2">$2.62</label>',
                            count=1,
                            html=True)

    def test_ticket_prices_with_preset_promo_lowercase(self):
        response = self.client.get('/reg23/?promo=p1')
        self.assertContains(response,
                            '<label for="ticket_T1">$5.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="ticket_T2">$2.62</label>',
                            count=1,
                            html=True)

    def test_ticket_prices_with_preset_no_such_promo(self):
        response = self.client.get('/reg23/?promo=NOSUCH')
        self.assertContains(response,
                            '<label for="ticket_T1">$10.00</label>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<label for="ticket_T2">$5.25</label>',
                            count=1,
                            html=True)


class ItemsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        ticket1_full = Ticket.objects.create(name='T1',
                                             description='T1 full',
                                             ticket_type='full',
                                             price=10,
                                             public=True,
                                             cash=False,
                                             upgradable=False)
        Ticket.objects.create(name='T2',
                              description='T2 expo',
                              ticket_type='expo',
                              price=5.25,
                              public=True,
                              cash=False,
                              upgradable=False)
        Item.objects.create(name='I1',
                            description='For all item',
                            price=17,
                            active=True,
                            promo=False,
                            ticket_offset=False,
                            applies_to_all=True)
        item2_full_only = Item.objects.create(name='I2',
                                              description='Full only item',
                                              price=16,
                                              active=True,
                                              promo=False,
                                              ticket_offset=False,
                                              applies_to_all=False)
        item2_full_only.applies_to.add(ticket1_full)
        Item.objects.create(name='I3',
                            description='Inactive item',
                            price=15,
                            active=False,
                            promo=False,
                            ticket_offset=False,
                            applies_to_all=True)

    def test_get_request(self):
        response = self.client.get('/reg23/add_items/')
        self.assertRedirects(response, '/reg23/')

    def test_no_info(self):
        response = self.client.post('/reg23/add_items/')
        self.assertContains(response,
                            '<p>No ticket information.</p>',
                            count=1,
                            html=True)

    def test_no_ticket(self):
        response = self.client.post('/reg23/add_items/', {'promo': ''})
        self.assertContains(response,
                            '<p>No ticket information.</p>',
                            count=1,
                            html=True)

    def test_bad_ticket(self):
        response = self.client.post('/reg23/add_items/', {
            'ticket': 'bad',
            'promo': ''
        })
        self.assertContains(response,
                            '<p>Ticket bad not found.</p>',
                            count=1,
                            html=True)

    def test_ticket_cost_full(self):
        response = self.client.post('/reg23/add_items/', {
            'ticket': 'T1',
            'promo': ''
        })
        self.assertContains(response,
                            '<p>Your T1 full costs $10.00.</p>',
                            count=1,
                            html=True)

    def test_ticket_cost_expo(self):
        response = self.client.post('/reg23/add_items/', {
            'ticket': 'T2',
            'promo': ''
        })
        self.assertContains(response,
                            '<p>Your T2 expo costs $5.25.</p>',
                            count=1,
                            html=True)

    def test_ticket_names_full(self):
        response = self.client.post('/reg23/add_items/', {
            'ticket': 'T1',
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

    def test_ticket_names_expo(self):
        response = self.client.post('/reg23/add_items/', {
            'ticket': 'T2',
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

    def test_ticket_descriptions_full(self):
        response = self.client.post('/reg23/add_items/', {
            'ticket': 'T1',
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

    def test_ticket_descriptions_expo(self):
        response = self.client.post('/reg23/add_items/', {
            'ticket': 'T2',
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

    def test_ticket_prices_full(self):
        response = self.client.post('/reg23/add_items/', {
            'ticket': 'T1',
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

    def test_ticket_prices_expo(self):
        response = self.client.post('/reg23/add_items/', {
            'ticket': 'T2',
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
        Ticket.objects.create(name='T1',
                              description='T1 full',
                              ticket_type='full',
                              price=10,
                              public=True,
                              cash=False,
                              upgradable=False)
        ticket2_expo = Ticket.objects.create(name='T2',
                                             description='T2 expo',
                                             ticket_type='expo',
                                             price=5.25,
                                             public=True,
                                             cash=False,
                                             upgradable=False)
        Item.objects.create(name='I1',
                            description='Applies to promo',
                            price=17,
                            active=True,
                            promo=True,
                            ticket_offset=False,
                            applies_to_all=True)
        Item.objects.create(name='I2',
                            description='Does not apply to promo',
                            price=16.11,
                            active=True,
                            promo=False,
                            ticket_offset=False,
                            applies_to_all=True)
        promo1_expo_only = PromoCode.objects.create(name='P1',
                                                    description='P1 expo only',
                                                    price_modifier=0.5,
                                                    active=True,
                                                    applies_to_all=False)
        promo1_expo_only.applies_to.add(ticket2_expo)

    def test_full_ticket_with_promo(self):
        response = self.client.post('/reg23/add_items/', {
            'ticket': 'T1',
            'promo': 'P1'
        })
        self.assertContains(response,
                            '<p>Your T1 full costs $10.00.</p>',
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

    def test_full_ticket_with_promo_lowercase(self):
        response = self.client.post('/reg23/add_items/', {
            'ticket': 'T1',
            'promo': 'p1'
        })
        self.assertContains(response,
                            '<p>Your T1 full costs $10.00.</p>',
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

    def test_full_ticket_with_no_such_promo(self):
        response = self.client.post('/reg23/add_items/', {
            'ticket': 'T1',
            'promo': 'BAD'
        })
        self.assertContains(response,
                            '<p>Your T1 full costs $10.00.</p>',
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

    def test_expo_ticket_with_promo(self):
        response = self.client.post('/reg23/add_items/', {
            'ticket': 'T2',
            'promo': 'P1'
        })
        self.assertContains(response,
                            '<p>Your T2 expo costs $2.62.</p>',
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

    def test_expo_ticket_with_no_such_promo(self):
        response = self.client.post('/reg23/add_items/', {
            'ticket': 'T2',
            'promo': 'BAD'
        })
        self.assertContains(response,
                            '<p>Your T2 expo costs $5.25.</p>',
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


class AttendeeTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        today = datetime.date.today()
        day = datetime.timedelta(days=1)
        Ticket.objects.create(name='T1',
                              description='T1 full',
                              ticket_type='full',
                              price=10,
                              public=True,
                              cash=False,
                              upgradable=False,
                              start_date=today - day,
                              end_date=today + day)
        Ticket.objects.create(name='T2',
                              description='T2 expo',
                              ticket_type='expo',
                              price=5.25,
                              public=True,
                              cash=False,
                              upgradable=False)
        Item.objects.create(name='I1',
                            description='The item',
                            price=6.77,
                            active=True,
                            promo=False,
                            ticket_offset=False,
                            applies_to_all=True)
        Item.objects.create(name='I2',
                            description='The offset item',
                            price=99.99,
                            active=True,
                            promo=False,
                            ticket_offset=True,
                            applies_to_all=True)

    def check_first_attendee(self, attendee):
        self.assertEqual(attendee.first_name, 'First')
        self.assertEqual(attendee.last_name, 'Last')
        self.assertEqual(attendee.email, 'a@a.com')
        self.assertEqual(attendee.zip_code, '12345')

    def check_second_attendee(self, attendee):
        self.assertEqual(attendee.first_name, 'Second')
        self.assertEqual(attendee.last_name, 'Last')
        self.assertEqual(attendee.email, 'b@a.com')
        self.assertEqual(attendee.zip_code, '54321')

    def test_get_request(self):
        response = self.client.get('/reg23/add_attendee/')
        self.assertRedirects(response, '/reg23/')

    def test_no_info(self):
        response = self.client.post('/reg23/add_attendee/')
        self.assertContains(response,
                            '<p>No ticket information.</p>',
                            count=1,
                            html=True)

    def test_no_ticket(self):
        response = self.client.post(
            '/reg23/add_attendee/', {'promo': ''},
            HTTP_REFERER='https://example.com/reg23/add_items/')
        self.assertContains(response,
                            '<p>No ticket information.</p>',
                            count=1,
                            html=True)

    def test_no_promo(self):
        response = self.client.post(
            '/reg23/add_attendee/', {'ticket': 'T1'},
            HTTP_REFERER='https://example.com/reg23/add_items/')
        self.assertContains(response,
                            '<p>No promo information.</p>',
                            count=1,
                            html=True)

    def test_no_referrer(self):
        response = self.client.post('/reg23/add_attendee/', {
            'ticket': 'T1',
            'promo': ''
        })
        self.assertContains(response,
                            '<p>Invalid referrer.</p>',
                            count=1,
                            html=True)

    def test_invalid_referrer(self):
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': ''
            },
            HTTP_REFERER='https://example.com/reg23/invalid/')
        self.assertContains(response,
                            '<p>Invalid referrer.</p>',
                            count=1,
                            html=True)

    def test_bad_ticket(self):
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'bad',
                'promo': ''
            },
            HTTP_REFERER='https://example.com/reg23/add_items/')
        self.assertContains(response,
                            '<p>Ticket bad not found.</p>',
                            count=1,
                            html=True)

    def test_ticket_empty_promo(self):
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': ''
            },
            HTTP_REFERER='https://example.com/reg23/add_items/')
        self.assertContains(response,
                            '<p>Your T1 full costs $10.00.</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>Your total is $10.00.</p>',
                            count=1,
                            html=True)
        self.assertNotContains(response, 'You are using promo code')
        self.assertNotContains(response, 'additional items')

    def test_ticket_empty_promo_and_item(self):
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': '',
                'item0': 'I1'
            },
            HTTP_REFERER='https://example.com/reg23/add_items/')
        self.assertContains(response,
                            '<p>Your T1 full costs $10.00.</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>* The item ($6.77)</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>Your total is $16.77.</p>',
                            count=1,
                            html=True)
        self.assertNotContains(response, 'You are using promo code')

    def test_ticket_empty_promo_and_offset_item(self):
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': '',
                'item0': 'I2'
            },
            HTTP_REFERER='https://example.com/reg23/add_items/')
        self.assertContains(response,
                            '<p>Your T1 full costs $10.00.</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>* The offset item ($99.99)</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>Your total is $99.99.</p>',
                            count=1,
                            html=True)
        self.assertContains(
            response,
            '<p>* The offset item waives the ticket price of $10.00.</p>',
            count=1,
            html=True)
        self.assertNotContains(response, 'You are using promo code')

    def test_ticket_empty_promo_and_no_such_item(self):
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': '',
                'item0': 'NOSUCH',
                'item1': 'NOSUCH',
                'item2': 'NOSUCH'
            },
            HTTP_REFERER='https://example.com/reg23/add_items/')
        self.assertContains(response,
                            '<p>Your T1 full costs $10.00.</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>Your total is $10.00.</p>',
                            count=1,
                            html=True)
        self.assertNotContains(response, 'You are using promo code')
        self.assertNotContains(response, 'additional items')

    def test_validate_missing_form_data(self):
        self.client.get('/reg23/')
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': ''
            },
            HTTP_REFERER='https://example.com/reg23/add_attendee/')
        self.assertContains(response, 'This field is required.')
        self.assertEqual(Attendee.objects.count(), 0)

    def test_validate_missing_cookie(self):
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': '',
                'first_name': 'First',
                'last_name': 'Last',
                'email': 'a@a.com',
                'zip_code': '12345'
            },
            HTTP_REFERER='https://example.com/reg23/add_attendee/')
        self.assertContains(response,
                            'Please do not register multiple attendees')
        self.assertEqual(Attendee.objects.count(), 0)

    def test_validate_double_post(self):
        self.client.get('/reg23/')
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': '',
                'first_name': 'First',
                'last_name': 'Last',
                'email': 'a@a.com',
                'zip_code': '12345'
            },
            HTTP_REFERER='https://example.com/reg23/add_attendee/')
        self.assertRedirects(response, '/reg23/registered_attendee/')
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': '',
                'first_name': 'First',
                'last_name': 'Last',
                'email': 'a@a.com',
                'zip_code': '54321'
            },
            HTTP_REFERER='https://example.com/reg23/add_attendee/')
        self.assertContains(response, 'Already added attendee')
        self.assertIn('payment', self.client.session.keys())
        self.assertEqual(self.client.session.get('payment'), [1])
        self.assertEqual(Attendee.objects.count(), 1)
        self.check_first_attendee(Attendee.objects.get(id=1))

    def test_validate_form_data(self):
        self.client.get('/reg23/')
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': '',
                'first_name': 'First',
                'last_name': 'Last',
                'email': 'a@a.com',
                'zip_code': '12345'
            },
            HTTP_REFERER='https://example.com/reg23/add_attendee/')
        self.assertRedirects(response, '/reg23/registered_attendee/')
        self.assertIn('payment', self.client.session.keys())
        self.assertEqual(self.client.session.get('payment'), [1])
        self.assertEqual(Attendee.objects.count(), 1)
        self.check_first_attendee(Attendee.objects.get(id=1))

    def test_validate_form_data_with_trailing_spaces(self):
        self.client.get('/reg23/')
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': '',
                'first_name': 'First ',
                'last_name': 'Last ',
                'email': 'a@a.com ',
                'zip_code': '12345 '
            },
            HTTP_REFERER='https://example.com/reg23/add_attendee/')
        self.assertRedirects(response, '/reg23/registered_attendee/')
        self.assertIn('payment', self.client.session.keys())
        self.assertEqual(self.client.session.get('payment'), [1])
        self.assertEqual(Attendee.objects.count(), 1)
        self.check_first_attendee(Attendee.objects.get(id=1))

    def test_validate_form_data_including_items(self):
        self.client.get('/reg23/')
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': '',
                'first_name': 'First',
                'last_name': 'Last',
                'email': 'a@a.com',
                'zip_code': '12345',
                'item0': 'I1'
            },
            HTTP_REFERER='https://example.com/reg23/add_attendee/')
        self.assertRedirects(response, '/reg23/registered_attendee/')
        self.assertIn('payment', self.client.session.keys())
        self.assertEqual(self.client.session.get('payment'), [1])
        self.assertEqual(Attendee.objects.count(), 1)
        self.check_first_attendee(Attendee.objects.get(id=1))

    def test_validate_multiple_attendees(self):
        self.client.get('/reg23/')
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': '',
                'first_name': 'First',
                'last_name': 'Last',
                'email': 'a@a.com',
                'zip_code': '12345'
            },
            HTTP_REFERER='https://example.com/reg23/add_attendee/')
        self.assertRedirects(response, '/reg23/registered_attendee/')
        self.client.post('/reg23/add_attendee/', {
            'ticket': 'T1',
            'promo': ''
        },
                         HTTP_REFERER='https://example.com/reg23/add_items/')
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': '',
                'first_name': 'Second',
                'last_name': 'Last',
                'email': 'b@a.com',
                'zip_code': '54321'
            },
            HTTP_REFERER='https://example.com/reg23/add_attendee/')
        self.assertRedirects(response, '/reg23/registered_attendee/')
        self.assertIn('payment', self.client.session.keys())
        self.assertEqual(self.client.session.get('payment'), [1, 2])
        self.assertEqual(Attendee.objects.count(), 2)
        self.check_first_attendee(Attendee.objects.get(id=1))
        self.check_second_attendee(Attendee.objects.get(id=2))


class AttendeeTestWithPromo(TestCase):

    @classmethod
    def setUpTestData(cls):
        Ticket.objects.create(name='T1',
                              description='T1 full',
                              ticket_type='full',
                              price=10,
                              public=True,
                              cash=False,
                              upgradable=False)
        ticket2_expo = Ticket.objects.create(name='T2',
                                             description='T2 expo',
                                             ticket_type='expo',
                                             price=5.25,
                                             public=True,
                                             cash=False,
                                             upgradable=False)
        Item.objects.create(name='I1',
                            description='Applies to promo',
                            price=17,
                            active=True,
                            promo=True,
                            ticket_offset=False,
                            applies_to_all=True)
        Item.objects.create(name='I2',
                            description='Does not apply to promo',
                            price=16.11,
                            active=True,
                            promo=False,
                            ticket_offset=False,
                            applies_to_all=True)
        promo1_expo_only = PromoCode.objects.create(name='P1',
                                                    description='P1 expo only',
                                                    price_modifier=0.5,
                                                    active=True,
                                                    applies_to_all=False)
        promo1_expo_only.applies_to.add(ticket2_expo)

    def test_full_ticket_with_promo(self):
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': 'P1'
            },
            HTTP_REFERER='https://example.com/reg23/add_items/')
        self.assertContains(response,
                            '<p>You are using promo code <b>P1</b>.</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>Your T1 full costs $10.00.</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>Your total is $10.00.</p>',
                            count=1,
                            html=True)
        self.assertNotContains(response, 'additional items')

    def test_full_ticket_with_promo_and_items(self):
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': 'P1',
                'item0': 'I1',
                'item1': 'I2'
            },
            HTTP_REFERER='https://example.com/reg23/add_items/')
        self.assertContains(response,
                            '<p>You are using promo code <b>P1</b>.</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>Your T1 full costs $10.00.</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>* Applies to promo ($8.50)</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>* Does not apply to promo ($16.11)</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>Your total is $34.61.</p>',
                            count=1,
                            html=True)

    def test_expo_ticket_with_promo(self):
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T2',
                'promo': 'P1'
            },
            HTTP_REFERER='https://example.com/reg23/add_items/')
        self.assertContains(response,
                            '<p>You are using promo code <b>P1</b>.</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>Your T2 expo costs $2.62.</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>Your total is $2.62.</p>',
                            count=1,
                            html=True)
        self.assertNotContains(response, 'additional items')

    def test_expo_ticket_with_promo_and_items(self):
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T2',
                'promo': 'P1',
                'item0': 'I1',
                'item1': 'I2'
            },
            HTTP_REFERER='https://example.com/reg23/add_items/')
        self.assertContains(response,
                            '<p>You are using promo code <b>P1</b>.</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>Your T2 expo costs $2.62.</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>* Applies to promo ($8.50)</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>* Does not apply to promo ($16.11)</p>',
                            count=1,
                            html=True)
        self.assertContains(response,
                            '<p>Your total is $27.23.</p>',
                            count=1,
                            html=True)

    def test_validate_missing_form_data(self):
        self.client.get('/reg23/')
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': 'P1'
            },
            HTTP_REFERER='https://example.com/reg23/add_attendee/')
        self.assertContains(response, 'This field is required.')

    def test_validate_form_data(self):
        self.client.get('/reg23/')
        response = self.client.post(
            '/reg23/add_attendee/', {
                'ticket': 'T1',
                'promo': 'P1',
                'first_name': 'First',
                'last_name': 'Last',
                'email': 'a@a.com',
                'zip_code': '12345'
            },
            HTTP_REFERER='https://example.com/reg23/add_attendee/')
        self.assertRedirects(response, '/reg23/registered_attendee/')
        self.assertIn('payment', self.client.session.keys())
        self.assertEqual(self.client.session.get('payment'), [1])
