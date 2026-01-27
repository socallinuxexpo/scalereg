from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from .admin import AttendeeAdmin
from .admin import OrderAdmin
from .admin import PaymentCodeAdmin
from .admin import UpgradeAdmin
from .models import Attendee
from .models import Order
from .models import PaymentCode
from .models import PromoCode
from .models import Ticket
from .models import Upgrade


class AttendeeAdminTest(TestCase):

    def setUp(self):
        site = AdminSite()
        self.admin = AttendeeAdmin(Attendee, site)

        ticket = Ticket.objects.create(name='FULL',
                                       description='Full Pass',
                                       price=100,
                                       public=True,
                                       cash=True,
                                       upgradable=True)
        order = Order.objects.create(order_num='ABCDE12345',
                                     name='Test User',
                                     address='123 St',
                                     city='City',
                                     state='ST',
                                     zip_code='12345',
                                     email='test@example.com',
                                     amount=100,
                                     payment_type='cash')
        promo = PromoCode.objects.create(name='DISC',
                                         description='Discount',
                                         price_modifier=0.9,
                                         active=True)
        self.attendee = Attendee(badge_type=ticket, order=order, promo=promo)

    def test_fieldsets(self):
        form = self.admin.get_form(self.client.request)()
        self.assertIn('first_name', form.fields)
        self.assertIn('last_name', form.fields)
        self.assertIn('ordered_items', form.fields)

    def test_link_to_badge_type(self):
        self.assertEqual(
            self.admin.link_to_badge_type(self.attendee),
            '<a href="/admin/reg23/ticket/FULL/change/">FULL</a>')

    def test_link_to_order(self):
        self.assertEqual(
            self.admin.link_to_order(self.attendee),
            '<a href="/admin/reg23/order/ABCDE12345/change/">ABCDE12345</a>')
        self.attendee.order = None
        self.assertEqual(self.admin.link_to_order(self.attendee), '-')

    def test_link_to_promo(self):
        self.assertEqual(
            self.admin.link_to_promo(self.attendee),
            '<a href="/admin/reg23/promocode/DISC/change/">DISC</a>')

        self.attendee.promo = None
        self.assertEqual(self.admin.link_to_promo(self.attendee), '-')


class OrderAdminTest(TestCase):

    def setUp(self):
        site = AdminSite()
        self.admin = OrderAdmin(Order, site)

    def test_fieldsets(self):
        form = self.admin.get_form(self.client.request)()
        self.assertIn('payflow_auth_code', form.fields)
        self.assertIn('payflow_pnref', form.fields)
        self.assertIn('payflow_resp_msg', form.fields)
        self.assertIn('payflow_result', form.fields)


class PaymentCodeAdminTest(TestCase):

    def setUp(self):
        site = AdminSite()
        self.admin = PaymentCodeAdmin(PaymentCode, site)

        ticket = Ticket.objects.create(name='FULL',
                                       description='Full Pass',
                                       price=100,
                                       public=True,
                                       cash=True,
                                       upgradable=True)
        order = Order.objects.create(order_num='ORDER12345',
                                     amount=0,
                                     payment_type='cash')
        self.payment_code = PaymentCode(code='PAYMENT123',
                                        badge_type=ticket,
                                        order=order,
                                        max_attendees=1)

    def test_link_to_badge_type(self):
        self.assertEqual(
            self.admin.link_to_badge_type(self.payment_code),
            '<a href="/admin/reg23/ticket/FULL/change/">FULL</a>')

    def test_link_to_order(self):
        self.assertEqual(
            self.admin.link_to_order(self.payment_code),
            '<a href="/admin/reg23/order/ORDER12345/change/">ORDER12345</a>')


class UpgradeAdminTest(TestCase):

    def setUp(self):
        site = AdminSite()
        self.admin = UpgradeAdmin(Upgrade, site)

        ticket_old = Ticket.objects.create(name='OLD',
                                           description='Old Pass',
                                           price=50,
                                           public=True,
                                           cash=True,
                                           upgradable=True)
        ticket_new = Ticket.objects.create(name='NEW',
                                           description='New Pass',
                                           price=100,
                                           public=True,
                                           cash=True,
                                           upgradable=True)
        order_old = Order.objects.create(order_num='ORDER00001',
                                         amount=50,
                                         payment_type='cash')
        order_new = Order.objects.create(order_num='ORDER00002',
                                         amount=50,
                                         payment_type='cash')
        attendee = Attendee.objects.create(badge_type=ticket_old,
                                           email='t@t.com',
                                           zip_code='12345',
                                           first_name='F',
                                           last_name='L')
        self.upgrade = Upgrade(attendee=attendee,
                               old_badge_type=ticket_old,
                               old_order=order_old,
                               new_badge_type=ticket_new,
                               new_order=order_new)

    def test_link_to_old_badge_type(self):
        self.assertEqual(self.admin.link_to_old_badge_type(self.upgrade),
                         '<a href="/admin/reg23/ticket/OLD/change/">OLD</a>')

    def test_link_to_new_badge_type(self):
        self.assertEqual(self.admin.link_to_new_badge_type(self.upgrade),
                         '<a href="/admin/reg23/ticket/NEW/change/">NEW</a>')

    def test_link_to_old_order(self):
        self.assertEqual(
            self.admin.link_to_old_order(self.upgrade),
            '<a href="/admin/reg23/order/ORDER00001/change/">ORDER00001</a>')

    def test_link_to_new_order(self):
        self.assertEqual(
            self.admin.link_to_new_order(self.upgrade),
            '<a href="/admin/reg23/order/ORDER00002/change/">ORDER00002</a>')
        self.upgrade.new_order = None
        self.assertEqual(self.admin.link_to_new_order(self.upgrade), '-')
