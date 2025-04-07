from django.urls import path
from . import views

urlpatterns = [
    path('', views.standard_list_view, name='standard_list'),
    path('<int:standard_id>/', views.standard_detail_view, name='standard_detail'),
    path("process-review/", views.process_review_view, name="process_review"),
]
