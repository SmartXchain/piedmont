from django.contrib import admin
# Ensure all models are imported
from .models import Method, ParameterToBeRecorded, ParameterTemplate
# You may need to import format_html if you use it in other functions not shown here


@admin.action(description="Backfill recorded parameters from templates")
def backfill_parameters(modeladmin, request, queryset):
    for method in queryset:
        if method.category and not method.recorded_parameters.exists():
            method.create_required_parameters_from_template()

# ----------------------------------------------------------------------
# 1. Define Inline for ParameterToBeRecorded
# ----------------------------------------------------------------------


class ParameterInline(admin.TabularInline):
    """Allows managing ParameterToBeRecorded instances within the MethodAdmin."""
    model = ParameterToBeRecorded
    # Since you removed the 'unit' field, ensure 'fields' reflects this.
    fields = ('description', 'is_nadcap_required')
    extra = 0  # Don't show extra blank rows by default
    verbose_name_plural = "Recorded Parameters for this Method"

    # Optional: Display parameter units/type if needed for context
    # readonly_fields = ('some_calculated_field',)


# ----------------------------------------------------------------------
# 2. Method Admin
# ----------------------------------------------------------------------

@admin.register(Method)
class MethodAdmin(admin.ModelAdmin):
    inlines = [ParameterInline]

    # Enhanced list display to show key flags
    list_display = (
        "title",
        "category",
        "method_type",
        "is_rectified",
        "is_masking_operation",
    )

    # Separate fieldsets for organization
    fieldsets = (
        ("General Details", {
            "fields": ('title', 'category', 'method_type', 'description'),
        }),
        ("Tank Parameters", {
            "fields": ('tank_name', ('temp_min', 'temp_max'), ('immersion_time_min', 'immersion_time_max'), 'chemical', 'rectifier_notes'),
            "classes": ('collapse',)  # Collapse this section by default
        }),
        ("Operation Flags", {
            "fields": ('is_rectified', 'is_strike_etch', 'is_masking_operation', 'is_stress_relief_operation', 'is_hydrogen_relief_operation'),
        }),
        ("Process Time", {
            "fields": ('touch_time_min', 'touch_time_max', 'run_time_min', 'run_time_max'),
        }),
    )
    ordering = ("title",)
    actions = [backfill_parameters]

# ----------------------------------------------------------------------
# 3. Parameter Template Admin (Kept as is)
# ----------------------------------------------------------------------


@admin.register(ParameterTemplate)
class ParameterTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "category",
        "description",
        "is_nadcap_required"
    )
    ordering = ("category",)
