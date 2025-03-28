from django.urls import path
from .views import tank_list, export_tanks_to_excel

urlpatterns = [
    path("", tank_list, name="tank_list"),
    path("export/", export_tanks_to_excel, name="export_tanks_to_excel"),
]
