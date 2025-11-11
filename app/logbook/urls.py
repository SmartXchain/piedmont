# logbook/urls.py
from django.urls import path
from .views import LogbookLandingView, logentry_create

app_name = "logbook"

urlpatterns = [
    path("", LogbookLandingView.as_view(), name="list"),
    path("new/", logentry_create, name="create"),
]

