from django.urls import path
from . import views


urlpatterns = [
    path('', views.landing_page, name='home'),
    path('capability/<int:pk>/pricing/', views.capability_pricing_detail, name='capability_pricing_detail'),
    path('capabilities/export/csv/', views.export_capabilities_csv, name='export_capabilities_csv'),
]
