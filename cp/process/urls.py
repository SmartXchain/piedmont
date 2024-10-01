from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_technical_sheets, name='list_technical_sheets'),
    path('create/', views.create_technical_sheet, name='create_technical_sheet'),  # Assuming you also have the create view
    path('<int:technical_sheet_id>/select_rework/', views.select_rework_steps, name='select_rework_steps'),
]