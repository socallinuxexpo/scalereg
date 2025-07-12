from django.test import TestCase

from .models import Ticket


class RootRedirectTest(TestCase):

    def test_root_redirect(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/reg23/')


class IndexTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        Ticket.objects.create(name='T1',
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
        Ticket.objects.create(name='T3',
                              description='T3 press',
                              ticket_type='press',
                              price=0,
                              public=False,
                              cash=False,
                              upgradable=False)

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
