from io import StringIO

from django.core.management import call_command
from django.test import SimpleTestCase
from django.urls import reverse


class PublicViewTests(SimpleTestCase):
    def test_homepage_returns_ok(self):
        response = self.client.get(reverse("bitacora:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Personal Bitacora")

    def test_owner_dashboard_redirects_anonymous_users_to_login(self):
        response = self.client.get(reverse("bitacora:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/?next=/dashboard/")

    def test_django_system_check_passes(self):
        output = StringIO()

        call_command("check", stdout=output)

        self.assertIn("System check identified no issues", output.getvalue())
