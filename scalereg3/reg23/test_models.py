from django.test import TestCase

from .models import Attendee
from .models import Item
from .models import Ticket


class TicketCostTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.ticket = Ticket.objects.create(name='T1',
                                           description='T1',
                                           ticket_type='full',
                                           price=10,
                                           public=True,
                                           cash=False,
                                           upgradable=False)
        cls.item1 = Item.objects.create(name='I1',
                                        description='Item 1',
                                        price=17,
                                        active=True,
                                        promo=False,
                                        ticket_offset=False,
                                        applies_to_all=True)
        cls.item2 = Item.objects.create(name='I2',
                                        description='Item 2',
                                        price=6,
                                        active=True,
                                        promo=False,
                                        ticket_offset=False,
                                        applies_to_all=True)
        cls.item3 = Item.objects.create(name='I3',
                                        description='Ticket offset 1',
                                        price=14,
                                        active=True,
                                        promo=False,
                                        ticket_offset=True,
                                        applies_to_all=True)
        cls.item4 = Item.objects.create(name='I4',
                                        description='Ticket offset 1',
                                        price=19,
                                        active=True,
                                        promo=False,
                                        ticket_offset=True,
                                        applies_to_all=True)

    def test_no_items(self):
        cost = self.ticket.ticket_cost([])
        self.assertEqual(cost, 10)

    def test_single_item(self):
        cost = self.ticket.ticket_cost([self.item1])
        self.assertEqual(cost, 27)

    def test_multiple_items(self):
        cost = self.ticket.ticket_cost([self.item1, self.item2])
        self.assertEqual(cost, 33)

    def test_with_ticket_offset_item(self):
        cost = self.ticket.ticket_cost([self.item3])
        self.assertEqual(cost, 14)

    def test_with_two_ticket_offset_items(self):
        cost = self.ticket.ticket_cost([self.item3, self.item4])
        self.assertEqual(cost, 33)

    def test_with_regular_item_and_ticket_offset_item(self):
        cost = self.ticket.ticket_cost([self.item2, self.item3])
        self.assertEqual(cost, 20)


class AttendeeFullNameTest(TestCase):

    def test_name(self):
        ticket = Ticket.objects.create(name='T1',
                                       description='T1',
                                       ticket_type='full',
                                       price=10,
                                       public=True,
                                       cash=False,
                                       upgradable=False)
        attendee = Attendee.objects.create(badge_type=ticket,
                                           first_name='Foo',
                                           last_name='Bar Qux')
        self.assertEqual(attendee.full_name(), 'Foo Bar Qux')


class AttendeeTicketCostTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        ticket = Ticket.objects.create(name='T1',
                                       description='T1',
                                       ticket_type='full',
                                       price=10,
                                       public=True,
                                       cash=False,
                                       upgradable=False)
        cls.item1 = Item.objects.create(name='I1',
                                        description='Promo',
                                        price=17,
                                        active=True,
                                        promo=False,
                                        ticket_offset=False,
                                        applies_to_all=True)
        cls.attendee = Attendee.objects.create(badge_type=ticket,
                                               first_name='Foo',
                                               last_name='Bar')

    def test_no_items(self):
        self.assertEqual(self.attendee.ticket_cost(), 10)

    def test_item_no_promo(self):
        self.attendee.ordered_items.add(self.item1)
        self.assertEqual(self.attendee.ticket_cost(), 27)
