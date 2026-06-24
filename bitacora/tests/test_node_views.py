from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from bitacora.models import Project, ProjectNode


class ProjectNodeViewTests(TestCase):
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
        self.project = Project.objects.create(
            owner=self.owner,
            name="Project",
            slug="project",
            visibility=Project.Visibility.PUBLIC,
        )

    def create_node(self, **overrides):
        defaults = {
            "project": self.project,
            "title": "Node",
            "slug": "node",
        }
        defaults.update(overrides)
        return ProjectNode.objects.create(**defaults)

    def test_public_project_tree_returns_ok_for_public_active_project(self):
        response = self.client.get(
            reverse("bitacora:public_project_tree", kwargs={"project_slug": self.project.slug})
        )

        self.assertEqual(response.status_code, 200)

    def test_public_tree_shows_public_nodes(self):
        self.create_node(title="Public Node", slug="public-node", visibility=ProjectNode.Visibility.PUBLIC)

        response = self.client.get(
            reverse("bitacora:public_project_tree", kwargs={"project_slug": self.project.slug})
        )

        self.assertContains(response, "Public Node")

    def test_public_tree_hides_private_nodes(self):
        self.create_node(title="Private Node", slug="private-node")

        response = self.client.get(
            reverse("bitacora:public_project_tree", kwargs={"project_slug": self.project.slug})
        )

        self.assertNotContains(response, "Private Node")

    def test_public_tree_hides_archived_nodes(self):
        self.create_node(
            title="Archived Node",
            slug="archived-node",
            visibility=ProjectNode.Visibility.PUBLIC,
            is_archived=True,
        )

        response = self.client.get(
            reverse("bitacora:public_project_tree", kwargs={"project_slug": self.project.slug})
        )

        self.assertNotContains(response, "Archived Node")

    def test_public_node_detail_returns_ok_for_effective_public_node(self):
        node = self.create_node(visibility=ProjectNode.Visibility.PUBLIC)

        response = self.client.get(reverse("bitacora:public_node_detail", kwargs={"node_id": node.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, node.title)

    def test_public_node_detail_returns_not_found_for_private_node(self):
        node = self.create_node()

        response = self.client.get(reverse("bitacora:public_node_detail", kwargs={"node_id": node.id}))

        self.assertEqual(response.status_code, 404)

    def test_public_node_detail_returns_not_found_for_public_child_under_private_parent(self):
        parent = self.create_node(title="Parent", slug="parent")
        child = self.create_node(
            title="Child",
            slug="child",
            parent=parent,
            visibility=ProjectNode.Visibility.PUBLIC,
        )

        response = self.client.get(reverse("bitacora:public_node_detail", kwargs={"node_id": child.id}))

        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_is_redirected_from_owner_tree_manager(self):
        response = self.client.get(
            reverse("bitacora:owner_project_tree", kwargs={"project_slug": self.project.slug})
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/?next=/dashboard/projects/project/tree/")

    def test_owner_can_access_owner_tree_manager(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("bitacora:owner_project_tree", kwargs={"project_slug": self.project.slug})
        )

        self.assertEqual(response.status_code, 200)

    def test_authenticated_non_owner_receives_forbidden_for_owner_tree_manager(self):
        self.client.force_login(self.non_owner)

        response = self.client.get(
            reverse("bitacora:owner_project_tree", kwargs={"project_slug": self.project.slug})
        )

        self.assertEqual(response.status_code, 403)

    def test_owner_can_create_root_node_through_form(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("bitacora:owner_node_create_root", kwargs={"project_slug": self.project.slug}),
            {
                "title": "Root",
                "slug": "root",
                "description": "Root description",
                "node_type": ProjectNode.NodeType.AREA,
                "visibility": ProjectNode.Visibility.PUBLIC,
                "position": 1,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(ProjectNode.objects.filter(slug="root", parent__isnull=True).exists())

    def test_owner_can_create_child_node_through_form(self):
        self.client.force_login(self.owner)
        parent = self.create_node(title="Parent", slug="parent")

        response = self.client.post(
            reverse("bitacora:owner_node_create_child", kwargs={"node_id": parent.id}),
            {
                "title": "Child",
                "slug": "child",
                "description": "Child description",
                "node_type": ProjectNode.NodeType.FEATURE,
                "visibility": ProjectNode.Visibility.PRIVATE,
                "position": 2,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(ProjectNode.objects.filter(slug="child", parent=parent).exists())

    def test_owner_can_edit_node_through_form(self):
        self.client.force_login(self.owner)
        node = self.create_node()

        response = self.client.post(
            reverse("bitacora:owner_node_edit", kwargs={"node_id": node.id}),
            {
                "title": "Edited",
                "slug": "edited",
                "description": "Edited description",
                "node_type": ProjectNode.NodeType.MODULE,
                "visibility": ProjectNode.Visibility.PUBLIC,
                "position": 3,
            },
        )

        self.assertEqual(response.status_code, 302)
        node.refresh_from_db()
        self.assertEqual(node.title, "Edited")
        self.assertEqual(node.slug, "edited")
        self.assertEqual(node.node_type, ProjectNode.NodeType.MODULE)
        self.assertEqual(node.visibility, ProjectNode.Visibility.PUBLIC)
        self.assertEqual(node.position, 3)

    def test_owner_can_move_node_through_form(self):
        self.client.force_login(self.owner)
        old_parent = self.create_node(title="Old Parent", slug="old-parent")
        new_parent = self.create_node(title="New Parent", slug="new-parent")
        node = self.create_node(title="Child", slug="child", parent=old_parent)

        response = self.client.post(
            reverse("bitacora:owner_node_move", kwargs={"node_id": node.id}),
            {"parent": new_parent.id, "position": 4},
        )

        self.assertEqual(response.status_code, 302)
        node.refresh_from_db()
        self.assertEqual(node.parent, new_parent)
        self.assertEqual(node.position, 4)

    def test_owner_can_archive_node_through_post(self):
        self.client.force_login(self.owner)
        node = self.create_node()

        response = self.client.post(reverse("bitacora:owner_node_archive", kwargs={"node_id": node.id}))

        self.assertEqual(response.status_code, 302)
        node.refresh_from_db()
        self.assertTrue(node.is_archived)

    def test_signup_route_still_does_not_exist(self):
        response = self.client.get("/accounts/signup/")

        self.assertEqual(response.status_code, 404)
