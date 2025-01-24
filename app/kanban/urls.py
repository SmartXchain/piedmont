from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='kanban'),
    path('add/', views.add_chemical, name='add_chemical'),
]