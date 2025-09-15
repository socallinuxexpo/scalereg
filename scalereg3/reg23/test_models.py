import decimal

from django.test import TestCase

from .models import Answer
from .models import Attendee
from .models import Item
from .models import PendingOrder
from .models import PromoCode
from .models import Question
from .models import Ticket


class TicketCostTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.ticket = Ticket.objects.create(name='T1',
                                           description='T1',
                                           ticket_type='full',
                                           price=decimal.Decimal(10),
                                           public=True,
                                           cash=False,
                                           upgradable=False)
        cls.promo = PromoCode.objects.create(
            name='P1',
            description='P1 all',
            price_modifier=decimal.Decimal(0.6),
            active=True,
            applies_to_all=True)
        cls.item1 = Item.objects.create(name='I1',
                                        description='Item 1',
                                        price=decimal.Decimal(17),
                                        active=True,
                                        promo=False,
                                        ticket_offset=False,
                                        applies_to_all=True)
        cls.item2 = Item.objects.create(name='I2',
                                        description='Item 2',
                                        price=decimal.Decimal(6),
                                        active=True,
                                        promo=True,
                                        ticket_offset=False,
                                        applies_to_all=True)
        cls.item3 = Item.objects.create(name='I3',
                                        description='Ticket offset 1',
                                        price=decimal.Decimal(14),
                                        active=True,
                                        promo=False,
                                        ticket_offset=True,
                                        applies_to_all=True)
        cls.item4 = Item.objects.create(name='I4',
                                        description='Ticket offset 1',
                                        price=decimal.Decimal(19),
                                        active=True,
                                        promo=True,
                                        ticket_offset=True,
                                        applies_to_all=True)

    def test_no_items(self):
        cost = self.ticket.ticket_cost([], None)
        self.assertEqual(cost, 10)
        cost = self.ticket.ticket_cost([], self.promo)
        self.assertEqual(cost, 6)

    def test_single_item(self):
        cost = self.ticket.ticket_cost([self.item1], None)
        self.assertEqual(cost, 27)
        cost = self.ticket.ticket_cost([self.item1], self.promo)
        self.assertEqual(cost, 23)

    def test_multiple_items(self):
        cost = self.ticket.ticket_cost([self.item1, self.item2], None)
        self.assertEqual(cost, 33)
        cost = self.ticket.ticket_cost([self.item1, self.item2], self.promo)
        self.assertAlmostEqual(cost, decimal.Decimal(26.60))

    def test_with_ticket_offset_item(self):
        cost = self.ticket.ticket_cost([self.item3], None)
        self.assertEqual(cost, 14)
        cost = self.ticket.ticket_cost([self.item3], self.promo)
        self.assertEqual(cost, 14)

    def test_with_two_ticket_offset_items(self):
        cost = self.ticket.ticket_cost([self.item3, self.item4], None)
        self.assertEqual(cost, 33)
        cost = self.ticket.ticket_cost([self.item3, self.item4], self.promo)
        self.assertAlmostEqual(cost, decimal.Decimal(25.40))

    def test_with_regular_item_and_ticket_offset_item(self):
        cost = self.ticket.ticket_cost([self.item2, self.item3], None)
        self.assertEqual(cost, 20)
        cost = self.ticket.ticket_cost([self.item2, self.item3], self.promo)
        self.assertAlmostEqual(cost, decimal.Decimal(17.60))


class AttendeeCheckinCodeTest(TestCase):

    def test_name(self):
        ticket = Ticket.objects.create(name='T1',
                                       description='T1',
                                       ticket_type='full',
                                       price=decimal.Decimal(10),
                                       public=True,
                                       cash=False,
                                       upgradable=False)
        attendee = Attendee.objects.create(badge_type=ticket,
                                           first_name='Foo',
                                           last_name='Bar Qux')
        self.assertEqual(attendee.checkin_code(), '00018d4d7f')


