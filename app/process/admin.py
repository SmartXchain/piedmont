# process/admin.py
from django.contrib import admin
from .models import Process, ProcessStep
from .forms import ProcessForm, ProcessStepInlineForm
from django.utils.html import format_html


class ProcessStepInline(admin.TabularInline):
    model = ProcessStep
    form = ProcessStepInlineForm
    extra = 1
    ordering = ('step_number',)
    fields = ('step_number', 'method')
    readonly_fields = ['method_details']

    @admin.display(description='Method Details')
    def method_details(self, obj):
        if obj.method:
            return format_html(
                "<strong>Category:</strong>{}<br/>"
                "<strong>Type:</strong>{}<br/>"
                "Time: {}–{} min, Temp: {}–{}°F",
                obj.method.category or 'N/A',
                obj.method.method_type,
                obj.method.immersion_time_min or '-',
                obj.method.immersion_time_max or '-',
                obj.method.temp_min or '-',
                obj.method.temp_max or '-'
            )
        return "-"

    class Media:
        js = [
            'admin/js/jquery.init.js',
        ]


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    form = ProcessForm
    list_display = ('standard', 'classification', 'created_at')
    list_filter = ('standard',)
    search_fields = ('standard__name',)
    inlines = [ProcessStepInline]

    @admin.display(description='Steps', ordering='_step_count')
    def step_count_display(self, obj):
        """Displays the count of ProcessSteps for this Process."""
        # This performs a query, but it's very useful for the list view
        count = obj.steps.count()
        if count == 0:
            return format_html('<span style="color: red;">{}</span>', count)
        return count
