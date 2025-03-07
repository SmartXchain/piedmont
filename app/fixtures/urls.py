from django.urls import path
from . import views


urlpatterns = [
    path("", views.fixture_list, name="fixture_list"),
    path("dashboard/", views.kanban_dashboard, name="fixture_kanban_dashboard"),
    path("add/", views.fixture_create, name="fixture_create"),
    path("<int:fixture_id>/", views.fixture_detail, name="fixture_detail"),
    path("<int:fixture_id>/edit/", views.fixture_edit, name="fixture_edit"),
]
