from django.urls import path
from . import views

urlpatterns = [
    path('', views.method_list_view, name='method_list'),
    path('add/', views.method_create_view, name='method_add'),
    path('<int:method_id>/', views.method_detail, name='method_detail'),
    path('<int:method_id>/edit/', views.method_edit_view, name='method_edit'),
    path('<int:method_id>/parameters/', views.parameter_list_view, name='parameter_list'),
    path('<int:method_id>/parameters/add/', views.parameter_create_view, name='parameter_add'),
    path('<int:method_id>/parameters/<int:parameter_id>/edit/', views.parameter_edit_view, name='parameter_edit'),
]
