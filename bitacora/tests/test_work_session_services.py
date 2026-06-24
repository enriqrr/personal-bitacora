from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from bitacora.models import (
    NodeDocument,
    Project,
    ProjectNode,
    WorkSession,
)
from bitacora.services import (
    archive_work_session,
    create_work_session,
    update_work_session,
)


class WorkSessionServiceTests(TestCase):
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

    def test_owner_can_create_work_session(self):
        work_session = self.create_session()

        self.assertEqual(work_session.project, self.project)
        self.assertEqual(work_session.title, "Session")

    def test_non_owner_cannot_create_work_session(self):
        with self.assertRaises(PermissionDenied):
            self.create_session(owner=self.non_owner)

    def test_anonymous_user_cannot_create_work_session(self):
        with self.assertRaises(PermissionDenied):
            self.create_session(owner=AnonymousUser())

    def test_cannot_create_work_session_for_another_owners_project(self):
        with self.assertRaises(PermissionDenied):
            self.create_session(project=self.other_project)

    def test_cannot_create_session_with_ended_at_before_started_at(self):
        with self.assertRaises(ValidationError):
            self.create_session(ended_at=self.started_at - timedelta(minutes=1))

    def test_can_create_session_with_node_references(self):
        work_session = self.create_session(referenced_nodes=[self.node])

        self.assertEqual(work_session.node_references.count(), 1)
        self.assertEqual(work_session.node_references.get().node, self.node)

    def test_can_create_session_with_document_references(self):
        work_session = self.create_session(referenced_documents=[self.document])

        self.assertEqual(work_session.document_references.count(), 1)
        self.assertEqual(work_session.document_references.get().document, self.document)

    def test_cannot_reference_node_from_another_project(self):
        with self.assertRaises(ValidationError):
            self.create_session(referenced_nodes=[self.other_node])

    def test_cannot_reference_document_from_another_project(self):
        with self.assertRaises(ValidationError):
            self.create_session(referenced_documents=[self.other_document])

    def test_duplicate_references_do_not_create_duplicate_rows(self):
        work_session = self.create_session(
            referenced_nodes=[self.node, self.node],
            referenced_documents=[self.document, self.document],
        )

        self.assertEqual(work_session.node_references.count(), 1)
        self.assertEqual(work_session.document_references.count(), 1)

    def test_can_update_work_session(self):
        work_session = self.create_session()
        ended_at = self.started_at + timedelta(hours=1)

        update_work_session(
            work_session,
            title="Updated",
            started_at=self.started_at,
            ended_at=ended_at,
            visibility=WorkSession.Visibility.PUBLIC,
            summary="Summary",
            goals="Goals",
            work_done="Work done",
            decisions_made="Decisions",
            doubts_opened="Doubts",
            next_actions="Next",
            referenced_nodes=[],
            referenced_documents=[],
        )

        work_session.refresh_from_db()
        self.assertEqual(work_session.title, "Updated")
        self.assertEqual(work_session.ended_at, ended_at)
        self.assertEqual(work_session.visibility, WorkSession.Visibility.PUBLIC)
        self.assertEqual(work_session.summary, "Summary")

    def test_updating_session_replaces_references(self):
        second_node = ProjectNode.objects.create(project=self.project, title="Second", slug="second")
        second_document = NodeDocument.objects.create(
            project=self.project,
            node=second_node,
            title="Second Document",
            slug="second-document",
        )
        work_session = self.create_session(
            referenced_nodes=[self.node],
            referenced_documents=[self.document],
        )

        update_work_session(
            work_session,
            title=work_session.title,
            started_at=work_session.started_at,
            ended_at=work_session.ended_at,
            visibility=work_session.visibility,
            summary=work_session.summary,
            goals=work_session.goals,
            work_done=work_session.work_done,
            decisions_made=work_session.decisions_made,
            doubts_opened=work_session.doubts_opened,
            next_actions=work_session.next_actions,
            referenced_nodes=[second_node],
            referenced_documents=[second_document],
        )

        self.assertEqual(work_session.node_references.get().node, second_node)
        self.assertEqual(work_session.document_references.get().document, second_document)

    def test_can_archive_work_session(self):
        work_session = self.create_session()

        archive_work_session(work_session)

        work_session.refresh_from_db()
        self.assertTrue(work_session.is_archived)

    def test_archive_sets_is_archived_and_does_not_delete_row(self):
        work_session = self.create_session()

        archive_work_session(work_session)

        self.assertTrue(WorkSession.objects.filter(pk=work_session.pk).exists())
        self.assertTrue(WorkSession.objects.get(pk=work_session.pk).is_archived)
