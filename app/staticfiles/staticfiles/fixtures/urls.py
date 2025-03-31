# urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.rack_list, name='rack_list'),
    path('fixture/<int:pk>/', views.rack_detail, name='rack_detail'),
    path('fixture/calendar/', views.pm_calendar, name='pm_calendar'),
]
