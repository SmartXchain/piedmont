# process/urls.py
from django.urls import path
from . import views


urlpatterns = [
    path('admin/process/get_classifications/', views.get_classifications, name='get_classifications'),
    path('admin/process/get_method_info/', views.get_method_info, name='get_method_info'),
]
