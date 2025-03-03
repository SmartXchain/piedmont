from django.urls import path
from .views import (
    masking_list, masking_process_detail, masking_process_create, masking_process_edit, masking_process_delete,
    masking_step_list, masking_step_create, masking_step_edit, masking_step_delete
)

urlpatterns = [
    # MaskingProcess URLs
    path('', masking_list, name='masking_list'),
    path('<int:process_id>/', masking_process_detail, name='masking_process_detail'),
    path('create/', masking_process_create, name='masking_process_create'),
    path('<int:process_id>/edit/', masking_process_edit, name='masking_process_edit'),
    path('<int:process_id>/delete/', masking_process_delete, name='masking_process_delete'),

    # MaskingStep URLs
    path('<int:process_id>/steps/', masking_step_list, name='masking_step_list'),
    path('<int:process_id>/steps/create/', masking_step_create, name='masking_step_create'),
    path('steps/<int:step_id>/edit/', masking_step_edit, name='masking_step_edit'),
    path('steps/<int:step_id>/delete/', masking_step_delete, name='masking_step_delete'),
]
