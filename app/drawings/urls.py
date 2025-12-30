# drawings/urls.py
from django.urls import path

from . import views

app_name = "drawings"

urlpatterns = [
    # -------------------------
    # Engineering (Engineer-only)
    # -------------------------
    path(
        "drawing/<int:drawing_id>/annotate/",
        views.annotate_drawing_view,
        name="annotate",
    ),
    path(
        "drawing/<int:drawing_id>/page-image/",
        views.page_image_view,
        name="page_image",
    ),
    path(
        "drawing/<int:drawing_id>/zones/",
        views.zones_json_view,
        name="zones_json",
    ),
    path(
        "drawing/<int:drawing_id>/zones/save/",
        views.save_zone_view,
        name="save_zone",
    ),
    path(
        "drawing/<int:drawing_id>/zones/<int:zone_id>/delete/",
        views.delete_zone_view,
        name="delete_zone",
    ),

    # -------------------------
    # Operators
    # -------------------------
    path(
        "area-cards/",
        views.operator_drawing_list_view,
        name="operator_list",
    ),
    path(
        "area-cards/<int:drawing_id>/",
        views.operator_plating_card_view,
        name="operator_card",
    ),
    path(
        "area-cards/<int:drawing_id>/zones/",
        views.operator_zones_json_view,
        name="operator_zones_json",
    ),
]

