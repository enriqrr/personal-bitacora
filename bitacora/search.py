"""Simple database-backed search helpers."""

from dataclasses import dataclass
import re

from django.db.models import Q
from django.urls import reverse

from .models import NodeDocument, Project, ProjectNode, Tag, WorkSession
from .selectors import (
    is_document_effectively_public,
    is_node_effectively_public,
    is_work_session_effectively_public,
)

MAX_QUERY_LENGTH = 100
SNIPPET_LENGTH = 160


@dataclass(frozen=True)
class SearchResult:
    result_type: str
    title: str
    url: str
    subtitle: str = ""
    snippet: str = ""
    metadata: str = ""


@dataclass(frozen=True)
class GroupedSearchResults:
    query: str
    groups: dict

    @property
    def has_results(self):
        return any(self.groups.values())


def normalize_query(query):
    return (query or "").strip()[:MAX_QUERY_LENGTH]


def _empty_groups(include_tags=False):
    groups = {
        "projects": [],
        "nodes": [],
        "documents": [],
        "sessions": [],
    }
    if include_tags:
        groups["tags"] = []
    return groups


def _contains_query(value, query):
    return query.lower() in (value or "").lower()


def _clean_text(value):
    return re.sub(r"\s+", " ", value or "").strip()


def _snippet(query, *values):
    for value in values:
        text = _clean_text(value)
        if text and _contains_query(text, query):
            return text[:SNIPPET_LENGTH]
    for value in values:
        text = _clean_text(value)
        if text:
            return text[:SNIPPET_LENGTH]
    return ""


def _owner_metadata(*, visibility=None, status=None, is_archived=None):
    parts = []
    if status:
        parts.append(f"status: {status}")
    if visibility:
        parts.append(f"visibility: {visibility}")
    if is_archived is not None:
        parts.append(f"archived: {is_archived}")
    return " | ".join(parts)


def search_public_projects(query):
    query = normalize_query(query)
    if not query:
        return []
    projects = Project.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query),
        visibility=Project.Visibility.PUBLIC,
    ).exclude(status=Project.Status.ARCHIVED)
    return [
        SearchResult(
            result_type="project",
            title=project.name,
            subtitle="Project",
            url=reverse("bitacora:public_project_detail", kwargs={"slug": project.slug}),
            snippet=_snippet(query, project.description),
        )
        for project in projects
    ]


def search_public_nodes(query):
    query = normalize_query(query)
    if not query:
        return []
    candidates = ProjectNode.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    ).select_related("project", "parent")
    return [
        SearchResult(
            result_type="node",
            title=node.title,
            subtitle=node.project.name,
            url=reverse("bitacora:public_node_detail", kwargs={"node_id": node.id}),
            snippet=_snippet(query, node.description),
        )
        for node in candidates
        if is_node_effectively_public(node)
    ]


def search_public_documents(query):
    query = normalize_query(query)
    if not query:
        return []
    candidates = NodeDocument.objects.filter(
        Q(title__icontains=query) | Q(body_markdown__icontains=query)
    ).select_related("project", "node", "node__project", "node__parent")
    return [
        SearchResult(
            result_type="document",
            title=document.title,
            subtitle=document.node.title,
            url=reverse("bitacora:public_document_detail", kwargs={"document_id": document.id}),
            snippet=_snippet(query, document.body_markdown),
        )
        for document in candidates
        if is_document_effectively_public(document)
    ]


def search_public_work_sessions(query):
    query = normalize_query(query)
    if not query:
        return []
    candidates = WorkSession.objects.filter(
        Q(title__icontains=query)
        | Q(summary__icontains=query)
        | Q(goals__icontains=query)
        | Q(work_done__icontains=query)
        | Q(decisions_made__icontains=query)
        | Q(doubts_opened__icontains=query)
        | Q(next_actions__icontains=query)
    ).select_related("project")
    return [
        SearchResult(
            result_type="session",
            title=work_session.title,
            subtitle=work_session.project.name,
            url=reverse("bitacora:public_session_detail", kwargs={"session_id": work_session.id}),
            snippet=_snippet(
                query,
                work_session.summary,
                work_session.goals,
                work_session.work_done,
                work_session.decisions_made,
                work_session.doubts_opened,
                work_session.next_actions,
            ),
        )
        for work_session in candidates
        if is_work_session_effectively_public(work_session)
    ]


