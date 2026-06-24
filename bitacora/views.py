from django.core.exceptions import ValidationError
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .forms import (
    NodeDocumentForm,
    ProjectForm,
    ProjectNodeForm,
    ProjectNodeMoveForm,
    WorkSessionForm,
)
from .models import NodeDocument, Project, ProjectNode, WorkSession
from .permissions import owner_required
from .rendering import render_markdown_to_safe_html
from .selectors import (
    get_breadcrumb_nodes,
    get_owner_document_by_id,
    get_owner_documents_for_node,
    get_owner_node_by_id,
    get_owner_project_by_slug,
    get_owner_projects,
    get_owner_root_nodes_for_project,
    get_owner_session_by_id,
    get_owner_sessions_for_project,
    get_owner_sessions_referencing_document,
    get_owner_sessions_referencing_node,
    get_owner_nodes_for_project,
    get_public_node_by_id,
    get_public_nodes_for_project,
    get_public_document_by_id,
    get_public_documents_for_node,
    get_public_document_references_for_session,
    get_public_project_by_slug,
    get_public_projects,
    get_public_session_by_id,
    get_public_node_references_for_session,
    get_public_sessions_for_project,
)
from .services import (
    archive_node_document,
    archive_project,
    archive_project_node,
    archive_work_session,
    create_project,
    create_project_node,
    create_node_document,
    create_work_session,
    move_project_node,
    update_node_document,
    update_project,
    update_project_node,
    update_work_session,
)


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


def public_session_list(request, project_slug):
    try:
        project = get_public_project_by_slug(project_slug)
    except Project.DoesNotExist as exc:
        raise Http404("Project not found.") from exc
    sessions = get_public_sessions_for_project(project)
    return render(
        request,
        "public/session_list.html",
        {"project": project, "sessions": sessions},
    )


def public_session_detail(request, session_id):
    try:
        work_session = get_public_session_by_id(session_id)
    except WorkSession.DoesNotExist as exc:
        raise Http404("Session not found.") from exc
    node_references = get_public_node_references_for_session(work_session)
    document_references = get_public_document_references_for_session(work_session)
    return render(
        request,
        "public/session_detail.html",
        {
            "work_session": work_session,
            "node_references": node_references,
            "document_references": document_references,
        },
    )


def public_project_tree(request, project_slug):
    try:
        project = get_public_project_by_slug(project_slug)
    except Project.DoesNotExist as exc:
        raise Http404("Project not found.") from exc
    nodes = get_public_nodes_for_project(project)
    return render(request, "public/project_tree.html", {"project": project, "nodes": nodes})


def public_node_detail(request, node_id):
    try:
        node = get_public_node_by_id(node_id)
    except ProjectNode.DoesNotExist as exc:
        raise Http404("Node not found.") from exc
    breadcrumbs = get_breadcrumb_nodes(node)
    documents = get_public_documents_for_node(node)
    return render(
        request,
        "public/node_detail.html",
        {"node": node, "breadcrumbs": breadcrumbs, "documents": documents},
    )


def public_document_detail(request, document_id):
    try:
        document = get_public_document_by_id(document_id)
    except NodeDocument.DoesNotExist as exc:
        raise Http404("Document not found.") from exc
    rendered_body = render_markdown_to_safe_html(document.body_markdown)
    return render(
        request,
        "public/document_detail.html",
        {"document": document, "rendered_body": rendered_body},
    )


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
def owner_session_list(request, project_slug):
    try:
        project = get_owner_project_by_slug(request.user, project_slug)
    except Project.DoesNotExist as exc:
        raise Http404("Project not found.") from exc
    sessions = get_owner_sessions_for_project(request.user, project)
    return render(
        request,
        "owner/session_list.html",
        {"project": project, "sessions": sessions},
    )


@owner_required
def owner_session_create(request, project_slug):
    try:
        project = get_owner_project_by_slug(request.user, project_slug)
    except Project.DoesNotExist as exc:
        raise Http404("Project not found.") from exc

    if request.method == "POST":
        form = WorkSessionForm(request.POST, project=project)
        if form.is_valid():
            try:
                work_session = create_work_session(
                    owner=request.user,
                    project=project,
                    **form.cleaned_data,
                )
                return redirect("bitacora:owner_session_detail", session_id=work_session.id)
            except ValidationError as exc:
                form.add_error(None, exc)
    else:
        form = WorkSessionForm(project=project)
    return render(
        request,
        "owner/session_form.html",
        {"form": form, "project": project, "work_session": None},
    )


