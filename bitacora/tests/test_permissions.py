from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from bitacora.permissions import is_owner


class PermissionTests(TestCase):
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
