from django.urls import path
from . import views

urlpatterns = [
    path('', views.part_list_view, name='part_list'),

    path('<int:part_id>/', views.part_detail_view, name='part_detail'),
    path('add/', views.part_create_view, name='part_create'),
    path('<int:part_id>/edit/', views.part_edit_view, name='part_edit'),

    path('<int:part_id>/add-details/', views.partdetails_add_view, name='partdetails_add'),
    path('details/<int:detail_id>/view/', views.partdetails_view_view, name='partdetails_view'),
    path('details/<int:detail_id>/edit/', views.partdetails_edit_view, name='partdetails_edit'),

    path('job/<int:job_id>/view/', views.jobdetails_view, name='jobdetails_view'),
    path('job/<int:job_id>/edit/', views.jobdetails_edit_view, name='jobdetails_edit'),
    path('part/<int:part_id>/add/job/', views.jobdetails_add_view, name='jobdetails_add'),
    path('<int:part_id>/jobs/', views.jobdetails_list_view, name='jobdetails_list'),
    path('<int:job_id>/job-process-steps/', views.job_process_steps_view, name='job_process_steps'),

    path('<int:detail_id>/part-process-steps/', views.part_process_steps_view, name='part_process_steps'),

    path('<int:job_id>/process-steps/print/', views.job_print_steps_view, name='job_print_steps'),
]
