from django.contrib.auth import get_user_model
from django.test import TestCase

from bitacora.models import Project
from bitacora.selectors import get_owner_projects, get_public_projects


class ProjectSelectorTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_superuser(
            username="owner",
            email="owner@example.com",
            password="password",
        )
        self.other_owner = get_user_model().objects.create_superuser(
            username="other-owner",
            email="other@example.com",
            password="password",
        )

    def create_project(self, **overrides):
        defaults = {
            "owner": self.owner,
            "name": "My Project",
            "slug": "my-project",
        }
        defaults.update(overrides)
        return Project.objects.create(**defaults)

    def test_public_selector_returns_public_active_projects(self):
        project = self.create_project(visibility=Project.Visibility.PUBLIC)

        self.assertIn(project, get_public_projects())

    def test_public_selector_excludes_private_projects(self):
        project = self.create_project(visibility=Project.Visibility.PRIVATE)

        self.assertNotIn(project, get_public_projects())

    def test_public_selector_excludes_archived_projects(self):
        project = self.create_project(
            status=Project.Status.ARCHIVED,
            visibility=Project.Visibility.PUBLIC,
        )

        self.assertNotIn(project, get_public_projects())

    def test_owner_selector_returns_private_public_and_archived_projects(self):
        private_project = self.create_project(
            name="Private",
            slug="private",
            visibility=Project.Visibility.PRIVATE,
        )
        public_project = self.create_project(
            name="Public",
            slug="public",
            visibility=Project.Visibility.PUBLIC,
        )
        archived_project = self.create_project(
            name="Archived",
            slug="archived",
            status=Project.Status.ARCHIVED,
            visibility=Project.Visibility.PUBLIC,
        )

        projects = get_owner_projects(self.owner)

        self.assertIn(private_project, projects)
        self.assertIn(public_project, projects)
        self.assertIn(archived_project, projects)

    def test_owner_selector_does_not_return_another_owners_projects(self):
        owner_project = self.create_project(slug="owner-project")
        other_project = self.create_project(
            owner=self.other_owner,
            slug="other-project",
        )

        projects = get_owner_projects(self.owner)

        self.assertIn(owner_project, projects)
        self.assertNotIn(other_project, projects)
