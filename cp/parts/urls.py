from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_parts, name='list_parts'),
    path('add/', views.add_part, name='add_part'),
    path('<int:part_id>/edit/', views.edit_part, name='edit_part'),
]