from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from bitacora.models import Project, ProjectNode
from bitacora.services import (
    archive_project_node,
    create_project_node,
    move_project_node,
    update_project_node,
)


class ProjectNodeServiceTests(TestCase):
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
        self.non_owner = get_user_model().objects.create_user(
            username="reader",
            email="reader@example.com",
            password="password",
        )
        self.project = Project.objects.create(
            owner=self.owner,
            name="Project",
            slug="project",
        )
        self.other_project = Project.objects.create(
            owner=self.other_owner,
            name="Other Project",
            slug="other-project",
        )

    def create_node(self, **overrides):
        defaults = {
            "owner": self.owner,
            "project": self.project,
            "title": "Node",
            "slug": "node",
        }
        defaults.update(overrides)
        return create_project_node(**defaults)

    def test_owner_can_create_root_node(self):
        node = self.create_node()

        self.assertEqual(node.project, self.project)
        self.assertIsNone(node.parent)

    def test_owner_can_create_child_node(self):
        parent = self.create_node(title="Parent", slug="parent")

        child = self.create_node(title="Child", slug="child", parent=parent)

        self.assertEqual(child.parent, parent)

    def test_non_owner_cannot_create_node(self):
        with self.assertRaises(PermissionDenied):
            self.create_node(owner=self.non_owner)

    def test_anonymous_user_cannot_create_node(self):
        with self.assertRaises(PermissionDenied):
            self.create_node(owner=AnonymousUser())

    def test_cannot_create_child_node_with_parent_from_another_project(self):
        other_parent = create_project_node(
            owner=self.other_owner,
            project=self.other_project,
            title="Other Parent",
            slug="other-parent",
        )

        with self.assertRaises(ValidationError):
            self.create_node(title="Child", slug="child", parent=other_parent)

    def test_can_update_node(self):
        node = self.create_node()

        update_project_node(
            node,
            title="Updated",
            slug="updated",
            description="Updated description",
            node_type=ProjectNode.NodeType.FEATURE,
            visibility=ProjectNode.Visibility.PUBLIC,
            position=2,
        )

        node.refresh_from_db()
        self.assertEqual(node.title, "Updated")
        self.assertEqual(node.slug, "updated")
        self.assertEqual(node.description, "Updated description")
        self.assertEqual(node.node_type, ProjectNode.NodeType.FEATURE)
        self.assertEqual(node.visibility, ProjectNode.Visibility.PUBLIC)
        self.assertEqual(node.position, 2)

    def test_can_archive_node(self):
        node = self.create_node()

        archive_project_node(node)

        node.refresh_from_db()
        self.assertTrue(node.is_archived)

    def test_archive_sets_is_archived_and_does_not_delete_row(self):
        node = self.create_node()

        archive_project_node(node)

        self.assertTrue(ProjectNode.objects.filter(pk=node.pk).exists())
        self.assertTrue(ProjectNode.objects.get(pk=node.pk).is_archived)

    def test_can_move_node_to_another_parent_in_same_project(self):
        old_parent = self.create_node(title="Old Parent", slug="old-parent")
        new_parent = self.create_node(title="New Parent", slug="new-parent")
        node = self.create_node(title="Child", slug="child", parent=old_parent)

        move_project_node(node, new_parent=new_parent, position=5)

        node.refresh_from_db()
        self.assertEqual(node.parent, new_parent)
        self.assertEqual(node.position, 5)

    def test_cannot_move_node_under_itself(self):
        node = self.create_node()

        with self.assertRaises(ValidationError):
            move_project_node(node, new_parent=node)

    def test_cannot_move_node_under_descendant(self):
        parent = self.create_node(title="Parent", slug="parent")
        child = self.create_node(title="Child", slug="child", parent=parent)
        grandchild = self.create_node(title="Grandchild", slug="grandchild", parent=child)

        with self.assertRaises(ValidationError):
            move_project_node(parent, new_parent=grandchild)

    def test_cannot_move_node_under_parent_from_another_project(self):
        node = self.create_node()
        other_parent = create_project_node(
            owner=self.other_owner,
            project=self.other_project,
            title="Other Parent",
            slug="other-parent",
        )

        with self.assertRaises(ValidationError):
            move_project_node(node, new_parent=other_parent)