class AttendeeFullNameTest(TestCase):

    def test_name(self):
        ticket = Ticket.objects.create(name='T1',
                                       description='T1',
                                       ticket_type='full',
                                       price=decimal.Decimal(10),
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
                                       price=decimal.Decimal(10),
                                       public=True,
                                       cash=False,
                                       upgradable=False)
        cls.item1 = Item.objects.create(name='I1',
                                        description='No promo item',
                                        price=decimal.Decimal(17),
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


class AttendeeTicketCostWithPromoTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        ticket = Ticket.objects.create(name='T1',
                                       description='T1',
                                       ticket_type='full',
                                       price=decimal.Decimal(10),
                                       public=True,
                                       cash=False,
                                       upgradable=False)
        promo = PromoCode.objects.create(name='P1',
                                         description='P1 all',
                                         price_modifier=decimal.Decimal(0.6),
                                         active=True,
                                         applies_to_all=True)
        cls.item1 = Item.objects.create(name='I1',
                                        description='No promo item',
                                        price=decimal.Decimal(17),
                                        active=True,
                                        promo=False,
                                        ticket_offset=False,
                                        applies_to_all=True)
        cls.item2 = Item.objects.create(name='I2',
                                        description='Promo item',
                                        price=decimal.Decimal(30),
                                        active=True,
                                        promo=True,
                                        ticket_offset=False,
                                        applies_to_all=True)
        cls.attendee = Attendee.objects.create(badge_type=ticket,
                                               first_name='Foo',
                                               last_name='Bar',
                                               promo=promo)

    def test_no_items(self):
        self.assertEqual(self.attendee.ticket_cost(), 6)
        # Make sure there are no side effects in the previous call.
        self.assertEqual(self.attendee.ticket_cost(), 6)

    def test_item_no_promo(self):
        self.attendee.ordered_items.add(self.item1)
        self.assertEqual(self.attendee.ticket_cost(), 23)
        # Make sure there are no side effects in the previous call.
        self.assertEqual(self.attendee.ticket_cost(), 23)

    def test_item_promo(self):
        self.attendee.ordered_items.add(self.item2)
        self.assertEqual(self.attendee.ticket_cost(), 24)
        # Make sure there are no side effects in the previous call.
        self.assertEqual(self.attendee.ticket_cost(), 24)

    def test_items(self):
        self.attendee.ordered_items.add(self.item1)
        self.attendee.ordered_items.add(self.item2)
        self.assertEqual(self.attendee.ticket_cost(), 41)
        # Make sure there are no side effects in the previous call.
        self.assertEqual(self.attendee.ticket_cost(), 41)


class PendingOrderTest(TestCase):

    def test_attendees_list(self):
        pending_order = PendingOrder.objects.create(order_num='1234567890',
                                                    attendees='1,2,34,567')
        empty_pending_order = PendingOrder.objects.create(
            order_num='EEEEEEEEEE', attendees='')
        self.assertEqual(pending_order.attendees_list(), [1, 2, 34, 567])
        self.assertEqual(empty_pending_order.attendees_list(), [])


class QuestionTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.ticket1 = Ticket.objects.create(name='T1',
                                            description='T1',
                                            ticket_type='full',
                                            price=decimal.Decimal(10),
                                            public=True,
                                            cash=False,
                                            upgradable=False)
        cls.item1 = Item.objects.create(name='I1',
                                        description='Item 1',
                                        price=decimal.Decimal(17),
                                        active=True,
                                        promo=False,
                                        ticket_offset=False,
                                        applies_to_all=True)

        cls.list_question = Question.objects.create(text='Color?',
                                                    applies_to_all=True)
        cls.answer1 = Answer.objects.create(question=cls.list_question,
                                            text='Red')
        cls.answer2 = Answer.objects.create(question=cls.list_question,
                                            text='Blue')
        cls.text_question = Question.objects.create(text='Name?',
                                                    applies_to_all=False,
                                                    is_text_question=True)
        cls.text_question.applies_to_tickets.add(cls.ticket1)
        cls.text_question.applies_to_items.add(cls.item1)

    def test_str(self):
        self.assertEqual(str(self.list_question), 'List Question: Color?')
        self.assertEqual(str(self.answer1), '(1) Red')
        self.assertEqual(str(self.answer2), '(1) Blue')
        self.assertEqual(str(self.text_question), 'Text Question: Name?')

    def test_get_list_answers(self):
        self.assertQuerySetEqual(self.list_question.get_list_answers(),
                                 (self.answer1, self.answer2))

    def test_is_applicable_to_ticket(self):
        ticket2 = Ticket.objects.create(name='T2',
                                        description='T2',
                                        ticket_type='expo',
                                        price=decimal.Decimal(5),
                                        public=True,
                                        cash=False,
                                        upgradable=False)
        self.assertTrue(
            self.list_question.is_applicable_to_ticket(self.ticket1))
        self.assertTrue(self.list_question.is_applicable_to_ticket(ticket2))
        self.assertTrue(
            self.text_question.is_applicable_to_ticket(self.ticket1))
        self.assertFalse(self.text_question.is_applicable_to_ticket(ticket2))

    def test_is_applicable_to_item(self):
        item2 = Item.objects.create(name='I2',
                                    description='Item 2',
                                    price=decimal.Decimal(6),
                                    active=True,
                                    promo=False,
                                    ticket_offset=False,
                                    applies_to_all=True)
        self.assertFalse(self.list_question.is_applicable_to_item(self.item1))
        self.assertFalse(self.list_question.is_applicable_to_item(item2))
        self.assertTrue(self.text_question.is_applicable_to_item(self.item1))
        self.assertFalse(self.text_question.is_applicable_to_item(item2))
