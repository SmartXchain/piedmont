from django.urls import path
from . import views

urlpatterns = [
    path('', views.process_list_view, name='process_list'),
    path('add/', views.process_create_view, name='process_add'),
    path('<int:process_id>/edit/', views.process_edit_view, name='process_edit'),
]
