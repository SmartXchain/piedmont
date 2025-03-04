from django.urls import path
from . import views

urlpatterns = [
    # Masking Process URLs
    path("", views.masking_list, name="masking_list"),  # List all masking processes
    path("process/add/", views.masking_process_form, name="masking_process_add"),  # Add new masking process
    path("process/<int:process_id>/", views.masking_process_detail, name="masking_process_detail"),  # View process details
    path("process/<int:process_id>/edit/", views.masking_process_form, name="masking_process_edit"),  # Edit a masking process

    # Masking Step URLs
    path("process/<int:process_id>/steps/", views.masking_step_list, name="masking_step_list"),  # List all steps for a process
    path("process/<int:process_id>/step/add/", views.masking_step_form, name="masking_step_add"),  # Add new masking step
    path("process/<int:process_id>/step/<int:step_id>/edit/", views.masking_step_form, name="masking_step_edit"),  # Edit masking step

    # Print to PDF
    path("process/<int:process_id>/export/pdf/", views.masking_process_pdf_view, name="masking_process_pdf"),
]
