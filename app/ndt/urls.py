# ndt/urls.py
from __future__ import annotations

from django.urls import path

from .views import (
    LotCreateView,
    LotListView,
    LotUpdateView,
    NDTLandingView,
    ProductCreateView,
    ProductListView,
    ProductLotListView,
    ProductUpdateView,
    CurveCreateView,
    CurveDetailView,
    CurveListView,
    CurvePointCreateView,
    CurvePointDeleteView,
    CurvePointUpdateView,
    CurveUpdateView,
    WeeklyCheckCreateView,
    WeeklyCheckDetailView,
    WeeklyCheckListView,
    WeeklyCheckUpdateView,
    MixListView,
    MixCreateView,
    MixUpdateView,
)

app_name = "ndt"

urlpatterns = [
    path("", NDTLandingView.as_view(), name="index"),

    # Products
    path("products/", ProductListView.as_view(), name="product_list"),
    path("products/add/", ProductCreateView.as_view(), name="product_add"),
    path("products/<int:pk>/edit/", ProductUpdateView.as_view(), name="product_edit"),

    # Lots
    path("lots/", LotListView.as_view(), name="lot_list"),
    path("lots/add/", LotCreateView.as_view(), name="lot_add"),
    path("lots/<int:pk>/edit/", LotUpdateView.as_view(), name="lot_edit"),

    # Lots per Product
    path(
        "products/<int:product_id>/lots/",
        ProductLotListView.as_view(),
        name="product_lot_list",
    ),
    # Mixes
    path("mixes/", MixListView.as_view(), name="mix_list"),
    path("mixes/add/", MixCreateView.as_view(), name="mix_add"),
    path("mixes/<int:pk>/edit/", MixUpdateView.as_view(), name="mix_edit"),

    # Curves
    path("curves/", CurveListView.as_view(), name="curve_list"),
    path("curves/add/", CurveCreateView.as_view(), name="curve_add"),
    path("curves/<int:pk>/", CurveDetailView.as_view(), name="curve_detail"),
    path("curves/<int:pk>/edit/", CurveUpdateView.as_view(), name="curve_edit"),

    # Curve points
    path("curves/<int:curve_id>/points/add/", CurvePointCreateView.as_view(), name="curvepoint_add"),
    path("points/<int:pk>/edit/", CurvePointUpdateView.as_view(), name="curvepoint_edit"),
    path("points/<int:pk>/delete/", CurvePointDeleteView.as_view(), name="curvepoint_delete"),

    path("logs/", WeeklyCheckListView.as_view(), name="log_list"),
    path("logs/add/", WeeklyCheckCreateView.as_view(), name="log_add"),
    path("logs/<int:pk>/", WeeklyCheckDetailView.as_view(), name="log_detail"),
    path("logs/<int:pk>/edit/", WeeklyCheckUpdateView.as_view(), name="log_edit"),
]
