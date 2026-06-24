"""Admin registrations for Bitacora."""

from django.contrib import admin

from .models import Project, ProjectNode


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "status", "visibility", "updated_at"]
    search_fields = ["name", "slug", "description"]


@admin.register(ProjectNode)
class ProjectNodeAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "project",
        "parent",
        "node_type",
        "visibility",
        "is_archived",
        "position",
        "updated_at",
    ]
    search_fields = ["title", "slug", "description", "project__name"]
    list_filter = ["node_type", "visibility", "is_archived", "project"]
