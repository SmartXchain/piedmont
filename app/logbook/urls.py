# logbook/urls.py
from django.urls import path
from .views import (
    IndexView,
    LogbookLandingView,
    logentry_create,
    ManagerDashboardView,
    download_log_data,
    operator_env_log_create
)

app_name = "logbook"

urlpatterns = [
    # 1. ROOT URL: Leads to the Central Navigation Page (UX Improvement)
    path("", IndexView.as_view(), name="index"), # Changed from "list" to "index"

    # --- Operator Entry Paths ---
    # The existing part/process log entry form
    path("parts/new/", logentry_create, name="create"), 
    # The existing part/process log list view
    path("parts/list/", LogbookLandingView.as_view(), name="list"),
    # Environmental Log Submission Page
    path("env/new/", operator_env_log_create, name="env_create"),
    # --- Manager/Reviewer Paths (Environmental Logs) ---
    path("env/dashboard/", ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('env/download/', download_log_data, name='download_logs'),
]
