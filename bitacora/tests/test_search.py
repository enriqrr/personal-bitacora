from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from bitacora.models import DocumentTag, NodeDocument, Project, ProjectNode, Tag, WorkSession
from bitacora.search import MAX_QUERY_LENGTH, search_owner, search_public
from bitacora.services import create_work_session


class SearchHelperTests(TestCase):
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
            name="Alpha Public Project",
            slug="alpha-public",
            description="Launch architecture notes",
            visibility=Project.Visibility.PUBLIC,
        )
        self.private_project = Project.objects.create(
            owner=self.owner,
            name="Private Secret Project",
            slug="private-secret",
            visibility=Project.Visibility.PRIVATE,
        )
        self.archived_project = Project.objects.create(
            owner=self.owner,
            name="Archived Search Project",
            slug="archived-search",
            status=Project.Status.ARCHIVED,
            visibility=Project.Visibility.PUBLIC,
        )
        self.node = ProjectNode.objects.create(
            project=self.project,
            title="Visible Node Topic",
            slug="visible-node",
            description="Node public architecture",
            visibility=ProjectNode.Visibility.PUBLIC,
        )
        self.private_node = ProjectNode.objects.create(
            project=self.project,
            title="Private Node Secret",
            slug="private-node",
            visibility=ProjectNode.Visibility.PRIVATE,
        )
        self.archived_node = ProjectNode.objects.create(
            project=self.project,
            title="Archived Node Secret",
            slug="archived-node",
            visibility=ProjectNode.Visibility.PUBLIC,
            is_archived=True,
        )
        self.private_parent = ProjectNode.objects.create(
            project=self.project,
            title="Private Parent",
            slug="private-parent",
        )
        self.public_child = ProjectNode.objects.create(
            project=self.project,
            parent=self.private_parent,
            title="Child Hidden Topic",
            slug="child-hidden",
            visibility=ProjectNode.Visibility.PUBLIC,
        )
        self.document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="Visible Document Topic",
            slug="visible-document",
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PUBLIC,
            body_markdown="Public document body needle",
        )
        self.private_document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="Private Document Secret",
            slug="private-document",
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PRIVATE,
            body_markdown="private-snippet-leak",
        )
        self.draft_document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="Draft Public Secret",
            slug="draft-document",
            status=NodeDocument.Status.DRAFT,
            visibility=NodeDocument.Visibility.PUBLIC,
        )
        self.review_document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="Review Public Secret",
            slug="review-document",
            status=NodeDocument.Status.NEEDS_REVIEW,
            visibility=NodeDocument.Visibility.PUBLIC,
        )
        self.archived_document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="Archived Document Secret",
            slug="archived-document",
            status=NodeDocument.Status.ARCHIVED,
            visibility=NodeDocument.Visibility.PUBLIC,
        )
        self.hidden_child_document = NodeDocument.objects.create(
            project=self.project,
            node=self.public_child,
            title="Child Hidden Document",
            slug="child-hidden-document",
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PUBLIC,
        )
        self.public_session = create_work_session(
            owner=self.owner,
            project=self.project,
            title="Visible Session Topic",
            started_at=timezone.now(),
            visibility=WorkSession.Visibility.PUBLIC,
            summary="Public session summary needle",
        )
        self.private_session = create_work_session(
            owner=self.owner,
            project=self.project,
            title="Private Session Secret",
            started_at=timezone.now(),
        )
        self.archived_session = create_work_session(
            owner=self.owner,
            project=self.project,
            title="Archived Session Secret",
            started_at=timezone.now(),
            visibility=WorkSession.Visibility.PUBLIC,
        )
        self.archived_session.is_archived = True
        self.archived_session.save(update_fields=["is_archived"])
        self.private_tag = Tag.objects.create(
            owner=self.owner,
            name="Private Tag Secret",
            slug="private-tag-secret",
        )
        self.public_tag = Tag.objects.create(
            owner=self.owner,
            name="Public Tag Topic",
            slug="public-tag-topic",
            visibility=Tag.Visibility.PUBLIC,
        )
        DocumentTag.objects.create(document=self.document, tag=self.private_tag)
        DocumentTag.objects.create(document=self.document, tag=self.public_tag)
        self.other_project = Project.objects.create(
            owner=self.other_owner,
            name="Other Owner Secret",
            slug="other-owner-secret",
            visibility=Project.Visibility.PUBLIC,
        )

    def group_titles(self, results, group):
        return [result.title for result in results.groups[group]]

    def test_empty_public_query_returns_empty_grouped_results(self):
        results = search_public("   ")

        self.assertEqual(results.query, "")
        self.assertFalse(results.has_results)

    def test_empty_owner_query_returns_empty_grouped_results(self):
        results = search_owner(self.owner, "")

        self.assertEqual(results.query, "")
        self.assertFalse(results.has_results)

    def test_public_search_finds_public_project_by_name(self):
        self.assertIn("Alpha Public Project", self.group_titles(search_public("alpha"), "projects"))

    def test_public_search_does_not_find_private_project(self):
        self.assertNotIn("Private Secret Project", self.group_titles(search_public("secret"), "projects"))

    def test_public_search_does_not_find_archived_project(self):
        self.assertNotIn("Archived Search Project", self.group_titles(search_public("archived"), "projects"))

    def test_public_search_finds_effective_public_node_by_title(self):
        self.assertIn("Visible Node Topic", self.group_titles(search_public("node topic"), "nodes"))

    def test_public_search_does_not_find_private_node(self):
        self.assertNotIn("Private Node Secret", self.group_titles(search_public("secret"), "nodes"))

    def test_public_search_does_not_find_archived_node(self):
        self.assertNotIn("Archived Node Secret", self.group_titles(search_public("archived"), "nodes"))

    def test_public_search_does_not_find_public_child_under_private_parent(self):
        self.assertNotIn("Child Hidden Topic", self.group_titles(search_public("child hidden"), "nodes"))

    def test_public_search_finds_effective_public_document_by_title(self):
        self.assertIn("Visible Document Topic", self.group_titles(search_public("document topic"), "documents"))

    def test_public_search_finds_effective_public_document_by_body_text(self):
        self.assertIn("Visible Document Topic", self.group_titles(search_public("needle"), "documents"))

    def test_public_search_does_not_find_private_document(self):
        results = search_public("private")

        self.assertNotIn("Private Document Secret", self.group_titles(results, "documents"))

    def test_public_search_does_not_find_draft_public_document(self):
        self.assertNotIn("Draft Public Secret", self.group_titles(search_public("draft"), "documents"))

    def test_public_search_does_not_find_needs_review_public_document(self):
        self.assertNotIn("Review Public Secret", self.group_titles(search_public("review"), "documents"))

    def test_public_search_does_not_find_archived_document(self):
        self.assertNotIn("Archived Document Secret", self.group_titles(search_public("archived"), "documents"))

    def test_public_search_does_not_find_document_inside_private_node(self):
        self.assertNotIn("Child Hidden Document", self.group_titles(search_public("child hidden"), "documents"))

    def test_public_search_finds_public_work_session_by_title(self):
        self.assertIn("Visible Session Topic", self.group_titles(search_public("session topic"), "sessions"))

    def test_public_search_does_not_find_private_work_session(self):
        self.assertNotIn("Private Session Secret", self.group_titles(search_public("secret"), "sessions"))

    def test_public_search_does_not_find_archived_work_session(self):
        self.assertNotIn("Archived Session Secret", self.group_titles(search_public("archived"), "sessions"))

    def test_public_search_does_not_expose_private_tag_names(self):
        result_text = str(search_public("private tag secret"))

        self.assertNotIn("Private Tag Secret", result_text)

    def test_owner_search_finds_private_project(self):
        self.assertIn("Private Secret Project", self.group_titles(search_owner(self.owner, "secret"), "projects"))

    def test_owner_search_finds_private_node(self):
        self.assertIn("Private Node Secret", self.group_titles(search_owner(self.owner, "secret"), "nodes"))

    def test_owner_search_finds_draft_document(self):
        self.assertIn("Draft Public Secret", self.group_titles(search_owner(self.owner, "draft"), "documents"))

    def test_owner_search_finds_archived_document(self):
        self.assertIn("Archived Document Secret", self.group_titles(search_owner(self.owner, "archived"), "documents"))

    def test_owner_search_finds_private_work_session(self):
        self.assertIn("Private Session Secret", self.group_titles(search_owner(self.owner, "secret"), "sessions"))

    def test_owner_search_finds_archived_work_session(self):
        self.assertIn("Archived Session Secret", self.group_titles(search_owner(self.owner, "archived"), "sessions"))

    def test_owner_search_finds_private_tag(self):
        self.assertIn("Private Tag Secret", self.group_titles(search_owner(self.owner, "private tag"), "tags"))

    def test_owner_search_does_not_return_another_owners_content(self):
        self.assertNotIn("Other Owner Secret", self.group_titles(search_owner(self.owner, "other"), "projects"))

    def test_query_trimming_works(self):
        self.assertEqual(search_public("  alpha  ").query, "alpha")

    def test_query_length_cap_works(self):
        query = "x" * (MAX_QUERY_LENGTH + 20)

        self.assertEqual(len(search_public(query).query), MAX_QUERY_LENGTH)


