from django.contrib.auth import get_user_model
from django.test import TestCase

from bitacora.models import Project, ProjectNode
from bitacora.selectors import (
    get_breadcrumb_nodes,
    get_owner_nodes_for_project,
    get_public_node_by_id,
    get_public_root_nodes_for_project,
)


class ProjectNodeSelectorTests(TestCase):
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
        self.project = Project.objects.create(
            owner=self.owner,
            name="Project",
            slug="project",
            visibility=Project.Visibility.PUBLIC,
        )
        self.other_project = Project.objects.create(
            owner=self.other_owner,
            name="Other Project",
            slug="other-project",
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

    def test_owner_selector_returns_all_nodes_for_owned_project(self):
        private_node = self.create_node(slug="private")
        public_node = self.create_node(slug="public", visibility=ProjectNode.Visibility.PUBLIC)
        archived_node = self.create_node(slug="archived", is_archived=True)

        nodes = get_owner_nodes_for_project(self.owner, self.project)

        self.assertIn(private_node, nodes)
        self.assertIn(public_node, nodes)
        self.assertIn(archived_node, nodes)

    def test_owner_selector_does_not_return_nodes_from_another_owners_project(self):
        self.create_node(slug="owner-node")
        other_node = self.create_node(project=self.other_project, slug="other-node")

        nodes = get_owner_nodes_for_project(self.owner, self.other_project)

        self.assertNotIn(other_node, nodes)
        self.assertEqual(list(nodes), [])

    def test_public_root_selector_returns_public_root_nodes_in_public_active_project(self):
        node = self.create_node(visibility=ProjectNode.Visibility.PUBLIC)

        self.assertIn(node, get_public_root_nodes_for_project(self.project))

    def test_public_root_selector_excludes_private_nodes(self):
        node = self.create_node(visibility=ProjectNode.Visibility.PRIVATE)

        self.assertNotIn(node, get_public_root_nodes_for_project(self.project))

    def test_public_root_selector_excludes_archived_nodes(self):
        node = self.create_node(
            visibility=ProjectNode.Visibility.PUBLIC,
            is_archived=True,
        )

        self.assertNotIn(node, get_public_root_nodes_for_project(self.project))

    def test_public_root_selector_excludes_nodes_from_private_projects(self):
        self.project.visibility = Project.Visibility.PRIVATE
        self.project.save(update_fields=["visibility"])
        node = self.create_node(visibility=ProjectNode.Visibility.PUBLIC)

        self.assertNotIn(node, get_public_root_nodes_for_project(self.project))

    def test_public_node_detail_selector_returns_public_effective_node(self):
        node = self.create_node(visibility=ProjectNode.Visibility.PUBLIC)

        self.assertEqual(get_public_node_by_id(node.id), node)

    def test_public_node_detail_selector_rejects_private_node(self):
        node = self.create_node(visibility=ProjectNode.Visibility.PRIVATE)

        with self.assertRaises(ProjectNode.DoesNotExist):
            get_public_node_by_id(node.id)

    def test_public_node_detail_selector_rejects_archived_node(self):
        node = self.create_node(
            visibility=ProjectNode.Visibility.PUBLIC,
            is_archived=True,
        )

        with self.assertRaises(ProjectNode.DoesNotExist):
            get_public_node_by_id(node.id)

    def test_public_node_detail_selector_rejects_public_child_under_private_parent(self):
        parent = self.create_node(title="Parent", slug="parent")
        child = self.create_node(
            title="Child",
            slug="child",
            parent=parent,
            visibility=ProjectNode.Visibility.PUBLIC,
        )

        with self.assertRaises(ProjectNode.DoesNotExist):
            get_public_node_by_id(child.id)

    def test_breadcrumb_selector_returns_root_to_current_path(self):
        root = self.create_node(title="Root", slug="root")
        child = self.create_node(title="Child", slug="child", parent=root)
        grandchild = self.create_node(title="Grandchild", slug="grandchild", parent=child)

        self.assertEqual(get_breadcrumb_nodes(grandchild), [root, child, grandchild])
