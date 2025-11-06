from django.contrib import admin
from django.forms.models import BaseInlineFormSet

from .models import Method, ParameterToBeRecorded, ParameterTemplate


# ----- Inline for per-method recordables -----

class ParameterInlineFormSet(BaseInlineFormSet):
    """
    Tie ParameterToBeRecorded rows to the parent Method automatically.
    """
    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        parent_method = self.instance
        obj.method = parent_method
        if commit:
            obj.save()
        return obj

    def save_existing(self, form, instance, commit=True):
        obj = super().save_existing(form, instance, commit=False)
        parent_method = self.instance
        obj.method = parent_method
        if commit:
            obj.save()
        return obj


class ParameterInline(admin.TabularInline):
    model = ParameterToBeRecorded
    formset = ParameterInlineFormSet
    extra = 1
    fields = ("title", "description", "unit", "is_nadcap_required")
    # we don't expose 'method' here — FK is set in formset


# ----- Method admin -----

@admin.register(Method)
class MethodAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "method_type",
        "tank_name",
        "chemical",
        "is_rectified",
        "is_strike_etch",
        "is_masking_operation",
        "is_bake_operation",
        "is_hydrogen_relief_operation",
        "has_parameters",
    )

    list_filter = (
        "category",
        "method_type",
        "is_rectified",
        "is_masking_operation",
        "is_bake_operation",
        "is_hydrogen_relief_operation",
    )

    search_fields = (
        "title",
        "description",
        "tank_name",
        "chemical",
    )

    ordering = ("title",)

    inlines = [ParameterInline]

    fieldsets = (
        ("General Info", {
            "fields": (
                "method_type",
                "title",
                "category",     # <--- new: normalized bucket from TITLE_CHOICES
                "description",
            ),
            "description": "Title is your free text (prod). Category drives default parameters.",
        }),

        ("Operation Flags / Routing", {
            "fields": (
                "is_masking_operation",
                "is_bake_operation",
                "is_hydrogen_relief_operation",
            ),
            "description": (
                "These flags affect traveler layout and special signoff blocks."
            ),
        }),

        ("Tank / Process Details", {
            "fields": (
                "tank_name",
                ("temp_min", "temp_max"),
                ("immersion_time_min", "immersion_time_max"),
                "chemical",
                "is_rectified",
                "is_strike_etch",
            ),
            "classes": ("collapse",),
            "description": "Fill this out for processing-tank steps; leave blank for manual methods.",
        }),

        ("Rectifier / Electrical Notes", {
            "fields": ("rectifier_notes",),
            "classes": ("collapse",),
        }),
    )

    class Media:
        # keep your custom JS if you use it to show/hide tank fields
        js = [
            "admin/js/jquery.init.js",
            "methods/js/toggle_tank_fields.js",
        ]

    def has_parameters(self, obj):
        return obj.recorded_parameters.exists()
    has_parameters.boolean = True
    has_parameters.short_description = "Has Record Blanks?"


# ----- Parameter template admin -----

@admin.register(ParameterTemplate)
class ParameterTemplateAdmin(admin.ModelAdmin):
    """
    Master list: for each category (Anodize, Electroplating...), define the
    standard parameters that should be auto-created for new Methods in that category.
    """
    list_display = ("category", "description", "unit", "is_nadcap_required")
    list_filter = ("category", "is_nadcap_required")
    search_fields = ("description",)
    ordering = ("category",)

