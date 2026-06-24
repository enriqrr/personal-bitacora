from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from bitacora.models import Project


class ProjectViewTests(TestCase):
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

    def create_project(self, **overrides):
        defaults = {
            "owner": self.owner,
            "name": "My Project",
            "slug": "my-project",
        }
        defaults.update(overrides)
        return Project.objects.create(**defaults)

    def test_public_project_list_returns_ok(self):
        response = self.client.get(reverse("bitacora:public_project_list"))

        self.assertEqual(response.status_code, 200)

    def test_public_project_list_shows_public_active_projects(self):
        self.create_project(
            name="Public Project",
            slug="public-project",
            visibility=Project.Visibility.PUBLIC,
        )

        response = self.client.get(reverse("bitacora:public_project_list"))

        self.assertContains(response, "Public Project")

    def test_public_project_list_does_not_show_private_projects(self):
        self.create_project(
            name="Private Project",
            slug="private-project",
            visibility=Project.Visibility.PRIVATE,
        )

        response = self.client.get(reverse("bitacora:public_project_list"))

        self.assertNotContains(response, "Private Project")

    def test_public_project_list_does_not_show_archived_projects(self):
        self.create_project(
            name="Archived Project",
            slug="archived-project",
            status=Project.Status.ARCHIVED,
            visibility=Project.Visibility.PUBLIC,
        )

        response = self.client.get(reverse("bitacora:public_project_list"))

        self.assertNotContains(response, "Archived Project")

    def test_public_project_detail_returns_ok_for_public_active_project(self):
        project = self.create_project(visibility=Project.Visibility.PUBLIC)

        response = self.client.get(
            reverse("bitacora:public_project_detail", kwargs={"slug": project.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, project.name)

    def test_public_project_detail_returns_not_found_for_private_project(self):
        project = self.create_project(visibility=Project.Visibility.PRIVATE)

        response = self.client.get(
            reverse("bitacora:public_project_detail", kwargs={"slug": project.slug})
        )

        self.assertEqual(response.status_code, 404)

    def test_public_project_detail_returns_not_found_for_archived_project(self):
        project = self.create_project(
            status=Project.Status.ARCHIVED,
            visibility=Project.Visibility.PUBLIC,
        )

        response = self.client.get(
            reverse("bitacora:public_project_detail", kwargs={"slug": project.slug})
        )

        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_is_redirected_from_owner_project_list(self):
        response = self.client.get(reverse("bitacora:owner_project_list"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/?next=/dashboard/projects/")

    def test_owner_can_access_owner_project_list(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("bitacora:owner_project_list"))

        self.assertEqual(response.status_code, 200)

    def test_authenticated_non_owner_receives_forbidden_for_owner_project_list(self):
        self.client.force_login(self.non_owner)

        response = self.client.get(reverse("bitacora:owner_project_list"))

        self.assertEqual(response.status_code, 403)

    def test_owner_can_create_project_through_form(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("bitacora:owner_project_create"),
            {
                "name": "Created Project",
                "slug": "created-project",
                "description": "Created description",
                "status": Project.Status.ACTIVE,
                "visibility": Project.Visibility.PUBLIC,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Project.objects.filter(slug="created-project").exists())

    def test_owner_can_edit_project_through_form(self):
        self.client.force_login(self.owner)
        project = self.create_project()

        response = self.client.post(
            reverse("bitacora:owner_project_edit", kwargs={"slug": project.slug}),
            {
                "name": "Edited Project",
                "slug": "edited-project",
                "description": "Edited description",
                "status": Project.Status.PAUSED,
                "visibility": Project.Visibility.PUBLIC,
            },
        )

        self.assertEqual(response.status_code, 302)
        project.refresh_from_db()
        self.assertEqual(project.name, "Edited Project")
        self.assertEqual(project.slug, "edited-project")
        self.assertEqual(project.status, Project.Status.PAUSED)
        self.assertEqual(project.visibility, Project.Visibility.PUBLIC)

    def test_owner_can_archive_project_through_post(self):
        self.client.force_login(self.owner)
        project = self.create_project()

        response = self.client.post(
            reverse("bitacora:owner_project_archive", kwargs={"slug": project.slug})
        )

        self.assertEqual(response.status_code, 302)
        project.refresh_from_db()
        self.assertEqual(project.status, Project.Status.ARCHIVED)

    def test_signup_route_still_does_not_exist(self):
        response = self.client.get("/accounts/signup/")

        self.assertEqual(response.status_code, 404)
