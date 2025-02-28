from django.contrib import admin
from .models import MaskingProcess, MaskingStep


@admin.register(MaskingProcess)
class MaskingProcessAdmin(admin.ModelAdmin):
    """Admin panel configuration for MaskingProcess."""
    list_display = ("part_number", "part_number_masking_description")
    search_fields = ("part_number", "part_number_masking_description")


@admin.register(MaskingStep)
class MaskingStepAdmin(admin.ModelAdmin):
    """Admin panel configuration for MaskingStep."""
    list_display = ("masking_process", "masking_step_number", "masking_repair_title", "image_preview")
    readonly_fields = ("image_preview",)
    list_filter = ("masking_process",)
    search_fields = ("masking_repair_title", "masking_description")
