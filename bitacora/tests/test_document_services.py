from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from bitacora.models import NodeDocument, Project, ProjectNode
from bitacora.services import (
    archive_node_document,
    create_node_document,
    update_node_document,
)


class NodeDocumentServiceTests(TestCase):
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
        self.node = ProjectNode.objects.create(
            project=self.project,
            title="Node",
            slug="node",
        )
        self.other_project = Project.objects.create(
            owner=self.other_owner,
            name="Other Project",
            slug="other-project",
        )
        self.other_node = ProjectNode.objects.create(
            project=self.other_project,
            title="Other Node",
            slug="other-node",
        )

    def create_document(self, **overrides):
        defaults = {
            "owner": self.owner,
            "node": self.node,
            "title": "Document",
            "slug": "document",
        }
        defaults.update(overrides)
        return create_node_document(**defaults)

    def test_owner_can_create_document(self):
        document = self.create_document()

        self.assertEqual(document.project, self.project)
        self.assertEqual(document.node, self.node)

    def test_non_owner_cannot_create_document(self):
        with self.assertRaises(PermissionDenied):
            self.create_document(owner=self.non_owner)

    def test_anonymous_user_cannot_create_document(self):
        with self.assertRaises(PermissionDenied):
            self.create_document(owner=AnonymousUser())

    def test_cannot_create_document_for_node_from_another_owners_project(self):
        with self.assertRaises(PermissionDenied):
            self.create_document(node=self.other_node)

    def test_cannot_create_duplicate_slug_inside_same_node(self):
        self.create_document(slug="notes")

        with self.assertRaises(ValidationError):
            self.create_document(title="Duplicate", slug="notes")

    def test_can_update_document(self):
        document = self.create_document()

        update_node_document(
            document,
            title="Updated",
            slug="updated",
            document_type=NodeDocument.DocumentType.SPECIFICATION,
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PUBLIC,
            body_markdown="# Updated",
        )

        document.refresh_from_db()
        self.assertEqual(document.title, "Updated")
        self.assertEqual(document.slug, "updated")
        self.assertEqual(document.document_type, NodeDocument.DocumentType.SPECIFICATION)
        self.assertEqual(document.status, NodeDocument.Status.ACTIVE)
        self.assertEqual(document.visibility, NodeDocument.Visibility.PUBLIC)
        self.assertEqual(document.body_markdown, "# Updated")

    def test_can_archive_document(self):
        document = self.create_document()

        archive_node_document(document)

        document.refresh_from_db()
        self.assertEqual(document.status, NodeDocument.Status.ARCHIVED)

    def test_archive_sets_status_and_does_not_delete_row(self):
        document = self.create_document()

        archive_node_document(document)

        self.assertTrue(NodeDocument.objects.filter(pk=document.pk).exists())
        self.assertEqual(NodeDocument.objects.get(pk=document.pk).status, NodeDocument.Status.ARCHIVED)
