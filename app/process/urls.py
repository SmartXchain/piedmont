# process/urls.py
from django.urls import path
from .views import get_classifications

urlpatterns = [
    path('admin/process/get_classifications/', get_classifications, name='get_classifications'),
]
