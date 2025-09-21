from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from .admin import OrderAdmin
from .models import Order


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
