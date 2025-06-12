from django.urls import path
from .views import chemical_list

urlpatterns = [
    path('', chemical_list, name='chemical_list'),
]
