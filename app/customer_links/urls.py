# customer_links/urls.py
from django.urls import path
from .views import customer_links_list


urlpatterns = [
    path('', customer_links_list, name='customer_links_list'),
]
