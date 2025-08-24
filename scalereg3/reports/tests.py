from django.contrib.auth import get_user_model
from django.test import TestCase


class IndexTest(TestCase):

    def test_not_logged_in(self):
        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/admin/login/?next=/reports/')

    def test_normal_user_logged_in(self):
        user = get_user_model().objects.create_user('user', is_staff=False)
        self.client.force_login(user)
        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/admin/login/?next=/reports/')

    def test_staff_user_logged_in(self):
        user = get_user_model().objects.create_user('user', is_staff=True)
        self.client.force_login(user)
        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            '<a href="sales_dashboard/">Sales Dashboard</a>')
