from django.urls import path

from . import views

urlpatterns = [
    path("tanks/", views.tank_list, name="tank_list"),
    path("tanks/<int:pk>/", views.tank_detail, name="tank_detail"),
]
