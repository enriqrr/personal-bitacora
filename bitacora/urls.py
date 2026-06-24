from django.urls import path

from . import views

app_name = "bitacora"

urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("projects/", views.public_project_list, name="public_project_list"),
    path("p/<slug:project_slug>/tree/", views.public_project_tree, name="public_project_tree"),
    path("p/<slug:slug>/", views.public_project_detail, name="public_project_detail"),
    path("public/nodes/<int:node_id>/", views.public_node_detail, name="public_node_detail"),
    path("public/documents/<int:document_id>/", views.public_document_detail, name="public_document_detail"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/projects/", views.owner_project_list, name="owner_project_list"),
    path("dashboard/projects/new/", views.owner_project_create, name="owner_project_create"),
    path("dashboard/projects/<slug:project_slug>/tree/", views.owner_project_tree, name="owner_project_tree"),
    path("dashboard/projects/<slug:project_slug>/nodes/new-root/", views.owner_node_create_root, name="owner_node_create_root"),
    path("dashboard/projects/<slug:slug>/", views.owner_project_detail, name="owner_project_detail"),
    path("dashboard/projects/<slug:slug>/edit/", views.owner_project_edit, name="owner_project_edit"),
    path("dashboard/projects/<slug:slug>/archive/", views.owner_project_archive, name="owner_project_archive"),
    path("dashboard/nodes/<int:node_id>/", views.owner_node_detail, name="owner_node_detail"),
    path("dashboard/nodes/<int:node_id>/new-child/", views.owner_node_create_child, name="owner_node_create_child"),
    path("dashboard/nodes/<int:node_id>/edit/", views.owner_node_edit, name="owner_node_edit"),
    path("dashboard/nodes/<int:node_id>/move/", views.owner_node_move, name="owner_node_move"),
    path("dashboard/nodes/<int:node_id>/archive/", views.owner_node_archive, name="owner_node_archive"),
    path("dashboard/nodes/<int:node_id>/documents/new/", views.owner_document_create, name="owner_document_create"),
    path("dashboard/documents/<int:document_id>/", views.owner_document_detail, name="owner_document_detail"),
    path("dashboard/documents/<int:document_id>/edit/", views.owner_document_edit, name="owner_document_edit"),
    path("dashboard/documents/<int:document_id>/archive/", views.owner_document_archive, name="owner_document_archive"),
]
