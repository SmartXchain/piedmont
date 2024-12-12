from django.urls import path
from . import views


urlpatterns = [
    path('', views.masking_profile_list, name='masking_profile_list'),
    path('<str:part_number>/<str:part_revision>/', views.masking_profile_detail, name='masking_profile_detail'),
    path('create/', views.masking_profile_create, name='masking_profile_create'),
    path('<int:profile_id>/add_detail/', views.masking_detail_add, name='masking_detail_add'),
]
