from django.contrib.auth import get_user_model
from django.test import TestCase

from bitacora.models import NodeDocument, Project, ProjectNode
from bitacora.selectors import (
    get_owner_documents_for_node,
    get_public_document_by_id,
    get_public_documents_for_node,
)


class NodeDocumentSelectorTests(TestCase):
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
        self.node = ProjectNode.objects.create(
            project=self.project,
            title="Node",
            slug="node",
            visibility=ProjectNode.Visibility.PUBLIC,
        )
        self.other_project = Project.objects.create(
            owner=self.other_owner,
            name="Other Project",
            slug="other-project",
            visibility=Project.Visibility.PUBLIC,
        )
        self.other_node = ProjectNode.objects.create(
            project=self.other_project,
            title="Other Node",
            slug="other-node",
            visibility=ProjectNode.Visibility.PUBLIC,
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

    def test_owner_selector_returns_all_documents_for_owned_node(self):
        private_document = self.create_document(slug="private")
        active_document = self.create_document(
            slug="active",
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PUBLIC,
        )
        archived_document = self.create_document(
            slug="archived",
            status=NodeDocument.Status.ARCHIVED,
        )

        documents = get_owner_documents_for_node(self.owner, self.node)

        self.assertIn(private_document, documents)
        self.assertIn(active_document, documents)
        self.assertIn(archived_document, documents)

    def test_owner_selector_does_not_return_another_owners_documents(self):
        other_document = self.create_document(
            project=self.other_project,
            node=self.other_node,
            slug="other",
        )

        documents = get_owner_documents_for_node(self.owner, self.other_node)

        self.assertNotIn(other_document, documents)
        self.assertEqual(list(documents), [])

    def test_public_selector_returns_public_active_document_inside_effective_public_node(self):
        document = self.create_document(
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PUBLIC,
        )

        self.assertIn(document, get_public_documents_for_node(self.node))

    def test_public_selector_returns_public_resolved_document_inside_effective_public_node(self):
        document = self.create_document(
            status=NodeDocument.Status.RESOLVED,
            visibility=NodeDocument.Visibility.PUBLIC,
        )

        self.assertIn(document, get_public_documents_for_node(self.node))

    def test_public_selector_excludes_private_document(self):
        document = self.create_document(status=NodeDocument.Status.ACTIVE)

        self.assertNotIn(document, get_public_documents_for_node(self.node))

    def test_public_selector_excludes_draft_document_even_if_public(self):
        document = self.create_document(visibility=NodeDocument.Visibility.PUBLIC)

        self.assertNotIn(document, get_public_documents_for_node(self.node))

    def test_public_selector_excludes_needs_review_document_even_if_public(self):
        document = self.create_document(
            status=NodeDocument.Status.NEEDS_REVIEW,
            visibility=NodeDocument.Visibility.PUBLIC,
        )

        self.assertNotIn(document, get_public_documents_for_node(self.node))

    def test_public_selector_excludes_archived_document(self):
        document = self.create_document(
            status=NodeDocument.Status.ARCHIVED,
            visibility=NodeDocument.Visibility.PUBLIC,
        )

        self.assertNotIn(document, get_public_documents_for_node(self.node))

    def test_public_selector_excludes_document_inside_private_node(self):
        self.node.visibility = ProjectNode.Visibility.PRIVATE
        self.node.save(update_fields=["visibility"])
        document = self.create_document(
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PUBLIC,
        )

        self.assertNotIn(document, get_public_documents_for_node(self.node))

    def test_public_selector_excludes_document_inside_public_child_under_private_parent(self):
        parent = ProjectNode.objects.create(
            project=self.project,
            title="Parent",
            slug="parent",
        )
        child = ProjectNode.objects.create(
            project=self.project,
            parent=parent,
            title="Child",
            slug="child",
            visibility=ProjectNode.Visibility.PUBLIC,
        )
        document = self.create_document(
            node=child,
            slug="child-doc",
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PUBLIC,
        )

        self.assertNotIn(document, get_public_documents_for_node(child))

    def test_public_document_detail_selector_returns_effective_public_document(self):
        document = self.create_document(
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PUBLIC,
        )

        self.assertEqual(get_public_document_by_id(document.id), document)

    def test_public_document_detail_selector_rejects_private_document(self):
        document = self.create_document(status=NodeDocument.Status.ACTIVE)

        with self.assertRaises(NodeDocument.DoesNotExist):
            get_public_document_by_id(document.id)
