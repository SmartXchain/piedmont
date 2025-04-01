from django.contrib import admin
from django.utils.html import format_html
from .models import MaskingProcess, MaskingStep


class MaskingStepInline(admin.TabularInline):
    """Inline admin for Masking Steps inside Masking Process."""
    model = MaskingStep
    extra = 1
    fields = ("step_number", "title", "description", "image", "image_preview")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        """Display image preview in admin panel."""
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;"/>', obj.image.url)
        return "No Image"

    image_preview.short_description = "Preview"


@admin.register(MaskingProcess)
class MaskingProcessAdmin(admin.ModelAdmin):
    """Admin configuration for MaskingProcess."""
    list_display = ("part_number", "masking_description", "created_at")
    search_fields = ("part_number", "masking_description")
    list_filter = ("created_at",)
    ordering = ("part_number",)
    inlines = [MaskingStepInline]


@admin.register(MaskingStep)
class MaskingStepAdmin(admin.ModelAdmin):
    """Admin configuration for MaskingStep (Only deletable via admin)."""
    list_display = ("step_number", "title", "masking_process", "image_preview")
    search_fields = ("title", "description", "masking_process__part_number")
    list_filter = ("masking_process",)
    ordering = ("masking_process", "step_number")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        """Display image preview in admin panel."""
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;"/>', obj.image.url)
        return "No Image"

    image_preview.short_description = "Preview"
