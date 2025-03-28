from django.urls import path
from . import views

urlpatterns = [
    path('', views.pm_landing_page, name='pm_landing_page'),  # Landing Page
]
