from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from bitacora.models import NodeDocument, Project, ProjectNode, WorkSession
from bitacora.selectors import (
    get_owner_sessions_for_project,
    get_owner_sessions_referencing_document,
    get_owner_sessions_referencing_node,
    get_public_document_references_for_session,
    get_public_node_references_for_session,
    get_public_session_by_id,
    get_public_sessions_for_project,
)
from bitacora.services import create_work_session


class WorkSessionSelectorTests(TestCase):
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
        self.other_project = Project.objects.create(
            owner=self.other_owner,
            name="Other",
            slug="other",
            visibility=Project.Visibility.PUBLIC,
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

    def test_owner_selector_returns_all_sessions_for_owned_project(self):
        private_session = self.create_session(title="Private")
        public_session = self.create_session(
            title="Public",
            visibility=WorkSession.Visibility.PUBLIC,
        )
        archived_session = self.create_session(title="Archived")
        archived_session.is_archived = True
        archived_session.save(update_fields=["is_archived"])

        sessions = get_owner_sessions_for_project(self.owner, self.project)

        self.assertIn(private_session, sessions)
        self.assertIn(public_session, sessions)
        self.assertIn(archived_session, sessions)

    def test_owner_selector_does_not_return_sessions_from_another_owners_project(self):
        other_session = create_work_session(
            owner=self.other_owner,
            project=self.other_project,
            title="Other",
            started_at=self.started_at,
        )

        sessions = get_owner_sessions_for_project(self.owner, self.other_project)

        self.assertNotIn(other_session, sessions)
        self.assertEqual(list(sessions), [])

    def test_public_selector_returns_public_non_archived_sessions_in_public_active_project(self):
        work_session = self.create_session(visibility=WorkSession.Visibility.PUBLIC)

        self.assertIn(work_session, get_public_sessions_for_project(self.project))

    def test_public_selector_excludes_private_sessions(self):
        work_session = self.create_session()

        self.assertNotIn(work_session, get_public_sessions_for_project(self.project))

    def test_public_selector_excludes_archived_sessions(self):
        work_session = self.create_session(visibility=WorkSession.Visibility.PUBLIC)
        work_session.is_archived = True
        work_session.save(update_fields=["is_archived"])

        self.assertNotIn(work_session, get_public_sessions_for_project(self.project))

    def test_public_selector_excludes_sessions_from_private_project(self):
        self.project.visibility = Project.Visibility.PRIVATE
        self.project.save(update_fields=["visibility"])
        work_session = self.create_session(visibility=WorkSession.Visibility.PUBLIC)

        self.assertNotIn(work_session, get_public_sessions_for_project(self.project))

    def test_public_session_detail_selector_returns_public_session(self):
        work_session = self.create_session(visibility=WorkSession.Visibility.PUBLIC)

        self.assertEqual(get_public_session_by_id(work_session.id), work_session)

    def test_public_session_detail_selector_rejects_private_session(self):
        work_session = self.create_session()

        with self.assertRaises(WorkSession.DoesNotExist):
            get_public_session_by_id(work_session.id)

    def test_public_session_detail_selector_rejects_archived_session(self):
        work_session = self.create_session(visibility=WorkSession.Visibility.PUBLIC)
        work_session.is_archived = True
        work_session.save(update_fields=["is_archived"])

        with self.assertRaises(WorkSession.DoesNotExist):
            get_public_session_by_id(work_session.id)

    def test_public_node_reference_selector_hides_private_archived_non_effective_nodes(self):
        private_node = ProjectNode.objects.create(project=self.project, title="Private", slug="private")
        archived_node = ProjectNode.objects.create(
            project=self.project,
            title="Archived",
            slug="archived",
            visibility=ProjectNode.Visibility.PUBLIC,
            is_archived=True,
        )
        private_parent = ProjectNode.objects.create(project=self.project, title="Parent", slug="parent")
        public_child = ProjectNode.objects.create(
            project=self.project,
            parent=private_parent,
            title="Child",
            slug="child",
            visibility=ProjectNode.Visibility.PUBLIC,
        )
        work_session = self.create_session(
            visibility=WorkSession.Visibility.PUBLIC,
            referenced_nodes=[self.node, private_node, archived_node, public_child],
        )

        references = get_public_node_references_for_session(work_session)

        self.assertIn(self.node, references)
        self.assertNotIn(private_node, references)
        self.assertNotIn(archived_node, references)
        self.assertNotIn(public_child, references)

    def test_public_document_reference_selector_hides_private_draft_archived_non_effective_documents(self):
        private_document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="Private",
            slug="private",
            status=NodeDocument.Status.ACTIVE,
        )
        draft_document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="Draft",
            slug="draft",
            visibility=NodeDocument.Visibility.PUBLIC,
        )
        archived_document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="Archived",
            slug="archived",
            status=NodeDocument.Status.ARCHIVED,
            visibility=NodeDocument.Visibility.PUBLIC,
        )
        private_node = ProjectNode.objects.create(project=self.project, title="Private Node", slug="private-node")
        hidden_document = NodeDocument.objects.create(
            project=self.project,
            node=private_node,
            title="Hidden",
            slug="hidden",
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PUBLIC,
        )
        work_session = self.create_session(
            visibility=WorkSession.Visibility.PUBLIC,
            referenced_documents=[
                self.document,
                private_document,
                draft_document,
                archived_document,
                hidden_document,
            ],
        )

        references = get_public_document_references_for_session(work_session)

        self.assertIn(self.document, references)
        self.assertNotIn(private_document, references)
        self.assertNotIn(draft_document, references)
        self.assertNotIn(archived_document, references)
        self.assertNotIn(hidden_document, references)

    def test_owner_sessions_referencing_node_selector_works(self):
        work_session = self.create_session(referenced_nodes=[self.node])

        self.assertIn(work_session, get_owner_sessions_referencing_node(self.owner, self.node))

    def test_owner_sessions_referencing_document_selector_works(self):
        work_session = self.create_session(referenced_documents=[self.document])

        self.assertIn(work_session, get_owner_sessions_referencing_document(self.owner, self.document))
