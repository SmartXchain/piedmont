# part/urls.py
from django.urls import path
from . import views


urlpatterns = [
    # --- PART MANAGEMENT ---
    path('', views.part_list_view, name='part_list'),
    path('parts/<int:part_id>/', views.part_detail_view, name='part_detail'),
    path('parts/add/', views.part_create_view, name='part_create'),
    path('parts/<int:part_id>/assign-standard/', views.part_assign_standard_view, name='part_assign_standard'),

    # --- WORK ORDER (TRACKED) ---
    path('parts/<int:part_id>/work_orders/add/', views.work_order_create_view, name='work_order_create'),
    path('work_orders/<int:work_order_id>/', views.work_order_detail_view, name='work_order_detail'),
    path('work_orders/<int:work_order_id>/pdf/', views.work_order_print_steps_view, name='work_order_pdf'),

    # --- TEMPLATE (UNTRACTED) FLOW ---
    path('templates/', views.global_template_list_view, name='global_template_list'),
    path('templates/process/<int:process_id>/select/', views.template_selection_view, name='template_selection'),
    path('templates/process/<int:process_id>/print/', views.template_process_print_view, name='template_process_print'),

    # --- API ENDPOINTS ---
    path('standards/<int:standard_id>/classifications/json/', views.standard_classifications_json, name='standard_classifications_json'),
]
