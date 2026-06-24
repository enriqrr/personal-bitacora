"""Input validation forms for Bitacora."""

from django import forms
from django.core.exceptions import ValidationError

from .models import NodeDocument, Project, ProjectNode, WorkSession


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "slug", "description", "status", "visibility"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        if not self.owner:
            return slug

        projects = Project.objects.filter(owner=self.owner, slug=slug)
        if self.instance.pk:
            projects = projects.exclude(pk=self.instance.pk)
        if projects.exists():
            raise ValidationError("You already have a project with this slug.")
        return slug


class ProjectNodeForm(forms.ModelForm):
    class Meta:
        model = ProjectNode
        fields = ["title", "slug", "description", "node_type", "visibility", "position"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, project=None, parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.parent = parent

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        if not self.project:
            return slug

        nodes = ProjectNode.objects.filter(
            project=self.project,
            parent=self.parent,
            slug=slug,
        )
        if self.instance.pk:
            nodes = nodes.exclude(pk=self.instance.pk)
        if nodes.exists():
            raise ValidationError("Sibling nodes must have unique slugs.")
        return slug


class ProjectNodeMoveForm(forms.Form):
    parent = forms.ModelChoiceField(
        queryset=ProjectNode.objects.none(),
        required=False,
        empty_label="Root node",
    )
    position = forms.IntegerField(min_value=0, initial=0)

    def __init__(self, *args, parent_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if parent_queryset is not None:
            self.fields["parent"].queryset = parent_queryset


class NodeDocumentForm(forms.ModelForm):
    class Meta:
        model = NodeDocument
        fields = [
            "title",
            "slug",
            "document_type",
            "status",
            "visibility",
            "body_markdown",
        ]
        widgets = {
            "body_markdown": forms.Textarea(attrs={"rows": 12}),
        }

    def __init__(self, *args, node=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.node = node

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        if not self.node:
            return slug

        documents = NodeDocument.objects.filter(node=self.node, slug=slug)
        if self.instance.pk:
            documents = documents.exclude(pk=self.instance.pk)
        if documents.exists():
            raise ValidationError("Documents inside the same node must have unique slugs.")
        return slug


class WorkSessionForm(forms.ModelForm):
    referenced_nodes = forms.ModelMultipleChoiceField(
        queryset=ProjectNode.objects.none(),
        required=False,
    )
    referenced_documents = forms.ModelMultipleChoiceField(
        queryset=NodeDocument.objects.none(),
        required=False,
    )

    class Meta:
        model = WorkSession
        fields = [
            "title",
            "started_at",
            "ended_at",
            "visibility",
            "summary",
            "goals",
            "work_done",
            "decisions_made",
            "doubts_opened",
            "next_actions",
            "referenced_nodes",
            "referenced_documents",
        ]
        widgets = {
            "started_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ended_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "summary": forms.Textarea(attrs={"rows": 3}),
            "goals": forms.Textarea(attrs={"rows": 3}),
            "work_done": forms.Textarea(attrs={"rows": 4}),
            "decisions_made": forms.Textarea(attrs={"rows": 3}),
            "doubts_opened": forms.Textarea(attrs={"rows": 3}),
            "next_actions": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        if project is not None:
            self.fields["referenced_nodes"].queryset = ProjectNode.objects.filter(project=project)
            self.fields["referenced_documents"].queryset = NodeDocument.objects.filter(project=project)
        if self.instance.pk:
            self.fields["referenced_nodes"].initial = self.instance.node_references.values_list(
                "node_id",
                flat=True,
            )
            self.fields["referenced_documents"].initial = self.instance.document_references.values_list(
                "document_id",
                flat=True,
            )

    def clean(self):
        cleaned_data = super().clean()
        started_at = cleaned_data.get("started_at")
        ended_at = cleaned_data.get("ended_at")
        if started_at and ended_at and ended_at < started_at:
            raise ValidationError("Session end time must be after or equal to start time.")
        return cleaned_data
