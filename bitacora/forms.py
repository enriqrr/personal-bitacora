"""Input validation forms for Bitacora."""

from django import forms
from django.core.exceptions import ValidationError

from .models import Project


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
