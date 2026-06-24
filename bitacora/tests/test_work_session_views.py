from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from bitacora.models import NodeDocument, Project, ProjectNode, WorkSession
from bitacora.services import create_work_session


class WorkSessionViewTests(TestCase):
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
        self.started_at = timezone.now()

    def create_session(self, **overrides):
        defaults = {
            "owner": self.owner,
            "project": self.project,
            "title": "Session",
            "started_at": self.started_at,
        }
        defaults.update(overrides)
        return create_work_session(**defaults)

    def form_data(self, **overrides):
        data = {
            "title": "Form Session",
            "started_at": self.started_at.strftime("%Y-%m-%dT%H:%M"),
            "ended_at": (self.started_at + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M"),
            "visibility": WorkSession.Visibility.PUBLIC,
            "summary": "Summary",
            "goals": "Goals",
            "work_done": "Work done",
            "decisions_made": "Decisions",
            "doubts_opened": "Doubts",
            "next_actions": "Next",
            "referenced_nodes": [str(self.node.id)],
            "referenced_documents": [str(self.document.id)],
        }
        data.update(overrides)
        return data

    def test_public_session_list_returns_ok_for_public_project(self):
        response = self.client.get(
            reverse("bitacora:public_session_list", kwargs={"project_slug": self.project.slug})
        )

        self.assertEqual(response.status_code, 200)

    def test_public_session_list_shows_public_sessions(self):
        self.create_session(title="Public Session", visibility=WorkSession.Visibility.PUBLIC)

        response = self.client.get(
            reverse("bitacora:public_session_list", kwargs={"project_slug": self.project.slug})
        )

        self.assertContains(response, "Public Session")

    def test_public_session_list_hides_private_sessions(self):
        self.create_session(title="Private Session")

        response = self.client.get(
            reverse("bitacora:public_session_list", kwargs={"project_slug": self.project.slug})
        )

        self.assertNotContains(response, "Private Session")

    def test_public_session_detail_returns_ok_for_public_session(self):
        work_session = self.create_session(visibility=WorkSession.Visibility.PUBLIC)

        response = self.client.get(
            reverse("bitacora:public_session_detail", kwargs={"session_id": work_session.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, work_session.title)

    def test_public_session_detail_returns_not_found_for_private_session(self):
        work_session = self.create_session()

        response = self.client.get(
            reverse("bitacora:public_session_detail", kwargs={"session_id": work_session.id})
        )

        self.assertEqual(response.status_code, 404)

    def test_public_session_detail_hides_private_node_references(self):
        private_node = ProjectNode.objects.create(project=self.project, title="Private Node", slug="private-node")
        work_session = self.create_session(
            visibility=WorkSession.Visibility.PUBLIC,
            referenced_nodes=[self.node, private_node],
        )

        response = self.client.get(
            reverse("bitacora:public_session_detail", kwargs={"session_id": work_session.id})
        )

        self.assertContains(response, self.node.title)
        self.assertNotContains(response, "Private Node")

    def test_public_session_detail_hides_private_document_references(self):
        private_document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="Private Document",
            slug="private-document",
            status=NodeDocument.Status.ACTIVE,
        )
        work_session = self.create_session(
            visibility=WorkSession.Visibility.PUBLIC,
            referenced_documents=[self.document, private_document],
        )

        response = self.client.get(
            reverse("bitacora:public_session_detail", kwargs={"session_id": work_session.id})
        )

        self.assertContains(response, self.document.title)
        self.assertNotContains(response, "Private Document")

    def test_anonymous_user_is_redirected_from_owner_session_list(self):
        response = self.client.get(
            reverse("bitacora:owner_session_list", kwargs={"project_slug": self.project.slug})
        )

        self.assertEqual(response.status_code, 302)

    def test_owner_can_access_owner_session_list(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("bitacora:owner_session_list", kwargs={"project_slug": self.project.slug})
        )

        self.assertEqual(response.status_code, 200)

    def test_authenticated_non_owner_receives_forbidden_for_owner_session_list(self):
        self.client.force_login(self.non_owner)

        response = self.client.get(
            reverse("bitacora:owner_session_list", kwargs={"project_slug": self.project.slug})
        )

        self.assertEqual(response.status_code, 403)

    def test_owner_can_access_create_session_page(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("bitacora:owner_session_create", kwargs={"project_slug": self.project.slug})
        )

        self.assertEqual(response.status_code, 200)

    def test_owner_can_create_session_through_form(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("bitacora:owner_session_create", kwargs={"project_slug": self.project.slug}),
            self.form_data(),
        )

        self.assertEqual(response.status_code, 302)
        work_session = WorkSession.objects.get(title="Form Session")
        self.assertEqual(work_session.node_references.count(), 1)
        self.assertEqual(work_session.document_references.count(), 1)

    def test_owner_can_view_owner_session_detail(self):
        self.client.force_login(self.owner)
        work_session = self.create_session()

        response = self.client.get(
            reverse("bitacora:owner_session_detail", kwargs={"session_id": work_session.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, work_session.title)

    def test_owner_can_edit_session_through_form(self):
        self.client.force_login(self.owner)
        work_session = self.create_session()

        response = self.client.post(
            reverse("bitacora:owner_session_edit", kwargs={"session_id": work_session.id}),
            self.form_data(title="Edited Session", referenced_nodes=[], referenced_documents=[]),
        )

        self.assertEqual(response.status_code, 302)
        work_session.refresh_from_db()
        self.assertEqual(work_session.title, "Edited Session")
        self.assertEqual(work_session.node_references.count(), 0)
        self.assertEqual(work_session.document_references.count(), 0)

    def test_owner_can_archive_session_through_post(self):
        self.client.force_login(self.owner)
        work_session = self.create_session()

        response = self.client.post(
            reverse("bitacora:owner_session_archive", kwargs={"session_id": work_session.id})
        )

        self.assertEqual(response.status_code, 302)
        work_session.refresh_from_db()
        self.assertTrue(work_session.is_archived)

    def test_signup_route_still_does_not_exist(self):
        response = self.client.get("/accounts/signup/")

        self.assertEqual(response.status_code, 404)
