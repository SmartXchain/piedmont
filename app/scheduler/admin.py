# scheduler/admin.py
from django.contrib import admin

from .models import DelayLog, ManufacturingOrder


@admin.register(ManufacturingOrder)
class ManufacturingOrderAdmin(admin.ModelAdmin):
    """Admin interface for entering and managing Manufacturing Orders."""

    list_display = (
        "work_order",
        "occurrence",
        "part_number",
        "quantity",
        "process",
        "planned_start_time",
        "status",
        "completed_at",
    )
    list_display_links = ("work_order", "occurrence", "part_number")
    list_filter = ("status", "planned_start_time")
    date_hierarchy = "planned_start_time"
    search_fields = ("work_order", "part_number")
    ordering = ("-planned_start_time",)

    # Helpful when you have lots of processes (requires ProcessAdmin.search_fields on target model)
    autocomplete_fields = ("process",)

    # Optional: make status editable directly in list view
    list_editable = ("status",)

    # Optional: keep occurrence visible but avoid accidental edits once created
    readonly_fields = ("created_at", "updated_at", "completed_at")


@admin.register(DelayLog)
class DelayLogAdmin(admin.ModelAdmin):
    """Admin interface for delay history (audit trail)."""

    list_display = (
        "order",
        "step_number",
        "added_minutes",
        "timestamp",
    )
    list_filter = ("timestamp",)
    search_fields = ("order__work_order", "order__part_number", "reason")
    ordering = ("-timestamp",)

