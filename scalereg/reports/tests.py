from django.test import TestCase, Client
from django.contrib.auth.models import User

class ReportsViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser3', password='password123')
        self.superuser = User.objects.create_superuser(username='superuser', email='super@user.com', password='password123')

    def test_reports_index_redirects_if_not_logged_in(self):
        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_reports_index_redirects_if_normal_user(self):
        self.client.login(username='testuser3', password='password123')
        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 302) # services_perm_checker will deny

    def test_reports_index_loads_for_superuser(self):
        self.client.login(username='superuser', password='password123')
        response = self.client.get('/reports/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reports") # Placeholder
