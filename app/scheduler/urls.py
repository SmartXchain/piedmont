# scheduler/urls.py
from django.urls import path
from . import views

app_name = "scheduler"

urlpatterns = [
    # Landing page: overview + gantt
    path('', views.schedule_dashboard, name='dashboard'),

    # Gantt JSON data for all operations
    path('gantt-data/', views.gantt_data, name='gantt_data'),

    # Per-order detail + gantt
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    path('order/<int:pk>/gantt-data/', views.order_gantt_data, name='order_gantt_data'),
    path('order/<int:pk>/shift/', views.order_shift, name='order_shift'),

    # Reschedule a single operation (AJAX)
    path('operation/<int:pk>/reschedule/', views.operation_reschedule, name='operation_reschedule'),
]

