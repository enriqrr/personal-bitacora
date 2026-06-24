from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from bitacora.permissions import is_owner


class PublicViewTests(SimpleTestCase):
    def test_homepage_returns_ok(self):
        response = self.client.get(reverse("bitacora:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Personal Bitacora")

    def test_login_page_returns_ok(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)

    def test_owner_dashboard_redirects_anonymous_users_to_login(self):
        response = self.client.get(reverse("bitacora:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/?next=/dashboard/")

    def test_signup_route_does_not_exist(self):
        response = self.client.get("/accounts/signup/")

        self.assertEqual(response.status_code, 404)

    def test_django_system_check_passes(self):
        output = StringIO()

        call_command("check", stdout=output)

        self.assertIn("System check identified no issues", output.getvalue())


class OwnerAccessTests(TestCase):
    def test_superuser_owner_can_access_dashboard(self):
        user = get_user_model().objects.create_superuser(
            username="owner",
            email="owner@example.com",
            password="password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("bitacora:dashboard"))

        self.assertEqual(response.status_code, 200)

    def test_authenticated_non_superuser_receives_forbidden_dashboard(self):
        user = get_user_model().objects.create_user(
            username="reader",
            email="reader@example.com",
            password="password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("bitacora:dashboard"))

        self.assertEqual(response.status_code, 403)

    def test_is_owner_returns_false_for_anonymous_user(self):
        self.assertFalse(is_owner(AnonymousUser()))

    def test_is_owner_returns_false_for_normal_authenticated_user(self):
        user = get_user_model().objects.create_user(
            username="reader",
            email="reader@example.com",
            password="password",
        )

        self.assertFalse(is_owner(user))

    def test_is_owner_returns_true_for_active_superuser(self):
        user = get_user_model().objects.create_superuser(
            username="owner",
            email="owner@example.com",
            password="password",
        )

        self.assertTrue(is_owner(user))

    def test_logout_route_accepts_post_and_redirects(self):
        user = get_user_model().objects.create_superuser(
            username="owner",
            email="owner@example.com",
            password="password",
        )
        self.client.force_login(user)

        response = self.client.post(reverse("logout"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
