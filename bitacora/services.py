"""Mutation and business-rule services for Bitacora."""

from django.core.exceptions import PermissionDenied, ValidationError

from .models import Project, ProjectNode
from .permissions import is_owner


def create_project(
    *,
    owner,
    name,
    slug,
    description="",
    status=Project.Status.ACTIVE,
    visibility=Project.Visibility.PRIVATE,
):
    if not is_owner(owner):
        raise PermissionDenied("Only the owner can create projects.")

    return Project.objects.create(
        owner=owner,
        name=name,
        slug=slug,
        description=description,
        status=status,
        visibility=visibility,
    )


def update_project(project, *, name, slug, description, status, visibility):
    project.name = name
    project.slug = slug
    project.description = description
    project.status = status
    project.visibility = visibility
    project.save(update_fields=["name", "slug", "description", "status", "visibility", "updated_at"])
    return project


def archive_project(project):
    project.status = Project.Status.ARCHIVED
    project.save(update_fields=["status", "updated_at"])
    return project


def _validate_owner_for_project(owner, project):
    if not is_owner(owner):
        raise PermissionDenied("Only the owner can mutate nodes.")
    if project.owner_id != owner.id:
        raise PermissionDenied("Only the project owner can mutate nodes.")


def _validate_parent_project(project, parent):
    if parent and parent.project_id != project.id:
        raise ValidationError("Parent node must belong to the same project.")


def _validate_sibling_slug(project, parent, slug, *, exclude_node=None):
    nodes = ProjectNode.objects.filter(project=project, parent=parent, slug=slug)
    if exclude_node:
        nodes = nodes.exclude(pk=exclude_node.pk)
    if nodes.exists():
        raise ValidationError("Sibling nodes must have unique slugs.")


def is_descendant(candidate_parent, node):
    current = candidate_parent
    while current is not None:
        if current.pk == node.pk:
            return True
        current = current.parent
    return False


def create_project_node(
    *,
    owner,
    project,
    title,
    slug,
    description="",
    node_type=ProjectNode.NodeType.OTHER,
    visibility=ProjectNode.Visibility.PRIVATE,
    parent=None,
    position=0,
):
    _validate_owner_for_project(owner, project)
    _validate_parent_project(project, parent)
    _validate_sibling_slug(project, parent, slug)

    return ProjectNode.objects.create(
        project=project,
        parent=parent,
        title=title,
        slug=slug,
        description=description,
        node_type=node_type,
        visibility=visibility,
        position=position,
    )


def update_project_node(node, *, title, slug, description, node_type, visibility, position):
    _validate_sibling_slug(node.project, node.parent, slug, exclude_node=node)

    node.title = title
    node.slug = slug
    node.description = description
    node.node_type = node_type
    node.visibility = visibility
    node.position = position
    node.save(
        update_fields=[
            "title",
            "slug",
            "description",
            "node_type",
            "visibility",
            "position",
            "updated_at",
        ]
    )
    return node


def move_project_node(node, *, new_parent=None, position=0):
    if new_parent and new_parent.pk == node.pk:
        raise ValidationError("A node cannot be its own parent.")
    if new_parent and new_parent.project_id != node.project_id:
        raise ValidationError("Parent node must belong to the same project.")
    if new_parent and is_descendant(new_parent, node):
        raise ValidationError("A node cannot be moved under one of its descendants.")
    _validate_sibling_slug(node.project, new_parent, node.slug, exclude_node=node)

    node.parent = new_parent
    node.position = position
    node.save(update_fields=["parent", "position", "updated_at"])
    return node


def archive_project_node(node):
    node.is_archived = True
    node.save(update_fields=["is_archived", "updated_at"])
    return node
