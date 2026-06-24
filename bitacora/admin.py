"""Admin registrations for Bitacora."""

from django.contrib import admin

from .models import (
    NodeDocument,
    Project,
    ProjectNode,
    WorkSession,
    WorkSessionDocumentReference,
    WorkSessionNodeReference,
)


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


@admin.register(NodeDocument)
class NodeDocumentAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "project",
        "node",
        "document_type",
        "status",
        "visibility",
        "updated_at",
    ]
    search_fields = ["title", "slug", "body_markdown", "node__title", "project__name"]
    list_filter = ["document_type", "status", "visibility", "project"]


@admin.register(WorkSession)
class WorkSessionAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "project",
        "visibility",
        "is_archived",
        "started_at",
        "ended_at",
        "updated_at",
    ]
    search_fields = [
        "title",
        "summary",
        "goals",
        "work_done",
        "decisions_made",
        "doubts_opened",
        "next_actions",
        "project__name",
    ]
    list_filter = ["visibility", "is_archived", "project", "started_at"]


@admin.register(WorkSessionNodeReference)
class WorkSessionNodeReferenceAdmin(admin.ModelAdmin):
    list_display = ["work_session", "node", "created_at"]


@admin.register(WorkSessionDocumentReference)
class WorkSessionDocumentReferenceAdmin(admin.ModelAdmin):
    list_display = ["work_session", "document", "created_at"]
