"""Read/query helpers for Bitacora."""

from .models import Project


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
