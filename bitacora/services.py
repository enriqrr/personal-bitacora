"""Mutation and business-rule services for Bitacora."""

from django.core.exceptions import PermissionDenied

from .models import Project
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
