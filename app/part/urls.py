from django.urls import path
from . import views

urlpatterns = [
    path('', views.part_list_view, name='part_list'),
    path('<int:part_id>/', views.part_detail_view, name='part_detail'),
    path('add/', views.part_create_view, name='part_create'),
    path('<int:part_id>/edit/', views.part_edit_view, name='part_edit'),
    path('<int:part_id>/job-details/add/', views.job_details_create_view, name='job_details_create'),
    path('jobs/', views.job_list_view, name='job_list'),
    path('jobs/<int:job_id>/', views.job_detail_view, name='job_detail'),
    path('jobs/add/', views.job_create_view, name='job_create'),
    path('jobs/<int:job_id>/edit/', views.job_edit_view, name='job_edit'),
    path('<int:part_id>/add-details/', views.partdetails_add_view, name='partdetails_add'),
    path('details/<int:detail_id>/view/', views.partdetails_view_view, name='partdetails_view'),
    path('details/<int:detail_id>/edit/', views.partdetails_edit_view, name='partdetails_edit'),
]