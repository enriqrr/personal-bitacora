from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from bitacora.models import Project, ProjectNode


class ProjectNodeModelTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_superuser(
            username="owner",
            email="owner@example.com",
            password="password",
        )
        self.project = Project.objects.create(
            owner=self.owner,
            name="Project",
            slug="project",
        )

    def create_node(self, **overrides):
        defaults = {
            "project": self.project,
            "title": "Node",
            "slug": "node",
        }
        defaults.update(overrides)
        return ProjectNode.objects.create(**defaults)

    def test_project_node_can_be_created_with_required_fields(self):
        node = self.create_node()

        self.assertEqual(node.project, self.project)
        self.assertEqual(node.title, "Node")
        self.assertEqual(node.slug, "node")

    def test_default_node_type_is_other(self):
        node = self.create_node()

        self.assertEqual(node.node_type, ProjectNode.NodeType.OTHER)

    def test_default_visibility_is_private(self):
        node = self.create_node()

        self.assertEqual(node.visibility, ProjectNode.Visibility.PRIVATE)

    def test_default_is_archived_is_false(self):
        node = self.create_node()

        self.assertFalse(node.is_archived)

    def test_string_representation_returns_node_title(self):
        node = self.create_node(title="Architecture")

        self.assertEqual(str(node), "Architecture")

    def test_sibling_slug_uniqueness_is_enforced(self):
        parent = self.create_node(title="Parent", slug="parent")
        self.create_node(title="First", slug="child", parent=parent)

        with self.assertRaises(IntegrityError):
            self.create_node(title="Second", slug="child", parent=parent)

    def test_root_slug_uniqueness_per_project_is_enforced(self):
        self.create_node(title="First", slug="root")

        with self.assertRaises(IntegrityError):
            self.create_node(title="Second", slug="root")

    def test_nodes_from_different_projects_may_use_same_slug(self):
        other_project = Project.objects.create(
            owner=self.owner,
            name="Other Project",
            slug="other-project",
        )
        self.create_node(slug="shared")

        node = self.create_node(project=other_project, slug="shared")

        self.assertEqual(node.slug, "shared")
