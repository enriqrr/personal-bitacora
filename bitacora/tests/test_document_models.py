from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from bitacora.models import NodeDocument, Project, ProjectNode


class NodeDocumentModelTests(TestCase):
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
        self.node = ProjectNode.objects.create(
            project=self.project,
            title="Node",
            slug="node",
        )

    def create_document(self, **overrides):
        defaults = {
            "project": self.project,
            "node": self.node,
            "title": "Document",
            "slug": "document",
        }
        defaults.update(overrides)
        return NodeDocument.objects.create(**defaults)

    def test_node_document_can_be_created_with_required_fields(self):
        document = self.create_document()

        self.assertEqual(document.project, self.project)
        self.assertEqual(document.node, self.node)
        self.assertEqual(document.title, "Document")
        self.assertEqual(document.slug, "document")

    def test_default_document_type_is_other(self):
        document = self.create_document()

        self.assertEqual(document.document_type, NodeDocument.DocumentType.OTHER)

    def test_default_status_is_draft(self):
        document = self.create_document()

        self.assertEqual(document.status, NodeDocument.Status.DRAFT)

    def test_default_visibility_is_private(self):
        document = self.create_document()

        self.assertEqual(document.visibility, NodeDocument.Visibility.PRIVATE)

    def test_string_representation_returns_document_title(self):
        document = self.create_document(title="Architecture Notes")

        self.assertEqual(str(document), "Architecture Notes")

    def test_slug_uniqueness_inside_same_node_is_enforced(self):
        self.create_document(slug="notes")

        with self.assertRaises(IntegrityError):
            self.create_document(title="Duplicate", slug="notes")

    def test_same_slug_is_allowed_in_different_nodes(self):
        other_node = ProjectNode.objects.create(
            project=self.project,
            title="Other Node",
            slug="other-node",
        )
        self.create_document(slug="notes")

        document = self.create_document(node=other_node, slug="notes")

        self.assertEqual(document.slug, "notes")

    def test_project_must_match_node_project(self):
        other_project = Project.objects.create(
            owner=self.owner,
            name="Other Project",
            slug="other-project",
        )
        document = NodeDocument(
            project=other_project,
            node=self.node,
            title="Mismatch",
            slug="mismatch",
        )

        with self.assertRaises(ValidationError):
            document.full_clean()
