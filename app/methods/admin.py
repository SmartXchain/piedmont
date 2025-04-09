from django.contrib import admin
from .models import Method, ParameterToBeRecorded


class ParameterInline(admin.TabularInline):
    model = ParameterToBeRecorded
    extra = 1
    autocomplete_fields = ['method']


@admin.register(Method)
class MethodAdmin(admin.ModelAdmin):
    list_display = ('title', 'method_type', 'tank_name', 'chemical', 'is_rectified', 'has_parameters')
    list_filter = ('method_type', 'is_rectified')
    search_fields = ('title', 'description', 'tank_name', 'chemical')
    ordering = ('title',)
    inlines = [ParameterInline]

    fieldsets = (
        ('General Info', {
            'fields': ('method_type', 'title', 'description'),
        }),
        ('Tank Details (Visible for Processing Tanks)', {
            'fields': (
                'tank_name',
                ('temp_min', 'temp_max'),
                ('immersion_time_min', 'immersion_time_max'),
                'chemical',
                'is_rectified',
            ),
            'classes': ('collapse', 'tank-details-section'),  # Collapsed by default for manual methods
        }),
    )

    class Media:
        js = ['admin/js/jquery.init.js', 'methods/js/toggle_tank_fields.js']

    def has_parameters(self, obj):
        return obj.parametertoberecorded_set.exists()
    has_parameters.boolean = True
    has_parameters.short_description = "Has Parameters?"
