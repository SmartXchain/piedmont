from django.urls import path
from .views import ProcessRunListView

urlpatterns = [
    path("", ProcessRunListView.as_view(), name="processrun_list"),
]

