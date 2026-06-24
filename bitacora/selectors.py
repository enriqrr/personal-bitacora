"""Read/query helpers for Bitacora."""

from .models import NodeDocument, Project, ProjectNode, Tag, WorkSession


def get_public_projects():
    return Project.objects.filter(
        visibility=Project.Visibility.PUBLIC,
    ).exclude(status=Project.Status.ARCHIVED)


def get_public_project_by_slug(slug):
    return get_public_projects().get(slug=slug)


def get_owner_projects(owner):
    return Project.objects.filter(owner=owner)


def get_owner_project_by_slug(owner, slug):
    return get_owner_projects(owner).get(slug=slug)


def get_owner_nodes_for_project(owner, project):
    if project.owner_id != owner.id:
        return ProjectNode.objects.none()
    return ProjectNode.objects.filter(project=project)


def get_owner_root_nodes_for_project(owner, project):
    return get_owner_nodes_for_project(owner, project).filter(parent__isnull=True)


def get_owner_node_by_id(owner, node_id):
    return ProjectNode.objects.filter(project__owner=owner).get(pk=node_id)


def is_node_effectively_public(node):
    if (
        node.project.visibility != Project.Visibility.PUBLIC
        or node.project.status == Project.Status.ARCHIVED
        or node.visibility != ProjectNode.Visibility.PUBLIC
        or node.is_archived
    ):
        return False

    current = node.parent
    while current is not None:
        if current.visibility != ProjectNode.Visibility.PUBLIC or current.is_archived:
            return False
        current = current.parent
    return True


def get_public_root_nodes_for_project(project):
    if (
        project.visibility != Project.Visibility.PUBLIC
        or project.status == Project.Status.ARCHIVED
    ):
        return ProjectNode.objects.none()
    return ProjectNode.objects.filter(
        project=project,
        parent__isnull=True,
        visibility=ProjectNode.Visibility.PUBLIC,
        is_archived=False,
    )


def get_public_nodes_for_project(project):
    candidates = ProjectNode.objects.filter(
        project=project,
        visibility=ProjectNode.Visibility.PUBLIC,
        is_archived=False,
    ).select_related("project", "parent")
    return [node for node in candidates if is_node_effectively_public(node)]


def get_public_node_by_id(node_id):
    node = ProjectNode.objects.select_related("project", "parent").get(pk=node_id)
    if not is_node_effectively_public(node):
        raise ProjectNode.DoesNotExist
    return node


def get_breadcrumb_nodes(node):
    breadcrumbs = []
    current = node
    while current is not None:
        breadcrumbs.append(current)
        current = current.parent
    return list(reversed(breadcrumbs))


def get_owner_documents_for_node(owner, node):
    if node.project.owner_id != owner.id:
        return NodeDocument.objects.none()
    return NodeDocument.objects.filter(node=node)


def get_owner_document_by_id(owner, document_id):
    return NodeDocument.objects.filter(project__owner=owner).get(pk=document_id)


def is_document_effectively_public(document):
    return (
        document.visibility == NodeDocument.Visibility.PUBLIC
        and document.status in [NodeDocument.Status.ACTIVE, NodeDocument.Status.RESOLVED]
        and is_node_effectively_public(document.node)
        and document.project_id == document.node.project_id
    )


def get_public_documents_for_node(node):
    if not is_node_effectively_public(node):
        return NodeDocument.objects.none()
    candidates = NodeDocument.objects.filter(
        node=node,
        visibility=NodeDocument.Visibility.PUBLIC,
        status__in=[NodeDocument.Status.ACTIVE, NodeDocument.Status.RESOLVED],
    ).select_related("project", "node", "node__project", "node__parent")
    return [document for document in candidates if is_document_effectively_public(document)]


def get_public_document_by_id(document_id):
    document = NodeDocument.objects.select_related(
        "project",
        "node",
        "node__project",
        "node__parent",
    ).get(pk=document_id)
    if not is_document_effectively_public(document):
        raise NodeDocument.DoesNotExist
    return document


def get_owner_sessions_for_project(owner, project):
    if project.owner_id != owner.id:
        return WorkSession.objects.none()
    return WorkSession.objects.filter(project=project)


def get_owner_session_by_id(owner, session_id):
    return WorkSession.objects.filter(project__owner=owner).get(pk=session_id)


def is_work_session_effectively_public(work_session):
    return (
        work_session.visibility == WorkSession.Visibility.PUBLIC
        and not work_session.is_archived
        and work_session.project.visibility == Project.Visibility.PUBLIC
        and work_session.project.status != Project.Status.ARCHIVED
    )


def get_public_sessions_for_project(project):
    if (
        project.visibility != Project.Visibility.PUBLIC
        or project.status == Project.Status.ARCHIVED
    ):
        return WorkSession.objects.none()
    return WorkSession.objects.filter(
        project=project,
        visibility=WorkSession.Visibility.PUBLIC,
        is_archived=False,
    )


def get_public_session_by_id(session_id):
    work_session = WorkSession.objects.select_related("project").get(pk=session_id)
    if not is_work_session_effectively_public(work_session):
        raise WorkSession.DoesNotExist
    return work_session


def get_public_node_references_for_session(work_session):
    nodes = [
        reference.node
        for reference in work_session.node_references.select_related(
            "node",
            "node__project",
            "node__parent",
        )
    ]
    return [node for node in nodes if is_node_effectively_public(node)]


def get_public_document_references_for_session(work_session):
    documents = [
        reference.document
        for reference in work_session.document_references.select_related(
            "document",
            "document__project",
            "document__node",
            "document__node__project",
            "document__node__parent",
        )
    ]
    return [document for document in documents if is_document_effectively_public(document)]


def get_owner_sessions_referencing_node(owner, node):
    return WorkSession.objects.filter(
        project__owner=owner,
        node_references__node=node,
    ).distinct()


def get_owner_sessions_referencing_document(owner, document):
    return WorkSession.objects.filter(
        project__owner=owner,
        document_references__document=document,
    ).distinct()


def get_owner_tags(owner):
    return Tag.objects.filter(owner=owner)


def get_active_owner_tags(owner):
    return get_owner_tags(owner).filter(is_archived=False)


def get_owner_tag_by_slug(owner, slug):
    return get_owner_tags(owner).get(slug=slug)


def get_owner_tags_for_document(owner, document):
    if document.project.owner_id != owner.id:
        return Tag.objects.none()
    return Tag.objects.filter(document_links__document=document).distinct()


def is_tag_effectively_public_for_document(tag, document):
    return (
        tag.visibility == Tag.Visibility.PUBLIC
        and not tag.is_archived
        and is_document_effectively_public(document)
        and tag.owner_id == document.project.owner_id
    )


def get_public_tags_for_document(document):
    if not is_document_effectively_public(document):
        return Tag.objects.none()
    return Tag.objects.filter(
        document_links__document=document,
        visibility=Tag.Visibility.PUBLIC,
        is_archived=False,
    ).distinct()


def get_owner_documents_for_tag(owner, tag):
    if tag.owner_id != owner.id:
        return NodeDocument.objects.none()
    return NodeDocument.objects.filter(tag_links__tag=tag, project__owner=owner).distinct()


def get_public_documents_for_tag(tag):
    if tag.visibility != Tag.Visibility.PUBLIC or tag.is_archived:
        return []
    documents = NodeDocument.objects.filter(tag_links__tag=tag).select_related(
        "project",
        "node",
        "node__project",
        "node__parent",
    )
    return [document for document in documents if is_document_effectively_public(document)]
