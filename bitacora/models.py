"""Persistent data models for Bitacora."""

from django.conf import settings
from django.db import models


class Project(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        PAUSED = "PAUSED", "Paused"
        ARCHIVED = "ARCHIVED", "Archived"

    class Visibility(models.TextChoices):
        PRIVATE = "PRIVATE", "Private"
        PUBLIC = "PUBLIC", "Public"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "slug"],
                name="unique_project_slug_per_owner",
            ),
        ]
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name


class ProjectNode(models.Model):
    class NodeType(models.TextChoices):
        ROOT = "ROOT", "Root"
        AREA = "AREA", "Area"
        MODULE = "MODULE", "Module"
        FEATURE = "FEATURE", "Feature"
        SUBSYSTEM = "SUBSYSTEM", "Subsystem"
        SCREEN = "SCREEN", "Screen"
        TECHNICAL_TOPIC = "TECHNICAL_TOPIC", "Technical topic"
        RESEARCH_TOPIC = "RESEARCH_TOPIC", "Research topic"
        DEPLOYMENT_TOPIC = "DEPLOYMENT_TOPIC", "Deployment topic"
        TESTING_TOPIC = "TESTING_TOPIC", "Testing topic"
        OTHER = "OTHER", "Other"

    class Visibility(models.TextChoices):
        PRIVATE = "PRIVATE", "Private"
        PUBLIC = "PUBLIC", "Public"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="nodes",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180)
    description = models.TextField(blank=True)
    node_type = models.CharField(
        max_length=40,
        choices=NodeType.choices,
        default=NodeType.OTHER,
    )
    position = models.PositiveIntegerField(default=0)
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "slug"],
                condition=models.Q(parent__isnull=True),
                name="unique_root_node_slug_per_project",
            ),
            models.UniqueConstraint(
                fields=["project", "parent", "slug"],
                condition=models.Q(parent__isnull=False),
                name="unique_sibling_node_slug_per_parent",
            ),
            models.CheckConstraint(
                check=~models.Q(parent=models.F("id")),
                name="project_node_cannot_parent_itself",
            ),
        ]
        ordering = ["position", "title"]

    def __str__(self):
        return self.title