class SearchViewTests(TestCase):
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
            name="Public Search Project",
            slug="public-search-project",
            visibility=Project.Visibility.PUBLIC,
        )
        self.private_project = Project.objects.create(
            owner=self.owner,
            name="Private Search Project",
            slug="private-search-project",
            visibility=Project.Visibility.PRIVATE,
        )
        self.node = ProjectNode.objects.create(
            project=self.project,
            title="Public Search Node",
            slug="public-search-node",
            visibility=ProjectNode.Visibility.PUBLIC,
        )
        self.document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="Public Search Document",
            slug="public-search-document",
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PUBLIC,
            body_markdown="public visible snippet",
        )
        self.private_document = NodeDocument.objects.create(
            project=self.project,
            node=self.node,
            title="Private Search Document",
            slug="private-search-document",
            status=NodeDocument.Status.ACTIVE,
            visibility=NodeDocument.Visibility.PRIVATE,
            body_markdown="private-hidden-snippet",
        )

    def test_public_search_returns_ok(self):
        response = self.client.get(reverse("bitacora:public_search"))

        self.assertEqual(response.status_code, 200)

    def test_public_search_with_query_returns_public_results(self):
        response = self.client.get(reverse("bitacora:public_search"), {"q": "public search"})

        self.assertContains(response, "Public Search Project")
        self.assertContains(response, "Public Search Document")

    def test_public_search_page_hides_private_results(self):
        response = self.client.get(reverse("bitacora:public_search"), {"q": "private search"})

        self.assertNotContains(response, "Private Search Project")
        self.assertNotContains(response, "Private Search Document")

    def test_public_search_page_hides_private_snippets(self):
        response = self.client.get(reverse("bitacora:public_search"), {"q": "private-hidden"})

        self.assertNotContains(response, "private-hidden-snippet")

    def test_owner_search_redirects_anonymous_users(self):
        response = self.client.get(reverse("bitacora:owner_search"))

        self.assertEqual(response.status_code, 302)

    def test_authenticated_non_owner_receives_forbidden_for_owner_search(self):
        self.client.force_login(self.non_owner)

        response = self.client.get(reverse("bitacora:owner_search"))

        self.assertEqual(response.status_code, 403)

    def test_owner_can_access_owner_search(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("bitacora:owner_search"))

        self.assertEqual(response.status_code, 200)

    def test_owner_search_page_returns_private_results_to_owner(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("bitacora:owner_search"), {"q": "private search"})

        self.assertContains(response, "Private Search Project")
        self.assertContains(response, "Private Search Document")

    def test_empty_search_page_shows_empty_state(self):
        response = self.client.get(reverse("bitacora:public_search"))

        self.assertContains(response, "Enter a search term.")

    def test_no_result_query_shows_no_results_state(self):
        response = self.client.get(reverse("bitacora:public_search"), {"q": "nothingmatches"})

        self.assertContains(response, "No results found.")

    def test_signup_route_still_returns_not_found(self):
        response = self.client.get("/accounts/signup/")

        self.assertEqual(response.status_code, 404)
