from django.urls import path

from . import views

app_name = "bitacora"

urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("projects/", views.public_project_list, name="public_project_list"),
    path("p/<slug:slug>/", views.public_project_detail, name="public_project_detail"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/projects/", views.owner_project_list, name="owner_project_list"),
    path("dashboard/projects/new/", views.owner_project_create, name="owner_project_create"),
    path("dashboard/projects/<slug:slug>/", views.owner_project_detail, name="owner_project_detail"),
    path("dashboard/projects/<slug:slug>/edit/", views.owner_project_edit, name="owner_project_edit"),
    path("dashboard/projects/<slug:slug>/archive/", views.owner_project_archive, name="owner_project_archive"),
]
