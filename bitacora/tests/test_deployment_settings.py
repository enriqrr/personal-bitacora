import importlib
import os
import sys
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse


def import_production_settings(env):
    sys.modules.pop("config.settings.production", None)
    with patch.dict(os.environ, env, clear=True):
        return importlib.import_module("config.settings.production")


class DeploymentSettingsTests(SimpleTestCase):
    def test_production_debug_defaults_to_false(self):
        settings = import_production_settings(
            {
                "SECRET_KEY": "test-secret",
                "DATABASE_URL": "sqlite:///production-test.sqlite3",
                "ALLOWED_HOSTS": "example.com",
            }
        )

        self.assertFalse(settings.DEBUG)

    def test_production_secret_key_is_required(self):
        with self.assertRaises(ImproperlyConfigured):
            import_production_settings(
                {
                    "DATABASE_URL": "sqlite:///production-test.sqlite3",
                    "ALLOWED_HOSTS": "example.com",
                }
            )

    def test_production_database_url_is_required(self):
        with self.assertRaises(ImproperlyConfigured):
            import_production_settings(
                {
                    "SECRET_KEY": "test-secret",
                    "ALLOWED_HOSTS": "example.com",
                }
            )

    def test_production_allowed_hosts_can_be_read_from_environment(self):
        settings = import_production_settings(
            {
                "SECRET_KEY": "test-secret",
                "DATABASE_URL": "sqlite:///production-test.sqlite3",
                "ALLOWED_HOSTS": "example.com,www.example.com",
            }
        )

        self.assertEqual(settings.ALLOWED_HOSTS, ["example.com", "www.example.com"])

    def test_local_settings_can_load_without_production_environment(self):
        sys.modules.pop("config.settings.local", None)
        with patch.dict(os.environ, {}, clear=True):
            settings = importlib.import_module("config.settings.local")

        self.assertTrue(settings.DEBUG)
        self.assertIn("localhost", settings.ALLOWED_HOSTS)

    def test_collectstatic_dry_run_works(self):
        call_command("collectstatic", interactive=False, dry_run=True, verbosity=0)


class DeploymentRouteRegressionTests(TestCase):
    def test_health_check_returns_ok(self):
        response = self.client.get(reverse("bitacora:health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    def test_signup_route_still_returns_not_found(self):
        response = self.client.get("/accounts/signup/")

        self.assertEqual(response.status_code, 404)

    def test_owner_dashboard_redirects_anonymous_users(self):
        response = self.client.get(reverse("bitacora:dashboard"))

        self.assertEqual(response.status_code, 302)

    def test_public_homepage_still_returns_ok(self):
        response = self.client.get(reverse("bitacora:home"))

        self.assertEqual(response.status_code, 200)
