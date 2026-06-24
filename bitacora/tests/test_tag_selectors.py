from django.contrib.auth import get_user_model
from django.test import TestCase

from bitacora.models import DocumentTag, NodeDocument, Project, ProjectNode, Tag
from bitacora.selectors import (
    get_active_owner_tags,
    get_owner_documents_for_tag,
    get_owner_tags,
    get_owner_tags_for_document,
    get_public_documents_for_tag,
    get_public_tags_for_document,
)


class TagSelectorTests(TestCase):
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
        self.document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="Document",
            slug="document",
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PUBLIC,
        )
        self.other_tag = Tag.objects.create(
            owner=self.other_owner,
            name="Other",
            slug="other",
        )

    def create_tag(self, **overrides):
        defaults = {
            "owner": self.owner,
            "name": "Architecture",
            "slug": "architecture",
        }
        defaults.update(overrides)
        return Tag.objects.create(**defaults)

    def test_owner_tag_selector_returns_all_owner_tags(self):
        private_tag = self.create_tag(slug="private")
        archived_tag = self.create_tag(slug="archived", is_archived=True)

        tags = get_owner_tags(self.owner)

        self.assertIn(private_tag, tags)
        self.assertIn(archived_tag, tags)

    def test_active_owner_tag_selector_excludes_archived_tags(self):
        active_tag = self.create_tag(slug="active")
        archived_tag = self.create_tag(slug="archived", is_archived=True)

        tags = get_active_owner_tags(self.owner)

        self.assertIn(active_tag, tags)
        self.assertNotIn(archived_tag, tags)

    def test_owner_tag_selector_does_not_return_another_owners_tags(self):
        self.assertNotIn(self.other_tag, get_owner_tags(self.owner))

    def test_owner_tags_for_document_selector_returns_all_tags_attached_to_owned_document(self):
        public_tag = self.create_tag(slug="public", visibility=Tag.Visibility.PUBLIC)
        private_tag = self.create_tag(slug="private")
        DocumentTag.objects.create(document=self.document, tag=public_tag)
        DocumentTag.objects.create(document=self.document, tag=private_tag)

        tags = get_owner_tags_for_document(self.owner, self.document)

        self.assertIn(public_tag, tags)
        self.assertIn(private_tag, tags)

    def test_public_tags_for_document_returns_public_non_archived_tags(self):
        tag = self.create_tag(visibility=Tag.Visibility.PUBLIC)
        DocumentTag.objects.create(document=self.document, tag=tag)

        self.assertIn(tag, get_public_tags_for_document(self.document))

    def test_public_tags_for_document_excludes_private_tags(self):
        tag = self.create_tag()
        DocumentTag.objects.create(document=self.document, tag=tag)

        self.assertNotIn(tag, get_public_tags_for_document(self.document))

    def test_public_tags_for_document_excludes_archived_tags(self):
        tag = self.create_tag(visibility=Tag.Visibility.PUBLIC, is_archived=True)
        DocumentTag.objects.create(document=self.document, tag=tag)

        self.assertNotIn(tag, get_public_tags_for_document(self.document))

    def test_public_tags_for_document_returns_no_tags_if_document_not_effectively_public(self):
        self.document.status = NodeDocument.Status.DRAFT
        self.document.save(update_fields=["status"])
        tag = self.create_tag(visibility=Tag.Visibility.PUBLIC)
        DocumentTag.objects.create(document=self.document, tag=tag)

        self.assertEqual(list(get_public_tags_for_document(self.document)), [])

    def test_owner_documents_for_tag_selector_returns_documents_using_the_tag(self):
        tag = self.create_tag()
        DocumentTag.objects.create(document=self.document, tag=tag)

        self.assertIn(self.document, get_owner_documents_for_tag(self.owner, tag))

    def test_public_documents_for_tag_returns_only_effectively_public_documents(self):
        private_document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="Private",
            slug="private",
            status=NodeDocument.Status.ACTIVE,
        )
        tag = self.create_tag(visibility=Tag.Visibility.PUBLIC)
        DocumentTag.objects.create(document=self.document, tag=tag)
        DocumentTag.objects.create(document=private_document, tag=tag)

        documents = get_public_documents_for_tag(tag)

        self.assertIn(self.document, documents)
        self.assertNotIn(private_document, documents)

    def test_public_documents_for_tag_returns_no_documents_if_tag_private_or_archived(self):
        private_tag = self.create_tag(slug="private")
        archived_tag = self.create_tag(
            slug="archived",
            visibility=Tag.Visibility.PUBLIC,
            is_archived=True,
        )
        DocumentTag.objects.create(document=self.document, tag=private_tag)
        DocumentTag.objects.create(document=self.document, tag=archived_tag)

        self.assertEqual(get_public_documents_for_tag(private_tag), [])
        self.assertEqual(get_public_documents_for_tag(archived_tag), [])