def search_public(query):
    query = normalize_query(query)
    groups = _empty_groups()
    if query:
        groups["projects"] = search_public_projects(query)
        groups["nodes"] = search_public_nodes(query)
        groups["documents"] = search_public_documents(query)
        groups["sessions"] = search_public_work_sessions(query)
    return GroupedSearchResults(query=query, groups=groups)


def search_owner_projects(owner, query):
    query = normalize_query(query)
    if not query:
        return []
    projects = Project.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query),
        owner=owner,
    )
    return [
        SearchResult(
            result_type="project",
            title=project.name,
            subtitle="Project",
            url=reverse("bitacora:owner_project_detail", kwargs={"slug": project.slug}),
            snippet=_snippet(query, project.description),
            metadata=_owner_metadata(visibility=project.visibility, status=project.status),
        )
        for project in projects
    ]


def search_owner_nodes(owner, query):
    query = normalize_query(query)
    if not query:
        return []
    nodes = ProjectNode.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query),
        project__owner=owner,
    ).select_related("project")
    return [
        SearchResult(
            result_type="node",
            title=node.title,
            subtitle=node.project.name,
            url=reverse("bitacora:owner_node_detail", kwargs={"node_id": node.id}),
            snippet=_snippet(query, node.description),
            metadata=_owner_metadata(visibility=node.visibility, is_archived=node.is_archived),
        )
        for node in nodes
    ]


def search_owner_documents(owner, query):
    query = normalize_query(query)
    if not query:
        return []
    documents = NodeDocument.objects.filter(
        Q(title__icontains=query) | Q(body_markdown__icontains=query),
        project__owner=owner,
    ).select_related("node")
    return [
        SearchResult(
            result_type="document",
            title=document.title,
            subtitle=document.node.title,
            url=reverse("bitacora:owner_document_detail", kwargs={"document_id": document.id}),
            snippet=_snippet(query, document.body_markdown),
            metadata=_owner_metadata(visibility=document.visibility, status=document.status),
        )
        for document in documents
    ]


def search_owner_work_sessions(owner, query):
    query = normalize_query(query)
    if not query:
        return []
    sessions = WorkSession.objects.filter(
        Q(title__icontains=query)
        | Q(summary__icontains=query)
        | Q(goals__icontains=query)
        | Q(work_done__icontains=query)
        | Q(decisions_made__icontains=query)
        | Q(doubts_opened__icontains=query)
        | Q(next_actions__icontains=query),
        project__owner=owner,
    ).select_related("project")
    return [
        SearchResult(
            result_type="session",
            title=work_session.title,
            subtitle=work_session.project.name,
            url=reverse("bitacora:owner_session_detail", kwargs={"session_id": work_session.id}),
            snippet=_snippet(
                query,
                work_session.summary,
                work_session.goals,
                work_session.work_done,
                work_session.decisions_made,
                work_session.doubts_opened,
                work_session.next_actions,
            ),
            metadata=_owner_metadata(
                visibility=work_session.visibility,
                is_archived=work_session.is_archived,
            ),
        )
        for work_session in sessions
    ]


def search_owner_tags(owner, query):
    query = normalize_query(query)
    if not query:
        return []
    tags = Tag.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query),
        owner=owner,
    )
    return [
        SearchResult(
            result_type="tag",
            title=tag.name,
            subtitle="Tag",
            url=reverse("bitacora:owner_tag_detail", kwargs={"slug": tag.slug}),
            snippet=_snippet(query, tag.description),
            metadata=_owner_metadata(visibility=tag.visibility, is_archived=tag.is_archived),
        )
        for tag in tags
    ]


def search_owner(owner, query):
    query = normalize_query(query)
    groups = _empty_groups(include_tags=True)
    if query:
        groups["projects"] = search_owner_projects(owner, query)
        groups["nodes"] = search_owner_nodes(owner, query)
        groups["documents"] = search_owner_documents(owner, query)
        groups["sessions"] = search_owner_work_sessions(owner, query)
        groups["tags"] = search_owner_tags(owner, query)
    return GroupedSearchResults(query=query, groups=groups)
