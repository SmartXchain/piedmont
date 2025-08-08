from django.urls import path
from . import views

urlpatterns = [
    path('', views.periodic_testing_landing, name='periodic_testing_landing'),
    path('failure-log', views.failure_log_view, name='failure_log_view'),
    path('daily/', views.daily_view, name='daily_view'),
    path('weekly/', views.weekly_view, name='weekly_view'),
    path('monthly/', views.monthly_view, name='monthly_view'),
    path('semi-annual/', views.semi_annual_view, name='semi_annual_view'),
    path('annual/', views.annual_view, name='annual_view')
]

