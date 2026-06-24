from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from bitacora.models import (
    NodeDocument,
    Project,
    ProjectNode,
    WorkSession,
    WorkSessionDocumentReference,
    WorkSessionNodeReference,
)


class WorkSessionModelTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_superuser(
            username="owner",
            email="owner@example.com",
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
        self.started_at = timezone.now()

    def create_session(self, **overrides):
        defaults = {
            "project": self.project,
            "title": "Session",
            "started_at": self.started_at,
        }
        defaults.update(overrides)
        return WorkSession.objects.create(**defaults)

    def test_work_session_can_be_created_with_required_fields(self):
        work_session = self.create_session()

        self.assertEqual(work_session.project, self.project)
        self.assertEqual(work_session.title, "Session")
        self.assertEqual(work_session.started_at, self.started_at)

    def test_default_visibility_is_private(self):
        work_session = self.create_session()

        self.assertEqual(work_session.visibility, WorkSession.Visibility.PRIVATE)

    def test_default_is_archived_is_false(self):
        work_session = self.create_session()

        self.assertFalse(work_session.is_archived)

    def test_string_representation_returns_session_title(self):
        work_session = self.create_session(title="Planning")

        self.assertEqual(str(work_session), "Planning")

    def test_ended_at_before_started_at_is_invalid(self):
        work_session = WorkSession(
            project=self.project,
            title="Invalid",
            started_at=self.started_at,
            ended_at=self.started_at - timedelta(minutes=1),
        )

        with self.assertRaises(ValidationError):
            work_session.full_clean()

    def test_node_reference_enforces_unique_session_node_pair(self):
        work_session = self.create_session()
        WorkSessionNodeReference.objects.create(work_session=work_session, node=self.node)

        with self.assertRaises(IntegrityError):
            WorkSessionNodeReference.objects.create(work_session=work_session, node=self.node)

    def test_document_reference_enforces_unique_session_document_pair(self):
        work_session = self.create_session()
        WorkSessionDocumentReference.objects.create(work_session=work_session, document=self.document)

        with self.assertRaises(IntegrityError):
            WorkSessionDocumentReference.objects.create(work_session=work_session, document=self.document)

    def test_node_reference_must_reference_node_from_same_project(self):
        other_project = Project.objects.create(owner=self.owner, name="Other", slug="other")
        other_node = ProjectNode.objects.create(project=other_project, title="Other Node", slug="other-node")
        work_session = self.create_session()
        reference = WorkSessionNodeReference(work_session=work_session, node=other_node)

        with self.assertRaises(ValidationError):
            reference.full_clean()

    def test_document_reference_must_reference_document_from_same_project(self):
        other_project = Project.objects.create(owner=self.owner, name="Other", slug="other")
        other_node = ProjectNode.objects.create(project=other_project, title="Other Node", slug="other-node")
        other_document = NodeDocument.objects.create(
            project=other_project,
            node=other_node,
            title="Other Document",
            slug="other-document",
        )
        work_session = self.create_session()
        reference = WorkSessionDocumentReference(work_session=work_session, document=other_document)

        with self.assertRaises(ValidationError):
            reference.full_clean()
