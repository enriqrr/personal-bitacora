from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from bitacora.models import Project


class ProjectModelTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_superuser(
            username="owner",
            email="owner@example.com",
            password="password",
        )

    def test_project_can_be_created_with_required_fields(self):
        project = Project.objects.create(
            owner=self.owner,
            name="My Project",
            slug="my-project",
        )

        self.assertEqual(project.owner, self.owner)
        self.assertEqual(project.name, "My Project")
        self.assertEqual(project.slug, "my-project")

    def test_default_status_is_active(self):
        project = Project.objects.create(
            owner=self.owner,
            name="My Project",
            slug="my-project",
        )

        self.assertEqual(project.status, Project.Status.ACTIVE)

    def test_default_visibility_is_private(self):
        project = Project.objects.create(
            owner=self.owner,
            name="My Project",
            slug="my-project",
        )

        self.assertEqual(project.visibility, Project.Visibility.PRIVATE)

    def test_owner_and_slug_uniqueness_is_enforced(self):
        Project.objects.create(
            owner=self.owner,
            name="My Project",
            slug="my-project",
        )

        with self.assertRaises(IntegrityError):
            Project.objects.create(
                owner=self.owner,
                name="Duplicate",
                slug="my-project",
            )

    def test_different_owners_may_share_slug(self):
        other_owner = get_user_model().objects.create_superuser(
            username="other-owner",
            email="other@example.com",
            password="password",
        )
        Project.objects.create(
            owner=self.owner,
            name="My Project",
            slug="shared",
        )

        project = Project.objects.create(
            owner=other_owner,
            name="Other Project",
            slug="shared",
        )

        self.assertEqual(project.slug, "shared")

    def test_string_representation_returns_project_name(self):
        project = Project.objects.create(
            owner=self.owner,
            name="My Project",
            slug="my-project",
        )

        self.assertEqual(str(project), "My Project")
