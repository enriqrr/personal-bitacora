"""Read/query helpers for Bitacora."""

from .models import Project, ProjectNode


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
