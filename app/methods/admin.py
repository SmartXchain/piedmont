from django.contrib import admin
from django.forms.models import BaseInlineFormSet

from .models import Method, ParameterToBeRecorded


class ParameterInlineFormSet(BaseInlineFormSet):
    """
    Inline formset for ParameterToBeRecorded under a Method.
    We automatically attach each parameter row to the parent Method,
    so the user doesn't have to (and can't accidentally link to the wrong Method).
    """

    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        parent_method = self.instance

        # Force the FK
        obj.method = parent_method

        if commit:
            obj.save()
        return obj

    def save_existing(self, form, instance, commit=True):
        obj = super().save_existing(form, instance, commit=False)
        parent_method = self.instance

        # Re-enforce FK in case user tried to change it somehow
        obj.method = parent_method

        if commit:
            obj.save()
        return obj


class ParameterInline(admin.TabularInline):
    model = ParameterToBeRecorded
    formset = ParameterInlineFormSet
    extra = 1

    # We do NOT show the 'method' foreign key in the inline row.
    # We'll display only what QA actually cares about for the traveler.
    fields = (
        'title',
        'description',
        'unit',
        'is_nadcap_required',
    )

    # no autocomplete_fields here; we handle FK assignment in the formset


@admin.register(Method)
class MethodAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'method_type',
        'tank_name',
        'chemical',
        'is_rectified',
        'is_strike_etch',
        'is_masking_operation',
        'is_bake_operation',
        'is_hydrogen_relief_operation',
        'has_parameters',
    )

    list_filter = (
        'method_type',
        'is_rectified',
        'is_masking_operation',
        'is_bake_operation',
        'is_hydrogen_relief_operation',
    )

    search_fields = (
        'title',
        'description',
        'tank_name',
        'chemical',
    )

    ordering = ('title',)

    inlines = [ParameterInline]

    fieldsets = (
        ('General Info', {
            'fields': (
                'method_type',
                'title',
                'description',
            ),
        }),

        ('Operation Flags / Routing', {
            'fields': (
                'is_masking_operation',
                'is_bake_operation',
                'is_hydrogen_relief_operation',
            ),
            'description': (
                "These flags drive traveler formatting and downstream routing. "
                "• Masking steps group under masking cell. "
                "• Bake steps get bake signoff blocks. "
                "• Hydrogen embrittlement relief is called out separately."
            ),
        }),

        ('Tank / Process Details', {
            'fields': (
                'tank_name',
                ('temp_min', 'temp_max'),
                ('immersion_time_min', 'immersion_time_max'),
                'chemical',
                'is_rectified',
                'is_strike_etch',
            ),
            'classes': ('collapse', 'tank-details-section'),
            'description': (
                "For processing_tank steps. If this is manual (tape masking, racking, etc.), "
                "you can leave these blank."
            ),
        }),

        ('Rectifier / Electrical Notes', {
            'fields': (
                'rectifier_notes',
            ),
            'classes': ('collapse',),
            'description': (
                "ASF, current density, polarity, ramp instructions, etc. "
                "Shown to operators for plating/electroclean steps."
            ),
        }),
    )

    class Media:
        # You already had this. Keeping in case you have custom JS that toggles
        # .tank-details-section based on method_type in the admin form.
        js = [
            'admin/js/jquery.init.js',
            'methods/js/toggle_tank_fields.js',
        ]

    def has_parameters(self, obj):
        return obj.recorded_parameters.exists()
    has_parameters.boolean = True
    has_parameters.short_description = "Has Required Recordables?"

