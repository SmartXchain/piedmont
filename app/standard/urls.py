from django.urls import path
from .views import standard_list_view, standard_detail_view, standard_create_view, standard_edit_view

urlpatterns = [
    path('', standard_list_view, name='standard_list'),
    path('<int:standard_id>/', standard_detail_view, name='standard_detail'),
    path('<int:standard_id>/edit/', standard_edit_view, name='standard_edit'),
    path('create/', standard_create_view, name='standard_create'),
]
