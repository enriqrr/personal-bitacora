from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import redirect, render

from .forms import ProjectForm
from .models import Project
from .permissions import owner_required
from .selectors import (
    get_owner_project_by_slug,
    get_owner_projects,
    get_public_project_by_slug,
    get_public_projects,
)
from .services import archive_project, create_project, update_project


def health(request):
    return HttpResponse("ok", content_type="text/plain")


def home(request):
    return render(request, "public/home.html")


@owner_required
def dashboard(request):
    return render(request, "owner/dashboard.html")


def public_project_list(request):
    projects = get_public_projects()
    return render(request, "public/project_list.html", {"projects": projects})


def public_project_detail(request, slug):
    try:
        project = get_public_project_by_slug(slug)
    except Project.DoesNotExist as exc:
        raise Http404("Project not found.") from exc
    return render(request, "public/project_detail.html", {"project": project})


@owner_required
def owner_project_list(request):
    projects = get_owner_projects(request.user)
    return render(request, "owner/project_list.html", {"projects": projects})


@owner_required
def owner_project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST, owner=request.user)
        if form.is_valid():
            project = create_project(owner=request.user, **form.cleaned_data)
            return redirect("bitacora:owner_project_detail", slug=project.slug)
    else:
        form = ProjectForm(owner=request.user)
    return render(request, "owner/project_form.html", {"form": form, "project": None})


@owner_required
def owner_project_detail(request, slug):
    try:
        project = get_owner_project_by_slug(request.user, slug)
    except Project.DoesNotExist as exc:
        raise Http404("Project not found.") from exc
    return render(request, "owner/project_detail.html", {"project": project})


@owner_required
def owner_project_edit(request, slug):
    try:
        project = get_owner_project_by_slug(request.user, slug)
    except Project.DoesNotExist as exc:
        raise Http404("Project not found.") from exc

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project, owner=request.user)
        if form.is_valid():
            project = update_project(project, **form.cleaned_data)
            return redirect("bitacora:owner_project_detail", slug=project.slug)
    else:
        form = ProjectForm(instance=project, owner=request.user)
    return render(request, "owner/project_form.html", {"form": form, "project": project})


@owner_required
def owner_project_archive(request, slug):
    if request.method != "POST":
        raise Http404("Project not found.")

    try:
        project = get_owner_project_by_slug(request.user, slug)
    except Project.DoesNotExist as exc:
        raise Http404("Project not found.") from exc
    archive_project(project)
    return redirect("bitacora:owner_project_detail", slug=project.slug)
