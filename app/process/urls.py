from django.urls import path
from . import views

urlpatterns = [
    path('', views.process_list_view, name='process_list'),
    path('add/', views.process_create_view, name='process_add'),
    path('<int:process_id>/edit/', views.process_edit_view, name='process_edit'),
    path('<int:process_id>/steps/', views.process_step_list_view, name='process_step_list'),
    path('<int:process_id>/steps/add/', views.process_step_add_view, name='process_step_add'),
    path('steps/<int:step_id>/edit/', views.process_step_edit_view, name='process_step_edit'),
    path('steps/<int:step_id>/delete/', views.process_step_delete_view, name='process_step_delete'), 
]
