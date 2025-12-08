# process/urls.py
from django.urls import path
from . import views


urlpatterns = [
    path('admin/process/get_classifications/', views.get_classifications, name='get_classifications'),
    path('admin/process/get_method_info/', views.get_method_info, name='get_method_info'),
    path('process/<int:pk>/flowchart/', views.process_flowchart_view, name='process_flowchart'),
    path('', views.ProcessLandingView.as_view(), name='process_landing'),
    path('<int:pk>/flowchart/download/', views.process_flowchart_download_view, name='process_flowchart_download'),
]
