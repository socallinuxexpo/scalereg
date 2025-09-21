from django.test import TestCase


class Reg6RedirectTest(TestCase):

    def test_reg6_redirect(self):
        response = self.client.get('/reg6/')
        self.assertRedirects(response, '/reg23/')
