from django.urls import path
from . import views

urlpatterns = [
    path("", views.kanban_dashboard, name="kanban_dashboard"),
    path("inventory/", views.chemical_list, name="chemical_list"),
    path("inventory/add/", views.chemical_create, name="chemical_create"),
    path("inventory/<int:chemical_id>/", views.chemical_detail, name="chemical_detail"),
    path("inventory/expiring/", views.chemical_expiring_list, name="chemical_expiring_list"),
    path("inventory/expired/", views.chemical_expired_list, name="chemical_expired_list"),
]
