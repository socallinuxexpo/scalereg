from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from .admin import AttendeeAdmin
from .admin import OrderAdmin
from .models import Attendee
from .models import Order


class AttendeeAdminTest(TestCase):

    def setUp(self):
        site = AdminSite()
        self.admin = AttendeeAdmin(Attendee, site)

    def test_fieldsets(self):
        form = self.admin.get_form(self.client.request)()
        self.assertIn('first_name', form.fields)
        self.assertIn('last_name', form.fields)
        self.assertIn('ordered_items', form.fields)


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
