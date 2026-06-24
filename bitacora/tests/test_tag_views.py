from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from bitacora.models import DocumentTag, NodeDocument, Project, ProjectNode, Tag


class TagViewTests(TestCase):
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

    def create_tag(self, **overrides):
        defaults = {
            "owner": self.owner,
            "name": "Architecture",
            "slug": "architecture",
        }
        defaults.update(overrides)
        return Tag.objects.create(**defaults)

    def test_anonymous_user_is_redirected_from_owner_tag_list(self):
        response = self.client.get(reverse("bitacora:owner_tag_list"))

        self.assertEqual(response.status_code, 302)

    def test_owner_can_access_owner_tag_list(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("bitacora:owner_tag_list"))

        self.assertEqual(response.status_code, 200)

    def test_authenticated_non_owner_receives_forbidden_for_owner_tag_list(self):
        self.client.force_login(self.non_owner)

        response = self.client.get(reverse("bitacora:owner_tag_list"))

        self.assertEqual(response.status_code, 403)

    def test_owner_can_create_tag_through_form(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("bitacora:owner_tag_create"),
            {
                "name": "Architecture",
                "slug": "architecture",
                "description": "Architecture notes",
                "visibility": Tag.Visibility.PUBLIC,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Tag.objects.filter(slug="architecture").exists())

    def test_owner_can_view_tag_detail(self):
        self.client.force_login(self.owner)
        tag = self.create_tag()

        response = self.client.get(reverse("bitacora:owner_tag_detail", kwargs={"slug": tag.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, tag.name)

    def test_owner_can_edit_tag_through_form(self):
        self.client.force_login(self.owner)
        tag = self.create_tag()

        response = self.client.post(
            reverse("bitacora:owner_tag_edit", kwargs={"slug": tag.slug}),
            {
                "name": "Backend",
                "slug": "backend",
                "description": "Backend notes",
                "visibility": Tag.Visibility.PUBLIC,
            },
        )

        self.assertEqual(response.status_code, 302)
        tag.refresh_from_db()
        self.assertEqual(tag.name, "Backend")
        self.assertEqual(tag.slug, "backend")

    def test_owner_can_archive_tag_through_post(self):
        self.client.force_login(self.owner)
        tag = self.create_tag()

        response = self.client.post(reverse("bitacora:owner_tag_archive", kwargs={"slug": tag.slug}))

        self.assertEqual(response.status_code, 302)
        tag.refresh_from_db()
        self.assertTrue(tag.is_archived)

    def test_owner_can_access_document_tag_management_page(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("bitacora:owner_document_tags", kwargs={"document_id": self.document.id})
        )

        self.assertEqual(response.status_code, 200)

    def test_owner_can_assign_document_tags_through_form(self):
        self.client.force_login(self.owner)
        tag = self.create_tag()

        response = self.client.post(
            reverse("bitacora:owner_document_tags", kwargs={"document_id": self.document.id}),
            {"tags": [str(tag.id)]},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(DocumentTag.objects.filter(document=self.document, tag=tag).exists())

    def test_authenticated_non_owner_receives_forbidden_for_document_tag_management_page(self):
        self.client.force_login(self.non_owner)

        response = self.client.get(
            reverse("bitacora:owner_document_tags", kwargs={"document_id": self.document.id})
        )

        self.assertEqual(response.status_code, 403)

    def test_owner_document_detail_shows_assigned_private_and_public_tags(self):
        self.client.force_login(self.owner)
        private_tag = self.create_tag(name="Private Tag", slug="private-tag")
        public_tag = self.create_tag(
            name="Public Tag",
            slug="public-tag",
            visibility=Tag.Visibility.PUBLIC,
        )
        DocumentTag.objects.create(document=self.document, tag=private_tag)
        DocumentTag.objects.create(document=self.document, tag=public_tag)

        response = self.client.get(
            reverse("bitacora:owner_document_detail", kwargs={"document_id": self.document.id})
        )

        self.assertContains(response, "Private Tag")
        self.assertContains(response, "Public Tag")

    def test_public_document_detail_shows_public_tag(self):
        tag = self.create_tag(name="Public Tag", slug="public-tag", visibility=Tag.Visibility.PUBLIC)
        DocumentTag.objects.create(document=self.document, tag=tag)

        response = self.client.get(
            reverse("bitacora:public_document_detail", kwargs={"document_id": self.document.id})
        )

        self.assertContains(response, "Public Tag")

    def test_public_document_detail_hides_private_tag(self):
        tag = self.create_tag(name="Private Tag", slug="private-tag")
        DocumentTag.objects.create(document=self.document, tag=tag)

        response = self.client.get(
            reverse("bitacora:public_document_detail", kwargs={"document_id": self.document.id})
        )

        self.assertNotContains(response, "Private Tag")

    def test_public_document_detail_hides_archived_tag(self):
        tag = self.create_tag(
            name="Archived Tag",
            slug="archived-tag",
            visibility=Tag.Visibility.PUBLIC,
            is_archived=True,
        )
        DocumentTag.objects.create(document=self.document, tag=tag)

        response = self.client.get(
            reverse("bitacora:public_document_detail", kwargs={"document_id": self.document.id})
        )

        self.assertNotContains(response, "Archived Tag")

    def test_signup_route_still_returns_not_found(self):
        response = self.client.get("/accounts/signup/")

        self.assertEqual(response.status_code, 404)
