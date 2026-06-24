from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from bitacora.models import Project
from bitacora.services import archive_project, create_project, update_project


class ProjectServiceTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_superuser(
            username="owner",
            email="owner@example.com",
            password="password",
        )
        self.non_owner = get_user_model().objects.create_user(
            username="reader",
            email="reader@example.com",
            password="password",
        )

    def test_owner_can_create_project_through_service(self):
        project = create_project(
            owner=self.owner,
            name="My Project",
            slug="my-project",
        )

        self.assertEqual(project.owner, self.owner)
        self.assertEqual(project.name, "My Project")

    def test_non_owner_cannot_create_project_through_service(self):
        with self.assertRaises(PermissionDenied):
            create_project(
                owner=self.non_owner,
                name="My Project",
                slug="my-project",
            )

    def test_anonymous_user_cannot_create_project_through_service(self):
        with self.assertRaises(PermissionDenied):
            create_project(
                owner=AnonymousUser(),
                name="My Project",
                slug="my-project",
            )

    def test_project_can_be_updated_through_service(self):
        project = create_project(
            owner=self.owner,
            name="My Project",
            slug="my-project",
        )

        update_project(
            project,
            name="Updated Project",
            slug="updated-project",
            description="Updated description",
            status=Project.Status.PAUSED,
            visibility=Project.Visibility.PUBLIC,
        )

        project.refresh_from_db()
        self.assertEqual(project.name, "Updated Project")
        self.assertEqual(project.slug, "updated-project")
        self.assertEqual(project.description, "Updated description")
        self.assertEqual(project.status, Project.Status.PAUSED)
        self.assertEqual(project.visibility, Project.Visibility.PUBLIC)

    def test_project_can_be_archived_through_service(self):
        project = create_project(
            owner=self.owner,
            name="My Project",
            slug="my-project",
        )

        archive_project(project)

        project.refresh_from_db()
        self.assertEqual(project.status, Project.Status.ARCHIVED)

    def test_archive_sets_status_and_does_not_delete_row(self):
        project = create_project(
            owner=self.owner,
            name="My Project",
            slug="my-project",
        )

        archive_project(project)

        self.assertTrue(Project.objects.filter(pk=project.pk).exists())
        self.assertEqual(Project.objects.get(pk=project.pk).status, Project.Status.ARCHIVED)
