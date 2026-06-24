from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from bitacora.models import NodeDocument, Project, ProjectNode


class NodeDocumentViewTests(TestCase):
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

    def create_document(self, **overrides):
        defaults = {
            "project": self.project,
            "node": self.node,
            "title": "Document",
            "slug": "document",
        }
        defaults.update(overrides)
        return NodeDocument.objects.create(**defaults)

    def test_public_node_detail_lists_public_documents(self):
        self.create_document(
            title="Public Document",
            slug="public-document",
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PUBLIC,
        )

        response = self.client.get(reverse("bitacora:public_node_detail", kwargs={"node_id": self.node.id}))

        self.assertContains(response, "Public Document")

    def test_public_node_detail_hides_private_documents(self):
        self.create_document(
            title="Private Document",
            slug="private-document",
            status=NodeDocument.Status.ACTIVE,
        )

        response = self.client.get(reverse("bitacora:public_node_detail", kwargs={"node_id": self.node.id}))

        self.assertNotContains(response, "Private Document")

    def test_public_document_detail_returns_ok_for_effective_public_document(self):
        document = self.create_document(
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PUBLIC,
            body_markdown="# Public Doc",
        )

        response = self.client.get(reverse("bitacora:public_document_detail", kwargs={"document_id": document.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Public Doc</h1>", html=True)

    def test_public_document_detail_returns_not_found_for_private_document(self):
        document = self.create_document(status=NodeDocument.Status.ACTIVE)

        response = self.client.get(reverse("bitacora:public_document_detail", kwargs={"document_id": document.id}))

        self.assertEqual(response.status_code, 404)

    def test_public_document_detail_returns_not_found_for_draft_document(self):
        document = self.create_document(visibility=NodeDocument.Visibility.PUBLIC)

        response = self.client.get(reverse("bitacora:public_document_detail", kwargs={"document_id": document.id}))

        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_is_redirected_from_owner_create_document_page(self):
        response = self.client.get(reverse("bitacora:owner_document_create", kwargs={"node_id": self.node.id}))

        self.assertEqual(response.status_code, 302)

    def test_owner_can_access_create_document_page(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("bitacora:owner_document_create", kwargs={"node_id": self.node.id}))

        self.assertEqual(response.status_code, 200)

    def test_authenticated_non_owner_receives_forbidden_for_owner_create_document_page(self):
        self.client.force_login(self.non_owner)

        response = self.client.get(reverse("bitacora:owner_document_create", kwargs={"node_id": self.node.id}))

        self.assertEqual(response.status_code, 403)

    def test_owner_can_create_document_through_form(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("bitacora:owner_document_create", kwargs={"node_id": self.node.id}),
            {
                "title": "Created Document",
                "slug": "created-document",
                "document_type": NodeDocument.DocumentType.THEORY,
                "status": NodeDocument.Status.ACTIVE,
                "visibility": NodeDocument.Visibility.PUBLIC,
                "body_markdown": "# Created",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(NodeDocument.objects.filter(slug="created-document").exists())

    def test_owner_can_view_owner_document_detail(self):
        self.client.force_login(self.owner)
        document = self.create_document()

        response = self.client.get(reverse("bitacora:owner_document_detail", kwargs={"document_id": document.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, document.title)

    def test_owner_can_edit_document_through_form(self):
        self.client.force_login(self.owner)
        document = self.create_document()

        response = self.client.post(
            reverse("bitacora:owner_document_edit", kwargs={"document_id": document.id}),
            {
                "title": "Edited Document",
                "slug": "edited-document",
                "document_type": NodeDocument.DocumentType.DECISION,
                "status": NodeDocument.Status.RESOLVED,
                "visibility": NodeDocument.Visibility.PUBLIC,
                "body_markdown": "# Edited",
            },
        )

        self.assertEqual(response.status_code, 302)
        document.refresh_from_db()
        self.assertEqual(document.title, "Edited Document")
        self.assertEqual(document.slug, "edited-document")
        self.assertEqual(document.status, NodeDocument.Status.RESOLVED)

    def test_owner_can_archive_document_through_post(self):
        self.client.force_login(self.owner)
        document = self.create_document()

        response = self.client.post(reverse("bitacora:owner_document_archive", kwargs={"document_id": document.id}))

        self.assertEqual(response.status_code, 302)
        document.refresh_from_db()
        self.assertEqual(document.status, NodeDocument.Status.ARCHIVED)

    def test_signup_route_still_does_not_exist(self):
        response = self.client.get("/accounts/signup/")

        self.assertEqual(response.status_code, 404)
