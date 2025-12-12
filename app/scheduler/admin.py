# scheduler/admin.py
from django.contrib import admin

from .models import ManufacturingOrder


@admin.register(ManufacturingOrder)
class ManufacturingOrderAdmin(admin.ModelAdmin):
    """Admin interface for entering Work Orders."""

    list_display = (
        "work_order",
        "part_number",
        "quantity",
        "process",
        "planned_start_time",
        "status",
    )
    list_filter = ("status", "planned_start_time")
    search_fields = ("work_order", "part_number")
