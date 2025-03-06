from django.urls import path
from .views import (
    chemical_list, chemical_detail, chemical_create, chemical_edit, 
    chemical_expired_list, chemical_expiring_list, kanban_dashboard
)

urlpatterns = [
    path("", kanban_dashboard, name="kanban_dashboard"),
    path("chemicals/", chemical_list, name="chemical_list"),
    path("chemicals/add/", chemical_create, name="chemical_create"),
    path("chemicals/<int:chemical_id>/", chemical_detail, name="chemical_detail"),
    path("chemicals/<int:chemical_id>/edit/", chemical_edit, name="chemical_edit"),
    path("chemicals/expired/", chemical_expired_list, name="chemical_expired_list"),
    path("chemicals/expiring/", chemical_expiring_list, name="chemical_expiring_list"),
]
