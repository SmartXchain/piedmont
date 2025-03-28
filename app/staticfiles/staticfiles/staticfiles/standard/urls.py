from django.urls import path
from . import views

urlpatterns = [
    path('', views.standard_list_view, name='standard_list'),
    path('<int:standard_id>/', views.standard_detail_view, name='standard_detail'),
    path('<int:standard_id>/edit/', views.standard_edit_view, name='standard_edit'),
    path('create/', views.standard_create_view, name='standard_create'),
    path('<int:standard_id>/inspections/', views.inspection_list_view, name='inspection_list'),
    path('<int:standard_id>/inspections/add/', views.inspection_create_view, name='inspection_create'),
    path('inspections/<int:inspection_id>/edit/', views.inspection_edit_view, name='inspection_edit'),
    path('<int:standard_id>/periodic-tests/', views.periodic_test_list_view, name='periodic_test_list'),
    path('<int:standard_id>/periodic-tests/add/', views.periodic_test_create_view, name='periodic_test_create'),
    path('periodic-tests/<int:periodic_test_id>/edit/', views.periodic_test_edit_view, name='periodic_test_edit'),
    path('<int:standard_id>/classifications/', views.classification_list_view, name='classification_list'),
    path('<int:standard_id>/classifications/add/', views.classification_create_view, name='classification_create'),
    path('classifications/<int:classification_id>/edit/', views.classification_edit_view, name='classification_edit'),

    # Process Review View
    path("process-review/", views.process_review_view, name="process_review"),
]
