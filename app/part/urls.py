from django.urls import path
from . import views

urlpatterns = [
    path('', views.part_list_view, name='part_list'),
    path('parts/<int:part_id>/', views.part_detail_view, name='part_detail'),

    path('work_orders/', views.work_order_list_view, name='work_order_list'),
    path('work_orders/<int:work_order_id>/', views.work_order_detail_view, name='work_order_detail'),
    path('parts/<int:part_id>/work_orders/add/', views.work_order_create_view, name='work_order_create'),
    path('work_orders/<int:work_order_id>/pdf/', views.work_order_print_steps_view, name='work_order_pdf'),
]
