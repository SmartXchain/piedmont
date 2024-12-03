from django.urls import path
from . import views

urlpatterns = [
    path('', views.masking_profile_list, name='masking_profile_list'),
    path('<int:profile_id>/', views.masking_profile_detail, name='masking_profile_detail'),
    path('add-photo/', views.masking_photo_create, name='masking_photo_create'),
    path('create/', views.masking_profile_create, name='masking_profile_create'),
    
]
