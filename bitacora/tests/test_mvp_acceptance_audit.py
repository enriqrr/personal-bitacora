import importlib
import os
import sys
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from bitacora.models import DocumentTag, NodeDocument, Project, ProjectNode, Tag, WorkSession
from bitacora.services import create_work_session


def import_production_settings(env):
    sys.modules.pop("config.settings.production", None)
    with patch.dict(os.environ, env, clear=True):
        return importlib.import_module("config.settings.production")


class MvpProductionSettingsCanaryTests(SimpleTestCase):
    def test_production_settings_load_with_secure_deployment_environment(self):
        settings = import_production_settings(
            {
                "SECRET_KEY": "not-for-real-deploys-but-long-enough-for-checks",
                "DATABASE_URL": "sqlite:///production-audit-test.sqlite3",
                "ALLOWED_HOSTS": "example.com,www.example.com",
                "CSRF_TRUSTED_ORIGINS": "https://example.com,https://www.example.com",
                "SECURE_SSL_REDIRECT": "True",
                "SESSION_COOKIE_SECURE": "True",
                "CSRF_COOKIE_SECURE": "True",
                "SECURE_HSTS_SECONDS": "31536000",
            }
        )

        self.assertFalse(settings.DEBUG)
        self.assertEqual(settings.ALLOWED_HOSTS, ["example.com", "www.example.com"])
        self.assertEqual(
            settings.CSRF_TRUSTED_ORIGINS,
            ["https://example.com", "https://www.example.com"],
        )
        self.assertTrue(settings.SECURE_SSL_REDIRECT)
        self.assertTrue(settings.SESSION_COOKIE_SECURE)
        self.assertTrue(settings.CSRF_COOKIE_SECURE)
        self.assertEqual(settings.SECURE_HSTS_SECONDS, 31536000)


class MvpAcceptanceAuditCanaryTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_superuser(
            username="owner",
            email="owner@example.com",
            password="password",
        )
        self.non_owner = user_model.objects.create_user(
            username="reader",
            email="reader@example.com",
            password="password",
        )
        self.other_owner = user_model.objects.create_superuser(
            username="other-owner",
            email="other@example.com",
            password="password",
        )

        self.project = Project.objects.create(
            owner=self.owner,
            name="Audit Public Project",
            slug="audit-public-project",
            description="Audit public project description",
            visibility=Project.Visibility.PUBLIC,
        )
        self.private_project = Project.objects.create(
            owner=self.owner,
            name="CANARY_PRIVATE_PROJECT_TITLE",
            slug="private-project",
            visibility=Project.Visibility.PRIVATE,
        )
        self.archived_project = Project.objects.create(
            owner=self.owner,
            name="CANARY_ARCHIVED_PROJECT_TITLE",
            slug="archived-project",
            status=Project.Status.ARCHIVED,
            visibility=Project.Visibility.PUBLIC,
        )
        self.other_project = Project.objects.create(
            owner=self.other_owner,
            name="CANARY_OTHER_OWNER_PROJECT_TITLE",
            slug="other-project",
            visibility=Project.Visibility.PRIVATE,
        )

        self.node = ProjectNode.objects.create(
            project=self.project,
            title="Audit Public Node",
            slug="audit-public-node",
            description="Audit public node description",
            visibility=ProjectNode.Visibility.PUBLIC,
        )
        self.private_node = ProjectNode.objects.create(
            project=self.project,
            title="CANARY_PRIVATE_NODE_TITLE",
            slug="private-node",
            visibility=ProjectNode.Visibility.PRIVATE,
        )
        self.archived_node = ProjectNode.objects.create(
            project=self.project,
            title="CANARY_ARCHIVED_NODE_TITLE",
            slug="archived-node",
            visibility=ProjectNode.Visibility.PUBLIC,
            is_archived=True,
        )
        self.private_parent = ProjectNode.objects.create(
            project=self.project,
            title="Audit Private Parent",
            slug="private-parent",
            visibility=ProjectNode.Visibility.PRIVATE,
        )
        self.child_under_private_parent = ProjectNode.objects.create(
            project=self.project,
            parent=self.private_parent,
            title="CANARY_CHILD_UNDER_PRIVATE_PARENT_TITLE",
            slug="child-under-private-parent",
            visibility=ProjectNode.Visibility.PUBLIC,
        )

        self.document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="Audit Public Document",
            slug="audit-public-document",
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PUBLIC,
            body_markdown=(
                "# Audit Public Body\n\n"
                "<script>alert('bad')</script>\n\n"
                '<a href="javascript:alert(1)" onclick="alert(2)">unsafe link</a>\n\n'
                '<img src="x" onerror="alert(3)">'
            ),
        )
        self.private_document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="CANARY_PRIVATE_DOCUMENT_TITLE",
            slug="private-document",
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PRIVATE,
            body_markdown="CANARY_PRIVATE_DOCUMENT_BODY",
        )
        self.draft_document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="CANARY_DRAFT_DOCUMENT_TITLE",
            slug="draft-document",
            status=NodeDocument.Status.DRAFT,
            visibility=NodeDocument.Visibility.PUBLIC,
        )
        self.review_document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="CANARY_REVIEW_DOCUMENT_TITLE",
            slug="review-document",
            status=NodeDocument.Status.NEEDS_REVIEW,
            visibility=NodeDocument.Visibility.PUBLIC,
        )
        self.archived_document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="CANARY_ARCHIVED_DOCUMENT_TITLE",
            slug="archived-document",
            status=NodeDocument.Status.ARCHIVED,
            visibility=NodeDocument.Visibility.PUBLIC,
        )
        self.child_document = NodeDocument.objects.create(
            project=self.project,
            node=self.child_under_private_parent,
            title="CANARY_CHILD_DOCUMENT_TITLE",
            slug="child-document",
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PUBLIC,
        )

        self.public_session = create_work_session(
            owner=self.owner,
            project=self.project,
            title="Audit Public Session",
            started_at=timezone.now(),
            visibility=WorkSession.Visibility.PUBLIC,
            summary="Audit public session summary",
            referenced_nodes=[self.node, self.private_node],
            referenced_documents=[self.document, self.private_document],
        )
        self.private_session = create_work_session(
            owner=self.owner,
            project=self.project,
            title="CANARY_PRIVATE_SESSION_TITLE",
            started_at=timezone.now(),
            summary="CANARY_PRIVATE_SESSION_BODY",
        )
        self.archived_session = create_work_session(
            owner=self.owner,
            project=self.project,
            title="CANARY_ARCHIVED_SESSION_TITLE",
            started_at=timezone.now(),
            visibility=WorkSession.Visibility.PUBLIC,
        )
        self.archived_session.is_archived = True
        self.archived_session.save(update_fields=["is_archived"])

        self.public_tag = Tag.objects.create(
            owner=self.owner,
            name="Audit Public Tag",
            slug="audit-public-tag",
            visibility=Tag.Visibility.PUBLIC,
        )
        self.private_tag = Tag.objects.create(
            owner=self.owner,
            name="CANARY_PRIVATE_TAG_TITLE",
            slug="private-tag",
        )
        self.archived_tag = Tag.objects.create(
            owner=self.owner,
            name="CANARY_ARCHIVED_TAG_TITLE",
            slug="archived-tag",
            visibility=Tag.Visibility.PUBLIC,
            is_archived=True,
        )
        DocumentTag.objects.create(document=self.document, tag=self.public_tag)
        DocumentTag.objects.create(document=self.document, tag=self.private_tag)
        DocumentTag.objects.create(document=self.document, tag=self.archived_tag)

    def assert_response_hides_leak_terms(self, response):
        leak_terms = [
            "CANARY_PRIVATE_PROJECT_TITLE",
            "CANARY_ARCHIVED_PROJECT_TITLE",
            "CANARY_OTHER_OWNER_PROJECT_TITLE",
            "CANARY_PRIVATE_NODE_TITLE",
            "CANARY_ARCHIVED_NODE_TITLE",
            "CANARY_CHILD_UNDER_PRIVATE_PARENT_TITLE",
            "CANARY_PRIVATE_DOCUMENT_TITLE",
            "CANARY_PRIVATE_DOCUMENT_BODY",
            "CANARY_DRAFT_DOCUMENT_TITLE",
            "CANARY_REVIEW_DOCUMENT_TITLE",
            "CANARY_ARCHIVED_DOCUMENT_TITLE",
            "CANARY_CHILD_DOCUMENT_TITLE",
            "CANARY_PRIVATE_SESSION_TITLE",
            "CANARY_PRIVATE_SESSION_BODY",
            "CANARY_ARCHIVED_SESSION_TITLE",
            "CANARY_PRIVATE_TAG_TITLE",
            "CANARY_ARCHIVED_TAG_TITLE",
        ]
        for term in leak_terms:
            self.assertNotContains(response, term)

    def test_public_surfaces_hide_private_archived_and_non_effective_canaries(self):
        public_urls = [
            reverse("bitacora:public_project_list"),
            reverse("bitacora:public_project_detail", kwargs={"slug": self.project.slug}),
            reverse("bitacora:public_project_tree", kwargs={"project_slug": self.project.slug}),
            reverse("bitacora:public_node_detail", kwargs={"node_id": self.node.id}),
            reverse("bitacora:public_document_detail", kwargs={"document_id": self.document.id}),
            reverse("bitacora:public_session_list", kwargs={"project_slug": self.project.slug}),
            reverse("bitacora:public_session_detail", kwargs={"session_id": self.public_session.id}),
        ]

        for url in public_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assert_response_hides_leak_terms(response)

    def test_public_search_hides_canaries_that_owner_search_can_see(self):
        public_response = self.client.get(reverse("bitacora:public_search"), {"q": "CANARY"})
        self.assertEqual(public_response.status_code, 200)
        self.assert_response_hides_leak_terms(public_response)

        self.client.force_login(self.owner)
        owner_response = self.client.get(reverse("bitacora:owner_search"), {"q": "CANARY"})

        self.assertContains(owner_response, "CANARY_PRIVATE_PROJECT_TITLE")
        self.assertContains(owner_response, "CANARY_PRIVATE_NODE_TITLE")
        self.assertContains(owner_response, "CANARY_PRIVATE_DOCUMENT_TITLE")
        self.assertContains(owner_response, "CANARY_PRIVATE_SESSION_TITLE")
        self.assertContains(owner_response, "CANARY_PRIVATE_TAG_TITLE")
        self.assertNotContains(owner_response, "CANARY_OTHER_OWNER_PROJECT_TITLE")

    def test_public_document_markdown_is_sanitized_before_safe_rendering(self):
        response = self.client.get(
            reverse("bitacora:public_document_detail", kwargs={"document_id": self.document.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Audit Public Body</h1>", html=True)
        self.assertNotContains(response, "<script")
        self.assertNotContains(response, "javascript:alert")
        self.assertNotContains(response, "onclick=")
        self.assertNotContains(response, "onerror=")

    def test_dashboard_routes_reject_anonymous_and_non_owner_users(self):
        owner_urls = [
            reverse("bitacora:dashboard"),
            reverse("bitacora:owner_search"),
            reverse("bitacora:owner_project_list"),
            reverse("bitacora:owner_project_create"),
            reverse("bitacora:owner_project_detail", kwargs={"slug": self.project.slug}),
            reverse("bitacora:owner_project_edit", kwargs={"slug": self.project.slug}),
            reverse("bitacora:owner_project_archive", kwargs={"slug": self.project.slug}),
            reverse("bitacora:owner_project_tree", kwargs={"project_slug": self.project.slug}),
            reverse("bitacora:owner_node_create_root", kwargs={"project_slug": self.project.slug}),
            reverse("bitacora:owner_session_list", kwargs={"project_slug": self.project.slug}),
            reverse("bitacora:owner_session_create", kwargs={"project_slug": self.project.slug}),
            reverse("bitacora:owner_node_detail", kwargs={"node_id": self.node.id}),
            reverse("bitacora:owner_node_create_child", kwargs={"node_id": self.node.id}),
            reverse("bitacora:owner_node_edit", kwargs={"node_id": self.node.id}),
            reverse("bitacora:owner_node_move", kwargs={"node_id": self.node.id}),
            reverse("bitacora:owner_node_archive", kwargs={"node_id": self.node.id}),
            reverse("bitacora:owner_document_create", kwargs={"node_id": self.node.id}),
            reverse("bitacora:owner_document_detail", kwargs={"document_id": self.document.id}),
            reverse("bitacora:owner_document_tags", kwargs={"document_id": self.document.id}),
            reverse("bitacora:owner_document_edit", kwargs={"document_id": self.document.id}),
            reverse("bitacora:owner_document_archive", kwargs={"document_id": self.document.id}),
            reverse("bitacora:owner_session_detail", kwargs={"session_id": self.public_session.id}),
            reverse("bitacora:owner_session_edit", kwargs={"session_id": self.public_session.id}),
            reverse("bitacora:owner_session_archive", kwargs={"session_id": self.public_session.id}),
            reverse("bitacora:owner_tag_list"),
            reverse("bitacora:owner_tag_create"),
            reverse("bitacora:owner_tag_detail", kwargs={"slug": self.public_tag.slug}),
            reverse("bitacora:owner_tag_edit", kwargs={"slug": self.public_tag.slug}),
            reverse("bitacora:owner_tag_archive", kwargs={"slug": self.public_tag.slug}),
        ]

        for url in owner_urls:
            with self.subTest(user="anonymous", url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)

        self.client.force_login(self.non_owner)
        for url in owner_urls:
            with self.subTest(user="non_owner", url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)
