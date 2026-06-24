from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from bitacora.models import DocumentTag, NodeDocument, Project, ProjectNode, Tag
from bitacora.services import archive_tag, create_tag, set_document_tags, update_tag


class TagServiceTests(TestCase):
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
        self.project = Project.objects.create(owner=self.owner, name="Project", slug="project")
        self.node = ProjectNode.objects.create(project=self.project, title="Node", slug="node")
        self.document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="Document",
            slug="document",
        )
        self.other_project = Project.objects.create(
            owner=self.other_owner,
            name="Other",
            slug="other",
        )
        self.other_node = ProjectNode.objects.create(
            project=self.other_project,
            title="Other Node",
            slug="other-node",
        )
        self.other_document = NodeDocument.objects.create(
            project=self.other_project,
            node=self.other_node,
            title="Other Document",
            slug="other-document",
        )

    def test_owner_can_create_tag(self):
        tag = create_tag(owner=self.owner, name="Architecture", slug="architecture")

        self.assertEqual(tag.owner, self.owner)
        self.assertEqual(tag.name, "Architecture")

    def test_non_owner_cannot_create_tag(self):
        with self.assertRaises(PermissionDenied):
            create_tag(owner=self.non_owner, name="Architecture", slug="architecture")

    def test_anonymous_user_cannot_create_tag(self):
        with self.assertRaises(PermissionDenied):
            create_tag(owner=AnonymousUser(), name="Architecture", slug="architecture")

    def test_owner_can_update_tag(self):
        tag = create_tag(owner=self.owner, name="Architecture", slug="architecture")

        update_tag(
            tag,
            name="Backend",
            slug="backend",
            description="Backend notes",
            visibility=Tag.Visibility.PUBLIC,
        )

        tag.refresh_from_db()
        self.assertEqual(tag.name, "Backend")
        self.assertEqual(tag.slug, "backend")
        self.assertEqual(tag.description, "Backend notes")
        self.assertEqual(tag.visibility, Tag.Visibility.PUBLIC)

    def test_owner_can_archive_tag(self):
        tag = create_tag(owner=self.owner, name="Architecture", slug="architecture")

        archive_tag(tag)

        tag.refresh_from_db()
        self.assertTrue(tag.is_archived)

    def test_archive_sets_is_archived_and_does_not_delete_row(self):
        tag = create_tag(owner=self.owner, name="Architecture", slug="architecture")

        archive_tag(tag)

        self.assertTrue(Tag.objects.filter(pk=tag.pk).exists())
        self.assertTrue(Tag.objects.get(pk=tag.pk).is_archived)

    def test_owner_can_assign_tags_to_owned_document(self):
        tag = create_tag(owner=self.owner, name="Architecture", slug="architecture")

        set_document_tags(owner=self.owner, document=self.document, tags=[tag])

        self.assertTrue(DocumentTag.objects.filter(document=self.document, tag=tag).exists())

    def test_assigning_tags_replaces_previous_document_tags(self):
        first = create_tag(owner=self.owner, name="Architecture", slug="architecture")
        second = create_tag(owner=self.owner, name="Backend", slug="backend")
        set_document_tags(owner=self.owner, document=self.document, tags=[first])

        set_document_tags(owner=self.owner, document=self.document, tags=[second])

        self.assertFalse(DocumentTag.objects.filter(document=self.document, tag=first).exists())
        self.assertTrue(DocumentTag.objects.filter(document=self.document, tag=second).exists())

    def test_duplicate_tag_input_does_not_create_duplicate_document_tag_rows(self):
        tag = create_tag(owner=self.owner, name="Architecture", slug="architecture")

        set_document_tags(owner=self.owner, document=self.document, tags=[tag, tag])

        self.assertEqual(DocumentTag.objects.filter(document=self.document, tag=tag).count(), 1)

    def test_cannot_assign_another_owners_tag_to_document(self):
        tag = create_tag(owner=self.other_owner, name="Architecture", slug="architecture")

        with self.assertRaises(ValidationError):
            set_document_tags(owner=self.owner, document=self.document, tags=[tag])

    def test_cannot_assign_tag_to_another_owners_document(self):
        tag = create_tag(owner=self.owner, name="Architecture", slug="architecture")

        with self.assertRaises(PermissionDenied):
            set_document_tags(owner=self.owner, document=self.other_document, tags=[tag])
