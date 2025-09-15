import decimal

from django.test import TestCase

from .models import Attendee, Item, Ticket
from .views import generate_notify_attendee_body, get_posted_items


class GetPostedItemsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.item1 = Item.objects.create(name='I1',
                                        description='Item 1',
                                        price=decimal.Decimal(10),
                                        active=True,
                                        promo=False,
                                        ticket_offset=False,
                                        applies_to_all=True)
        cls.item2 = Item.objects.create(name='I2',
                                        description='Item 2',
                                        price=decimal.Decimal(20),
                                        active=True,
                                        promo=False,
                                        ticket_offset=False,
                                        applies_to_all=True)
        cls.item3 = Item.objects.create(name='I3',
                                        description='Item 3',
                                        price=decimal.Decimal(30),
                                        active=False,
                                        promo=False,
                                        ticket_offset=False,
                                        applies_to_all=True)

    def test_no_items_posted(self):
        post = {}
        avail_items = [self.item1, self.item2]
        selected_items = get_posted_items(post, avail_items)
        self.assertEqual(len(selected_items), 0)

    def test_one_item_posted(self):
        post = {'item0': 'I1'}
        avail_items = [self.item1, self.item2]
        selected_items = get_posted_items(post, avail_items)
        self.assertEqual(len(selected_items), 1)
        self.assertIn(self.item1, selected_items)

    def test_multiple_items_posted(self):
        post = {'item0': 'I1', 'item1': 'I2'}
        avail_items = [self.item1, self.item2]
        selected_items = get_posted_items(post, avail_items)
        self.assertEqual(len(selected_items), 2)
        self.assertIn(self.item1, selected_items)
        self.assertIn(self.item2, selected_items)

    def test_item_not_in_avail_items(self):
        post = {'item0': 'I3'}
        avail_items = [self.item1, self.item2]
        selected_items = get_posted_items(post, avail_items)
        self.assertEqual(len(selected_items), 0)

    def test_item_name_does_not_exist(self):
        post = {'item0': 'I4'}
        avail_items = [self.item1, self.item2]
        selected_items = get_posted_items(post, avail_items)
        self.assertEqual(len(selected_items), 0)

    def test_post_with_extra_keys(self):
        post = {'item0': 'I1', 'foo': 'bar'}
        avail_items = [self.item1, self.item2]
        selected_items = get_posted_items(post, avail_items)
        self.assertEqual(len(selected_items), 1)
        self.assertIn(self.item1, selected_items)

    def test_too_many_items_posted(self):
        post = {'item0': 'I1', 'item1': 'I2'}
        avail_items = [self.item1]
        selected_items = get_posted_items(post, avail_items)
        self.assertEqual(len(selected_items), 1)
        self.assertIn(self.item1, selected_items)

    def test_repeated_items_posted(self):
        post = {'item0': 'I1', 'item1': 'I1', 'item2': 'I2'}
        avail_items = [self.item1, self.item2]
        selected_items = get_posted_items(post, avail_items)
        self.assertEqual(len(selected_items), 1)
        self.assertIn(self.item1, selected_items)


class GenerateNotifyAttendeeBodyTest(TestCase):

    def test_generate_body(self):
        ticket = Ticket.objects.create(name='T1',
                                       description='Ticket 1',
                                       price=decimal.Decimal(100),
                                       public=True,
                                       cash=False,
                                       upgradable=False,
                                       ticket_type='full')
        attendee = Attendee.objects.create(first_name='Test',
                                           last_name='User II',
                                           email='a@b.com',
                                           zip_code='12345',
                                           badge_type=ticket)

        expected = '''Thank you for registering for SCALE.
The details of your registration are included below.

Please note the Express Check-In Code below, which will allow you to
speed up your check-in and badge pickup on-site.

First Name: Test
Last Name: User II
Email: a@b.com
Zip Code: 12345

Badge Type: Ticket 1
Express Check-In Code: 0001cf7b36
'''
        self.assertEqual(generate_notify_attendee_body(attendee), expected)
