from django.test import SimpleTestCase
from django.urls import reverse


class HealthCheckTests(SimpleTestCase):
    def test_health_check_returns_ok(self):
        response = self.client.get(reverse("bitacora:health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")
