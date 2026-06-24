"""Admin registrations for Bitacora."""

from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "status", "visibility", "updated_at"]
    search_fields = ["name", "slug", "description"]
