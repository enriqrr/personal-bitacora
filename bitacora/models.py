"""Persistent data models for Bitacora."""

from django.conf import settings
from django.core.exceptions import ValidationError
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


class NodeDocument(models.Model):
    class DocumentType(models.TextChoices):
        THEORY = "THEORY", "Theory"
        SPECIFICATION = "SPECIFICATION", "Specification"
        PSEUDOCODE = "PSEUDOCODE", "Pseudocode"
        CODE_SNIPPET = "CODE_SNIPPET", "Code snippet"
        QUESTION = "QUESTION", "Question"
        TODO_LIST = "TODO_LIST", "Todo list"
        DECISION = "DECISION", "Decision"
        BUG_NOTE = "BUG_NOTE", "Bug note"
        DEPLOYMENT_NOTE = "DEPLOYMENT_NOTE", "Deployment note"
        REFERENCE = "REFERENCE", "Reference"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        NEEDS_REVIEW = "NEEDS_REVIEW", "Needs review"
        RESOLVED = "RESOLVED", "Resolved"
        ARCHIVED = "ARCHIVED", "Archived"

    class Visibility(models.TextChoices):
        PRIVATE = "PRIVATE", "Private"
        PUBLIC = "PUBLIC", "Public"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    node = models.ForeignKey(
        ProjectNode,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200)
    document_type = models.CharField(
        max_length=40,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )
    body_markdown = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["node", "slug"],
                name="unique_document_slug_per_node",
            ),
        ]
        ordering = ["-updated_at"]

    def clean(self):
        super().clean()
        if self.node_id and self.project_id and self.node.project_id != self.project_id:
            raise ValidationError("Document project must match the node project.")

    def __str__(self):
        return self.title


class WorkSession(models.Model):
    class Visibility(models.TextChoices):
        PRIVATE = "PRIVATE", "Private"
        PUBLIC = "PUBLIC", "Public"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="work_sessions",
    )
    title = models.CharField(max_length=200)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
    )
    is_archived = models.BooleanField(default=False)
    summary = models.TextField(blank=True)
    goals = models.TextField(blank=True)
    work_done = models.TextField(blank=True)
    decisions_made = models.TextField(blank=True)
    doubts_opened = models.TextField(blank=True)
    next_actions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-started_at", "-created_at"]

    def clean(self):
        super().clean()
        if self.ended_at and self.ended_at < self.started_at:
            raise ValidationError("Session end time must be after or equal to start time.")

    def __str__(self):
        return self.title


class WorkSessionNodeReference(models.Model):
    work_session = models.ForeignKey(
        WorkSession,
        on_delete=models.CASCADE,
        related_name="node_references",
    )
    node = models.ForeignKey(
        ProjectNode,
        on_delete=models.CASCADE,
        related_name="work_session_references",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["work_session", "node"],
                name="unique_work_session_node_reference",
            ),
        ]

    def clean(self):
        super().clean()
        if (
            self.work_session_id
            and self.node_id
            and self.work_session.project_id != self.node.project_id
        ):
            raise ValidationError("Referenced node must belong to the session project.")

    def __str__(self):
        return f"{self.work_session} -> {self.node}"


class WorkSessionDocumentReference(models.Model):
    work_session = models.ForeignKey(
        WorkSession,
        on_delete=models.CASCADE,
        related_name="document_references",
    )
    document = models.ForeignKey(
        NodeDocument,
        on_delete=models.CASCADE,
        related_name="work_session_references",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["work_session", "document"],
                name="unique_work_session_document_reference",
            ),
        ]

    def clean(self):
        super().clean()
        if (
            self.work_session_id
            and self.document_id
            and self.work_session.project_id != self.document.project_id
        ):
            raise ValidationError("Referenced document must belong to the session project.")

    def __str__(self):
        return f"{self.work_session} -> {self.document}"