@owner_required
def owner_session_detail(request, session_id):
    try:
        work_session = get_owner_session_by_id(request.user, session_id)
    except WorkSession.DoesNotExist as exc:
        raise Http404("Session not found.") from exc
    return render(
        request,
        "owner/session_detail.html",
        {"work_session": work_session},
    )


@owner_required
def owner_session_edit(request, session_id):
    try:
        work_session = get_owner_session_by_id(request.user, session_id)
    except WorkSession.DoesNotExist as exc:
        raise Http404("Session not found.") from exc

    if request.method == "POST":
        form = WorkSessionForm(request.POST, instance=work_session, project=work_session.project)
        if form.is_valid():
            try:
                work_session = update_work_session(work_session, **form.cleaned_data)
                return redirect("bitacora:owner_session_detail", session_id=work_session.id)
            except ValidationError as exc:
                form.add_error(None, exc)
    else:
        form = WorkSessionForm(instance=work_session, project=work_session.project)
    return render(
        request,
        "owner/session_form.html",
        {"form": form, "project": work_session.project, "work_session": work_session},
    )


@owner_required
def owner_session_archive(request, session_id):
    if request.method != "POST":
        raise Http404("Session not found.")

    try:
        work_session = get_owner_session_by_id(request.user, session_id)
    except WorkSession.DoesNotExist as exc:
        raise Http404("Session not found.") from exc
    archive_work_session(work_session)
    return redirect("bitacora:owner_session_detail", session_id=work_session.id)


@owner_required
def owner_project_tree(request, project_slug):
    try:
        project = get_owner_project_by_slug(request.user, project_slug)
    except Project.DoesNotExist as exc:
        raise Http404("Project not found.") from exc
    nodes = get_owner_nodes_for_project(request.user, project)
    root_nodes = get_owner_root_nodes_for_project(request.user, project)
    return render(
        request,
        "owner/project_tree.html",
        {"project": project, "nodes": nodes, "root_nodes": root_nodes},
    )


@owner_required
def owner_node_create_root(request, project_slug):
    try:
        project = get_owner_project_by_slug(request.user, project_slug)
    except Project.DoesNotExist as exc:
        raise Http404("Project not found.") from exc

    if request.method == "POST":
        form = ProjectNodeForm(request.POST, project=project)
        if form.is_valid():
            node = create_project_node(
                owner=request.user,
                project=project,
                parent=None,
                **form.cleaned_data,
            )
            return redirect("bitacora:owner_node_detail", node_id=node.id)
    else:
        form = ProjectNodeForm(project=project)
    return render(
        request,
        "owner/node_form.html",
        {"form": form, "project": project, "parent": None, "node": None},
    )


@owner_required
def owner_node_detail(request, node_id):
    try:
        node = get_owner_node_by_id(request.user, node_id)
    except ProjectNode.DoesNotExist as exc:
        raise Http404("Node not found.") from exc
    breadcrumbs = get_breadcrumb_nodes(node)
    documents = get_owner_documents_for_node(request.user, node)
    sessions = get_owner_sessions_referencing_node(request.user, node)
    return render(
        request,
        "owner/node_detail.html",
        {
            "node": node,
            "breadcrumbs": breadcrumbs,
            "documents": documents,
            "sessions": sessions,
        },
    )


@owner_required
def owner_node_create_child(request, node_id):
    try:
        parent = get_owner_node_by_id(request.user, node_id)
    except ProjectNode.DoesNotExist as exc:
        raise Http404("Node not found.") from exc

    if request.method == "POST":
        form = ProjectNodeForm(request.POST, project=parent.project, parent=parent)
        if form.is_valid():
            node = create_project_node(
                owner=request.user,
                project=parent.project,
                parent=parent,
                **form.cleaned_data,
            )
            return redirect("bitacora:owner_node_detail", node_id=node.id)
    else:
        form = ProjectNodeForm(project=parent.project, parent=parent)
    return render(
        request,
        "owner/node_form.html",
        {"form": form, "project": parent.project, "parent": parent, "node": None},
    )


