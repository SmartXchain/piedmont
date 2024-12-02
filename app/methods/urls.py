from django.urls import path
from . import views

urlpatterns = [
    path('', views.method_list_view, name='method_list'),
    path('add/', views.method_create_view, name='method_add'),
    path('<int:method_id>/edit/', views.method_edit_view, name='method_edit'),
]
