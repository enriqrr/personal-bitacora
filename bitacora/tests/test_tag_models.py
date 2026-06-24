from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from bitacora.models import DocumentTag, NodeDocument, Project, ProjectNode, Tag


class TagModelTests(TestCase):
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
        self.project = Project.objects.create(owner=self.owner, name="Project", slug="project")
        self.node = ProjectNode.objects.create(project=self.project, title="Node", slug="node")
        self.document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="Document",
            slug="document",
        )

    def test_tag_can_be_created_with_required_fields(self):
        tag = Tag.objects.create(owner=self.owner, name="Architecture", slug="architecture")

        self.assertEqual(tag.owner, self.owner)
        self.assertEqual(tag.name, "Architecture")
        self.assertEqual(tag.slug, "architecture")

    def test_default_visibility_is_private(self):
        tag = Tag.objects.create(owner=self.owner, name="Architecture", slug="architecture")

        self.assertEqual(tag.visibility, Tag.Visibility.PRIVATE)

    def test_default_is_archived_is_false(self):
        tag = Tag.objects.create(owner=self.owner, name="Architecture", slug="architecture")

        self.assertFalse(tag.is_archived)

    def test_string_representation_returns_tag_name(self):
        tag = Tag.objects.create(owner=self.owner, name="Architecture", slug="architecture")

        self.assertEqual(str(tag), "Architecture")

    def test_owner_and_slug_uniqueness_is_enforced(self):
        Tag.objects.create(owner=self.owner, name="Architecture", slug="architecture")

        with self.assertRaises(IntegrityError):
            Tag.objects.create(owner=self.owner, name="Duplicate", slug="architecture")

    def test_different_owners_may_use_same_tag_slug(self):
        Tag.objects.create(owner=self.owner, name="Architecture", slug="architecture")

        tag = Tag.objects.create(
            owner=self.other_owner,
            name="Architecture",
            slug="architecture",
        )

        self.assertEqual(tag.slug, "architecture")

    def test_document_tag_unique_document_tag_pair_is_enforced(self):
        tag = Tag.objects.create(owner=self.owner, name="Architecture", slug="architecture")
        DocumentTag.objects.create(document=self.document, tag=tag)

        with self.assertRaises(IntegrityError):
            DocumentTag.objects.create(document=self.document, tag=tag)

    def test_document_tag_cannot_link_document_to_another_owners_tag(self):
        tag = Tag.objects.create(
            owner=self.other_owner,
            name="Architecture",
            slug="architecture",
        )
        document_tag = DocumentTag(document=self.document, tag=tag)

        with self.assertRaises(ValidationError):
            document_tag.full_clean()
