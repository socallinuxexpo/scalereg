from django.test import TestCase, Client

class SponsorshipViewsTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_sponsorship_index_loads(self):
        response = self.client.get('/sponsorship/')
        self.assertEqual(response.status_code, 200)
        # self.assertContains(response, "Sponsor Registration") # Placeholder
