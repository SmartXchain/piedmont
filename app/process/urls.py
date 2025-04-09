# process/urls.py
from django.urls import path
from .views import get_classifications, get_method_info

urlpatterns = [
    path('admin/process/get_classifications/', get_classifications, name='get_classifications'),
    path('admin/process/get_method_info/', get_method_info, name='get_method_info'),
]
