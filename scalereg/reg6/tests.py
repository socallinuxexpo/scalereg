from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission, Group
from django.urls import reverse # Not heavily used here due to lack of named URLs
from scalereg.auth_helper.models import Service # Corrected import path

class AuthHelperViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.staff_user = User.objects.create_user(username='staffuser', password='password123', is_staff=True)

    def test_auth_helper_profile_redirects_if_not_logged_in(self):
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_auth_helper_profile_loads_if_logged_in(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get('/accounts/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Available Services")

class Reg6ViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser2', password='password123')
        self.staff_user = User.objects.create_user(username='staffuser2', password='password123', is_staff=True)

        # Setup for services_perm_checker
        staff_group, _ = Group.objects.get_or_create(name='StaffGroupForTest')
        self.staff_user.groups.add(staff_group)

        # Create a service that grants access to /reg6/staff/
        service_url = '/reg6/staff'  # Removed trailing slash
        # Use get_or_create to avoid issues if service already exists from a previous test run or initial data
        service, created = Service.objects.get_or_create(
            name='Reg6StaffServiceForTests',
            defaults={'url': service_url, 'active': True}
        )
        if not created and not service.active: # Ensure it's active if it already existed
            service.active = True
            service.save()
        service.groups.add(staff_group)

        self.staff_user = User.objects.get(pk=self.staff_user.pk) # Refresh user from DB

    def test_reg6_index_loads(self):
        # This view might require some initial data (e.g., Ticket types) to render fully.
        # For a basic smoke test, we just check if it loads.
        response = self.client.get('/reg6/')
        self.assertEqual(response.status_code, 200)
        # A more specific assertion could be:
        # self.assertContains(response, "Registration is a two part process")

    def test_reg6_staff_index_redirects_if_not_staff_or_no_perms(self):
        self.client.login(username='testuser2', password='password123')
        response = self.client.get('/reg6/staff/')
        self.assertEqual(response.status_code, 302)
        # It should redirect to login or /accounts/profile/ if permission denied by services_perm_checker

    def test_reg6_staff_index_loads_if_staff_with_perms(self):
        self.client.login(username='staffuser2', password='password123')
        response = self.client.get('/reg6/staff/')
        # The services_perm_checker for '/reg6/staff/' in scalereg/common/utils.py
        # checks access based on the Service model.
        self.assertEqual(response.status_code, 200, f"Staff index should load. Status code was {response.status_code} instead.")
        self.assertContains(response, "Staff Page") # Corrected placeholder
