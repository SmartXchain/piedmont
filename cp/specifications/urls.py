from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_specifications, name='list_specifications'),
    path('add/', views.add_specification, name='add_specification'),
    path('<int:specification_id>/edit/', views.edit_specification, name='edit_specification'),
]