@owner_required
def owner_node_edit(request, node_id):
    try:
        node = get_owner_node_by_id(request.user, node_id)
    except ProjectNode.DoesNotExist as exc:
        raise Http404("Node not found.") from exc

    if request.method == "POST":
        form = ProjectNodeForm(
            request.POST,
            instance=node,
            project=node.project,
            parent=node.parent,
        )
        if form.is_valid():
            node = update_project_node(node, **form.cleaned_data)
            return redirect("bitacora:owner_node_detail", node_id=node.id)
    else:
        form = ProjectNodeForm(instance=node, project=node.project, parent=node.parent)
    return render(
        request,
        "owner/node_form.html",
        {"form": form, "project": node.project, "parent": node.parent, "node": node},
    )


@owner_required
def owner_node_move(request, node_id):
    try:
        node = get_owner_node_by_id(request.user, node_id)
    except ProjectNode.DoesNotExist as exc:
        raise Http404("Node not found.") from exc

    parent_queryset = get_owner_nodes_for_project(request.user, node.project).exclude(pk=node.pk)
    if request.method == "POST":
        form = ProjectNodeMoveForm(request.POST, parent_queryset=parent_queryset)
        if form.is_valid():
            try:
                node = move_project_node(
                    node,
                    new_parent=form.cleaned_data["parent"],
                    position=form.cleaned_data["position"],
                )
                return redirect("bitacora:owner_node_detail", node_id=node.id)
            except ValidationError as exc:
                form.add_error(None, exc)
    else:
        form = ProjectNodeMoveForm(
            initial={"parent": node.parent, "position": node.position},
            parent_queryset=parent_queryset,
        )
    return render(request, "owner/node_move_form.html", {"form": form, "node": node})


@owner_required
def owner_node_archive(request, node_id):
    if request.method != "POST":
        raise Http404("Node not found.")

    try:
        node = get_owner_node_by_id(request.user, node_id)
    except ProjectNode.DoesNotExist as exc:
        raise Http404("Node not found.") from exc
    archive_project_node(node)
    return redirect("bitacora:owner_node_detail", node_id=node.id)


@owner_required
def owner_document_create(request, node_id):
    try:
        node = get_owner_node_by_id(request.user, node_id)
    except ProjectNode.DoesNotExist as exc:
        raise Http404("Node not found.") from exc

    if request.method == "POST":
        form = NodeDocumentForm(request.POST, node=node)
        if form.is_valid():
            try:
                document = create_node_document(
                    owner=request.user,
                    node=node,
                    **form.cleaned_data,
                )
                return redirect("bitacora:owner_document_detail", document_id=document.id)
            except ValidationError as exc:
                form.add_error(None, exc)
    else:
        form = NodeDocumentForm(node=node)
    return render(
        request,
        "owner/document_form.html",
        {"form": form, "node": node, "document": None},
    )


@owner_required
def owner_document_detail(request, document_id):
    try:
        document = get_owner_document_by_id(request.user, document_id)
    except NodeDocument.DoesNotExist as exc:
        raise Http404("Document not found.") from exc
    rendered_body = render_markdown_to_safe_html(document.body_markdown)
    sessions = get_owner_sessions_referencing_document(request.user, document)
    return render(
        request,
        "owner/document_detail.html",
        {
            "document": document,
            "rendered_body": rendered_body,
            "sessions": sessions,
        },
    )


@owner_required
def owner_document_edit(request, document_id):
    try:
        document = get_owner_document_by_id(request.user, document_id)
    except NodeDocument.DoesNotExist as exc:
        raise Http404("Document not found.") from exc

    if request.method == "POST":
        form = NodeDocumentForm(request.POST, instance=document, node=document.node)
        if form.is_valid():
            try:
                document = update_node_document(document, **form.cleaned_data)
                return redirect("bitacora:owner_document_detail", document_id=document.id)
            except ValidationError as exc:
                form.add_error(None, exc)
    else:
        form = NodeDocumentForm(instance=document, node=document.node)
    return render(
        request,
        "owner/document_form.html",
        {"form": form, "node": document.node, "document": document},
    )


@owner_required
def owner_document_archive(request, document_id):
    if request.method != "POST":
        raise Http404("Document not found.")

    try:
        document = get_owner_document_by_id(request.user, document_id)
    except NodeDocument.DoesNotExist as exc:
        raise Http404("Document not found.") from exc
    archive_node_document(document)
    return redirect("bitacora:owner_document_detail", document_id=document.id)


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
