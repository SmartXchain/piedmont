from django.urls import path
from . import views

urlpatterns = [
    # Dashboard View
    path("", views.kanban_dashboard, name="kanban_dashboard"),

    # Product Views
    path("products/", views.product_list, name="product_list"),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),

    # Export Inventory Report
    path("export-inventory/", views.export_inventory_report, name="export_inventory_report"),
]
