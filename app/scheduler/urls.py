# scheduler/urls.py
from django.urls import path
from .views import SchedulerView, SchedulerDataView, AddDelayView, UpdateStatusView

app_name = "scheduler"

urlpatterns = [
    path("", SchedulerView.as_view(), name="main"),
    path("api/data/", SchedulerDataView.as_view(), name="data"),
    path("api/add-delay/", AddDelayView.as_view(), name="add_delay"),
    path("api/update-status/", UpdateStatusView.as_view(), name="update_status"),
]

